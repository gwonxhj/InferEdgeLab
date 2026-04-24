from __future__ import annotations

import importlib.util
import re
import sys
import types
from contextlib import contextmanager
from pathlib import Path
import tomllib

import inferedgelab
import inferedgelab.api as api


@contextmanager
def _temporary_sys_modules(module_names: list[str]):
    saved = {name: sys.modules.get(name) for name in module_names}
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def import_cli_module():
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    command_specs = {
        "inferedgelab.commands.analyze": "analyze_cmd",
        "inferedgelab.commands.profile": "profile_cmd",
        "inferedgelab.commands.evaluate": "evaluate_cmd",
        "inferedgelab.commands.evaluate_detection": "evaluate_detection_cmd",
        "inferedgelab.commands.summarize": "summarize",
        "inferedgelab.commands.compare": "compare_cmd",
        "inferedgelab.commands.compare_latest": "compare_latest_cmd",
        "inferedgelab.commands.enrich_pair": "enrich_pair_cmd",
        "inferedgelab.commands.enrich_result": "enrich_result_cmd",
        "inferedgelab.commands.list_results": "list_results_cmd",
        "inferedgelab.commands.history_report": "history_report_cmd",
        "inferedgelab.commands.serve": "serve_cmd",
    }
    touched_modules = ["typer", "test_cli_module", *command_specs.keys()]
    captured = {"echo": []}

    with _temporary_sys_modules(touched_modules):
        typer_stub = types.ModuleType("typer")

        class BadParameter(Exception):
            pass

        class Exit(Exception):
            def __init__(self, code: int = 0):
                super().__init__(code)
                self.exit_code = code

        class Typer:
            def __init__(self, *args, **kwargs):
                self.registered_commands = []

            def command(self, name=None, **kwargs):
                def decorator(fn):
                    self.registered_commands.append((name, fn))
                    return fn
                return decorator

        def echo(value):
            captured["echo"].append(value)

        def option(default=None, *args, **kwargs):
            return default

        def argument(default=None, *args, **kwargs):
            return default

        typer_stub.Typer = Typer
        typer_stub.echo = echo
        typer_stub.Option = option
        typer_stub.Argument = argument
        typer_stub.BadParameter = BadParameter
        typer_stub.Exit = Exit
        sys.modules["typer"] = typer_stub

        for module_name, attr_name in command_specs.items():
            stub = types.ModuleType(module_name)
            setattr(stub, attr_name, lambda *args, **kwargs: None)
            sys.modules[module_name] = stub

        module_path = repo_root / "inferedgelab" / "cli.py"
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

    assert captured["echo"] == [inferedgelab.__version__]


def test_health_endpoint_includes_status_service_and_version():
    app = api.create_app()
    endpoint = next(route.endpoint for route in app.routes if getattr(route, "path", None) == "/health")

    assert endpoint() == {
        "status": "ok",
        "service": "inferedgelab-api",
        "version": inferedgelab.__version__,
    }


def test_package_version_matches_pyproject_version():
    pyproject_text = Path(__file__).resolve().parents[1].joinpath("pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"', pyproject_text, re.MULTILINE)
    assert match is not None
    assert inferedgelab.__version__ == match.group(1)


def test_pyproject_exposes_inferedgelab_primary_script_and_edgebench_compat_alias():
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    scripts = data["project"]["scripts"]

    assert scripts["inferedgelab"] == "inferedgelab.cli:app"
    assert scripts["edgebench"] == "inferedgelab.cli:app"
