"""Transformaciones y utilidades para análisis y machine learning."""

from __future__ import annotations

from typing import Iterable, List, Tuple

import numpy as np
import pandas as pd


def compute_returns(df: pd.DataFrame, *, price_col: str = "adj close") -> pd.Series:
    """Calcula retornos simples porcentuales."""

    returns = df.set_index("date")[price_col].pct_change()
    return returns.dropna()


def compute_log_returns(df: pd.DataFrame, *, price_col: str = "adj close") -> pd.Series:
    """Calcula retornos logarítmicos."""

    prices = df.set_index("date")[price_col]
    log_returns = np.log(prices / prices.shift(1))
    return log_returns.dropna()


def compute_cumulative_returns(returns: pd.Series) -> pd.Series:
    """Calcula retornos acumulados (1 + r).cumprod() - 1."""

    cumulative = (1 + returns).cumprod() - 1
    return cumulative


def normalize_to_base(df: pd.DataFrame, *, price_col: str = "adj close", base: float = 100.0) -> pd.Series:
    """Convierte precios a una base fija."""

    prices = df.set_index("date")[price_col]
    normalized = (prices / prices.iloc[0]) * base
    return normalized


def rolling_mean(data, *, window: int, price_col: str = "adj close") -> pd.Series:
    """Media móvil simple. Acepta DataFrame o Series."""
    
    if isinstance(data, pd.Series):
        return data.rolling(window=window, min_periods=1).mean()
    elif isinstance(data, pd.DataFrame):
        if "date" in data.columns:
            return data.set_index("date")[price_col].rolling(window=window, min_periods=1).mean()
        else:
            return data[price_col].rolling(window=window, min_periods=1).mean()
    else:
        raise TypeError("data debe ser DataFrame o Series")


def exponential_moving_average(data, *, span: int, price_col: str = "adj close") -> pd.Series:
    """Media móvil exponencial. Acepta DataFrame o Series."""
    
    if isinstance(data, pd.Series):
        return data.ewm(span=span, adjust=False).mean()
    elif isinstance(data, pd.DataFrame):
        if "date" in data.columns:
            return data.set_index("date")[price_col].ewm(span=span, adjust=False).mean()
        else:
            return data[price_col].ewm(span=span, adjust=False).mean()
    else:
        raise TypeError("data debe ser DataFrame o Series")


def bollinger_bands(
    data,
    *,
    window: int = 20,
    num_std: float = 2.0,
    price_col: str = "adj close",
) -> pd.DataFrame:
    """Calcula las bandas de Bollinger clásicas. Acepta DataFrame o Series."""
    
    if isinstance(data, pd.Series):
        prices = data
    elif isinstance(data, pd.DataFrame):
        if "date" in data.columns:
            prices = data.set_index("date")[price_col]
        else:
            prices = data[price_col]
    else:
        raise TypeError("data debe ser DataFrame o Series")
    
    middle = prices.rolling(window, min_periods=1).mean()
    std = prices.rolling(window, min_periods=1).std()

    upper = middle + num_std * std
    lower = middle - num_std * std

    return pd.DataFrame({
        "middle": middle,
        "upper": upper,
        "lower": lower,
    })


def rsi(data, *, periods: int = 14, price_col: str = "adj close") -> pd.Series:
    """Calcula el indicador RSI. Acepta DataFrame o Series."""
    
    if isinstance(data, pd.Series):
        prices = data
    elif isinstance(data, pd.DataFrame):
        if "date" in data.columns:
            prices = data.set_index("date")[price_col]
        else:
            prices = data[price_col]
    else:
        raise TypeError("data debe ser DataFrame o Series")
    
    delta = prices.diff().dropna()
    gain = (delta.clip(lower=0)).rolling(window=periods, min_periods=periods).mean()
    loss = (-delta.clip(upper=0)).rolling(window=periods, min_periods=periods).mean()
    rs = gain / loss.replace({0: np.nan})
    rsi_values = 100 - (100 / (1 + rs))
    return rsi_values.dropna()


def macd(
    data,
    *,
    price_col: str = "adj close",
    fast_span: int = 12,
    slow_span: int = 26,
    signal_span: int = 9,
) -> pd.DataFrame:
    """Calcula el indicador MACD clásico. Acepta DataFrame o Series."""
    
    if isinstance(data, pd.Series):
        prices = data
    elif isinstance(data, pd.DataFrame):
        if "date" in data.columns:
            prices = data.set_index("date")[price_col]
        else:
            prices = data[price_col]
    else:
        raise TypeError("data debe ser DataFrame o Series")
    
    ema_fast = prices.ewm(span=fast_span, adjust=False).mean()
    ema_slow = prices.ewm(span=slow_span, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal = macd_line.ewm(span=signal_span, adjust=False).mean()
    histogram = macd_line - signal
    return pd.DataFrame({
        "macd": macd_line,
        "signal": signal,
        "histogram": histogram,
    })


def create_time_windows(
    series: pd.Series,
    *,
    window_size: int,
    horizon: int = 1,
) -> Tuple[np.ndarray, np.ndarray]:
    """Genera ventanas deslizantes para ML."""

    if len(series) < window_size + horizon:
        raise ValueError("La serie es demasiado corta para generar ventanas.")

    features: List[np.ndarray] = []
    targets: List[np.ndarray] = []

    values = series.to_numpy()
    for start in range(0, len(values) - window_size - horizon + 1):
        end = start + window_size
        feature_window = values[start:end]
        target_window = values[end : end + horizon]
        features.append(feature_window)
        targets.append(target_window)

    return np.array(features), np.array(targets)


def min_max_scale(series: pd.Series, *, feature_range: Tuple[float, float] = (0.0, 1.0)) -> pd.Series:
    """Escalado Min-Max clásico."""

    min_val, max_val = feature_range
    data_min = series.min()
    data_max = series.max()
    if data_max == data_min:
        return pd.Series(np.zeros_like(series), index=series.index)

    scaled = (series - data_min) / (data_max - data_min)
    return scaled * (max_val - min_val) + min_val


def z_score_normalize(series: pd.Series) -> pd.Series:
    """Normaliza un vector a z-score."""

    mean = series.mean()
    std = series.std(ddof=0)
    if std == 0:
        return pd.Series(np.zeros_like(series), index=series.index)
    return (series - mean) / std



