import os
import json
import pytest
from pathlib import Path

from app.calculator_config import get_config, reset_config, CalculatorConfig
from app.exceptions import ConfigurationError


def test_get_config_global_cache_and_reset(tmp_path, monkeypatch):
    reset_config()
    c1 = get_config()
    c2 = get_config()
    assert c1 is c2

    reset_config()
    c3 = get_config(reload=True)
    assert c3 is get_config()


def test_export_config_and_reload(tmp_path, monkeypatch):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    out = tmp_path / "cfg.json"
    s = cfg.export_config(str(out))
    assert out.exists() and json.loads(s)

    # Set env overrides and reload
    monkeypatch.setenv("CALCULATOR_LOG_LEVEL", "DEBUG")
    cfg.reload_config()
    assert cfg.get_log_level() == "DEBUG"


def test_create_directories_for_enabled_features(tmp_path):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=True)
    cfg.set_config_value("CALCULATOR_ENABLE_LOGGING", True)
    cfg.set_config_value("CALCULATOR_ENABLE_AUTO_SAVE", True)
    cfg.set_config_value("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))
    cfg.set_config_value("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    # Trigger directory creation via reload
    cfg.reload_config()
    assert Path(cfg.get_log_dir()).exists()
    assert Path(cfg.get_history_dir()).exists()


def test_invalid_encoding_in_env(monkeypatch):
    # Use a fresh instance that will read from env
    monkeypatch.setenv("CALCULATOR_DEFAULT_ENCODING", "__invalid_encoding__")
    with pytest.raises(ConfigurationError):
        CalculatorConfig(env_file=None)
