from __future__ import annotations

from typing import Optional, Sequence
import pandas as pd
import numpy as np


def standardize_price_df(
    df: pd.DataFrame,
    *,
    date_col: str,
    close_col: str,
    adjclose_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Estandariza a columnas: 'date', 'close', 'adj close'.  
    """
    mapping = {date_col: 'date', close_col: 'close'}
    if adjclose_col is not None:
        mapping[adjclose_col] = 'adj close'

    cols_present = [c for c in mapping.keys() if c in df.columns]
    if not cols_present:
        raise ValueError("No se encuentran columnas requeridas para estandarizar")

    out = df[cols_present].rename(columns=mapping).copy()

    # Asegurar que 'close' existe (si no, crear desde cualquier columna de precio)
    if 'close' not in out.columns:
        raise ValueError("No se pudo mapear ninguna columna a 'close'")

    # Crear 'adj close' si no existe
    if 'adj close' not in out.columns:
        out['adj close'] = out['close']

    if not pd.api.types.is_datetime64_any_dtype(out['date']):
        out['date'] = pd.to_datetime(out['date'])

    # Convertir a numérico solo las columnas que existen
    for c in ['close', 'adj close']:
        if c in out.columns:
            out[c] = pd.to_numeric(out[c], errors='coerce')

    out = out.sort_values('date').reset_index(drop=True)
    return out


def infer_and_standardize_price_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Heurística simple para aceptar inputs variados.  
    """
    candidates_date = ['date', 'timestamp', 'time', 'datetime', 'Date']
    candidates_close = ['adj close', 'Adj Close', 'close', 'Close', 'price', 'Price']
    candidates_adj = ['adj close', 'Adj Close']

    date_col = next((c for c in candidates_date if c in df.columns), None)
    close_col = next((c for c in candidates_close if c in df.columns), None)
    adj_col = next((c for c in candidates_adj if c in df.columns), None)

    if date_col is None or close_col is None:
        raise ValueError("No se detectaron columnas de fecha/cierre")

    return standardize_price_df(df, date_col=date_col, close_col=close_col, adjclose_col=adj_col)


def drop_duplicate_dates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(subset=['date']).copy()


def fill_missing_prices(df: pd.DataFrame, method: str = 'ffill') -> pd.DataFrame:
    out = df.copy()
    if method == 'ffill':
        out[['close', 'adj close']] = out[['close', 'adj close']].ffill()
    elif method == 'bfill':
        out[['close', 'adj close']] = out[['close', 'adj close']].bfill()
    else:
        out[['close', 'adj close']] = out[['close', 'adj close']].interpolate(limit_direction='both')
    return out


def ensure_numeric_prices(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in ['close', 'adj close']:
        out[c] = pd.to_numeric(out[c], errors='coerce')
    return out


def resample_prices(df: pd.DataFrame, freq: str = 'D') -> pd.DataFrame:
    """
    Re-muestrea por frecuencia manteniendo último valor del día.  
    """
    out = df.copy()
    out = out.set_index('date').sort_index()
    out = out.resample(freq).last()
    out = out.reset_index()
    return out


