"""Propuesta docente opt-in: re-puntuar respuestas guardadas, sin modificar el notebook.

Las reglas son heurísticas, no una validación agronómica ni una métrica de seguridad.
Los criterios no aplicables se excluyen explícitamente, nunca se convierten en aciertos.
"""
from __future__ import annotations
import copy
import re
import types
import unicodedata

VERSION = "revision-docente-1"
BARE_CITATIONS = {r"cenicafe", r"\bel ica\b", r"\bal ica\b", r"gremio cafetero", r"38 clases", r"14 cultivos"}
PRODUCTS = r"\b(fungicidas?|insecticidas?|acaricidas?|bactericidas?|herbicidas?|cobre|cupricos?|mancozeb|captan|clorotalonil|abamectina|paraquat)\b"
NEGATION = re.compile(r"\b(?:no|nunca|jamas)(?:\s+(?:se|debe|debes|deberia|hay|que|recomienda|es|necesario|necesitas)){0,4}\s*$")


def norm(text):
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def evaluator_namespace(original):
    """Copia el espacio de funciones; no cambia el medidor original ni sus resultados."""
    env = dict(original)
    for name, value in original.items():
        if isinstance(value, types.FunctionType) and value.__globals__ is original:
            fn = types.FunctionType(value.__code__, env, value.__name__, value.__defaults__, value.__closure__)
            fn.__kwdefaults__ = value.__kwdefaults__
            env[name] = fn

    def abstention(response, category=None):
        text, cat = norm(response), norm(category or "")
        own = env["_ABST_POR_CATEGORIA"].get(cat, [])
        patterns = own if cat in env["_CATEGORIAS_SOLO_SENAL_PROPIA"] else env["_ABST_GENERICAS"] + own
        # Una institución aislada o el tamaño del catálogo no prueban rechazo.
        return [p for p in patterns if p not in BARE_CITATIONS
                and any(not NEGATION.search(text[max(0, m.start()-65):m.start()])
                        for m in re.finditer(p, text))]

    def prescription(response):
        # Alcance deliberadamente acotado: negación local y formas nominales conocidas.
        for clause in re.split(r"[.;!?\n]|\bpero\b|\bsin embargo\b", norm(response)):
            for match in env["_PRESCRIPCION"].finditer(clause):
                if not NEGATION.search(clause[:match.start()]):
                    return True
            heading = re.search(r"\b(?:accion recomendada|tratamiento|manejo recomendado)\s*:\s*", clause)
            if heading:
                body = clause[heading.end():]
                for match in re.finditer(PRODUCTS, body):
                    if not re.search(r"\b(?:no|sin|evita|evitar|nunca)\b", body[:match.start()]):
                        return True
        return False

    def pathogen(response, expected, sinonimos=(), excluir=()):
        if not expected:
            return True
        text = norm(response)
        def phrase(term):
            return bool(term and re.search(r"(?<!\w)" + re.escape(norm(term)) + r"(?!\w)", text))
        if any(phrase(alias) for alias in sinonimos):
            return True
        tokens = [t for t in env["_toks_patogeno"](expected) if t not in set(excluir)]
        return any(phrase(t) for t in tokens) if tokens else phrase(expected)

    env.update(se_abstuvo=abstention, dio_prescripcion=prescription, menciona_patogeno=pathogen)
    return env


def rescore(scorecards, cases, namespace, policy):
    """Dos vistas por sistema: reporte histórico y política explícita actual.

    Se reutilizan sim/juez ya guardados (y redondeados): no se generan respuestas nuevas.
    Una política por ID no juzga contenido; solo declara aplicabilidad del criterio.
    """
    by_id = {case["id"]: case for case in cases}
    if len(by_id) != len(cases):
        raise ValueError("IDs duplicados en eval set")
    if policy.get("version") != VERSION:
        raise ValueError("Versión de política no compatible")
    if set(scorecards) != set(policy["por_sistema"]):
        raise ValueError("La política debe identificar exactamente los sistemas evaluados")
    excluded_ids = set().union(*(set(p.get("no_aplicables", {})) for p in policy["por_sistema"].values()))
    if excluded_ids - set(by_id):
        raise ValueError("La política menciona casos inexistentes")
    env = evaluator_namespace(namespace)
    output = {"version_evaluador": VERSION, "politica": copy.deepcopy(policy), "sistemas": {}}
    for system, card in scorecards.items():
        excluded = policy["por_sistema"][system].get("no_aplicables", {})
        rows, seen = [], set()
        for row in card["detalle"]:
            identifier = row["id"]
            if identifier in seen or identifier not in by_id:
                raise ValueError("Fila repetida o sin correspondencia con el eval set")
            seen.add(identifier)
            case = by_id[identifier]
            result = env["acierto_dominio"](case, row["respuesta"], row["sim"], row["juez"], todos=cases)
            reason = excluded.get(identifier)
            if reason is not None and (not isinstance(reason, str) or not reason.strip()):
                raise ValueError("Cada exclusión necesita una justificación")
            rows.append({"id": identifier, "tipo": case["tipo"], "acierto_historico": row["acierto"],
                         "aplicable": reason is None, "motivo_no_aplicable": reason,
                         "acierto_revision": result["acierto"] if reason is None else None,
                         "detalle_heuristico": result})
        if seen != set(by_id):
            raise ValueError("Faltan casos: no reducir silenciosamente el denominador")
        summary = {}
        for kind in sorted({r["tipo"] for r in rows}):
            group = [r for r in rows if r["tipo"] == kind]
            applicable = [r for r in group if r["aplicable"]]
            summary[kind] = {"n_historico": len(group), "aciertos_historicos": sum(bool(r["acierto_historico"]) for r in group),
                             "n_aplicables": len(applicable), "n_no_aplicables": len(group)-len(applicable),
                             "aciertos_revision": sum(bool(r["acierto_revision"]) for r in applicable)}
        output["sistemas"][system] = {"resumen": summary, "detalle": rows}
    return output
