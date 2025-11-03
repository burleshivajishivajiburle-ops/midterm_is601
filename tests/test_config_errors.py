import os
from pathlib import Path
import pytest

from app.calculator_config import CalculatorConfig, ConfigurationError


def test_config_validation_errors(monkeypatch, tmp_path):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)

    # invalid precision
    with pytest.raises(ConfigurationError):
        cfg.set_config_value("CALCULATOR_PRECISION", 100)

    # invalid log level
    with pytest.raises(ConfigurationError):
        cfg.set_config_value("CALCULATOR_LOG_LEVEL", "NOPE")

    # invalid encoding
    with pytest.raises(ConfigurationError):
        cfg.set_config_value("CALCULATOR_DEFAULT_ENCODING", "definitely-not-an-encoding-xyz")

    # invalid max history size
    with pytest.raises(ConfigurationError):
        cfg.set_config_value("CALCULATOR_MAX_HISTORY_SIZE", 0)

    # invalid max input value
    with pytest.raises(ConfigurationError):
        cfg.set_config_value("CALCULATOR_MAX_INPUT_VALUE", 0)


def test_config_reload_export_and_summary(monkeypatch, tmp_path):
    # Set env overrides then reload
    monkeypatch.setenv("CALCULATOR_PRECISION", "7")
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    cfg.reload_config()
    assert cfg.get_precision() == 7

    # Export to file and JSON string
    out = tmp_path / "cfg.json"
    js = cfg.export_config(str(out))
    assert out.exists() and "CALCULATOR_PRECISION" in js

    # get_summary shows states; directories likely don't exist
    summary = cfg.get_summary()
    assert isinstance(summary, dict) and "features_enabled" in summary


def test_config_dir_creation_errors(monkeypatch, tmp_path):
    # Enable features via env so _create_directories would try to create
    monkeypatch.setenv("CALCULATOR_ENABLE_LOGGING", "true")
    monkeypatch.setenv("CALCULATOR_ENABLE_AUTO_SAVE", "true")

    # Monkeypatch Path.mkdir to throw for first call to simulate failure
    calls = {"n": 0}
    real_mkdir = Path.mkdir

    def bad_mkdir(self, *args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("no permission")
        return real_mkdir(self, *args, **kwargs)

    monkeypatch.setattr(Path, "mkdir", bad_mkdir)

    with pytest.raises(ConfigurationError):
        CalculatorConfig(env_file=None, auto_create_dirs=True)
