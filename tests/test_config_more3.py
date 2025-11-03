import pytest

from app.calculator_config import CalculatorConfig
from app.exceptions import ConfigurationError


def test_config_find_env_file_missing(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    assert cfg._env_file is None
    assert cfg.get_config_value("__missing__", "fallback") == "fallback"


def test_config_invalid_env_value_from_environment(monkeypatch):
    monkeypatch.setenv("CALCULATOR_MAX_HISTORY_SIZE", "not-an-int")
    with pytest.raises(ConfigurationError):
        CalculatorConfig(env_file=None, auto_create_dirs=False)


def test_set_config_value_type_conversion_failure():
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    with pytest.raises(ConfigurationError):
        cfg.set_config_value("CALCULATOR_PRECISION", "invalid-int")


def test_export_config_failure_wraps_exception(monkeypatch):
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)

    def boom(*args, **kwargs):
        raise TypeError("cannot serialise")

    monkeypatch.setattr("app.calculator_config.json.dumps", boom)
    with pytest.raises(ConfigurationError):
        cfg.export_config()


def test_get_all_config_returns_copy_and_repr():
    cfg = CalculatorConfig(env_file=None, auto_create_dirs=False)
    snapshot = cfg.get_all_config()
    snapshot["CALCULATOR_LOG_DIR"] = "modified"

    assert cfg.get_log_dir() != "modified"
    assert isinstance(cfg.is_logging_enabled(), bool)
    assert isinstance(cfg.is_auto_save_enabled(), bool)
    assert cfg.get_config_file()
    assert isinstance(cfg.get_observer_timeout(), int)
    assert "CalculatorConfig(env_file=" in str(cfg)
    assert "CalculatorConfig(env_file='" in repr(cfg)
