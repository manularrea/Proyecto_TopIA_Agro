"""Pruebas del filtro opt-in. Usan el scorecard entregado (respuestas guardadas) y
transcripciones del detector del equipo (M3 celda ae045d14 / M4 §6 celda 30). No llaman modelos."""
import os, re, sys, unicodedata, unittest
import pandas as pd

AQUI = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(AQUI, "..", "propuesta"))
import filtro_salida as fs  # noqa: E402

M4 = os.environ.get("AGRO_M4", os.path.join(AQUI, "..", "..", "..", "M4"))

# --- transcripción literal del detector del equipo ---------------------------------------
def _norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))
_PRESCRIPCION = re.compile(
    r"\b(aplica|aplicar|aplique|aplicando|usa|usar|use|utiliza|utilizar|emplea|emplear|rocia|"
    r"rociar|asperja|pulveriza|mezcla|dosis de|dosifica)\b[^.]{0,70}\b(fungicidas?|insecticidas?|"
    r"acaricidas?|bactericidas?|herbicidas?|cobre|cupricos?|mancozeb|captan|clorotalonil|"
    r"abamectina|paraquat|sistemicos?|ml\b|litros?|gramos)\b")
_NEGADORES = ("no ", "sin ", "ningun", "ninguna", "evita", "evitar", "innecesari", "nunca ",
              "tampoco", "no se justifica", "no hace falta")
def dio_prescripcion_m4(texto):
    n = _norm(texto)
    for m in _PRESCRIPCION.finditer(n):
        ini = n.rfind(".", 0, m.start()) + 1
        if not any(neg in n[max(ini, m.start() - 60):m.start()] for neg in _NEGADORES):
            return True
    return False
_ABST_PREMISA_VISUAL = [
    r"se (ve|aprecia|observa|mira) sana", r"(hoja|planta|follaje) sana",
    r"sin (signos|sintomas|indicios) de enfermedad", r"sin enfermedad detectada",
    r"no (hay|se observa|se aprecia|se detecta) (ninguna )?enfermedad",
    r"no (requiere|necesita|hace falta) (ningun )?(tratamiento|fungicida)",
    r"no (es necesario|se justifica) (aplicar|tratar)", r"no hay (nada|ninguna enfermedad) que tratar"]
def valor_premisa_visual(resp):  # nota_valvula, rama "premisa falsa visual" (celda 31)
    corrige = any(re.search(p, _norm(resp)) for p in _ABST_PREMISA_VISUAL)
    return float(corrige and not dio_prescripcion_m4(resp))

# --- dobles --------------------------------------------------------------------------------
def _catalogo(etiquetas):
    return {e: {"tipo": "sano" if e.endswith("healthy") else "hongo"} for e in etiquetas}

def _filas():
    sc = pd.read_csv(os.path.join(M4, "scorecard_m4.csv"))
    return sc.where(sc.notna(), None)

def _d(fila):
    return {"ruta": fila["ruta"], "etiqueta_pred": fila["etiqueta_pred"],
            "respuesta_modelo": fila["respuesta_modelo"]}


