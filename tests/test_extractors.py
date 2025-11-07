"""
Test de Extractores - Muestra paso a paso cómo funcionan los extractores de datos.

Ejecutar desde terminal:
    python tests/test_extractors.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

# Semilla común para reproducibilidad
np.random.seed(42)

# Configurar path del proyecto (función común desde conftest)
from conftest import setup_project_path
setup_project_path()

try:
    from src.extractors import YFinanceExtractor, AlphaVantageExtractor
    from src.data_classes import PriceSeries
    import pandas as pd
except ImportError as e:
    print(f"ERROR: Error al importar modulos: {e}")
    print("\nPor favor, asegurate de que:")
    print("1. Estas en el directorio raiz del proyecto")
    print("2. Has instalado las dependencias: pip install -r requirements.txt")
    sys.exit(1)


# Importar función común desde conftest
from conftest import print_separator


def test_yfinance_extractor():
    """Test del extractor de Yahoo Finance - Paso a paso"""
    print_separator("TEST: EXTRACTOR YAHOO FINANCE (YFinance)")
    
    print("PASO 1: Creando instancia del extractor YFinanceExtractor")
    print("-" * 200)
    extractor = YFinanceExtractor()
    print(f"[OK] Extractor creado: {type(extractor).__name__}")
    print(f"  - Clase base: {extractor.__class__.__bases__[0].__name__}")
    print(f"  - API key requerida: {extractor.api_key is None}")
    
    print("\nPASO 2: Configurando parámetros de descarga")
    print("-" * 200)
    ticker = "AAPL"
    start_date = datetime.now() - timedelta(days=180)
    end_date = datetime.now()
    print(f"  - Ticker: {ticker}")
    print(f"  - Fecha inicio: {start_date.date()}")
    print(f"  - Fecha fin: {end_date.date()}")
    print(f"  - Período: {(end_date - start_date).days} días")
    
    print("\nPASO 3: Descargando datos históricos desde Yahoo Finance")
    print("-" * 200)
    try:
        price_series = extractor.fetch_historical_prices(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date
        )
        print(f"[OK] Descarga completada exitosamente")
        
        print("\nPASO 4: Mostrando datos descargados")
        print("-" * 200)
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Nombre: {price_series.name}")
        print(f"  - Tipo de activo: {price_series.asset_type}")
        print(f"  - Total de puntos de datos: {len(price_series.data)}")
        print(f"  - Rango de fechas: {price_series.data['date'].min().date()} a {price_series.data['date'].max().date()}")
        
        print("\nPASO 5: Mostrando estructura de datos")
        print("-" * 200)
        print("  Columnas disponibles:")
        for col in price_series.data.columns:
            print(f"    - {col}")
        
        print("\nPASO 6: Mostrando primeras 5 filas de datos")
        print("-" * 200)
        print(price_series.data[['date', 'close', 'adj close']].head().to_string())
        
        print("\nPASO 7: Mostrando últimas 5 filas de datos")
        print("-" * 200)
        print(price_series.data[['date', 'close', 'adj close']].tail().to_string())
        
        print("\nPASO 8: Validando datos descargados")
        print("-" * 200)
        print(f"  - Datos vacíos: {price_series.data.empty}")
        print(f"  - Valores nulos en 'close': {price_series.data['close'].isna().sum()}")
        print(f"  - Valores nulos en 'adj close': {price_series.data['adj close'].isna().sum()}")
        print(f"  - Precio mínimo: ${price_series.data['adj close'].min():.2f}")
        print(f"  - Precio máximo: ${price_series.data['adj close'].max():.2f}")
        print(f"  - Precio promedio: ${price_series.data['adj close'].mean():.2f}")
        
        return price_series
        
    except Exception as e:
        print(f"[ERROR] Error durante la descarga: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_alphavantage_extractor():
    """Test del extractor de Alpha Vantage - Paso a paso"""
    print_separator("TEST: EXTRACTOR ALPHA VANTAGE")
    
    print("PASO 1: Verificando configuración de API key")
    print("-" * 200)
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        api_key = os.getenv('ALPHAVANTAGE_API_KEY')
        
        if not api_key:
            print("[WARNING] API key no encontrada en .env")
            print("  Para usar Alpha Vantage:")
            print("  1. Crea un archivo .env en la raíz del proyecto")
            print("  2. Añade: ALPHAVANTAGE_API_KEY=tu_clave_aqui")
            print("  3. Obtén una API key gratis en: https://www.alphavantage.co/support/#api-key")
            return None
        
        print(f"[OK] API key encontrada (longitud: {len(api_key)} caracteres)")
        
    except ImportError:
        print("[WARNING] python-dotenv no instalado. Saltando carga de .env")
        return None
    except Exception as e:
        print(f"[ERROR] Error al cargar configuración: {str(e)}")
        return None
    
    print("\nPASO 2: Creando instancia del extractor AlphaVantageExtractor")
    print("-" * 200)
    try:
        extractor = AlphaVantageExtractor(api_key=api_key, cache_ttl=3600)
        print(f"[OK] Extractor creado: {type(extractor).__name__}")
        print(f"  - API key configurada: {extractor.api_key is not None}")
        print(f"  - Cache TTL: {extractor.cache.ttl} segundos")
        print(f"  - Rate limiting: {extractor._min_request_interval} segundos entre requests")
        
    except Exception as e:
        print(f"[ERROR] Error al crear extractor: {str(e)}")
        return None
    
    print("\nPASO 3: Descargando datos de MSFT (últimos 100 puntos)")
    print("-" * 200)
    try:
        price_series = extractor.fetch_historical_prices(
            ticker="MSFT",
            outputsize='compact'
        )
        print(f"[OK] Descarga completada exitosamente")
        
        print("\nPASO 4: Mostrando datos descargados")
        print("-" * 200)
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Total de puntos: {len(price_series.data)}")
        print(f"  - Rango: {price_series.data['date'].min().date()} a {price_series.data['date'].max().date()}")
        
        print("\nPASO 5: Mostrando primeras 5 filas")
        print("-" * 200)
        print(price_series.data[['date', 'close', 'adj close']].head().to_string())
        
        return price_series
        
    except Exception as e:
        print(f"[ERROR] Error durante la descarga: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def test_fetch_multiple():
    """Test de descarga múltiple en paralelo - Paso a paso"""
    print_separator("TEST: DESCARGA MÚLTIPLE DE TICKERS (PARALELO)")
    
    print("PASO 1: Creando extractor YFinance")
    print("-" * 200)
    extractor = YFinanceExtractor()
    print(f"[OK] Extractor creado")
    
    print("\nPASO 2: Configurando lista de tickers a descargar")
    print("-" * 200)
    tickers = ["AAPL", "MSFT", "GOOGL"]
    print(f"  - Tickers a descargar: {tickers}")
    print(f"  - Total de tickers: {len(tickers)}")
    
    print("\nPASO 3: Configurando parámetros de descarga paralela")
    print("-" * 200)
    start_date = datetime.now() - timedelta(days=90)
    max_workers = 3
    print(f"  - Fecha inicio: {start_date.date()}")
    print(f"  - Max workers (paralelo): {max_workers}")
    
    print("\nPASO 4: Ejecutando descarga en paralelo")
    print("-" * 200)
    try:
        price_series_list = extractor.fetch_multiple(
            tickers=tickers,
            start_date=start_date,
            max_workers=max_workers
        )
        
        print(f"[OK] Descarga paralela completada")
        print(f"  - Series obtenidas: {len(price_series_list)}")
        
        print("\nPASO 5: Mostrando resultados de cada ticker")
        print("-" * 200)
        for ps in price_series_list:
            print(f"  - {ps.ticker}:")
            print(f"    * Nombre: {ps.name}")
            print(f"    * Puntos de datos: {len(ps.data)}")
            print(f"    * Rango: {ps.data['date'].min().date()} a {ps.data['date'].max().date()}")
            print(f"    * Precio promedio: ${ps.data['adj close'].mean():.2f}")
        
        return price_series_list
        
    except Exception as e:
        print(f"[ERROR] Error durante descarga paralela: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Función principal que ejecuta todos los tests de extractores"""
    print_separator("INICIO DE TESTS DE EXTRACTORES")
    print("Este script prueba todas las funcionalidades de los extractores paso a paso.")
    print("Cada sección muestra el funcionamiento interno con prints explicativos.\n")
    
    # Test 1: YFinance Extractor
    price_series_aapl = test_yfinance_extractor()
    
    # Test 2: Alpha Vantage Extractor (opcional)
    test_alphavantage_extractor()
    
    # Test 3: Descarga múltiple
    test_fetch_multiple()
    
    print_separator("FIN DE TESTS DE EXTRACTORES")
    print("[OK] Todos los tests de extractores completados.")


if __name__ == "__main__":
    main()

