"""
Test de Preprocessing - Muestra paso a paso cómo funcionan validación, limpieza y transformaciones.

Ejecutar desde terminal:
    python tests/test_preprocessing.py
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np

# Semilla común para reproducibilidad
np.random.seed(42)

# Configurar path del proyecto (función común desde conftest)
from conftest import setup_project_path
setup_project_path()

try:
    from src.preprocessing import (
        DataCleaner,
        ValidationReport,
        validate_time_series_completeness,
        validate_price_ranges,
        validate_volume_information,
        standardize_price_df,
        infer_and_standardize_price_df,
        compute_returns,
        compute_log_returns,
        compute_cumulative_returns,
        normalize_to_base,
        rolling_mean,
        exponential_moving_average,
        bollinger_bands,
        rsi,
        macd,
    )
    from src.data_classes import PriceSeries
except ImportError as e:
    print(f"ERROR: Error al importar modulos: {e}")
    print("\nPor favor, asegurate de que:")
    print("1. Estas en el directorio raiz del proyecto")
    print("2. Has instalado las dependencias: pip install -r requirements.txt")
    sys.exit(1)


# Importar función común desde conftest
from conftest import print_separator


def test_validators():
    """Test de validadores - Paso a paso"""
    print_separator("TEST: VALIDADORES DE DATOS")
    
    print("PASO 1: Descargando datos reales para validar")
    print("-" * 200)
    try:
        from src.extractors import YFinanceExtractor
        from datetime import datetime, timedelta
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="AAPL",
            start_date=datetime.now() - timedelta(days=90)
        )
        df = price_series.data.copy()
        print(f"[OK] Datos descargados: {len(df)} filas, {len(df.columns)} columnas")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Rango: {df['date'].min().date()} a {df['date'].max().date()}")
    except Exception as e:
        print(f"[WARNING] Error al descargar datos: {e}")
        print("  Usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=30, freq='B')
        df = pd.DataFrame({
            'date': dates,
            'open': 100 + np.random.randn(30).cumsum(),
            'high': 102 + np.random.randn(30).cumsum(),
            'low': 98 + np.random.randn(30).cumsum(),
            'close': 100 + np.random.randn(30).cumsum(),
            'adj close': 100 + np.random.randn(30).cumsum(),
            'volume': np.random.randint(1000, 5000, 30)
        })
        print(f"[OK] DataFrame creado: {len(df)} filas, {len(df.columns)} columnas")
    
    print("\nPASO 2: Validando completitud de la serie temporal")
    print("-" * 200)
    report = validate_time_series_completeness(df)
    print(f"[OK] Validación de completitud completada")
    print(f"  - Tiene errores: {report.has_errors}")
    print(f"  - Número de issues: {len(report.issues)}")
    
    print("\nPASO 3: Validando rangos de precios")
    print("-" * 200)
    report = validate_price_ranges(df)
    print(f"[OK] Validación de rangos completada")
    print(f"  - Tiene errores: {report.has_errors}")
    print(f"  - Número de issues: {len(report.issues)}")
    
    print("\nPASO 4: Validando información de volumen")
    print("-" * 200)
    report = validate_volume_information(df)
    print(f"[OK] Validación de volumen completada")
    print(f"  - Tiene errores: {report.has_errors}")
    print(f"  - Número de issues: {len(report.issues)}")
    
    print("\nPASO 5: Probando validación con datos inválidos")
    print("-" * 200)
    df_invalid = df.copy()
    df_invalid.loc[0, 'close'] = -10  # Precio negativo
    report = validate_price_ranges(df_invalid)
    print(f"[OK] Validación con datos inválidos")
    print(f"  - Tiene errores: {report.has_errors}")
    if report.has_errors:
        print(f"  - Issues encontrados:")
        for issue in report.issues[:3]:
            print(f"    * {issue.severity}: {issue.message}")


def test_data_cleaner():
    """Test de DataCleaner - Paso a paso"""
    print_separator("TEST: DATA CLEANER (LIMPIEZA DE DATOS)")
    
    print("PASO 1: Descargando datos reales y añadiendo problemas artificiales")
    print("-" * 200)
    try:
        from src.extractors import YFinanceExtractor
        from datetime import datetime, timedelta
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="MSFT",
            start_date=datetime.now() - timedelta(days=60)
        )
        df = price_series.data.copy()
        print(f"[OK] Datos descargados: {len(df)} filas")
        # Añadir problemas para demostrar limpieza
        if len(df) > 10:
            df.loc[5, 'adj close'] = np.nan  # Valor faltante
            df = pd.concat([df, df.iloc[[10]]], ignore_index=True)  # Fecha duplicada
        print(f"  - Problemas añadidos para demostración")
    except Exception as e:
        print(f"[WARNING] Error al descargar datos: {e}")
        print("  Usando datos de prueba con problemas...")
        dates = pd.date_range(start='2024-01-01', periods=30, freq='B')
        df = pd.DataFrame({
            'date': dates,
            'close': 100 + np.random.randn(30).cumsum(),
            'adj close': 100 + np.random.randn(30).cumsum()
        })
        df.loc[5, 'adj close'] = np.nan
        df = pd.concat([df, df.iloc[[10]]], ignore_index=True)
    
    print(f"[OK] DataFrame con problemas: {len(df)} filas")
    print(f"  - Valores nulos: {df['adj close'].isna().sum()}")
    print(f"  - Fechas duplicadas: {df['date'].duplicated().sum()}")
    
    print("\nPASO 2: Creando instancia de DataCleaner")
    print("-" * 200)
    cleaner = DataCleaner(df.copy())
    print(f"[OK] DataCleaner creado")
    
    print("\nPASO 3: Eliminando fechas duplicadas")
    print("-" * 200)
    cleaner.drop_duplicate_dates()
    print(f"[OK] Fechas duplicadas eliminadas")
    print(f"  - Filas después: {len(cleaner.df)}")
    
    print("\nPASO 4: Asegurando que los precios sean numéricos")
    print("-" * 200)
    cleaner.ensure_numeric_prices()
    print(f"[OK] Precios convertidos a numéricos")
    
    print("\nPASO 5: Rellenando valores faltantes (forward fill)")
    print("-" * 200)
    cleaner.handle_missing_values(method='ffill')
    print(f"[OK] Valores faltantes rellenados")
    print(f"  - Valores nulos restantes: {cleaner.df['adj close'].isna().sum()}")
    
    print("\nPASO 6: Obteniendo resultado final")
    print("-" * 200)
    cleaned_df = cleaner.result()
    print(f"[OK] DataFrame limpio obtenido")
    print(f"  - Filas finales: {len(cleaned_df)}")
    print(f"  - Valores nulos: {cleaned_df['adj close'].isna().sum()}")
    print(f"  - Primeras 5 filas:")
    print(cleaned_df.head().to_string())


def test_standardization():
    """Test de estandarización - Paso a paso"""
    print_separator("TEST: ESTANDARIZACION DE DATOS")
    
    print("PASO 1: Creando DataFrame con nombres de columnas variados")
    print("-" * 200)
    dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
    df_variado = pd.DataFrame({
        'timestamp': dates,
        'Price': 100 + np.random.randn(30).cumsum(),
        'Adj Close': 100 + np.random.randn(30).cumsum() * 0.98
    })
    print(f"[OK] DataFrame con nombres variados creado")
    print(f"  - Columnas originales: {list(df_variado.columns)}")
    print(f"  - Primeras 5 filas:")
    print(df_variado.head().to_string())
    
    print("\nPASO 2: Aplicando inferencia y estandarización automática")
    print("-" * 200)
    df_standardized = infer_and_standardize_price_df(df_variado)
    print(f"[OK] Estandarización completada")
    print(f"  - Columnas finales: {list(df_standardized.columns)}")
    print(f"  - Primeras 5 filas estandarizadas:")
    print(df_standardized.head().to_string())
    
    print("\nPASO 3: Creando PriceSeries desde datos estandarizados")
    print("-" * 200)
    price_series = PriceSeries(
        ticker="TEST",
        data=df_standardized,
        name="Activo de Prueba"
    )
    print(f"[OK] PriceSeries creado exitosamente")
    print(f"  - Ticker: {price_series.ticker}")
    print(f"  - Puntos de datos: {len(price_series.data)}")
    print(f"  - Media: ${price_series.mean_price:.2f}")


def test_transformations():
    """Test de transformaciones - Paso a paso"""
    print_separator("TEST: TRANSFORMACIONES DE DATOS")
    
    print("PASO 1: Descargando datos reales para transformaciones")
    print("-" * 200)
    try:
        from src.extractors import YFinanceExtractor
        from datetime import datetime, timedelta
        extractor = YFinanceExtractor()
        price_series = extractor.fetch_historical_prices(
            ticker="GOOGL",
            start_date=datetime.now() - timedelta(days=120)
        )
        df = price_series.data.copy()
        print(f"[OK] Datos descargados: {len(df)} puntos de datos")
        print(f"  - Ticker: {price_series.ticker}")
        print(f"  - Precio promedio: ${df['adj close'].mean():.2f}")
    except Exception as e:
        print(f"[WARNING] Error al descargar datos: {e}")
        print("  Usando datos de prueba...")
        dates = pd.date_range(start='2024-01-01', periods=50, freq='B')
        prices = 100 + np.random.randn(50).cumsum()
        df = pd.DataFrame({
            'date': dates,
            'close': prices,
            'adj close': prices
        })
        print(f"[OK] DataFrame creado: {len(df)} puntos de datos")
    
    print("\nPASO 2: Calculando retornos simples")
    print("-" * 200)
    returns = compute_returns(df)
    print(f"[OK] Retornos calculados: {len(returns)} valores")
    print(f"  - Media: {returns.mean():.6f}")
    print(f"  - Desviación estándar: {returns.std():.6f}")
    print(f"  - Primeros 5 retornos:")
    print(returns.head().to_string())
    
    print("\nPASO 3: Calculando retornos logarítmicos")
    print("-" * 200)
    log_returns = compute_log_returns(df)
    print(f"[OK] Retornos logarítmicos calculados: {len(log_returns)} valores")
    print(f"  - Media: {log_returns.mean():.6f}")
    print(f"  - Primeros 5 retornos log:")
    print(log_returns.head().to_string())
    
    print("\nPASO 4: Calculando retornos acumulados")
    print("-" * 200)
    cum_returns = compute_cumulative_returns(returns)
    print(f"[OK] Retornos acumulados calculados")
    print(f"  - Retorno total: {cum_returns.iloc[-1]:.6f} ({cum_returns.iloc[-1]*100:.2f}%)")
    
    print("\nPASO 5: Normalizando a base 100")
    print("-" * 200)
    normalized = normalize_to_base(df)
    print(f"[OK] Normalización completada")
    print(f"  - Valor inicial: {normalized.iloc[0]:.2f}")
    print(f"  - Valor final: {normalized.iloc[-1]:.2f}")
    
    print("\nPASO 6: Calculando media móvil simple (SMA)")
    print("-" * 200)
    sma = rolling_mean(df['adj close'], window=10)
    print(f"[OK] SMA calculada: {len(sma)} valores")
    print(f"  - Primeros 5 valores SMA:")
    print(sma.head().to_string())
    
    print("\nPASO 7: Calculando media móvil exponencial (EMA)")
    print("-" * 200)
    ema = exponential_moving_average(df['adj close'], span=10)
    print(f"[OK] EMA calculada: {len(ema)} valores")
    print(f"  - Primeros 5 valores EMA:")
    print(ema.head().to_string())
    
    print("\nPASO 8: Calculando bandas de Bollinger")
    print("-" * 200)
    bb = bollinger_bands(df['adj close'], window=20, num_std=2)
    print(f"[OK] Bandas de Bollinger calculadas")
    print(f"  - Columnas: {list(bb.columns)}")
    print(f"  - Primeras 5 filas:")
    print(bb.head().to_string())
    
    print("\nPASO 9: Calculando RSI (Relative Strength Index)")
    print("-" * 200)
    rsi_values = rsi(df['adj close'], periods=14)
    print(f"[OK] RSI calculado: {len(rsi_values)} valores")
    print(f"  - Media RSI: {rsi_values.mean():.2f}")
    print(f"  - RSI actual: {rsi_values.iloc[-1]:.2f}")
    
    print("\nPASO 10: Calculando MACD")
    print("-" * 200)
    macd_result = macd(df['adj close'])
    print(f"[OK] MACD calculado")
    print(f"  - Columnas: {list(macd_result.columns)}")
    print(f"  - Primeras 5 filas:")
    print(macd_result.head().to_string())


def main():
    """Función principal que ejecuta todos los tests de preprocessing"""
    print_separator("INICIO DE TESTS DE PREPROCESSING")
    print("Este script prueba todas las funcionalidades de preprocessing paso a paso.\n")
    
    # Test 1: Validadores
    test_validators()
    
    # Test 2: DataCleaner
    test_data_cleaner()
    
    # Test 3: Estandarización
    test_standardization()
    
    # Test 4: Transformaciones
    test_transformations()
    
    print_separator("FIN DE TESTS DE PREPROCESSING")
    print("[OK] Todos los tests de preprocessing completados.")


if __name__ == "__main__":
    main()

