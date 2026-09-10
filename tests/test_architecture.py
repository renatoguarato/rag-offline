from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).parents[1] / "app"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _app_imports(path: Path) -> set[str]:
    return {name for name in _imports(path) if name == "app" or name.startswith("app.")}


def test_dependency_direction_is_enforced() -> None:
    forbidden_frameworks = {
        "fastapi",
        "pydantic",
        "sqlalchemy",
        "chromadb",
        "ollama",
        "httpx",
        "docx",
        "pypdf",
    }
    rules = {
        "domain": {"app.domain"},
        "application": {"app.domain", "app.application"},
        "adapters": {"app.domain", "app.application", "app.adapters", "app.bootstrap"},
        "bootstrap": {"app.domain", "app.application", "app.adapters", "app.bootstrap"},
        "main": {"app.adapters", "app.bootstrap"},
    }
    for layer, allowed in rules.items():
        paths = (
            [ROOT / layer]
            if layer in {"domain", "application", "adapters", "bootstrap"}
            else [ROOT / "main.py"]
        )
        files = [
            path for base in paths for path in (base.rglob("*.py") if base.is_dir() else [base])
        ]
        for path in files:
            violations = {
                imported
                for imported in _app_imports(path)
                if not any(
                    imported == prefix or imported.startswith(f"{prefix}.") for prefix in allowed
                )
            }
            assert not violations, f"{path}: forbidden imports {sorted(violations)}"
            if layer in {"domain", "application"}:
                external = {
                    name for name in _imports(path) if name.split(".", 1)[0] in forbidden_frameworks
                }
                assert not external, f"{path}: framework imports in inner layer {sorted(external)}"


def test_legacy_layers_are_not_present() -> None:
    for name in ("api", "core", "middleware", "models", "schemas", "services"):
        assert not list((ROOT / name).glob("*.py")), f"legacy layer remains: app/{name}"
