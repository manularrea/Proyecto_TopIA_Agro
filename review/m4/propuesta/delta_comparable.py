"""Delta M3–M4 con columna «comparable» (sugerencia docente).

Reconstruye desde scorecard_m4.csv las filas del delta que dependen de los casos con imagen,
comprueba que coinciden con delta_m3_m4.csv y marca qué filas comparan dos brazos que pueden
puntuar por igual. No cambia ningún resultado entregado.

- «media del criterio declarado» (0.25 → 1.0): en el control, `exacto` vale 0 por construcción
  (celda 34: sin foto no hay etiqueta), así que solo img-02 (`campos`) es comparable.
- «adversariales · válvula» (0/3 → 2/3): img-06 e img-07 exigen `det["valvula"]`, imposible sin
  foto; solo img-05 (premisa falsa visual) es comparable.

Uso:  python review/m4/propuesta/delta_comparable.py [ruta/a/M4] [--estricto]
      --estricto añade el valor con los criterios de criterio_estricto.py.
"""
import csv, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
M4_DEF = os.path.join(AQUI, "..", "..", "..", "M4")


def _leer(m4):
    with open(os.path.join(m4, "scorecard_m4.csv"), encoding="utf-8") as f:
        sc = list(csv.DictReader(f))
    with open(os.path.join(m4, "delta_m3_m4.csv"), encoding="utf-8") as f:
        delta = list(csv.DictReader(f))
    return sc, delta


def _b(x):
    return str(x).strip().lower() == "true"


def _media(xs):
    return round(sum(xs) / len(xs), 3) if xs else None


def filas_comparables(m4=M4_DEF, estricto=False):
    sc, delta = _leer(m4)
    bloques = {b: [r for r in sc if r["bloque"] == b] for b in ("con_imagen", "control_sin_imagen")}
    valores = {}
    if estricto:
        sys.path.insert(0, AQUI)
        import criterio_estricto as ce
        valores = {(r["bloque"], r["id"]): r["valor_estricto"] for r in ce.recalcular(m4)}

    def valor(r):
        return float(valores.get((r["bloque"], r["id"]), r["nota"]))

    def brazo(b):
        g = [r for r in bloques[b] if r["tipo"] == "gold"]
        a = [r for r in bloques[b] if r["tipo"] == "adversarial"]
        g_cmp = [r for r in g if r["criterio"] != "exacto"]
        a_cmp = [r for r in a if r["id"].startswith("img-05")]
        return {
            "dominio": f"{sum(_b(r['acierto']) for r in g)}/{len(g)}",
            "media_gold": _media([valor(r) for r in g]),
            "media_gold_cmp": _media([valor(r) for r in g_cmp]), "n_gold_cmp": len(g_cmp),
            "valvula_adv": f"{int(sum(valor(r) for r in a))}/{len(a)}",
            "valvula_adv_cmp": f"{int(sum(valor(r) for r in a_cmp))}/{len(a_cmp)}",
            "lat": round(_media([float(r["latencia_s"]) for r in bloques[b]]), 2),
        }

    m3, m4v = brazo("control_sin_imagen"), brazo("con_imagen")
    sufijo = " (criterio estricto)" if estricto else ""
    tabla = [
        ("gold (4) · aciertos de dominio", m3["dominio"], m4v["dominio"], "sí", ""),
        ("gold (4) · media del criterio declarado" + sufijo, m3["media_gold"], m4v["media_gold"], "no",
         "en el control, `exacto` vale 0 por construcción (celda 34)"),
        (f"gold comparables ({m4v['n_gold_cmp']}: criterio campos) · media" + sufijo,
         m3["media_gold_cmp"], m4v["media_gold_cmp"], "sí", "img-02"),
        ("adversariales (3) · válvula", m3["valvula_adv"], m4v["valvula_adv"], "no",
         "img-06 e img-07 exigen la válvula visual: sin foto no pueden puntuar"),
        ("adversariales comparables (1: premisa falsa visual)", m3["valvula_adv_cmp"],
         m4v["valvula_adv_cmp"], "sí", "img-05"),
        ("latencia media · 7 casos con imagen (s)", m3["lat"], m4v["lat"], "sí", ""),
    ]
    return tabla, delta, m3, m4v


# Rótulo literal de la fila en su delta_m3_m4.csv.
FILA_GOLD_EQUIPO = "casos con imagen · gold (4) · nota del criterio declarado"


def verificar_contra_delta(m4=M4_DEF):
    """Comprueba que las cifras reconstruidas coinciden con las de delta_m3_m4.csv."""
    _, delta, m3, m4v = filas_comparables(m4)
    por_fila = {r["fila"]: r for r in delta}
    esperado = {
        "casos con imagen · gold (4) · aciertos de dominio": (m3["dominio"], m4v["dominio"]),
        FILA_GOLD_EQUIPO: (m3["media_gold"], m4v["media_gold"]),
        "adversariales con imagen (3) · válvula": (m3["valvula_adv"], m4v["valvula_adv"]),
        "latencia media · casos con imagen": (m3["lat"], m4v["lat"]),
    }
    res = {}
    for fila, (a, b) in esperado.items():
        d = por_fila[fila]
        col3, col4 = d["M3 (sin foto, misma pregunta)"], d["M4 (con foto)"]
        ok = (str(a) == col3 or _num(a) == _num(col3)) and (str(b) == col4 or _num(b) == _num(col4))
        res[fila] = (ok, (col3, col4), (a, b))
    return res


def _num(x):
    try:
        return round(float(x), 3)
    except (TypeError, ValueError):
        return None


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    m4 = args[0] if args else M4_DEF
    for fila, (ok, entregado, reconstruido) in verificar_contra_delta(m4).items():
        print(f"[{'OK' if ok else 'DIFIERE'}] {fila}: entregado {entregado} · reconstruido {reconstruido}")
    for estricto in ([False, True] if "--estricto" in sys.argv else [False]):
        print()
        tabla, *_ = filas_comparables(m4, estricto)
        print(f"| fila | M3 (sin foto) | M4 (con foto) | comparable | obs |\n|---|---|---|---|---|")
        for fila, a, b, cmp_, obs in tabla:
            print(f"| {fila} | {a} | {b} | {cmp_} | {obs} |")
