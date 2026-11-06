import importlib.util
import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

def load_service_app(service_dir_name: str):
    root = Path(__file__).resolve().parents[2]
    service_path = root / "services" / service_dir_name
    sys.path.insert(0, str(service_path))
    sys.path.insert(0, str(root))

    # We import dynamically to avoid collisions
    spec = importlib.util.spec_from_file_location(
        f"{service_dir_name.replace('-', '_')}_main",
        service_path / "app" / "main.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.app

