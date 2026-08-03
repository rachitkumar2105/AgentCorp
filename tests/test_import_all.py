# tests/test_import_all.py
"""Test that imports all modules in the app package to increase coverage."""
import os, sys, importlib, pkgutil

# Ensure the backend app path is in PYTHONPATH for imports
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "apps", "backend"))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

def test_import_all_modules():
    import app as root
    for _, module_name, _ in pkgutil.iter_modules(root.__path__, root.__name__ + "."):
        importlib.import_module(module_name)
