import os
from pathlib import Path

from app.calculator_config import CalculatorConfig


def test_config_defaults_and_paths(monkeypatch, tmp_path):
    # Ensure no env overrides
    monkeypatch.delenv("CALCULATOR_LOG_DIR", raising=False)
    monkeypatch.delenv("CALCULATOR_HISTORY_DIR", raising=False)

    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    # Defaults
    assert cfg.get_precision() == 6
    assert cfg.get_memento_max_size() > 0
    assert isinstance(cfg.is_logging_enabled(), bool)

    # File path getters assemble paths
    log_path = cfg.get_log_file_path()
    hist_path = cfg.get_history_file_path()
    assert isinstance(log_path, str) and isinstance(hist_path, str)


def test_config_env_overrides_and_dir_creation(monkeypatch, tmp_path):
    # Override dirs via env and enable features so directories can be created
    monkeypatch.setenv("CALCULATOR_LOG_DIR", str(tmp_path / "logs"))
    monkeypatch.setenv("CALCULATOR_HISTORY_DIR", str(tmp_path / "hist"))
    monkeypatch.setenv("CALCULATOR_ENABLE_LOGGING", "true")
    monkeypatch.setenv("CALCULATOR_ENABLE_AUTO_SAVE", "true")

    cfg = CalculatorConfig(env_file=None, auto_create_dirs=True)

    # Directories should exist because features enabled
    assert Path(cfg.get_log_dir()).exists()
    assert Path(cfg.get_history_dir()).exists()

    # Toggle config value and ensure validation still passes
    cfg.set_config_value("CALCULATOR_PRECISION", 4)
    assert cfg.get_precision() == 4
