"""
Configuration management for the calculator application.

This module manages configuration settings using a .env file and the python-dotenv
package. It provides centralized configuration with validation, default values,
and runtime configuration updates.
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
# Optional dependency: python-dotenv. If unavailable, fall back to a no-op.
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # ModuleNotFoundError or others
    def load_dotenv(*args, **kwargs):  # type: ignore
        return False
import json

from .exceptions import ConfigurationError, ValidationError

# Type aliases
ConfigValue = Union[str, int, float, bool, List[str]]
ConfigDict = Dict[str, ConfigValue]


class CalculatorConfig:
    """
    Configuration manager for the calculator application.
    
    Manages all configuration settings including base directories, history settings,
    calculation settings, and logging configuration using environment variables
    and .env files.
    """
    
    # Default configuration values
    DEFAULT_CONFIG = {
        # Base Directories
        "CALCULATOR_LOG_DIR": "logs",
        "CALCULATOR_HISTORY_DIR": "history",
        
        # History Settings
    "CALCULATOR_MAX_HISTORY_SIZE": 100,
    "CALCULATOR_AUTO_SAVE": False,
        
        # Calculation Settings
        "CALCULATOR_PRECISION": 6,
        "CALCULATOR_MAX_INPUT_VALUE": 1e15,
        "CALCULATOR_DEFAULT_ENCODING": "utf-8",
        
        # Logging Settings
        "CALCULATOR_LOG_LEVEL": "INFO",
        "CALCULATOR_LOG_FILE": "calculator.log",
        "CALCULATOR_LOG_FORMAT": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        
        # File Settings
        "CALCULATOR_HISTORY_FILE": "calculator_history.csv",
        "CALCULATOR_CONFIG_FILE": ".calculator_config",
        
        # Performance Settings
        "CALCULATOR_MEMENTO_MAX_SIZE": 50,
        "CALCULATOR_OBSERVER_TIMEOUT": 5,
        
        # Feature Flags
        "CALCULATOR_ENABLE_LOGGING": True,
    "CALCULATOR_ENABLE_AUTO_SAVE": False,
        "CALCULATOR_ENABLE_UNDO_REDO": True,
    }
    
    def __init__(self, env_file: Optional[str] = None, auto_create_dirs: bool = False):
        """
        Initialize the configuration manager.
        
        Args:
            env_file (str, optional): Path to .env file. Defaults to project root/.env
            auto_create_dirs (bool): Whether to automatically create directories
        """
        self._config: ConfigDict = {}
        self._env_file = env_file or self._find_env_file()
        self._auto_create_dirs = auto_create_dirs
        
        # Load configuration
        self._load_configuration()
        
        # Create directories if requested (and only for enabled features)
        if self._auto_create_dirs:
            self._create_directories()
    
    def _find_env_file(self) -> Optional[str]:
        """
        Find the .env file in the project hierarchy.
        
        Returns:
            Optional[str]: Path to .env file or None if not found
        """
        current_path = Path.cwd()
        
        # Search up the directory tree
        for path in [current_path] + list(current_path.parents):
            env_file = path / ".env"
            if env_file.exists():
                return str(env_file)
        
        return None
    
    def _load_configuration(self) -> None:
        """Load configuration from environment variables and .env file."""
        # Load .env file if it exists
        if self._env_file and Path(self._env_file).exists():
            load_dotenv(self._env_file)
        
        # Load default values first
        self._config = self.DEFAULT_CONFIG.copy()
        
        # Override with environment variables
        for key, default_value in self.DEFAULT_CONFIG.items():
            env_value = os.getenv(key)
            
            if env_value is not None:
                try:
                    # Convert environment variable to appropriate type
                    self._config[key] = self._convert_env_value(env_value, type(default_value))
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        key, 
                        f"Invalid value '{env_value}' for {key}: {str(e)}"
                    )
        
        # Validate configuration
        self._validate_configuration()
    
    def _convert_env_value(self, value: str, target_type: type) -> ConfigValue:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value (str): Environment variable value
            target_type (type): Target type for conversion
            
        Returns:
            ConfigValue: Converted value
            
        Raises:
            ValueError: If conversion fails
        """
        if target_type == bool:
            return value.lower() in ('true', '1', 'yes', 'on', 'enabled')
        elif target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == list:
            # Handle comma-separated lists
            return [item.strip() for item in value.split(',')]
        else:
            return value
    
    def _validate_configuration(self) -> None:
        """Validate configuration values."""
        # Validate numeric ranges
        if self.get_max_history_size() < 1:
            raise ConfigurationError(
                "CALCULATOR_MAX_HISTORY_SIZE",
                "Must be at least 1"
            )
        
        if self.get_precision() < 0 or self.get_precision() > 50:
            raise ConfigurationError(
                "CALCULATOR_PRECISION",
                "Must be between 0 and 50"
            )
        
        if self.get_max_input_value() <= 0:
            raise ConfigurationError(
                "CALCULATOR_MAX_INPUT_VALUE",
                "Must be positive"
            )
        
        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.get_log_level().upper() not in valid_log_levels:
            raise ConfigurationError(
                "CALCULATOR_LOG_LEVEL",
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        
        # Validate file encoding
        try:
            "test".encode(self.get_default_encoding())
        except LookupError:
            raise ConfigurationError(
                "CALCULATOR_DEFAULT_ENCODING",
                f"Invalid encoding: {self.get_default_encoding()}"
            )
    
    def _create_directories(self) -> None:
        """Create required directories for enabled features.

        Only create the log directory when logging is enabled and the history
        directory when auto-save is enabled. This keeps the repository root
        clean and aligned with assignment structure while remaining functional
        when features are used.
        """
        directories = []
        if self.is_logging_enabled():
            directories.append(self.get_log_dir())
        if self.is_auto_save_enabled():
            directories.append(self.get_history_dir())

        for directory in directories:
            try:
                Path(directory).mkdir(parents=True, exist_ok=True)
            except OSError as e:
                raise ConfigurationError(
                    directory,
                    f"Failed to create directory: {str(e)}"
                )
    
    # Base Directory Settings
    def get_log_dir(self) -> str:
        """Get the log directory path."""
        return str(self._config["CALCULATOR_LOG_DIR"])
    
    def get_history_dir(self) -> str:
        """Get the history directory path."""
        return str(self._config["CALCULATOR_HISTORY_DIR"])
    
    # History Settings
    def get_max_history_size(self) -> int:
        """Get maximum number of history entries."""
        return int(self._config["CALCULATOR_MAX_HISTORY_SIZE"])
    
    def get_auto_save(self) -> bool:
        """Get auto-save enabled status."""
        return bool(self._config["CALCULATOR_AUTO_SAVE"])
    
    # Calculation Settings
    def get_precision(self) -> int:
        """Get number of decimal places for calculations."""
        return int(self._config["CALCULATOR_PRECISION"])
    
    def get_max_input_value(self) -> float:
        """Get maximum allowed input value."""
        return float(self._config["CALCULATOR_MAX_INPUT_VALUE"])
    
    def get_default_encoding(self) -> str:
        """Get default file encoding."""
        return str(self._config["CALCULATOR_DEFAULT_ENCODING"])
    
    # Logging Settings
    def get_log_level(self) -> str:
        """Get logging level."""
        return str(self._config["CALCULATOR_LOG_LEVEL"])
    
    def get_log_file(self) -> str:
        """Get log file name."""
        return str(self._config["CALCULATOR_LOG_FILE"])
    
    def get_log_file_path(self) -> str:
        """Get full log file path."""
        return str(Path(self.get_log_dir()) / self.get_log_file())
    
    def get_log_format(self) -> str:
        """Get log message format."""
        return str(self._config["CALCULATOR_LOG_FORMAT"])
    
    # File Settings
    def get_history_file(self) -> str:
        """Get history file name."""
        return str(self._config["CALCULATOR_HISTORY_FILE"])
    
    def get_history_file_path(self) -> str:
        """Get full history file path."""
        return str(Path(self.get_history_dir()) / self.get_history_file())
    
    def get_config_file(self) -> str:
        """Get configuration file name."""
        return str(self._config["CALCULATOR_CONFIG_FILE"])
    
    # Performance Settings
    def get_memento_max_size(self) -> int:
        """Get maximum memento stack size."""
        return int(self._config["CALCULATOR_MEMENTO_MAX_SIZE"])
    
    def get_observer_timeout(self) -> int:
        """Get observer operation timeout in seconds."""
        return int(self._config["CALCULATOR_OBSERVER_TIMEOUT"])
    
    # Feature Flags
    def is_logging_enabled(self) -> bool:
        """Check if logging is enabled."""
        return bool(self._config["CALCULATOR_ENABLE_LOGGING"])
    
    def is_auto_save_enabled(self) -> bool:
        """Check if auto-save is enabled."""
        return bool(self._config["CALCULATOR_ENABLE_AUTO_SAVE"])
    
    def is_undo_redo_enabled(self) -> bool:
        """Check if undo/redo is enabled."""
        return bool(self._config["CALCULATOR_ENABLE_UNDO_REDO"])
    
    # Configuration Management
    def get_config_value(self, key: str, default: Any = None) -> ConfigValue:
        """
        Get a configuration value by key.
        
        Args:
            key (str): Configuration key
            default: Default value if key not found
            
        Returns:
            ConfigValue: Configuration value
        """
        return self._config.get(key, default)
    
    def set_config_value(self, key: str, value: ConfigValue) -> None:
        """
        Set a configuration value.
        
        Args:
            key (str): Configuration key
            value (ConfigValue): New value
            
        Raises:
            ConfigurationError: If value is invalid
        """
        # Validate key exists in defaults (optional)
        if key in self.DEFAULT_CONFIG:
            # Validate type matches default
            default_type = type(self.DEFAULT_CONFIG[key])
            if not isinstance(value, default_type):
                try:
                    value = self._convert_env_value(str(value), default_type)
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        key,
                        f"Invalid type for {key}: expected {default_type.__name__}, got {type(value).__name__}"
                    )
        
        self._config[key] = value
        
        # Re-validate configuration
        self._validate_configuration()
    
    def get_all_config(self) -> ConfigDict:
        """
        Get all configuration values.
        
        Returns:
            ConfigDict: Copy of all configuration values
        """
        return self._config.copy()
    
    def reload_config(self) -> None:
        """Reload configuration from .env file and environment variables."""
        self._load_configuration()
        
        if self._auto_create_dirs:
            self._create_directories()
    
    def export_config(self, file_path: Optional[str] = None) -> str:
        """
        Export configuration to JSON file.
        
        Args:
            file_path (str, optional): Path to export file
            
        Returns:
            str: JSON string of configuration
        """
        try:
            config_json = json.dumps(self._config, indent=2, default=str)
            
            if file_path:
                with open(file_path, 'w', encoding=self.get_default_encoding()) as f:
                    f.write(config_json)
            
            return config_json
            
        except Exception as e:
            raise ConfigurationError(
                file_path or "export",
                f"Failed to export configuration: {str(e)}"
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current configuration.
        
        Returns:
            Dict[str, Any]: Configuration summary
        """
        return {
            "env_file": self._env_file,
            "log_dir": self.get_log_dir(),
            "history_dir": self.get_history_dir(),
            "log_file_path": self.get_log_file_path(),
            "history_file_path": self.get_history_file_path(),
            "precision": self.get_precision(),
            "max_history_size": self.get_max_history_size(),
            "features_enabled": {
                "logging": self.is_logging_enabled(),
                "auto_save": self.is_auto_save_enabled(),
                "undo_redo": self.is_undo_redo_enabled()
            },
            "directories_exist": {
                "log_dir": Path(self.get_log_dir()).exists(),
                "history_dir": Path(self.get_history_dir()).exists()
            }
        }
    
    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"CalculatorConfig(env_file={self._env_file}, keys={len(self._config)})"
    
    def __repr__(self) -> str:
        """Developer representation of the configuration."""
        return (f"CalculatorConfig(env_file='{self._env_file}', "
                f"log_dir='{self.get_log_dir()}', "
                f"history_dir='{self.get_history_dir()}', "
                f"precision={self.get_precision()})")


# Global configuration instance
_config_instance: Optional[CalculatorConfig] = None


def get_config(env_file: Optional[str] = None, reload: bool = False) -> CalculatorConfig:
    """
    Get the global configuration instance.
    
    Args:
        env_file (str, optional): Path to .env file
        reload (bool): Whether to reload configuration
        
    Returns:
        CalculatorConfig: Global configuration instance
    """
    global _config_instance
    
    if _config_instance is None or reload:
        _config_instance = CalculatorConfig(env_file)
    
    return _config_instance


def reset_config() -> None:
    """Reset the global configuration instance."""
    global _config_instance
    _config_instance = None