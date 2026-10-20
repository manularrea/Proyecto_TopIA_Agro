"""Crea una M3 nueva con helpers activados; nunca modifica la entrega original.

El nuevo directorio retiene los artefactos históricos como archivos .entregado y
el notebook de trabajo comienza sin outputs. Ejecutar luego desde ESE directorio.
"""
import argparse
import ast
import json
import shutil
from pathlib import Path
from source_loader import read_notebook


def prepare(source, target):
    source, target = Path(source).resolve(), Path(target).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("La copia de trabajo debe estar fuera de la carpeta fuente y no ser su antecesora")
    if target.exists():
        raise FileExistsError("No se sobrescribe una copia de trabajo anterior")
    notebook = read_notebook(source / "notebookM3.ipynb")
    cell = next(c for c in notebook["cells"] if c.get("id") == "94ea1a00")
    text = "".join(cell["source"])
    tree = ast.parse(text)
    definition = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "responder_con_tools")
    lines = text.splitlines(keepends=True)
    position = definition.end_lineno
    lines[position:position] = ["\n# Propuesta docente: instalada solo en esta copia de trabajo.\n",
                               "from tools_review import install as _install_revision_tools\n",
                               "_install_revision_tools(globals())\n"]
    cell["source"] = lines
    for candidate in notebook["cells"]:
        if candidate["cell_type"] == "code":
            candidate["outputs"] = []
            candidate["execution_count"] = None
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".env", ".git", "__pycache__"))
    # No trasladar secretos; configurar el entorno autorizado de forma independiente.
    for path in target.iterdir():
        if path.is_file() and path.suffix in {".csv", ".json", ".txt"}:
            shutil.copy2(path, path.with_name(path.name + ".entregado"))
    shutil.copy2(Path(__file__).with_name("tools_review.py"), target / "tools_review.py")
    (target / "notebookM3_revision.ipynb").write_text(json.dumps(notebook, ensure_ascii=False, indent=1)+"\n", encoding="utf-8")
    return target / "notebookM3_revision.ipynb"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m3", required=True, type=Path)
    parser.add_argument("--destino", required=True, type=Path)
    args = parser.parse_args()
    print(prepare(args.m3, args.destino))
    print("Ejecutar la copia desde su directorio. C1 se aplica aparte sobre sus respuestas guardadas.")


if __name__ == "__main__":
    main()
