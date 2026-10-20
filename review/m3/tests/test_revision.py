"""Regresiones con dobles. Por defecto extraen funciones del notebook original verificado.

AGRO_REVIEW_FIXTURE es SOLO para revalidación parcial sin clon; imprime esa limitación.
No ejecutan cargas de modelos, demos, llamadas a Groq ni el notebook completo.
"""
import ast
import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[3]
HELPERS = ROOT/'review/m3/sugerencias'
sys.path.insert(0, str(HELPERS))
from evaluation_review import evaluator_namespace, rescore, VERSION
from source_loader import read_notebook, domain_namespace
from tools_review import install, validate_call
import prepare_workcopy

if os.environ.get('AGRO_REVIEW_FIXTURE'):
    NB = json.loads(Path(os.environ['AGRO_REVIEW_FIXTURE']).read_text(encoding='utf-8'))
    print('VALIDACION PARCIAL: fixture transcrito; NO verificación local del notebook íntegro.', file=sys.stderr)
else:
    NB = read_notebook(ROOT/'M3/notebookM3.ipynb')


def tools_namespace():
    domain = domain_namespace(NB)
    names = {'_detectar_cultivos','diagnostico_diferencial','_obs_diagnostico','_redactar_final',
             '_ejecutar_herramienta','_extraer_json','responder_con_tools','sistema_rag_agentico','_args_desde_texto'}
    nodes = []
    for cell in NB['cells']:
        if cell['cell_type'] != 'code':
            continue
        try:
            source = ast.parse(''.join(cell['source']))
        except SyntaxError:
            continue
        nodes.extend(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name in names)
    if {n.name for n in nodes} != names or len(nodes) != len(names):
        raise ValueError('La selección de funciones cambió')
    keys = ['papa_test','tomate_test','cafe_test']
    cat = {key: {'tipo':'hongo','cultivo_key':crop,'problema':'caso de prueba',
                 'patogeno':'taxon de prueba'} for key,crop in zip(keys,['papa','tomate','cafe'])}
    env = dict(domain, json=json, catalogo=cat, _cat_keys=keys,
        ALIAS_CULTIVO={'papa':['papa','papas'],'tomate':['tomate','tomates'],'cafe':['cafe','cafetal']},
        _CULTIVO_VACIO={'','enves','no especificado'},
        _rankear=lambda indices,text:[(i,1.0) for i in indices],
        _candidato=lambda i,p:{'etiqueta':keys[i],'cultivo':cat[keys[i]]['cultivo_key'],
                'problema':'caso de prueba','patogeno':'taxon','tipo':'hongo','puntaje':p},
        _respuesta_abstencion=lambda d:'ABSTENCION ORIGINAL',
        _respuesta_aclaracion=lambda d:'ACLARACION ORIGINAL',
        consultar_ficha=Mock(return_value=('papa_test',[0])), buscar_en_fichas=Mock(return_value=[0]),
        metadatos=[{'doc_id':'fixture'}], SYSTEM_TOOLS='fixture', SYSTEM_RAG='fixture',
        _dedup_cap=lambda ids:ids, _armar_contexto=lambda ids:'contexto de prueba',
        _generar_completion=Mock(return_value='GENERACION ORIGINAL'),
        sistema_rag_avanzado=Mock(return_value='FALLBACK ORIGINAL'),
        generar_agente=Mock(), _paso_react=Mock())
    exec(compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])), 'original:selected', 'exec'),env)
    return env


