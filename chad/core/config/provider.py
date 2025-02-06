"""Configuration management implementation for CHAD."""

from typing import Any, Dict, Optional
import os
import yaml
from pathlib import Path
from ..interfaces import ConfigurationProvider
from ..errors import ConfigurationError, ConfigNotFoundError, InvalidConfigError


class YAMLConfigProvider(ConfigurationProvider):
    """Configuration provider using YAML files with environment override support."""

    def __init__(
        self,
        config_path: str,
        env_prefix: str = "CHAD_",
        secrets_path: Optional[str] = None
    ):
        self._config: Dict[str, Any] = {}
        self._config_path = Path(config_path)
        self._env_prefix = env_prefix
        self._secrets_path = Path(secrets_path) if secrets_path else None
        self._loaded = False

    async def load(self, source: str) -> Dict[str, Any]:
        """Load configuration from a source.

        Args:
            source: Path to configuration file

        Returns:
            Loaded configuration dictionary
        """
        try:
            config = await self._load_yaml(Path(source))
            return config
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {source}: {str(e)}")

    async def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the configuration provider."""
        try:
            # Load base configuration
            self._config = await self.load(str(self._config_path))

            # Load secrets if configured
            if self._secrets_path and self._secrets_path.exists():
                secrets = await self.load(str(self._secrets_path))
                self._merge_dict(self._config, secrets)

            # Override with environment variables
            self._apply_env_overrides()

            # Apply any additional config passed to initialize
            if config:
                self._merge_dict(self._config, config)

            self._loaded = True

        except Exception as e:
            raise ConfigurationError(
                f"Failed to initialize configuration: {str(e)}")

    async def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        if not self._loaded:
            raise ConfigurationError("Configuration not initialized")

        try:
            value = self._get_nested(self._config, key)
            return value if value is not None else default
        except KeyError:
            return default

    async def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        if not self._loaded:
            raise ConfigurationError("Configuration not initialized")

        try:
            self._set_nested(self._config, key, value)
        except Exception as e:
            raise InvalidConfigError(f"Failed to set config value: {str(e)}")

    async def has(self, key: str) -> bool:
        """Check if configuration key exists."""
        try:
            value = await self.get(key)
            return value is not None
        except:
            return False

    async def get_namespace(self, namespace: str) -> Dict[str, Any]:
        """Get all configuration values under a namespace."""
        if not self._loaded:
            raise ConfigurationError("Configuration not initialized")

        result = {}
        for key, value in self._flatten_dict(self._config).items():
            if key.startswith(namespace):
                result[key] = value
        return result

    @staticmethod
    async def _load_yaml(path: Path) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load config file {path}: {str(e)}")

    def _merge_dict(self, base: Dict, override: Dict) -> None:
        """Recursively merge override dict into base dict."""
        for key, value in override.items():
            if (
                key in base and
                isinstance(base[key], dict) and
                isinstance(value, dict)
            ):
                self._merge_dict(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        for key, value in os.environ.items():
            if key.startswith(self._env_prefix):
                config_key = key[len(self._env_prefix):].lower().replace('__', '.')
                try:
                    # Try to parse as YAML for type conversion
                    parsed_value = yaml.safe_load(value)
                    # Ensure numeric strings are converted to numbers
                    if isinstance(parsed_value, str):
                        try:
                            if '.' in parsed_value:
                                parsed_value = float(parsed_value)
                            else:
                                parsed_value = int(parsed_value)
                        except ValueError:
                            pass  # Keep as string if conversion fails
                    self._set_nested(self._config, config_key, parsed_value)
                except yaml.YAMLError:
                    # Fallback to string value if YAML parsing fails
                    self._set_nested(self._config, config_key, value)

    def _get_nested(self, d: Dict, key: str) -> Any:
        """Get nested dictionary value using dot notation."""
        keys = key.split('.')
        current = d

        for k in keys:
            if not isinstance(current, dict):
                raise KeyError(f"Cannot access '{k}' in '{key}'")
            if k not in current:
                raise KeyError(f"Key '{k}' not found in '{key}'")
            current = current[k]

        return current

    def _set_nested(self, d: Dict, key: str, value: Any) -> None:
        """Set nested dictionary value using dot notation."""
        keys = key.split('.')
        current = d

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def _flatten_dict(self, d: Dict, parent_key: str = '') -> Dict[str, Any]:
        """Flatten nested dictionary using dot notation."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
