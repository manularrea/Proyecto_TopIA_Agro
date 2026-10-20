"""Adaptadores opt-in para §13/14. Conservan ranking/generación del equipo.

No certifican cobertura por sinónimos desconocidos ni seguridad agronómica.
El nuevo estado de conflicto se propaga hasta la respuesta final y detiene ReAct.
"""
from __future__ import annotations

SCHEMAS = {
    "diagnostico_diferencial": {"cultivo", "sintomas"},
    "consultar_ficha": {"etiqueta"},
    "buscar_en_fichas": {"consulta"},
}


def validate_call(name, arguments):
    if not isinstance(name, str) or name not in SCHEMAS:
        return "herramienta desconocida"
    if not isinstance(arguments, dict):
        return "args debe ser un objeto JSON"
    if set(arguments) - SCHEMAS[name]:
        return "hay argumentos no definidos en el esquema"
    if any(not isinstance(value, str) for value in arguments.values()):
        return "todos los argumentos de esta herramienta deben ser texto"
    if name == "consultar_ficha" and not arguments.get("etiqueta", "").strip():
        return "etiqueta es obligatoria y no puede estar vacía"
    return None


def install(namespace):
    """Instalar después de definir responder_con_tools, antes de sus demos.

    Usar en copia de trabajo. Reejecutar esta función es idempotente. No captura ni
    oculta errores de modelos o herramientas válidas; esos errores se propagan.
    """
    if namespace.get("_revision_tools_instalada"):
        return
    required = ("diagnostico_diferencial", "_obs_diagnostico", "_redactar_final", "_ejecutar_herramienta",
                "_detectar_cultivos", "_norm", "_CULTIVO_VACIO", "responder_con_tools")
    if any(name not in namespace for name in required):
        raise ValueError("Faltan las definiciones originales de §13; no se instaló ningún cambio")
    old_diag = namespace["diagnostico_diferencial"]
    old_obs = namespace["_obs_diagnostico"]
    old_final = namespace["_redactar_final"]
    old_dispatch = namespace["_ejecutar_herramienta"]

    def conflict(crops, reason):
        return {"estado": "conflicto_cultivo", "cultivo": None, "candidatos": [],
                "cultivos_detectados": sorted(set(crops)), "motivo": reason}

    def diagnose(crop, symptoms, top=3):
        if not isinstance(crop, str) or not isinstance(symptoms, str):
            raise TypeError("cultivo y sintomas deben ser texto")
        detect = namespace["_detectar_cultivos"]
        argument, text = set(detect(crop)), set(detect(symptoms))
        normalized = namespace["_norm"](crop).strip(" .,:;\"'")
        empty = (normalized in namespace["_CULTIVO_VACIO"] or normalized.startswith("no ")
                 or len(normalized.split()) > 3)
        if len(argument) > 1 or len(text) > 1:
            return conflict(argument | text, "La consulta o el argumento menciona varios cultivos")
        if argument and text and argument != text:
            return conflict(argument | text, "El cultivo del planificador contradice al texto")
        if normalized and not empty and not argument and text:
            return conflict(text | {crop.strip()}, "El argumento no reconocido contradice un cultivo del texto")
        return old_diag(crop, symptoms, top)

    def clarification(diagnostic):
        crops = ", ".join(diagnostic.get("cultivos_detectados", []))
        return (f"Hay información de cultivo incompatible o ambigua ({crops}). "
                "Antes de recomendar un manejo, dime qué cultivo quieres consultar.")

    def observation(diagnostic):
        if diagnostic["estado"] == "conflicto_cultivo":
            return clarification(diagnostic) + " Escribe Responder[ok]: se solicitará aclaración."
        return old_obs(diagnostic)

    def final(question, state):
        diagnostic = state.get("diag")
        if diagnostic is None:
            diagnostic = state["diag"] = diagnose("", question)
        if diagnostic["estado"] == "conflicto_cultivo":
            return clarification(diagnostic)
        if diagnostic["estado"] == "cubierto":
            checked = diagnose(diagnostic.get("cultivo") or "", question)
            if checked["estado"] == "conflicto_cultivo":
                state["diag"] = checked
                return clarification(checked)
            chosen = namespace.get("catalogo", {}).get(state.get("etiqueta"))
            if chosen and chosen["cultivo_key"] != diagnostic["cultivo"]:
                checked = conflict({chosen["cultivo_key"], diagnostic["cultivo"]},
                                   "La ficha elegida no corresponde al cultivo del diagnóstico")
                state["diag"] = checked
                return clarification(checked)
        return old_final(question, state)

    def dispatch(name, arguments, question, state):
        error = validate_call(name, arguments)
        if error:
            observation_text = "error_validacion: " + error
            state.setdefault("errores_tools", []).append(observation_text)
            return observation_text
        if name == "diagnostico_diferencial":
            # Contrastar con la pregunta ORIGINAL antes de anexar síntomas del planificador.
            checked = diagnose(arguments.get("cultivo", ""), question)
            if checked["estado"] == "conflicto_cultivo":
                state["diag"] = checked
                return observation(checked)
        return old_dispatch(name, arguments, question, state)

    def one_turn(question, verbose=True):
        state = {"diag": None, "etiqueta": None, "idxs": []}
        raw = namespace["generar_agente"](namespace["SYSTEM_TOOLS"], f"Pregunta: {question}", 160)
        request = namespace["_extraer_json"](raw)
        if isinstance(request, dict) and "tool" in request:
            obs = dispatch(request["tool"], request.get("args", {}), question, state)
        else:
            obs = "error_validacion: la salida no contiene un objeto de llamada válido"
            state.setdefault("errores_tools", []).append(obs)
        if verbose:
            print(obs)
        return final(question, state)

    namespace.update(diagnostico_diferencial=diagnose, _obs_diagnostico=observation,
                     _redactar_final=final, _ejecutar_herramienta=dispatch,
                     responder_con_tools=one_turn, _revision_tools_instalada=True)
