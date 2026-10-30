"""Criterios `exacto` y `campos` alineados con el `criterio_texto` de casos_m4.csv (sugerencia docente).

No modifica notebookM4.ipynb ni recalifica la entrega. Recalcula, desde las respuestas guardadas en
scorecard_m4.csv, lo que el texto de cada caso declara:

- exacto_estricto = etiqueta top-1 correcta  Y  la respuesta nombra el patógeno esperado
                    Y  no nombra el género del patógeno de otra de las 38 clases (ficha
                    PlantVillage del repo; los virus, nombrados por el cultivo, no se comparan).
- campos_estricto = fracción de campos presentes, pero 0 si la respuesta nombra el patógeno de otra
                    clase del mismo catálogo («FALLA si nombra el patógeno de otra enfermedad»).

La acción esperada (híbridos resistentes, poda) no se comprueba aquí: queda en `cobertura_clave`.
Uso:  python review/m4/propuesta/criterio_estricto.py [ruta/a/M4]
"""
import csv, json, os, re, sys, unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
M4_DEF = os.path.join(AQUI, "..", "..", "..", "M4")


def _norm(s):
    s = unicodedata.normalize("NFKD", (s or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


_NO_GENERO = {"Tomato", "Tobacco", "Candidatus"}  # virus nombrados por el cultivo; prefijo de Liberibacter


def _toks(patogeno):
    """Género del nombre científico (primera palabra en mayúscula, ≥5 letras). Los virus se omiten."""
    generos = [g for g in re.findall(r"\b[A-Z][a-z]{4,}\b", patogeno or "") if g not in _NO_GENERO]
    return {_norm(generos[0])} if generos else set()


def cargar(m4=M4_DEF):
    with open(os.path.join(m4, "datos", "base_conocimiento_plantvillage.json"), encoding="utf-8") as f:
        catalogo = json.load(f)
    with open(os.path.join(m4, "eval_set", "casos_m4.csv"), encoding="utf-8") as f:
        casos = {r["id"]: r for r in csv.DictReader(f)}
    with open(os.path.join(m4, "scorecard_m4.csv"), encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return catalogo, casos, filas


def patogeno_ajeno(texto, caso, catalogo):
    """Devuelve la clase PlantVillage cuyo patógeno se nombra y no es el esperado, o None."""
    n = _norm(texto)
    propios = _toks(caso.get("patogeno_esperado", "")) | _toks(
        (catalogo.get(caso.get("etiqueta_real") or "", {}) or {}).get("patogeno", ""))
    for label, ficha in catalogo.items():
        if label == caso.get("etiqueta_real"):
            continue
        ajenos = _toks(ficha.get("patogeno") or "") - propios
        if any(re.search(r"\b" + t + r"\b", n) for t in ajenos):
            return label
    return None


def nombra_esperado(texto, caso):
    toks = _toks(caso.get("patogeno_esperado", ""))
    n = _norm(texto)
    return bool(toks) and any(re.search(r"\b" + t + r"\b", n) for t in toks)


def exacto_estricto(fila, caso, catalogo):
    return float(fila["etiqueta_pred"] == caso["etiqueta_real"]
                 and nombra_esperado(fila["respuesta"], caso)
                 and patogeno_ajeno(fila["respuesta"], caso, catalogo) is None)


def campos_estricto(fila, caso, catalogo):
    campos = json.loads(caso.get("campos_esperados") or "{}")
    n = _norm(fila["respuesta"])
    base = sum(1 for v in campos.values() if _norm(str(v)) in n) / max(1, len(campos))
    return 0.0 if patogeno_ajeno(fila["respuesta"], caso, catalogo) else base


def recalcular(m4=M4_DEF):
    catalogo, casos, filas = cargar(m4)
    out = []
    for f in filas:
        if f["bloque"] == "texto_m3" or f["criterio"] not in ("exacto", "campos"):
            continue
        caso = casos[f["id"]]
        nueva = (exacto_estricto if f["criterio"] == "exacto" else campos_estricto)(f, caso, catalogo)
        if f["bloque"] == "control_sin_imagen" and f["criterio"] == "exacto":
            nueva = 0.0  # sin foto no hay etiqueta: se mantiene la convención del equipo (celda 34)
        out.append({"bloque": f["bloque"], "id": f["id"], "criterio": f["criterio"],
                    "valor_entregado": float(f["nota"]), "valor_estricto": nueva,
                    "patogeno_ajeno": patogeno_ajeno(f["respuesta"], caso, catalogo) or ""})
    return out


if __name__ == "__main__":
    filas = recalcular(sys.argv[1] if len(sys.argv) > 1 else M4_DEF)
    print(f"{'bloque':<20}{'id':<34}{'criterio':<9}{'entregada':>10}{'estricta':>10}  patógeno ajeno")
    for r in filas:
        marca = "  <-- cambia" if r["valor_entregado"] != r["valor_estricto"] else ""
        print(f"{r['bloque']:<20}{r['id']:<34}{r['criterio']:<9}{r['valor_entregado']:>10.2f}"
              f"{r['valor_estricto']:>10.2f}  {r['patogeno_ajeno']}{marca}")
