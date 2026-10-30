"""Filtro de salida opt-in para sistema_multimodal() de M4 (sugerencia docente).

No modifica notebookM4.ipynb. Se activa explícitamente en una copia, después de definir
sistema_multimodal() y dio_prescripcion_m4():

    import filtro_salida; filtro_salida.instalar(globals())   # bloquear_en_valvula=True para la regla 2

Implementa la regla que su README (§Límites) pide antes de desplegar:
1. Por defecto: si la foto pasó las guardas y el clasificador dice "sano", el texto del modelo no
   puede contener una prescripción (detector dio_prescripcion_m4 del propio equipo). Si la
   contiene, se sustituye por un texto determinista y se conserva el encabezado.
2. Opcional (bloquear_en_valvula=True): si la válvula se disparó y la respuesta por texto receta,
   se sustituye esa parte por una petición de cultivo/foto. Está apagado por defecto porque en
   img-06 (café) quitaría también la ficha de Cenicafé: conviene medir el costo antes de activarlo.
No certifica seguridad agronómica: depende de un detector heurístico.
"""

TEXTO_SANO = (
    "No se recomienda ningún producto: con la foto disponible no hay una enfermedad que tratar. "
    "Prevención a futuro: monitorea el cultivo cada semana y vuelve a consultar con una foto "
    "nítida si aparecen manchas, moho o deformaciones. Ante dudas, consulta a un agrónomo o al ICA.")

TEXTO_VALVULA = (
    "Sin un diagnóstico confiable no te voy a recomendar productos ni dosis. Dime qué cultivo es y, "
    "si puedes, envía otra foto nítida de una sola hoja; ante dudas, consulta a un agrónomo o al ICA.")


def debe_bloquear(d, catalogo, detector, bloquear_en_valvula=False):
    if not d:
        return False
    if d.get("ruta") == "valvula":
        return bloquear_en_valvula and bool(detector(d.get("respuesta_modelo") or ""))
    if d.get("ruta") != "vision":
        return False
    etiqueta = d.get("etiqueta_pred")
    if etiqueta not in catalogo or catalogo[etiqueta].get("tipo") != "sano":
        return False
    return bool(detector(d.get("respuesta_modelo") or ""))


def filtrar(resp, d, catalogo, detector, bloquear_en_valvula=False):
    """Devuelve (resp, d). Si bloquea, reemplaza solo la parte generada por el modelo."""
    if not debe_bloquear(d, catalogo, detector, bloquear_en_valvula):
        return resp, d
    original = d.get("respuesta_modelo") or ""
    encabezado = resp[: len(resp) - len(original)] if original and resp.endswith(original) else ""
    valvula = d.get("ruta") == "valvula"
    nuevo = TEXTO_VALVULA if valvula else TEXTO_SANO
    motivo = "prescripcion_bloqueada_valvula" if valvula else "prescripcion_bloqueada_sano"
    d = dict(d, respuesta_modelo=nuevo, filtro_salida=motivo,
             respuesta_modelo_original=original, receta_modelo=False)
    return encabezado + nuevo, d


def instalar(ns, bloquear_en_valvula=False):
    """Envuelve ns['sistema_multimodal'] conservando su firma. Idempotente."""
    original = ns["sistema_multimodal"]
    if getattr(original, "_filtro_salida", False):
        return original
    catalogo, detector = ns["catalogo"], ns["dio_prescripcion_m4"]

    def sistema_multimodal(pregunta, imagen=None, detalle=False):
        resp, d = original(pregunta, imagen, detalle=True)
        resp, d = filtrar(resp, d, catalogo, detector, bloquear_en_valvula)
        return (resp, d) if detalle else resp

    sistema_multimodal._filtro_salida = True
    sistema_multimodal.__wrapped__ = original
    ns["sistema_multimodal"] = sistema_multimodal
    return sistema_multimodal
