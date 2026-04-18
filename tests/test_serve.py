from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def import_serve_module():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    if "typer" not in sys.modules:
        typer_stub = types.ModuleType("typer")

        def option(default=None, *args, **kwargs):
            return default

        typer_stub.Option = option
        sys.modules["typer"] = typer_stub

    if "uvicorn" not in sys.modules:
        uvicorn_stub = types.ModuleType("uvicorn")

        def run(*args, **kwargs):
            return None

        uvicorn_stub.run = run
        sys.modules["uvicorn"] = uvicorn_stub

    module_path = repo_root / "edgebench" / "commands" / "serve.py"
    spec = importlib.util.spec_from_file_location("test_serve_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_serve_cmd_calls_uvicorn_run_with_defaults(monkeypatch):
    serve_module = import_serve_module()
    captured = {}

    def fake_run(app, host, port, reload):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr(serve_module.uvicorn, "run", fake_run)

    serve_module.serve_cmd()

    assert captured == {
        "app": "edgebench.api:app",
        "host": "127.0.0.1",
        "port": 8000,
        "reload": False,
    }


def test_serve_cmd_calls_uvicorn_run_with_custom_args(monkeypatch):
    serve_module = import_serve_module()
    captured = {}

    def fake_run(app, host, port, reload):
        captured["app"] = app
        captured["host"] = host
        captured["port"] = port
        captured["reload"] = reload

    monkeypatch.setattr(serve_module.uvicorn, "run", fake_run)

    serve_module.serve_cmd(host="0.0.0.0", port=9000, reload=True)

    assert captured == {
        "app": "edgebench.api:app",
        "host": "0.0.0.0",
        "port": 9000,
        "reload": True,
    }
