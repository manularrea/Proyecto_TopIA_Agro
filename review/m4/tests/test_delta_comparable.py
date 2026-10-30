"""Pruebas de delta_comparable.py: reconstruye cifras de delta_m3_m4.csv desde scorecard_m4.csv."""
import os, sys, unittest

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, "..", "propuesta"))
import delta_comparable as dc  # noqa: E402

M4 = os.environ.get("AGRO_M4", os.path.join(AQUI, "..", "..", "..", "M4"))


class DeltaComparable(unittest.TestCase):
    def test_reconstruye_las_filas_entregadas(self):
        for fila, (ok, entregado, reconstruido) in dc.verificar_contra_delta(M4).items():
            self.assertTrue(ok, f"{fila}: {entregado} != {reconstruido}")

    def test_filas_comparables(self):
        tabla, *_ = dc.filas_comparables(M4)
        t = {f[0]: f for f in tabla}
        self.assertEqual(t["gold (4) · media del criterio declarado"][3], "no")
        cmp_gold = [f for f in tabla if f[0].startswith("gold comparables")][0]
        self.assertEqual((cmp_gold[1], cmp_gold[2]), (1.0, 1.0))
        cmp_adv = [f for f in tabla if f[0].startswith("adversariales comparables")][0]
        self.assertEqual((cmp_adv[1], cmp_adv[2]), ("0/1", "0/1"))

    def test_estricto_baja_img02(self):
        tabla, *_ = dc.filas_comparables(M4, estricto=True)
        cmp_gold = [f for f in tabla if f[0].startswith("gold comparables")][0]
        self.assertEqual((cmp_gold[1], cmp_gold[2]), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
