"""CLI sin LLM. Ejecutar desde cualquier directorio con --m3 y --salida explícitos."""
import argparse
import json
from pathlib import Path
from evaluation_review import rescore
from source_loader import read_notebook, domain_namespace


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--m3", type=Path, required=True)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    notebook = read_notebook(args.m3 / "notebookM3.ipynb")
    cases = json.loads((args.m3 / "eval_set_m3.json").read_text(encoding="utf-8"))
    scorecards = json.loads((args.m3 / "scorecard_rag_m3.json").read_text(encoding="utf-8"))
    policy = json.loads(Path(__file__).with_name("politica_eval.json").read_text(encoding="utf-8"))
    report = rescore(scorecards, cases, domain_namespace(notebook), policy)
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    with args.salida.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, allow_nan=False)
    print(f"Reporte NUEVO: {args.salida}. No sustituye los resultados entregados.")


if __name__ == "__main__":
    main()
