"""
Test de Reporting - Muestra paso a paso cómo funcionan reportes y visualizaciones.

Ejecutar desde terminal:
    python tests/test_reporting.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Semilla común para reproducibilidad
np.random.seed(42)

# Configurar path del proyecto (función común desde conftest)
from conftest import setup_project_path
setup_project_path()

try:
    from src.reporting import MarkdownReportGenerator, VisualizationReport
    from src.data_classes import PriceSeries, Portfolio
    from src.extractors import YFinanceExtractor
except ImportError as e:
    print(f"ERROR: Error al importar modulos: {e}")
    print("\nPor favor, asegurate de que:")
    print("1. Estas en el directorio raiz del proyecto")
    print("2. Has instalado las dependencias: pip install -r requirements.txt")
    sys.exit(1)

# Configurar matplotlib - REQUERIDO para visualizaciones
try:
    import matplotlib
    matplotlib.use('Agg')  # Backend sin display para tests
    import matplotlib.pyplot as plt
    import seaborn as sns
    from scipy import stats
    HAS_MATPLOTLIB = True
except ImportError as e:
    print(f"[ERROR] Dependencias de visualización no instaladas: {e}")
    print("\nPor favor, instala las dependencias necesarias:")
    print("  pip install matplotlib seaborn scipy")
    print("\nO instala todas las dependencias del proyecto:")
    print("  pip install -r requirements.txt")
    HAS_MATPLOTLIB = False
    matplotlib = None


# Importar función común desde conftest
from conftest import print_separator


def test_markdown_report_price_series():
    """Test de generación de reporte Markdown para PriceSeries - Paso a paso"""
    print_separator("TEST: REPORTE MARKDOWN PARA PRICE SERIES")
    
    print("PASO 1: Descargando datos reales desde Yahoo Finance")
    print("-" * 200)
    try:
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="AAPL",
            start_date=datetime.now() - timedelta(days=180)
        )
        print(f"[OK] Datos descargados: {len(price_series.data)} puntos")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Rango: {price_series.data['date'].min().date()} a {price_series.data['date'].max().date()}")
    except Exception as e:
        print(f"[WARNING] Error al descargar datos: {e}")
        print("  Usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        prices = 100 + np.random.randn(100).cumsum()
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'adj close': prices
        })
        price_series = PriceSeries(ticker="TEST", data=df, name="Activo de Prueba")
        print(f"[OK] PriceSeries creado: {len(price_series.data)} puntos")
    
    print("\nPASO 2: Creando generador de reportes Markdown")
    print("-" * 200)
    generator = MarkdownReportGenerator()
    print(f"[OK] Generador creado")
    
    print("\nPASO 3: Generando reporte para PriceSeries")
    print("-" * 200)
    report = generator.price_series_report(price_series)
    print(f"[OK] Reporte generado")
    print(f"  - Longitud del reporte: {len(report)} caracteres")
    print(f"  - Líneas: {len(report.split(chr(10)))}")
    
    print("\nPASO 4: Mostrando secciones del reporte")
    print("-" * 200)
    sections = ["Resumen Ejecutivo", "Métricas Clave", "Análisis de Riesgo"]
    for section in sections:
        if section in report:
            print(f"  [OK] Sección '{section}' encontrada")
        else:
            print(f"  ✗ Sección '{section}' no encontrada")
    
    print("\nPASO 5: Mostrando primeras 20 líneas del reporte")
    print("-" * 200)
    lines = report.split('\n')[:20]
    for i, line in enumerate(lines, 1):
        print(f"  {i:2d}: {line}")


def test_markdown_report_portfolio():
    """Test de generación de reporte Markdown para Portfolio - Paso a paso"""
    print_separator("TEST: REPORTE MARKDOWN PARA PORTFOLIO")
    
    print("PASO 1: Descargando datos reales para crear portfolio")
    print("-" * 200)
    try:
        extractor = YFinanceExtractor()
        print("  Descargando AAPL...")
        ps1 = extractor.fetch_historical_prices("AAPL", start_date=datetime.now() - timedelta(days=180))
        print("  Descargando MSFT...")
        ps2 = extractor.fetch_historical_prices("MSFT", start_date=datetime.now() - timedelta(days=180))
        print(f"[OK] Datos descargados: AAPL ({len(ps1.data)} puntos), MSFT ({len(ps2.data)} puntos)")
    except Exception as e:
        print(f"[WARNING] Error al descargar datos: {e}")
        print("  Usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        ps1 = PriceSeries(ticker="AAA", data=pd.DataFrame({
            'date': dates,
            'close': 100 + np.random.randn(100).cumsum(),
            'adj close': 100 + np.random.randn(100).cumsum()
        }))
        ps2 = PriceSeries(ticker="BBB", data=pd.DataFrame({
            'date': dates,
            'close': 150 + np.random.randn(100).cumsum(),
            'adj close': 150 + np.random.randn(100).cumsum()
        }))
    
    portfolio = Portfolio(
        holdings={"AAA": ps1, "BBB": ps2},
        weights={"AAA": 0.6, "BBB": 0.4},
        name="Portfolio de Prueba"
    )
    print(f"[OK] Portfolio creado: {len(portfolio.holdings)} activos")
    
    print("\nPASO 2: Generando reporte para Portfolio")
    print("-" * 200)
    generator = MarkdownReportGenerator()
    report = generator.portfolio_report(portfolio)
    print(f"[OK] Reporte generado")
    print(f"  - Longitud: {len(report)} caracteres")
    
    print("\nPASO 3: Verificando secciones del reporte")
    print("-" * 200)
    sections = ["Composición", "Métricas", "Riesgo"]
    for section in sections:
        if section in report:
            print(f"  [OK] Sección '{section}' encontrada")


def test_visualizations():
    """Test de generación de visualizaciones - Paso a paso"""
    print_separator("TEST: VISUALIZACIONES")
    
    # Verificar si matplotlib está disponible
    if not HAS_MATPLOTLIB:
        print("[ERROR] matplotlib no está instalado. Este test requiere visualizaciones.")
        print("  Por favor, instala las dependencias:")
        print("  pip install matplotlib seaborn scipy")
        print("  O: pip install -r requirements.txt")
        return
    
    print("PASO 1: Descargando datos reales desde Yahoo Finance")
    print("-" * 200)
    try:
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="MSFT",
            start_date=datetime.now() - timedelta(days=180)
        )
        print(f"[OK] Datos descargados: {len(price_series.data)} puntos")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Nombre: {price_series.name}")
    except Exception as e:
        print(f"[WARNING] Error al descargar datos: {e}")
        print("  Usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        prices = 100 + np.random.randn(100).cumsum()
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'adj close': prices
        })
        price_series = PriceSeries(ticker="TEST", data=df)
        print(f"[OK] PriceSeries creado: {len(price_series.data)} puntos")
    
    print("\nPASO 2: Creando generador de visualizaciones")
    print("-" * 200)
    try:
        viz = VisualizationReport(theme="light")
        print(f"[OK] Generador creado (tema: {viz.theme})")
    except Exception as e:
        print(f"[ERROR] Error al crear generador de visualizaciones: {str(e)}")
        print("  Asegúrate de tener instalado: matplotlib, seaborn, scipy")
        return
    
    print("\nPASO 3: Generando gráficos para PriceSeries")
    print("-" * 200)
    try:
        figures = viz.price_series_plots(price_series)
        print(f"[OK] Gráficos generados")
        print(f"  - Número de figuras: {len(figures)}")
        print(f"  - Tipos de gráficos:")
        for key in figures.keys():
            print(f"    * {key}")
    except Exception as e:
        print(f"[ERROR] Error al generar gráficos: {str(e)}")
        return
    
    print("\nPASO 4: Cerrando figuras para liberar memoria")
    print("-" * 200)
    for fig in figures.values():
        plt.close(fig)
    print(f"[OK] Figuras cerradas")
    
    print("\nPASO 5: Generando gráficos para Portfolio")
    print("-" * 200)
    print("  Descargando datos para portfolio...")
    try:
        extractor = YFinanceExtractor()
        ps1 = extractor.fetch_historical_prices("AAPL", start_date=datetime.now() - timedelta(days=180))
        ps2 = extractor.fetch_historical_prices("GOOGL", start_date=datetime.now() - timedelta(days=180))
        print(f"  [OK] Datos descargados: AAPL ({len(ps1.data)} puntos), GOOGL ({len(ps2.data)} puntos)")
    except Exception as e:
        print(f"  [WARNING] Error al descargar: {e}, usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        ps1 = PriceSeries(ticker="AAA", data=pd.DataFrame({
            'date': dates,
            'close': 100 + np.random.randn(100).cumsum(),
            'adj close': 100 + np.random.randn(100).cumsum()
        }))
        ps2 = PriceSeries(ticker="BBB", data=pd.DataFrame({
            'date': dates,
            'close': 150 + np.random.randn(100).cumsum(),
            'adj close': 150 + np.random.randn(100).cumsum()
        }))
    
    portfolio = Portfolio(
        holdings={"AAA": ps1, "BBB": ps2},
        weights={"AAA": 0.6, "BBB": 0.4}
    )
    
    try:
        portfolio_figures = viz.portfolio_plots(portfolio, benchmark=price_series)
        print(f"[OK] Gráficos de portfolio generados")
        print(f"  - Número de figuras: {len(portfolio_figures)}")
        print(f"  - Tipos de gráficos:")
        for key in portfolio_figures.keys():
            print(f"    * {key}")
    except Exception as e:
        print(f"[ERROR] Error al generar gráficos de portfolio: {str(e)}")
        return
    
    print("\nPASO 6: Cerrando todas las figuras")
    print("-" * 200)
    for fig in portfolio_figures.values():
        plt.close(fig)
    print(f"[OK] Todas las figuras cerradas")


def main():
    """Función principal que ejecuta todos los tests de reporting"""
    print_separator("INICIO DE TESTS DE REPORTING")
    print("Este script prueba todas las funcionalidades de reporting paso a paso.\n")
    
    # Test 1: Reporte Markdown para PriceSeries
    test_markdown_report_price_series()
    
    # Test 2: Reporte Markdown para Portfolio
    test_markdown_report_portfolio()
    
    # Test 3: Visualizaciones
    test_visualizations()
    
    print_separator("FIN DE TESTS DE REPORTING")
    print("[OK] Todos los tests de reporting completados.")


if __name__ == "__main__":
    main()

