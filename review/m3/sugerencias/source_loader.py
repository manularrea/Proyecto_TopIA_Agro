"""Extrae solo definiciones de las celdas revisadas. No carga modelos ni ejecuta demos."""
import ast
import hashlib
import json
import re
import unicodedata
from pathlib import Path

BASE_NOTEBOOK_BLOB = "635893ad876792da07f8d149bf50d0dd8c51cb9b"


def read_notebook(path):
    raw = Path(path).read_bytes()
    blob = hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
    if blob != BASE_NOTEBOOK_BLOB:
        raise ValueError("El notebook cambió: revisar la propuesta antes de aplicarla a otra versión")
    return json.loads(raw)


def domain_namespace(notebook):
    cell = next(c for c in notebook["cells"] if c.get("id") == "ae045d14")
    nodes = [n for n in ast.parse("".join(cell["source"])).body if isinstance(n, (ast.FunctionDef, ast.Assign))]
    env = dict(re=re, unicodedata=unicodedata, UMBRAL_SIM=0.60, UMBRAL_JUEZ=4.0, UMBRAL_CLAVE=0.40)
    code = ast.fix_missing_locations(ast.Module(body=nodes, type_ignores=[]))
    exec(compile(code, "notebookM3:ae045d14", "exec"), env)
    return env
