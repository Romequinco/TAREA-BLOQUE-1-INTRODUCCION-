"""Carga y validación avanzada de configuración."""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from dotenv import load_dotenv

from .exceptions import ConfigurationError


def _import_python_config(module_path: str) -> Dict[str, Any]:
    """Importa un módulo de configuración estilo Flask (constantes en mayúsculas)."""

    try:
        module = __import__(module_path, fromlist=["*"])
    except ImportError:
        return {}

    return {
        key: getattr(module, key)
        for key in dir(module)
        if key.isupper()
    }


def _apply_overrides(base: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    result.update({key: value for key, value in overrides.items() if value is not None})
    return result


@dataclass
class ConfigManager:
    """Combinación de configuración desde archivo, entorno y CLI."""

    module_path: str = "config"
    env_file: Path = Path(".env")
    env_prefix: str = "APP_"
    defaults: Dict[str, Any] = field(default_factory=dict)
    config: Dict[str, Any] = field(init=False)

    def __post_init__(self) -> None:
        self.config = self.defaults.copy()
        self._load_from_module()
        self._load_from_env_file()
        self._load_from_environment()

    def _load_from_module(self) -> None:
        module_config = _import_python_config(self.module_path)
        self.config = _apply_overrides(self.config, module_config)

    def _load_from_env_file(self) -> None:
        if self.env_file.exists():
            load_dotenv(self.env_file, override=False)

    def _load_from_environment(self) -> None:
        env_config = {
            key[len(self.env_prefix) :]: value
            for key, value in os.environ.items()
            if key.startswith(self.env_prefix)
        }
        self.config = _apply_overrides(self.config, env_config)

    def apply_cli_arguments(self, args: Optional[Iterable[str]] = None) -> None:
        parser = argparse.ArgumentParser(add_help=False)
        for key in self.config.keys():
            parser.add_argument(f"--{key.lower()}")

        namespace, _ = parser.parse_known_args(args=args)
        cli_config = {
            key.upper(): value
            for key, value in vars(namespace).items()
            if value is not None
        }
        self.config = _apply_overrides(self.config, cli_config)

    def require(self, *keys: str) -> None:
        missing = [key for key in keys if key not in self.config or self.config[key] in (None, "")]
        if missing:
            raise ConfigurationError(f"Faltan claves obligatorias en la configuración: {missing}")

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return self.config.copy()


# Instancia global lista para usar
settings = ConfigManager(
    defaults={
        "ALPHAVANTAGE_API_KEY": None,
        "DATA_CACHE_DIR": ".cache",
        "LOG_LEVEL": "INFO",
        "ENV": "development",
    }
)


