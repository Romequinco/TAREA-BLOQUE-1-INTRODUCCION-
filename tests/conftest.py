"""Funciones y utilidades compartidas para los tests."""

from __future__ import annotations
import os
import sys
from pathlib import Path


def setup_project_path():
    """Configura el path del proyecto automáticamente. Llamar al inicio de cada test."""
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    # Buscar directorio raíz (maneja estructuras anidadas)
    for potential_root in [current_dir.parent, current_dir.parent.parent]:
        if (potential_root / "src").exists() and (potential_root / "tests").exists():
            project_root = potential_root
            break
    
    sys.path.insert(0, str(project_root))
    os.chdir(project_root)
    return project_root


def print_separator(title: str = ""):
    """Función común para imprimir separadores visuales en tests."""
    print("\n" + "=" * 200)
    if title:
        print(f"  {title}")
        print("=" * 200 + "\n")


