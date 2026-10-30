"""Pruebas de criterio_estricto.py sobre los artefactos entregados (scorecard_m4.csv, casos_m4.csv,
base_conocimiento_plantvillage.json). Solo biblioteca estándar; no llaman modelos."""
import os, sys, unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "propuesta"))
import criterio_estricto as ce  # noqa: E402

M4 = os.environ.get("AGRO_M4", os.path.join(AQUI, "..", "..", "..", "M4"))


class CriterioEstricto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.filas = {(r["bloque"], r["id"][:6]): r for r in ce.recalcular(M4)}
        cls.catalogo, cls.casos, _ = ce.cargar(M4)

    def test_solo_cambia_img02_en_ambos_brazos(self):
        cambian = sorted(k for k, r in self.filas.items() if r["valor_entregado"] != r["valor_estricto"])
        self.assertEqual(cambian, [("con_imagen", "img-02"), ("control_sin_imagen", "img-02")])

    def test_img02_nombra_corynespora(self):
        self.assertEqual(self.filas[("con_imagen", "img-02")]["patogeno_ajeno"], "Tomato___Target_Spot")

    def test_exacto_con_imagen_se_mantiene(self):
        for i in ("img-01", "img-03", "img-04"):
            self.assertEqual(self.filas[("con_imagen", i)]["valor_estricto"], 1.0, i)

    def test_mismo_genero_no_es_ajeno(self):
        caso = self.casos["img-01-papa-tizon-tardio"]
        self.assertIsNone(ce.patogeno_ajeno("Tizón tardío (Phytophthora infestans) en papa.", caso, self.catalogo))
        self.assertEqual(ce.patogeno_ajeno("Es Alternaria solani.", caso, self.catalogo), "Potato___Early_blight")

    def test_palabras_comunes_no_disparan(self):
        caso = self.casos["img-04-vid-esca"]
        self.assertIsNone(ce.patogeno_ajeno("aparecen manchas antes de cosecha", caso, self.catalogo))


if __name__ == "__main__":
    unittest.main()
