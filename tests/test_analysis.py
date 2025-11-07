"""
Test de Analysis (Monte Carlo) - Muestra paso a paso cómo funcionan las simulaciones.

Ejecutar desde terminal:
    python tests/test_analysis.py
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
    from src.analysis import MonteCarloSimulator, MonteCarloResult
    from src.data_classes import PriceSeries, Portfolio
    from src.extractors import YFinanceExtractor
except ImportError as e:
    print(f"ERROR: Error al importar modulos: {e}")
    print("\nPor favor, asegurate de que:")
    print("1. Estas en el directorio raiz del proyecto")
    print("2. Has instalado las dependencias: pip install -r requirements.txt")
    sys.exit(1)


# Importar función común desde conftest
from conftest import print_separator


def test_monte_carlo_gbm():
    """Test de simulación Monte Carlo con método GBM - Paso a paso"""
    print_separator("TEST: SIMULACION MONTE CARLO - METODO GBM")
    
    print("PASO 1: Obteniendo datos históricos para simulación")
    print("-" * 200)
    try:
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="AAPL",
            start_date=datetime.now() - timedelta(days=365)
        )
        print(f"[OK] Datos obtenidos: {len(price_series.data)} puntos")
    except:
        # Datos de prueba si falla
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        prices = 100 + np.random.randn(100).cumsum()
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'adj close': prices
        })
        price_series = PriceSeries(ticker="TEST", data=df)
        print(f"[OK] Datos de prueba creados: {len(price_series.data)} puntos")
    
    print("\nPASO 2: Configurando simulador Monte Carlo (método GBM)")
    print("-" * 200)
    simulator = MonteCarloSimulator(
        method="gbm",
        horizon=252,  # 1 año de trading days
        num_simulations=100,
        freq="D",
        seed=42  # Semilla común para reproducibilidad
    )
    print(f"[OK] Simulador configurado")
    print(f"  - Método: GBM (Geometric Brownian Motion)")
    print(f"  - Horizonte: {simulator.horizon} días")
    print(f"  - Número de simulaciones: {simulator.num_simulations}")
    print(f"  - Frecuencia: {simulator.freq}")
    print(f"  - Seed: {simulator.seed}")
    
    print("\nPASO 3: Ejecutando simulación Monte Carlo")
    print("-" * 200)
    result = simulator.simulate_price_series(price_series)
    print(f"[OK] Simulación completada")
    print(f"  - Shape de paths: {result.paths.shape}")
    print(f"  - Número de fechas: {len(result.dates)}")
    print(f"  - Metadata: {result.metadata}")
    
    print("\nPASO 4: Analizando resultados de la simulación")
    print("-" * 200)
    print(f"[OK] Análisis de resultados:")
    print(f"  - Precio inicial: ${result.paths[0, 0]:.2f}")
    print(f"  - Precio final promedio: ${result.paths[:, -1].mean():.2f}")
    print(f"  - Precio final mínimo: ${result.paths[:, -1].min():.2f}")
    print(f"  - Precio final máximo: ${result.paths[:, -1].max():.2f}")
    
    print("\nPASO 5: Calculando percentiles")
    print("-" * 200)
    percentiles = result.percentile([5, 50, 95])
    print(f"[OK] Percentiles calculados:")
    print(f"  - Percentil 5 (worst case): ${percentiles['p5'].iloc[-1]:.2f}")
    print(f"  - Percentil 50 (median): ${percentiles['p50'].iloc[-1]:.2f}")
    print(f"  - Percentil 95 (best case): ${percentiles['p95'].iloc[-1]:.2f}")
    
    print("\nPASO 6: Calculando Value at Risk (VaR)")
    print("-" * 200)
    var_5 = result.value_at_risk(alpha=0.05)
    var_1 = result.value_at_risk(alpha=0.01)
    print(f"[OK] VaR calculado:")
    print(f"  - VaR 5%: ${var_5:.2f}")
    print(f"  - VaR 1%: ${var_1:.2f}")
    
    print("\nPASO 7: Calculando Conditional Value at Risk (CVaR)")
    print("-" * 200)
    cvar_5 = result.conditional_value_at_risk(alpha=0.05)
    print(f"[OK] CVaR calculado:")
    print(f"  - CVaR 5%: ${cvar_5:.2f}")
    
    print("\nPASO 8: Obteniendo resumen de escenarios")
    print("-" * 200)
    summary = result.scenario_summary(best=95.0, base=50.0, worst=5.0)
    print(f"[OK] Resumen de escenarios:")
    for key, value in summary.items():
        print(f"  - {key}: ${value:.2f}")


def test_monte_carlo_historical():
    """Test de simulación Monte Carlo con método histórico - Paso a paso"""
    print_separator("TEST: SIMULACION MONTE CARLO - METODO HISTORICO")
    
    print("PASO 1: Descargando datos históricos para bootstrap")
    print("-" * 200)
    try:
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="TSLA",
            start_date=datetime.now() - timedelta(days=180)
        )
        print(f"[OK] Datos descargados: {len(price_series.data)} puntos")
        print(f"  - Ticker: {price_series.ticker}")
    except Exception as e:
        print(f"[WARNING] Error al descargar: {e}")
        print("  Usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
        prices = 100 + np.random.randn(100).cumsum()
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'adj close': prices
        })
        price_series = PriceSeries(ticker="TEST", data=df)
        print(f"[OK] Datos creados: {len(price_series.data)} puntos")
    
    print("\nPASO 2: Configurando simulador (método histórico/bootstrap)")
    print("-" * 200)
    simulator = MonteCarloSimulator(
        method="historical",
        horizon=60,
        num_simulations=50,
        seed=42  # Semilla común para reproducibilidad
    )
    print(f"[OK] Simulador configurado (método histórico)")
    
    print("\nPASO 3: Ejecutando simulación bootstrap histórico")
    print("-" * 200)
    result = simulator.simulate_price_series(price_series)
    print(f"[OK] Simulación completada")
    print(f"  - Shape: {result.paths.shape}")
    print(f"  - Precio final promedio: ${result.paths[:, -1].mean():.2f}")


def test_monte_carlo_portfolio():
    """Test de simulación Monte Carlo para portfolio - Paso a paso"""
    print_separator("TEST: SIMULACION MONTE CARLO PARA PORTFOLIO")
    
    print("PASO 1: Descargando datos reales para crear portfolio")
    print("-" * 200)
    extractor = YFinanceExtractor()
    tickers = ["AAPL", "MSFT"]
    holdings = {}
    
    for ticker in tickers:
        try:
            print(f"  Descargando {ticker}...")
            ps = extractor.fetch_historical_prices(
                ticker=ticker,
                start_date=datetime.now() - timedelta(days=180)
            )
            holdings[ticker] = ps
            print(f"    [OK] {ticker}: {len(ps.data)} puntos")
        except Exception as e:
            print(f"    [ERROR] {ticker}: {e}")
            # Crear datos de prueba si falla
            dates = pd.date_range(start='2024-01-01', periods=100, freq='B')
            prices = 100 + np.random.randn(100).cumsum() if ticker == "AAPL" else 150 + np.random.randn(100).cumsum()
            holdings[ticker] = PriceSeries(ticker=ticker, data=pd.DataFrame({
                'date': dates,
                'close': prices,
                'adj close': prices
            }))
            print(f"    [OK] {ticker}: Datos de prueba creados")
    
    from src.data_classes import Portfolio
    portfolio = Portfolio(
        holdings=holdings,
        weights={ticker: 1.0/len(holdings) for ticker in holdings.keys()},
        name="Test Portfolio"
    )
    print(f"[OK] Portfolio creado: {len(portfolio.holdings)} activos")
    print(f"  - Activos: {list(portfolio.holdings.keys())}")
    
    print("\nPASO 2: Configurando simulador para portfolio")
    print("-" * 200)
    simulator = MonteCarloSimulator(
        method="gbm",
        horizon=60,
        num_simulations=30,
        seed=42  # Semilla común para reproducibilidad
    )
    print(f"[OK] Simulador configurado")
    
    print("\nPASO 3: Ejecutando simulación para portfolio")
    print("-" * 200)
    result = portfolio.monte_carlo(
        method="gbm",
        horizon=60,
        num_simulations=30,
        seed=42  # Semilla común para reproducibilidad
    )
    print(f"[OK] Simulación de portfolio completada")
    print(f"  - Shape: {result.paths.shape}")
    print(f"  - Valor inicial: ${result.paths[0, 0]:.2f}")
    print(f"  - Valor final promedio: ${result.paths[:, -1].mean():.2f}")


def main():
    """Función principal que ejecuta todos los tests de análisis"""
    print_separator("INICIO DE TESTS DE ANALYSIS (MONTE CARLO)")
    print("Este script prueba todas las funcionalidades de análisis Monte Carlo paso a paso.\n")
    
    # Test 1: GBM
    test_monte_carlo_gbm()
    
    # Test 2: Histórico
    test_monte_carlo_historical()
    
    # Test 3: Portfolio
    test_monte_carlo_portfolio()
    
    print_separator("FIN DE TESTS DE ANALYSIS")
    print("[OK] Todos los tests de análisis completados.")


if __name__ == "__main__":
    main()

