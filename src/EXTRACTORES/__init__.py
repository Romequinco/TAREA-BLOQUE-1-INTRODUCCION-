"""
Paquetes de extractores de datos.

Cada extractir hereda de una base llamada BaseExtractor, para garantizar 
que todos tengan una interfaz y estructura comun.
"""

from .base_extractor import BaseExtractor
from .yfinance_extractor import YFinanceExtractor
from .alphavantage_extractor import AlphaVantageExtractor

__all__ = [
    'BaseExtractor',
    'YFinanceExtractor',
    'AlphaVantageExtractor',
]
