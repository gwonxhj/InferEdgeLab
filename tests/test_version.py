from __future__ import annotations

import importlib.util
import re
import sys
import types
from pathlib import Path

import edgebench
import edgebench.api as api


def import_cli_module():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    typer_stub = types.ModuleType("typer")

    class Typer:
        def __init__(self, *args, **kwargs):
            self.registered_commands = []

        def command(self, name=None, **kwargs):
            def decorator(fn):
                self.registered_commands.append((name, fn))
                return fn
            return decorator

    captured = {"echo": []}

    def echo(value):
        captured["echo"].append(value)

    typer_stub.Typer = Typer
    typer_stub.echo = echo
    sys.modules["typer"] = typer_stub

    command_specs = {
        "edgebench.commands.analyze": "analyze_cmd",
        "edgebench.commands.profile": "profile_cmd",
        "edgebench.commands.evaluate": "evaluate_cmd",
        "edgebench.commands.summarize": "summarize",
        "edgebench.commands.compare": "compare_cmd",
        "edgebench.commands.compare_latest": "compare_latest_cmd",
        "edgebench.commands.enrich_pair": "enrich_pair_cmd",
        "edgebench.commands.enrich_result": "enrich_result_cmd",
        "edgebench.commands.list_results": "list_results_cmd",
        "edgebench.commands.history_report": "history_report_cmd",
        "edgebench.commands.serve": "serve_cmd",
    }

    for module_name, attr_name in command_specs.items():
        stub = types.ModuleType(module_name)
        setattr(stub, attr_name, lambda *args, **kwargs: None)
        sys.modules[module_name] = stub

    module_path = repo_root / "edgebench" / "cli.py"
    spec = importlib.util.spec_from_file_location("test_cli_module", module_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, captured


def test_cli_version_command_emits_package_version():
    cli_module, captured = import_cli_module()

    cli_module.version_cmd()

    assert captured["echo"] == [edgebench.__version__]


def test_health_endpoint_includes_status_service_and_version():
    app = api.create_app()
    endpoint = next(route.endpoint for route in app.routes if getattr(route, "path", None) == "/health")

    assert endpoint() == {
        "status": "ok",
        "service": "edgebench-api",
        "version": edgebench.__version__,
    }


def test_package_version_matches_pyproject_version():
    pyproject_text = Path(__file__).resolve().parents[1].joinpath("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject_text, re.MULTILINE)
    assert match is not None
    assert edgebench.__version__ == match.group(1)
