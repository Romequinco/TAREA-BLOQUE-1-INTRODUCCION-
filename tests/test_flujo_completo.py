"""
Test de Flujo Completo - Muestra el flujo end-to-end: Extracción → Preprocessing → Análisis → Reporting

Este test demuestra cómo los datos descargados se usan para análisis y reportes.

Ejecutar desde terminal:
    python tests/test_flujo_completo.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Semilla común para reproducibilidad
np.random.seed(42)

# Configurar path del proyecto
from conftest import setup_project_path, print_separator
setup_project_path()

try:
    from src.extractors import YFinanceExtractor
    from src.data_classes import PriceSeries, Portfolio
    from src.preprocessing import DataCleaner, validate_time_series_completeness
    from src.analysis import MonteCarloSimulator
    from src.reporting import MarkdownReportGenerator, VisualizationReport
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError as e:
    print(f"ERROR: Error al importar modulos: {e}")
    print("\nPor favor, asegurate de que:")
    print("1. Estas en el directorio raiz del proyecto")
    print("2. Has instalado las dependencias: pip install -r requirements.txt")
    sys.exit(1)


def test_flujo_completo_activo():
    """Test del flujo completo para un activo individual"""
    print_separator("FLUJO COMPLETO: ACTIVO INDIVIDUAL")
    
    # ========================================================================
    # PASO 1: EXTRACCIÓN
    # ========================================================================
    print("PASO 1: EXTRACCIÓN DE DATOS")
    print("=" * 200)
    print("Descargando datos históricos desde Yahoo Finance...")
    print("-" * 200)
    
    extractor = YFinanceExtractor()
    price_series = extractor.fetch_historical_prices(
        ticker="AAPL",
        start_date=datetime.now() - timedelta(days=365)
    )
    
    print(f"[OK] Datos descargados exitosamente")
    print(f"  - Ticker: {price_series.ticker}")
    print(f"  - Nombre: {price_series.name}")
    print(f"  - Puntos de datos: {len(price_series.data)}")
    print(f"  - Rango: {price_series.data['date'].min().date()} a {price_series.data['date'].max().date()}")
    print(f"  - Precio promedio: ${price_series.data['adj close'].mean():.2f}")
    
    # ========================================================================
    # PASO 2: PREPROCESSING
    # ========================================================================
    print("\nPASO 2: PREPROCESSING (Validación y Limpieza)")
    print("=" * 200)
    
    print("2.1: Validando datos descargados...")
    print("-" * 200)
    validation = price_series.validate()
    print(f"[OK] Validación completada")
    print(f"  - Tiene errores: {validation.has_errors}")
    print(f"  - Issues encontrados: {len(validation.issues)}")
    if validation.issues:
        for issue in validation.issues[:3]:
            print(f"    * {issue.severity}: {issue.message}")
    
    print("\n2.2: Limpiando datos...")
    print("-" * 200)
    price_series.clean()
    print(f"[OK] Limpieza completada")
    print(f"  - Valores nulos: {price_series.data['adj close'].isna().sum()}")
    print(f"  - Fechas duplicadas: {price_series.data['date'].duplicated().sum()}")
    
    # ========================================================================
    # PASO 3: ANÁLISIS
    # ========================================================================
    print("\nPASO 3: ANÁLISIS MONTE CARLO")
    print("=" * 200)
    
    print("3.1: Configurando simulador...")
    print("-" * 200)
    simulator = MonteCarloSimulator(
        method="gbm",
        horizon=252,
        num_simulations=100,
        seed=42
    )
    print(f"[OK] Simulador configurado")
    print(f"  - Método: GBM")
    print(f"  - Horizonte: 252 días (1 año)")
    print(f"  - Simulaciones: 100")
    
    print("\n3.2: Ejecutando simulación...")
    print("-" * 200)
    mc_result = simulator.simulate_price_series(price_series)
    print(f"[OK] Simulación completada")
    print(f"  - Shape: {mc_result.paths.shape}")
    
    print("\n3.3: Analizando resultados...")
    print("-" * 200)
    summary = mc_result.scenario_summary()
    print(f"[OK] Análisis completado")
    print(f"  - Escenario base (50%): ${summary['base_case']:.2f}")
    print(f"  - Escenario peor (5%): ${summary['worst_case']:.2f}")
    print(f"  - Escenario mejor (95%): ${summary['best_case']:.2f}")
    print(f"  - VaR 5%: ${summary['var_5']:.2f}")
    print(f"  - CVaR 5%: ${summary['cvar_5']:.2f}")
    
    # ========================================================================
    # PASO 4: REPORTING
    # ========================================================================
    print("\nPASO 4: REPORTING")
    print("=" * 200)
    
    print("4.1: Generando reporte Markdown...")
    print("-" * 200)
    generator = MarkdownReportGenerator()
    report_md = generator.price_series_report(price_series)
    print(f"[OK] Reporte Markdown generado")
    print(f"  - Longitud: {len(report_md)} caracteres")
    print(f"  - Líneas: {len(report_md.split(chr(10)))}")
    
    print("\n4.2: Generando visualizaciones...")
    print("-" * 200)
    if HAS_MATPLOTLIB:
        viz = VisualizationReport(theme="light")
        figures = viz.price_series_plots(price_series)
        print(f"[OK] Visualizaciones generadas")
        print(f"  - Número de gráficos: {len(figures)}")
        print(f"  - Tipos: {list(figures.keys())}")
        
        # Cerrar figuras
        for fig in figures.values():
            plt.close(fig)
        print(f"  - Figuras cerradas")
    else:
        print("[WARNING] matplotlib no disponible, saltando visualizaciones")
    
    print("\n" + "=" * 200)
    print("[OK] FLUJO COMPLETO FINALIZADO")
    print("=" * 200)
    print("\nResumen del flujo:")
    print("  1. ✓ Datos descargados desde Yahoo Finance")
    print("  2. ✓ Datos validados y limpiados")
    print("  3. ✓ Simulación Monte Carlo ejecutada")
    print("  4. ✓ Reportes y visualizaciones generados")
    print("\nTodos los pasos usaron los mismos datos descargados inicialmente.")


def test_flujo_completo_portfolio():
    """Test del flujo completo para un portfolio"""
    print_separator("FLUJO COMPLETO: PORTFOLIO")
    
    # ========================================================================
    # PASO 1: EXTRACCIÓN MÚLTIPLE
    # ========================================================================
    print("PASO 1: EXTRACCIÓN DE MÚLTIPLES ACTIVOS")
    print("=" * 200)
    
    extractor = YFinanceExtractor()
    tickers = ["AAPL", "MSFT"]
    holdings = {}
    
    for ticker in tickers:
        print(f"  Descargando {ticker}...")
        try:
            series = extractor.fetch_historical_prices(
                ticker=ticker,
                start_date=datetime.now() - timedelta(days=180)
            )
            holdings[ticker] = series
            print(f"    [OK] {ticker}: {len(series.data)} puntos")
        except Exception as e:
            print(f"    [ERROR] {ticker}: {e}")
    
    if len(holdings) < 2:
        print("[WARNING] No se pudieron descargar suficientes datos, usando datos de prueba")
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        holdings = {
            "AAPL": PriceSeries(ticker="AAPL", data=pd.DataFrame({
                'date': dates,
                'close': 100 + np.random.randn(100).cumsum(),
                'adj close': 100 + np.random.randn(100).cumsum()
            })),
            "MSFT": PriceSeries(ticker="MSFT", data=pd.DataFrame({
                'date': dates,
                'close': 150 + np.random.randn(100).cumsum(),
                'adj close': 150 + np.random.randn(100).cumsum()
            }))
        }
    
    print(f"[OK] Total de activos descargados: {len(holdings)}")
    
    # ========================================================================
    # PASO 2: CREAR PORTFOLIO
    # ========================================================================
    print("\nPASO 2: CREACIÓN DE PORTFOLIO")
    print("=" * 200)
    
    weights = {ticker: 1.0/len(holdings) for ticker in holdings.keys()}
    portfolio = Portfolio(
        holdings=holdings,
        weights=weights,
        name="Portfolio de Prueba"
    )
    print(f"[OK] Portfolio creado")
    print(f"  - Activos: {list(portfolio.holdings.keys())}")
    print(f"  - Pesos: {weights}")
    
    # ========================================================================
    # PASO 3: ANÁLISIS DEL PORTFOLIO
    # ========================================================================
    print("\nPASO 3: ANÁLISIS DEL PORTFOLIO")
    print("=" * 200)
    
    print("3.1: Métricas del portfolio...")
    print("-" * 200)
    returns = portfolio.get_portfolio_returns()
    volatility = portfolio.portfolio_volatility()
    print(f"[OK] Métricas calculadas")
    print(f"  - Retorno medio diario: {returns.mean()*100:.4f}%")
    print(f"  - Volatilidad anualizada: {volatility*100:.2f}%")
    
    print("\n3.2: Simulación Monte Carlo del portfolio...")
    print("-" * 200)
    mc_result = portfolio.monte_carlo(
        method="gbm",
        horizon=60,
        num_simulations=50,
        seed=42
    )
    print(f"[OK] Simulación completada")
    print(f"  - Shape: {mc_result.paths.shape}")
    print(f"  - Valor final promedio: ${mc_result.paths[:, -1].mean():.2f}")
    
    # ========================================================================
    # PASO 4: REPORTES DEL PORTFOLIO
    # ========================================================================
    print("\nPASO 4: REPORTES DEL PORTFOLIO")
    print("=" * 200)
    
    print("4.1: Generando reporte Markdown...")
    print("-" * 200)
    generator = MarkdownReportGenerator()
    report = generator.portfolio_report(portfolio)
    print(f"[OK] Reporte generado: {len(report)} caracteres")
    
    print("\n4.2: Generando visualizaciones...")
    print("-" * 200)
    if HAS_MATPLOTLIB:
        viz = VisualizationReport()
        figures = viz.portfolio_plots(portfolio)
        print(f"[OK] Visualizaciones generadas: {len(figures)} gráficos")
        for fig in figures.values():
            plt.close(fig)
    else:
        print("[WARNING] matplotlib no disponible")
    
    print("\n" + "=" * 200)
    print("[OK] FLUJO COMPLETO DE PORTFOLIO FINALIZADO")
    print("=" * 200)


def main():
    """Función principal que ejecuta el flujo completo"""
    print_separator("INICIO DE TEST DE FLUJO COMPLETO")
    print("Este test demuestra el flujo completo del sistema:")
    print("  1. Extracción de datos desde APIs externas")
    print("  2. Preprocessing (validación y limpieza)")
    print("  3. Análisis (simulaciones Monte Carlo)")
    print("  4. Reporting (reportes Markdown y visualizaciones)")
    print("\nTodos los pasos usan los mismos datos descargados.\n")
    
    # Test 1: Activo individual
    test_flujo_completo_activo()
    
    # Test 2: Portfolio
    test_flujo_completo_portfolio()
    
    print_separator("FIN DE TEST DE FLUJO COMPLETO")
    print("[OK] Todos los flujos completados exitosamente.")


if __name__ == "__main__":
    main()

