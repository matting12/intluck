import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # <-- points to your project root

def load_json_file(relative_path: str):
    file_path = BASE_DIR / relative_path
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
