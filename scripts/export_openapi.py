"""Зберігає схему OpenAPI у frontend/openapi.json (з неї генеруються типи фронтенду).

    python scripts/export_openapi.py && (cd frontend && npm run gen:api)
"""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from app.main import create_app  # noqa: E402

OUT = pathlib.Path(__file__).resolve().parent.parent / "frontend" / "openapi.json"


def schema() -> str:
    return json.dumps(create_app(run_seed=False).openapi(), ensure_ascii=False, indent=1, sort_keys=True) + "\n"


if __name__ == "__main__":
    OUT.write_text(schema(), encoding="utf-8")
    print(f"Збережено {OUT}")
