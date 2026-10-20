# Sugerencias ejecutables — activación explícita

Base: `7fe531f2a4250aaf0b2d537987d92a45c1671fec`. **El PR añade helpers; NO modifica el notebook ni las salidas entregadas.** Mantener borrador hasta verificar las pruebas contra el notebook íntegro y una ejecución pequeña en el entorno del equipo. Ningún resultado de estas contribuciones se atribuye retroactivamente al trabajo original.

## C1: re-puntuar respuestas guardadas sin volver a llamar a modelos

Desde la raíz del repo, con Python 3.10+:

```bash
python review/m3/sugerencias/rescore_saved.py --m3 M3 --salida /ruta/nueva/revision_medidor.json
```

`source_loader.py` verifica el hash del notebook inspeccionado, extrae únicamente definiciones de §5 y usa sus umbrales declarados (0.60 / 4.0 / 0.40). No ejecuta cargas, demos ni entrenamientos. Si cambió el notebook, se detiene: revisar la fuente antes de adaptar el hash.

`evaluation_review.py` crea un espacio separado del medidor, corrige coincidencias acotadas y conserva los resultados históricos. `politica_eval.json` explicita la cobertura por sistema: el caso de café sigue fuera del dominio del baseline sin RAG, pero su criterio histórico de abstención no aplica a la biblioteca M3. Se informa como no aplicable, no como acierto. Confirmar esa política antes de interpretar la nueva vista. No se reescribe `eval_set.json`.

Se guardan ambos denominadores y resultados, con versión de política y causas de no aplicabilidad. Las reglas son heurísticas, no sustituyen juicio agronómico. Los valores sim/juez reutilizados están redondeados en el artefacto; revisar decisiones próximas a un umbral. No atribuir el cambio de puntaje al sistema: cambió el medidor. El archivo de salida se crea con modo exclusivo y no se sobrescribe.

## C2: probar validación y conflicto de cultivo en una copia

```bash
python review/m3/sugerencias/prepare_workcopy.py --m3 M3 --destino /ruta/fuera_del_repo/agro_revision
```

El destino debe ser nuevo y no estar dentro de M3 ni ser su antecesor. Se copia M3, se omiten `.env` y `.git`, se conservan respaldos `.entregado` de los artefactos superiores y se crea `notebookM3_revision.ipynb` sin outputs. El notebook entregado no se modifica. No cambiar de nombre los respaldos para presentarlos como corridas nuevas.

Abrir la copia en **un kernel nuevo**, con su directorio como directorio de trabajo. El script inserta `tools_review.install(globals())` después de definir `responder_con_tools` y antes de sus demos. Esta instalación adapta diagnóstico, observación, final y despacho: ReAct sigue usando las funciones existentes, pero detiene el recorrido ante el nuevo estado `conflicto_cultivo`. La generación, el ranking y los modelos originales se conservan.

La validación detecta `args` incorrecto, campos no definidos y valores no textuales; una llamada inválida devuelve observación de validación, y el modo de un turno conserva su fallback. Los errores de ejecución de llamadas válidas se propagan. Se pide aclaración si el planificador contradice el texto, aparecen varios cultivos o la ficha elegida corresponde a otro. La comparación es por alias conocidos; no interpreta exhaustivamente todo lenguaje natural.

La copia de trabajo conserva el evaluador original para distinguir el cambio del sistema. Después se puede aplicar C1 a las respuestas nuevas y a las antiguas por separado, siempre con políticas y denominadores comparables. No leer un delta entre protocolos distintos como ganancia de generación.

## Pruebas

```bash
python -m unittest discover -s review/m3/tests -p test_revision.py -v
```

Por defecto, la suite verifica el notebook original completo y extrae las funciones mediante AST, sin cargas de modelos. La ejecución local de la docente usó `AGRO_REVIEW_FIXTURE` y un fixture parcial transcrito por bloqueo de descarga. **Ese modo parcial no verifica el blob original**; quedó identificado en la salida. Las 45 pruebas aprobaron en ese alcance. El fixture no se usa por defecto en el checkout.

Pendiente antes de fusionar: repetir la suite sin el modo fixture, inspeccionar la copia generada, ejecutar con las dependencias del equipo y comprobar el contrato de cada consumidor. No se ha ejecutado el notebook completo, descargado modelos o llamado Groq en la validación docente. No se certifica seguridad agronómica ni equivalencia numérica end-to-end.
