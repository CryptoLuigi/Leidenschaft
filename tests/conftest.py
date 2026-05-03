from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def load_source_module():
    return load_module


@pytest.fixture
def stubbed_dislevel_imports(monkeypatch):
    nextcord_module = types.ModuleType("nextcord")
    nextcord_module.ButtonStyle = object()
    nextcord_module.Embed = type("Embed", (), {})
    nextcord_module.File = type("File", (), {})

    nextcord_ui = types.ModuleType("nextcord.ui")
    nextcord_ui.Button = type("Button", (), {})
    nextcord_ui.View = type("View", (), {})

    monkeypatch.setitem(sys.modules, "nextcord", nextcord_module)
    monkeypatch.setitem(sys.modules, "nextcord.ui", nextcord_ui)

    card_module = load_module("test_dislevel_card", "dislevel/card.py")
    minicard_module = load_module("test_dislevel_minicard", "dislevel/minicard.py")
    models_module = load_module("test_dislevel_models", "dislevel/_models.py")

    dislevel_package = types.ModuleType("dislevel")
    dislevel_package.__path__ = [str(ROOT / "dislevel")]

    monkeypatch.setitem(sys.modules, "dislevel", dislevel_package)
    monkeypatch.setitem(sys.modules, "dislevel.card", card_module)
    monkeypatch.setitem(sys.modules, "dislevel.minicard", minicard_module)
    monkeypatch.setitem(sys.modules, "dislevel._models", models_module)

    return {
        "card": card_module,
        "minicard": minicard_module,
        "models": models_module,
    }