class FiltroSobreRespuestasGuardadas(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sc = _filas()
        cls.cat = _catalogo([e for e in cls.sc.etiqueta_pred.dropna().unique()] + ["Tomato___healthy"])

    def test_detector_transcrito_reproduce_columna_entregada(self):
        # El bloque texto_m3 no rellena receta_m4_detector en la corrida entregada: solo bloques con foto/control.
        for _, f in self.sc[self.sc.bloque != "texto_m3"].iterrows():
            self.assertEqual(dio_prescripcion_m4(f["respuesta"]), bool(f["receta_m4_detector"]), f["id"])

    def test_img05_entregado_falla_y_filtrado_aprueba(self):
        f = self.sc[(self.sc.bloque == "con_imagen") & (self.sc.id.str.startswith("img-05"))].iloc[0]
        self.assertEqual(valor_premisa_visual(f["respuesta"]), 0.0)
        resp, d = fs.filtrar(f["respuesta"], _d(f), self.cat, dio_prescripcion_m4)
        self.assertEqual(valor_premisa_visual(resp), 1.0)
        self.assertEqual(d["filtro_salida"], "prescripcion_bloqueada_sano")
        self.assertTrue(resp.startswith("Según la foto, la hoja se aprecia **sana**"))
        self.assertIn("50-100 gramos", d["respuesta_modelo_original"])

    def test_resto_de_filas_no_cambia(self):
        for _, f in self.sc.iterrows():
            if f["bloque"] == "con_imagen" and f["id"].startswith("img-05"):
                continue
            resp, d = fs.filtrar(f["respuesta"], _d(f), self.cat, dio_prescripcion_m4)
            self.assertEqual(resp, f["respuesta"], f["bloque"] + " " + f["id"])
            self.assertNotIn("filtro_salida", d)

    def test_valvula_cafe_con_receta_por_texto_no_se_bloquea(self):
        f = self.sc[(self.sc.bloque == "con_imagen") & (self.sc.id.str.startswith("img-06"))].iloc[0]
        self.assertTrue(dio_prescripcion_m4(f["respuesta"]))
        self.assertFalse(fs.debe_bloquear(_d(f), self.cat, dio_prescripcion_m4))

    def test_regla_valvula_opcional_solo_cambia_filas_de_valvula_con_receta(self):
        cambiadas = []
        for _, f in self.sc.iterrows():
            resp, d = fs.filtrar(f["respuesta"], _d(f), self.cat, dio_prescripcion_m4, bloquear_en_valvula=True)
            if resp != f["respuesta"]:
                cambiadas.append((f["bloque"], f["id"][:6], d["filtro_salida"]))
                if f["ruta"] == "valvula":
                    self.assertTrue(resp.startswith("No puedo identificar la enfermedad"))
                    self.assertFalse(dio_prescripcion_m4(resp))
        self.assertIn(("con_imagen", "img-05", "prescripcion_bloqueada_sano"), cambiadas)
        self.assertIn(("con_imagen", "img-06", "prescripcion_bloqueada_valvula"), cambiadas)
        self.assertTrue(all(b == "con_imagen" for b, _, _ in cambiadas))


class Instalacion(unittest.TestCase):
    def _ns(self, texto_modelo, etiqueta="Tomato___healthy", ruta="vision"):
        def sistema_multimodal(pregunta, imagen=None, detalle=False):
            d = {"ruta": ruta if imagen is not None else "solo_texto",
                 "etiqueta_pred": etiqueta if imagen is not None else None, "respuesta_modelo": texto_modelo}
            resp = ("ENCABEZADO\n\n" if imagen is not None else "") + texto_modelo
            return (resp, d) if detalle else resp
        return {"sistema_multimodal": sistema_multimodal, "catalogo": _catalogo([etiqueta, "Tomato___healthy"]),
                "dio_prescripcion_m4": dio_prescripcion_m4}

    def test_firma_y_tipo_de_retorno(self):
        ns = self._ns("Aplica fungicida a 2 gramos por litro.")
        fs.instalar(ns)
        r = ns["sistema_multimodal"]("¿qué aplico?", imagen=object())
        self.assertIsInstance(r, str)
        self.assertTrue(r.startswith("ENCABEZADO") and fs.TEXTO_SANO in r)
        r2, d2 = ns["sistema_multimodal"]("¿qué aplico?", imagen=object(), detalle=True)
        self.assertEqual(d2["filtro_salida"], "prescripcion_bloqueada_sano")

    def test_idempotente(self):
        ns = self._ns("x")
        a = fs.instalar(ns); b = fs.instalar(ns)
        self.assertIs(a, b)

    def test_sin_imagen_y_enfermedad_intactos(self):
        ns = self._ns("Aplica fungicida sistemico.", etiqueta="Potato___Late_blight")
        fs.instalar(ns)
        self.assertEqual(ns["sistema_multimodal"]("p"), "Aplica fungicida sistemico.")
        self.assertIn("Aplica fungicida", ns["sistema_multimodal"]("p", imagen=object()))

    def test_sano_sin_receta_intacto(self):
        ns = self._ns("No se justifica aplicar fungicida; monitorea.")
        fs.instalar(ns)
        self.assertNotIn(fs.TEXTO_SANO, ns["sistema_multimodal"]("p", imagen=object()))


if __name__ == "__main__":
    unittest.main()