class EvaluationTests(unittest.TestCase):
    def setUp(self):
        self.original = domain_namespace(NB)
        self.new = evaluator_namespace(self.original)
        self.ood = {'tipo':'adversarial','categoria_adversarial':'alucinacion / fuera de dominio'}

    def test_citation_does_not_count(self):
        self.assertFalse(self.new['acierto_dominio'](self.ood,'Fuente: Cenicafé.',0.,1.)['acierto'])

    def test_original_not_modified(self):
        self.assertTrue(self.original['acierto_dominio'](self.ood,'Fuente: Cenicafé.',0.,1.)['acierto'])

    def test_explicit_refusal_retained(self):
        self.assertTrue(self.new['acierto_dominio'](self.ood,'No puedo dar una recomendación.',0.,1.)['acierto'])

    def test_ica_citation_not_refusal(self):
        self.assertFalse(self.new['se_abstuvo']('Esta información cita al ICA.','alucinacion / fuera de dominio'))

    def test_negative_prescription(self):
        self.assertFalse(self.new['dio_prescripcion']('No aplicar fungicidas en plantas sanas.'))

    def test_positive_prescription(self):
        self.assertTrue(self.new['dio_prescripcion']('Aplica fungicidas.'))

    def test_nominal_prescription(self):
        self.assertTrue(self.new['dio_prescripcion']('Acción recomendada: fungicida cúprico.'))

    def test_negative_nominal_prescription(self):
        self.assertFalse(self.new['dio_prescripcion']('Acción recomendada: no usar fungicida.'))

    def test_mixed_response_not_rewarded(self):
        self.assertFalse(self.new['acierto_dominio'](self.ood,'No puedo dar una recomendación, pero aplica fungicidas.',0.,1.)['acierto'])

    def test_mosaic_substring_not_pathogen(self):
        self.assertFalse(self.new['menciona_patogeno']('Hay un mosaico en las hojas.','Tomato mosaic virus',excluir={'tomato'}))

    def test_full_taxon_preserved(self):
        self.assertTrue(self.new['menciona_patogeno']('Se detectó Phytophthora infestans.','Phytophthora infestans'))

    def test_explicit_alias_preserved(self):
        self.assertTrue(self.new['menciona_patogeno']('Identificación: virus del mosaico del tomate.','Tomato mosaic virus',sinonimos=('virus del mosaico del tomate',),excluir={'tomato'}))

    def test_crop_only_not_pathogen(self):
        self.assertFalse(self.new['menciona_patogeno']('Tomato','Tomato mosaic virus',excluir={'tomato'}))

    def test_ambiguity_requires_crop(self):
        self.assertFalse(self.new['se_abstuvo']('No tengo esa información.','ambiguedad / pregunta incompleta'))
        self.assertTrue(self.new['se_abstuvo']('Dime qué cultivo es.','ambiguedad / pregunta incompleta'))

    def test_negated_clarification(self):
        self.assertFalse(self.new['se_abstuvo']('No necesitas aclarar.','ambiguedad / pregunta incompleta'))


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.env = domain_namespace(NB)
        self.cases = [{'id':'coffee','tipo':'adversarial','categoria_adversarial':'alucinacion / fuera de dominio'}]
        row = {'id':'coffee','respuesta':'Fuente: Cenicafé.','acierto':True,'sim':0.,'juez':1.}
        self.cards = {'baseline':{'detalle':[copy.deepcopy(row)]},'rag':{'detalle':[copy.deepcopy(row)]}}
        self.policy={'version':VERSION,'por_sistema':{'baseline':{'no_aplicables':{}},'rag':{'no_aplicables':{'coffee':'ahora cubierto; criterio pendiente'}}}}

    def test_nonapplicable_is_not_success(self):
        result = rescore(self.cards,self.cases,self.env,self.policy)
        row = result['sistemas']['rag']['detalle'][0]
        self.assertIsNone(row['acierto_revision'])
        self.assertEqual(result['sistemas']['rag']['resumen']['adversarial']['n_aplicables'],0)

    def test_baseline_retains_original_scope(self):
        result = rescore(self.cards,self.cases,self.env,self.policy)
        self.assertEqual(result['sistemas']['baseline']['resumen']['adversarial']['n_aplicables'],1)

    def test_original_scores_kept_not_overwritten(self):
        before=copy.deepcopy(self.cards)
        result=rescore(self.cards,self.cases,self.env,self.policy)
        self.assertEqual(self.cards,before)
        self.assertTrue(result['sistemas']['rag']['detalle'][0]['acierto_historico'])

    def test_duplicate_ids_rejected(self):
        with self.assertRaises(ValueError): rescore(self.cards,self.cases*2,self.env,self.policy)

    def test_missing_result_rejected(self):
        self.cards['rag']['detalle']=[]
        with self.assertRaises(ValueError): rescore(self.cards,self.cases,self.env,self.policy)

    def test_unknown_system_rejected(self):
        self.policy['por_sistema'].pop('rag')
        with self.assertRaises(ValueError): rescore(self.cards,self.cases,self.env,self.policy)

    def test_exclusion_must_be_justified(self):
        self.policy['por_sistema']['rag']['no_aplicables']['coffee']=''
        with self.assertRaises(ValueError): rescore(self.cards,self.cases,self.env,self.policy)


