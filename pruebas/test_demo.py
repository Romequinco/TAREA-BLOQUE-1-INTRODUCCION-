"""
Script de demostración y pruebas del sistema de análisis financiero.
Muestra paso a paso cómo funciona cada componente con prints explicativos.
"""

import sys
import os
from datetime import datetime, timedelta

# Añadir el directorio src al path para importar los módulos
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.extractors import YFinanceExtractor, AlphaVantageExtractor
from src.data_classes import PriceSeries, Portfolio
from src.preprocessing import infer_and_standardize_price_df
import pandas as pd
import numpy as np


def print_separator(title: str = ""):
    """Imprime un separador visual con título opcional"""
    print("\n" + "=" * 200)
    if title:
        print(f"  {title}")
        print("=" * 200 + "\n")


def test_yfinance_extractor():
    """Prueba el extractor de Yahoo Finance"""
    print_separator("TEST 1: EXTRACTOR YAHOO FINANCE (YFinance)")
    
    print("Paso 1: Creando instancia del extractor...")
    extractor = YFinanceExtractor()
    print(f"✓ Extractor creado: {type(extractor).__name__}")
    
    print("\nPaso 2: Descargando datos históricos de AAPL (último año)...")
    start_date = datetime.now() - timedelta(days=365)
    end_date = datetime.now()
    
    try:
        price_series = extractor.fetch_historical_prices(
            ticker="AAPL",
            start_date=start_date,
            end_date=end_date
        )
        print(f"✓ Datos descargados exitosamente")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Nombre: {price_series.name}")
        print(f"  - Tipo: {price_series.asset_type}")
        print(f"  - Puntos de datos: {len(price_series.data)}")
        print(f"  - Rango: {price_series.data['date'].min()} a {price_series.data['date'].max()}")
        print(f"\nPrimeras 5 filas:")
        print(price_series.data[['date', 'close', 'adj close']].head())
        return price_series
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def test_alphavantage_extractor():
    """Prueba el extractor de Alpha Vantage (requiere API key)"""
    print_separator("TEST 2: EXTRACTOR ALPHA VANTAGE")
    
    print("Paso 1: Intentando cargar API key desde .env...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        
        if not api_key:
            print("⚠ API key no encontrada. Saltando este test.")
            print("  Para usar Alpha Vantage, crea un archivo .env con ALPHAVANTAGE_API_KEY=tu_clave")
            return None
        
        print(f"✓ API key cargada")
        
        print("\nPaso 2: Creando extractor de Alpha Vantage...")
        extractor = AlphaVantageExtractor(api_key=api_key)
        print(f"✓ Extractor creado")
        
        print("\nPaso 3: Descargando datos de MSFT (últimos 100 puntos)...")
        price_series = extractor.fetch_historical_prices(
            ticker="MSFT",
            outputsize='compact'
        )
        print(f"✓ Datos descargados exitosamente")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Puntos de datos: {len(price_series.data)}")
        print(f"\nPrimeras 5 filas:")
        print(price_series.data[['date', 'close', 'adj close']].head())
        return price_series
        
    except ImportError:
        print("⚠ python-dotenv no instalado. Saltando carga de .env")
        return None
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def test_price_series_methods(price_series: PriceSeries):
    """Prueba los métodos de PriceSeries"""
    print_separator("TEST 3: MÉTODOS DE PRICE SERIES")
    
    if price_series is None:
        print("⚠ No hay datos disponibles. Saltando test.")
        return
    
    print("Paso 1: Estadísticas básicas calculadas automáticamente...")
    print(f"  - Media de precios: ${price_series.mean_price:.2f}")
    print(f"  - Desviación estándar: ${price_series.std_dev:.2f}")
    
    print("\nPaso 2: Calculando rendimientos diarios...")
    returns = price_series.get_returns()
    print(f"  - Total de rendimientos calculados: {len(returns)}")
    print(f"  - Primeros 5 rendimientos:")
    print(returns.head())
    print(f"  - Media de rendimientos: {returns.mean():.4f} ({returns.mean()*100:.2f}%)")
    
    print("\nPaso 3: Calculando rendimientos acumulados...")
    cum_returns = price_series.get_cumulative_returns()
    print(f"  - Rendimiento acumulado total: {cum_returns.iloc[-1]:.4f} ({cum_returns.iloc[-1]*100:.2f}%)")
    
    print("\nPaso 4: Calculando volatilidad anualizada...")
    vol = price_series.volatility(annualize=True)
    print(f"  - Volatilidad anualizada: {vol:.4f} ({vol*100:.2f}%)")
    
    print("\nPaso 5: Resumen completo de estadísticas...")
    stats = price_series.summary_stats()
    for key, value in stats.items():
        print(f"  - {key}: {value}")
    
    print("\nPaso 6: Probando método de limpieza...")
    original_len = len(price_series.data)
    price_series.clean(fill_method='ffill')
    print(f"  - Datos antes de limpieza: {original_len}")
    print(f"  - Datos después de limpieza: {len(price_series.data)}")
    print(f"  ✓ Limpieza completada")


def test_multiple_tickers():
    """Prueba la descarga de múltiples tickers en paralelo"""
    print_separator("TEST 4: DESCARGA MÚLTIPLE DE TICKERS (PARALELO)")
    
    print("Paso 1: Creando extractor...")
    extractor = YFinanceExtractor()
    
    print("\nPaso 2: Descargando múltiples tickers en paralelo...")
    tickers = ["AAPL", "MSFT", "GOOGL"]
    print(f"  - Tickers a descargar: {tickers}")
    
    try:
        start_date = datetime.now() - timedelta(days=180)
        price_series_list = extractor.fetch_multiple(
            tickers=tickers,
            start_date=start_date,
            max_workers=3
        )
        
        print(f"\n✓ Descarga completada: {len(price_series_list)} series obtenidas")
        for ps in price_series_list:
            print(f"  - {ps.ticker}: {len(ps.data)} puntos de datos")
        
        return price_series_list
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return None


def test_portfolio(price_series_list):
    """Prueba la creación y análisis de un portfolio"""
    print_separator("TEST 5: CREACIÓN Y ANÁLISIS DE PORTFOLIO")
    
    if price_series_list is None or len(price_series_list) < 2:
        print("⚠ No hay suficientes series de precios. Creando portfolio con datos de prueba...")
        # Crear datos de prueba
        extractor = YFinanceExtractor()
        tickers = ["AAPL", "MSFT"]
        price_series_list = []
        for ticker in tickers:
            try:
                ps = extractor.fetch_historical_prices(
                    ticker=ticker,
                    start_date=datetime.now() - timedelta(days=180)
                )
                price_series_list.append(ps)
            except:
                pass
        
        if len(price_series_list) < 2:
            print("✗ No se pudieron obtener suficientes datos para el portfolio")
            return
    
    print("Paso 1: Preparando datos para el portfolio...")
    holdings = {ps.ticker: ps for ps in price_series_list[:3]}  # Máximo 3 para no sobrecargar
    print(f"  - Activos en el portfolio: {list(holdings.keys())}")
    
    print("\nPaso 2: Creando pesos (equiponderado)...")
    n = len(holdings)
    weights = {ticker: 1.0/n for ticker in holdings.keys()}
    print(f"  - Pesos: {weights}")
    print(f"  - Suma de pesos: {sum(weights.values()):.6f}")
    
    print("\nPaso 3: Creando portfolio...")
    try:
        portfolio = Portfolio(
            holdings=holdings,
            weights=weights,
            name="Portfolio de Prueba"
        )
        print(f"✓ Portfolio creado: {portfolio.name}")
        print(f"  - Número de activos: {len(portfolio.holdings)}")
        
        print("\nPaso 4: Calculando rendimientos del portfolio...")
        portfolio_returns = portfolio.get_portfolio_returns()
        print(f"  - Total de rendimientos: {len(portfolio_returns)}")
        print(f"  - Rendimiento medio diario: {portfolio_returns.mean():.4f} ({portfolio_returns.mean()*100:.2f}%)")
        
        print("\nPaso 5: Calculando volatilidad del portfolio...")
        vol = portfolio.portfolio_volatility(annualize=True)
        print(f"  - Volatilidad anualizada: {vol:.4f} ({vol*100:.2f}%)")
        
        print("\nPaso 6: Calculando matriz de correlación...")
        corr_matrix = portfolio.correlation_matrix()
        print("  - Matriz de correlación:")
        print(corr_matrix)
        
        print("\nPaso 7: Evolución del valor del portfolio (capital inicial $10,000)...")
        value_history = portfolio.portfolio_value_history(initial_value=10000)
        print(f"  - Valor inicial: ${value_history['value'].iloc[0]:.2f}")
        print(f"  - Valor final: ${value_history['value'].iloc[-1]:.2f}")
        print(f"  - Retorno total: {(value_history['value'].iloc[-1]/value_history['value'].iloc[0] - 1)*100:.2f}%")
        
        print("\nPaso 8: Resumen completo del portfolio...")
        summary = portfolio.summary()
        print(f"  - Nombre: {summary['name']}")
        print(f"  - Número de holdings: {summary['num_holdings']}")
        print(f"  - Volatilidad del portfolio: {summary['portfolio_volatility']:.4f}")
        print(f"  - Estadísticas individuales:")
        for ticker, stats in summary['individual_stats'].items():
            print(f"    * {ticker}:")
            print(f"      - Media: ${stats['mean_price']:.2f}")
            print(f"      - Volatilidad: {stats['volatility']:.4f}")
            print(f"      - Retorno total: {stats['total_return']*100:.2f}%")
        
    except Exception as e:
        print(f"✗ Error al crear portfolio: {str(e)}")
        import traceback
        traceback.print_exc()


def test_preprocessing():
    """Prueba las funciones de preprocesamiento"""
    print_separator("TEST 6: FUNCIONES DE PREPROCESAMIENTO")
    
    print("Paso 1: Creando DataFrame de ejemplo con nombres de columnas variados...")
    # Simular datos con nombres diferentes
    dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
    df_variado = pd.DataFrame({
        'timestamp': dates,
        'Price': 100 + np.random.randn(30).cumsum(),
        'Adj Close': 100 + np.random.randn(30).cumsum() * 0.98
    })
    print(f"  - Columnas originales: {list(df_variado.columns)}")
    print(f"\nPrimeras 5 filas:")
    print(df_variado.head())
    
    print("\nPaso 2: Aplicando inferencia y estandarización automática...")
    try:
        df_standardized = infer_and_standardize_price_df(df_variado)
        print(f"✓ Estandarización completada")
        print(f"  - Columnas finales: {list(df_standardized.columns)}")
        print(f"\nPrimeras 5 filas estandarizadas:")
        print(df_standardized.head())
        
        print("\nPaso 3: Creando PriceSeries desde datos estandarizados...")
        price_series = PriceSeries(
            ticker="TEST",
            data=df_standardized,
            name="Activo de Prueba"
        )
        print(f"✓ PriceSeries creado exitosamente")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Puntos de datos: {len(price_series.data)}")
        print(f"  - Media: ${price_series.mean_price:.2f}")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


def main():
    """Función principal que ejecuta todos los tests"""
    print_separator("INICIO DE TESTS Y DEMOSTRACIÓN DEL SISTEMA")
    print("Este script prueba todas las funcionalidades del sistema paso a paso.")
    print("Cada sección muestra el funcionamiento interno con prints explicativos.\n")
    
    # Test 1: YFinance Extractor
    price_series_aapl = test_yfinance_extractor()
    
    # Test 2: Alpha Vantage Extractor (opcional, requiere API key)
    test_alphavantage_extractor()
    
    # Test 3: Métodos de PriceSeries
    if price_series_aapl:
        test_price_series_methods(price_series_aapl)
    
    # Test 4: Múltiples tickers
    price_series_list = test_multiple_tickers()
    
    # Test 5: Portfolio
    test_portfolio(price_series_list)
    
    # Test 6: Preprocessing
    test_preprocessing()
    
    print_separator("FIN DE TESTS")
    print("✓ Todos los tests completados. Revisa los resultados arriba para ver cómo funciona cada componente.")


if __name__ == "__main__":
    main()

