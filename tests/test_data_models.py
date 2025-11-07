"""
Test de Data Models (PriceSeries y Portfolio) - Muestra paso a paso cómo funcionan.

Ejecutar desde terminal:
    python tests/test_data_models.py
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


def test_price_series_creation():
    """Test de creación de PriceSeries - Paso a paso"""
    print_separator("TEST: CREACION DE PRICE SERIES")
    
    print("PASO 1: Creando DataFrame de ejemplo con datos de precios")
    print("-" * 200)
    dates = pd.date_range(start='2024-01-01', periods=30, freq='B')
    prices = 100 + np.random.randn(30).cumsum()
    df = pd.DataFrame({
        'date': dates,
        'close': prices,
        'adj close': prices * 0.99,
        'open': prices * 0.98,
        'high': prices * 1.02,
        'low': prices * 0.97,
        'volume': np.random.randint(1000, 5000, 30)
    })
    print(f"[OK] DataFrame creado con {len(df)} filas")
    print(f"  - Columnas: {list(df.columns)}")
    print(f"  - Rango de fechas: {df['date'].min().date()} a {df['date'].max().date()}")
    
    print("\nPASO 2: Creando instancia de PriceSeries")
    print("-" * 200)
    price_series = PriceSeries(
        ticker="TEST",
        data=df,
        name="Activo de Prueba",
        asset_type="stock"
    )
    print(f"[OK] PriceSeries creado exitosamente")
    print(f"  - Ticker: {price_series.ticker}")
    print(f"  - Nombre: {price_series.name}")
    print(f"  - Tipo: {price_series.asset_type}")
    
    print("\nPASO 3: Verificando estadísticas calculadas automáticamente")
    print("-" * 200)
    print(f"  - Precio medio: ${price_series.mean_price:.2f}")
    print(f"  - Desviación estándar: ${price_series.std_dev:.2f}")
    print(f"  - Precio mínimo: ${price_series.data['adj close'].min():.2f}")
    print(f"  - Precio máximo: ${price_series.data['adj close'].max():.2f}")
    
    return price_series


def test_price_series_methods(price_series: PriceSeries):
    """Test de métodos de PriceSeries - Paso a paso"""
    print_separator("TEST: METODOS DE PRICE SERIES")
    
    print("PASO 1: Calculando rendimientos diarios")
    print("-" * 200)
    returns = price_series.get_returns()
    print(f"[OK] Rendimientos calculados: {len(returns)} valores")
    print(f"  - Media de rendimientos: {returns.mean():.6f} ({returns.mean()*100:.4f}%)")
    print(f"  - Desviación estándar: {returns.std():.6f}")
    print(f"  - Primeros 5 rendimientos:")
    print(returns.head().to_string())
    
    print("\nPASO 2: Calculando rendimientos acumulados")
    print("-" * 200)
    cum_returns = price_series.get_cumulative_returns()
    print(f"[OK] Rendimientos acumulados calculados")
    print(f"  - Rendimiento total: {cum_returns.iloc[-1]:.6f} ({cum_returns.iloc[-1]*100:.4f}%)")
    print(f"  - Primeros 5 valores acumulados:")
    print(cum_returns.head().to_string())
    
    print("\nPASO 3: Calculando volatilidad")
    print("-" * 200)
    vol_daily = price_series.volatility(annualize=False)
    vol_annual = price_series.volatility(annualize=True)
    print(f"[OK] Volatilidad calculada")
    print(f"  - Volatilidad diaria: {vol_daily:.6f} ({vol_daily*100:.4f}%)")
    print(f"  - Volatilidad anualizada: {vol_annual:.6f} ({vol_annual*100:.4f}%)")
    
    print("\nPASO 4: Obteniendo resumen de estadísticas")
    print("-" * 200)
    stats = price_series.summary_stats()
    print(f"[OK] Estadísticas calculadas:")
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  - {key}: {value:.6f}")
        else:
            print(f"  - {key}: {value}")
    
    print("\nPASO 5: Aplicando limpieza de datos")
    print("-" * 200)
    original_len = len(price_series.data)
    price_series.clean(fill_method='ffill')
    print(f"[OK] Limpieza completada")
    print(f"  - Datos antes: {original_len} filas")
    print(f"  - Datos después: {len(price_series.data)} filas")
    print(f"  - Valores nulos: {price_series.data['adj close'].isna().sum()}")
    
    print("\nPASO 6: Validando datos")
    print("-" * 200)
    validation_report = price_series.validate()
    print(f"[OK] Validación completada")
    print(f"  - Tiene errores: {validation_report.has_errors}")
    print(f"  - Número de issues: {len(validation_report.issues)}")
    if validation_report.issues:
        for issue in validation_report.issues[:3]:  # Mostrar solo los primeros 3
            print(f"    * {issue.severity}: {issue.message}")


def test_portfolio_creation():
    """Test de creación de Portfolio - Paso a paso"""
    print_separator("TEST: CREACION DE PORTFOLIO")
    
    print("PASO 1: Descargando datos para múltiples activos")
    print("-" * 200)
    extractor = YFinanceExtractor()
    tickers = ["AAPL", "MSFT"]
    holdings = {}
    
    for ticker in tickers:
        try:
            ps = extractor.fetch_historical_prices(
                ticker=ticker,
                start_date=datetime.now() - timedelta(days=90)
            )
            holdings[ticker] = ps
            print(f"  [OK] {ticker}: {len(ps.data)} puntos de datos")
        except Exception as e:
            print(f"  [ERROR] {ticker}: Error - {str(e)}")
            # Crear datos de prueba si falla
            dates = pd.date_range(start='2024-01-01', periods=30, freq='B')
            prices = 100 + np.random.randn(30).cumsum()
            df = pd.DataFrame({
                'date': dates,
                'close': prices,
                'adj close': prices
            })
            holdings[ticker] = PriceSeries(ticker=ticker, data=df)
            print(f"  [OK] {ticker}: Datos de prueba creados")
    
    print(f"\n[OK] Total de holdings: {len(holdings)}")
    
    print("\nPASO 2: Configurando pesos del portfolio")
    print("-" * 200)
    n = len(holdings)
    weights = {ticker: 1.0/n for ticker in holdings.keys()}
    print(f"[OK] Pesos configurados (equiponderado):")
    for ticker, weight in weights.items():
        print(f"  - {ticker}: {weight:.4f} ({weight*100:.2f}%)")
    print(f"  - Suma total: {sum(weights.values()):.6f}")
    
    print("\nPASO 3: Creando instancia de Portfolio")
    print("-" * 200)
    portfolio = Portfolio(
        holdings=holdings,
        weights=weights,
        name="Portfolio de Prueba"
    )
    print(f"[OK] Portfolio creado exitosamente")
    print(f"  - Nombre: {portfolio.name}")
    print(f"  - Número de activos: {len(portfolio.holdings)}")
    print(f"  - Activos: {list(portfolio.holdings.keys())}")
    
    return portfolio


def test_portfolio_methods(portfolio: Portfolio):
    """Test de métodos de Portfolio - Paso a paso"""
    print_separator("TEST: METODOS DE PORTFOLIO")
    
    print("PASO 1: Calculando rendimientos del portfolio")
    print("-" * 200)
    portfolio_returns = portfolio.get_portfolio_returns()
    print(f"[OK] Rendimientos del portfolio calculados: {len(portfolio_returns)} valores")
    print(f"  - Rendimiento medio diario: {portfolio_returns.mean():.6f} ({portfolio_returns.mean()*100:.4f}%)")
    print(f"  - Desviación estándar: {portfolio_returns.std():.6f}")
    print(f"  - Primeros 5 rendimientos:")
    print(portfolio_returns.head().to_string())
    
    print("\nPASO 2: Calculando volatilidad del portfolio")
    print("-" * 200)
    vol = portfolio.portfolio_volatility(annualize=True)
    print(f"[OK] Volatilidad del portfolio calculada")
    print(f"  - Volatilidad anualizada: {vol:.6f} ({vol*100:.4f}%)")
    
    print("\nPASO 3: Calculando matriz de correlación")
    print("-" * 200)
    corr_matrix = portfolio.correlation_matrix()
    print(f"[OK] Matriz de correlación calculada")
    print(f"  - Dimensiones: {corr_matrix.shape}")
    print(f"  - Matriz:")
    print(corr_matrix.to_string())
    
    print("\nPASO 4: Calculando evolución del valor del portfolio")
    print("-" * 200)
    initial_value = 10000
    value_history = portfolio.portfolio_value_history(initial_value=initial_value)
    print(f"[OK] Evolución del valor calculada")
    print(f"  - Valor inicial: ${value_history['value'].iloc[0]:.2f}")
    print(f"  - Valor final: ${value_history['value'].iloc[-1]:.2f}")
    print(f"  - Retorno total: {(value_history['value'].iloc[-1]/value_history['value'].iloc[0] - 1)*100:.2f}%")
    print(f"  - Primeros 5 valores:")
    print(value_history.head().to_string())
    
    print("\nPASO 5: Obteniendo resumen del portfolio")
    print("-" * 200)
    summary = portfolio.summary()
    print(f"[OK] Resumen del portfolio:")
    print(f"  - Nombre: {summary['name']}")
    print(f"  - Número de holdings: {summary['num_holdings']}")
    print(f"  - Volatilidad del portfolio: {summary['portfolio_volatility']:.6f}")
    print(f"  - Estadísticas individuales:")
    for ticker, stats in summary['individual_stats'].items():
        print(f"    * {ticker}:")
        print(f"      - Media: ${stats['mean_price']:.2f}")
        print(f"      - Volatilidad: {stats['volatility']:.6f}")
        print(f"      - Retorno total: {stats['total_return']*100:.2f}%")


def main():
    """Función principal que ejecuta todos los tests de data models"""
    print_separator("INICIO DE TESTS DE DATA MODELS")
    print("Este script prueba todas las funcionalidades de PriceSeries y Portfolio paso a paso.\n")
    
    # Test 1: Creación de PriceSeries
    price_series = test_price_series_creation()
    
    # Test 2: Métodos de PriceSeries
    test_price_series_methods(price_series)
    
    # Test 3: Creación de Portfolio
    portfolio = test_portfolio_creation()
    
    # Test 4: Métodos de Portfolio
    test_portfolio_methods(portfolio)
    
    print_separator("FIN DE TESTS DE DATA MODELS")
    print("[OK] Todos los tests de data models completados.")


if __name__ == "__main__":
    main()