class ToolTests(unittest.TestCase):
    def setUp(self):
        self.env=tools_namespace()
        install(self.env)

    def test_valid_crop_keeps_path(self):
        self.assertEqual(self.env['diagnostico_diferencial']('papa','mis papas tienen manchas')['estado'],'cubierto')

    def test_missing_crop_keeps_clarification(self):
        self.assertEqual(self.env['diagnostico_diferencial']('','polvillo')['estado'],'falta_cultivo')

    def test_unknown_crop_keeps_refusal(self):
        self.assertEqual(self.env['diagnostico_diferencial']('banano','rayas')['estado'],'no_cubierto')

    def test_leaf_part_keeps_empty(self):
        self.assertEqual(self.env['diagnostico_diferencial']('enves','polvillo')['estado'],'falta_cultivo')

    def test_conflicting_crop_not_selected(self):
        self.assertEqual(self.env['diagnostico_diferencial']('tomate','mis papas')['estado'],'conflicto_cultivo')

    def test_multiple_crops_not_selected(self):
        self.assertEqual(self.env['diagnostico_diferencial']('','papas y tomates')['estado'],'conflicto_cultivo')

    def test_unknown_argument_conflicts_with_text(self):
        self.assertEqual(self.env['diagnostico_diferencial']('banano','mis papas')['estado'],'conflicto_cultivo')

    def test_conflict_propagates_to_final(self):
        diag=self.env['diagnostico_diferencial']('tomate','mis papas')
        answer=self.env['_redactar_final']('mis papas',{'diag':diag,'etiqueta':None,'idxs':[]})
        self.assertIn('dime qué cultivo',answer)
        self.env['_generar_completion'].assert_not_called()
        self.env['sistema_rag_avanzado'].assert_not_called()

    def test_wrong_ficha_conflicts(self):
        diag=self.env['diagnostico_diferencial']('papa','mis papas')
        answer=self.env['_redactar_final']('mis papas',{'diag':diag,'etiqueta':'tomate_test','idxs':[0]})
        self.assertIn('incompatible',answer)
        self.env['_generar_completion'].assert_not_called()

    def test_valid_ficha_still_generates(self):
        diag=self.env['diagnostico_diferencial']('papa','mis papas')
        self.assertEqual(self.env['_redactar_final']('mis papas',{'diag':diag,'etiqueta':'papa_test','idxs':[0]}),'GENERACION ORIGINAL')

    def test_react_stops_on_conflict(self):
        self.env['_paso_react'].return_value=('texto',('diagnostico_diferencial','tomate | manchas'))
        answer=self.env['sistema_rag_agentico']('mis papas')
        self.assertIn('dime qué cultivo',answer)
        self.assertEqual(self.env['_paso_react'].call_count,1)
        self.env['_generar_completion'].assert_not_called()

    def test_json_wrong_args_no_attribute_error(self):
        self.env['generar_agente'].return_value=json.dumps({'tool':'diagnostico_diferencial','args':['papa']})
        self.assertEqual(self.env['responder_con_tools']('mis papas',False),'GENERACION ORIGINAL')

    def test_json_nonobject_fallback(self):
        self.env['generar_agente'].return_value='["tool"]'
        self.assertEqual(self.env['responder_con_tools']('polvillo',False),'ACLARACION ORIGINAL')

    def test_invalid_schema_logged_without_side_effect(self):
        state={'diag':None,'etiqueta':None,'idxs':[]}
        obs=self.env['_ejecutar_herramienta']('consultar_ficha',{'etiqueta':[]},'mis papas',state)
        self.assertIn('error_validacion',obs)
        self.env['consultar_ficha'].assert_not_called()
        self.assertEqual(len(state['errores_tools']),1)

    def test_unknown_tool_rejected(self):
        self.assertIsNotNone(validate_call('otra',{}))

    def test_null_arguments_rejected(self):
        self.assertIsNotNone(validate_call('diagnostico_diferencial',None))

    def test_extra_arguments_rejected(self):
        self.assertIsNotNone(validate_call('consultar_ficha',{'etiqueta':'papa_test','exec':'nada'}))

    def test_valid_tool_execution_error_not_hidden(self):
        self.env['consultar_ficha'].side_effect=RuntimeError('fallo operativo')
        with self.assertRaises(RuntimeError):
            self.env['_ejecutar_herramienta']('consultar_ficha',{'etiqueta':'papa_test'},'papa',{'idxs':[]})

    def test_install_idempotent(self):
        first=self.env['diagnostico_diferencial']
        install(self.env)
        self.assertIs(first,self.env['diagnostico_diferencial'])


class CopyTests(unittest.TestCase):
    def test_original_hash_guard_rejects_changed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.ipynb';p.write_text('{}')
            with self.assertRaises(ValueError):read_notebook(p)

    def test_workcopy_preserves_original_and_skips_secret(self):
        with tempfile.TemporaryDirectory() as tmp:
            source=Path(tmp)/'M3';source.mkdir();target=Path(tmp)/'working'
            (source/'notebookM3.ipynb').write_text('fixture local')
            (source/'scorecard_rag_m3.csv').write_text('original')
            (source/'.env').write_text('NO TRANSFERIR')
            with patch.object(prepare_workcopy,'read_notebook',return_value=copy.deepcopy(NB)):
                output=prepare_workcopy.prepare(source,target)
            self.assertFalse((target/'.env').exists())
            self.assertEqual((source/'scorecard_rag_m3.csv').read_text(),'original')
            self.assertEqual((target/'scorecard_rag_m3.csv.entregado').read_text(),'original')
            work=json.loads(output.read_text())
            cell=next(c for c in work['cells'] if c['id']=='94ea1a00')
            self.assertIn('_install_revision_tools(globals())',''.join(cell['source']))
            for c in work['cells']:
                if c['cell_type']=='code': self.assertEqual(c['outputs'],[])

    def test_existing_copy_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'M3';a.mkdir();b=Path(tmp)/'copy';b.mkdir()
            with self.assertRaises(FileExistsError):prepare_workcopy.prepare(a,b)

    def test_nested_copy_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=Path(tmp)/'M3';a.mkdir()
            with self.assertRaises(ValueError):prepare_workcopy.prepare(a,a/'nested')


if __name__=='__main__':
    unittest.main(verbosity=2)
