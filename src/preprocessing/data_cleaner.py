"""Herramientas de limpieza y preprocesado de series de precios."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

import numpy as np
import pandas as pd


def standardize_price_df(
    df: pd.DataFrame,
    *,
    date_col: str,
    close_col: str,
    adjclose_col: Optional[str] = None,
    open_col: Optional[str] = None,
    high_col: Optional[str] = None,
    low_col: Optional[str] = None,
    volume_col: Optional[str] = None,
) -> pd.DataFrame:
    """Estandariza columnas de un DataFrame de precios."""

    mapping = {date_col: "date", close_col: "close"}
    if adjclose_col:
        mapping[adjclose_col] = "adj close"
    if open_col:
        mapping[open_col] = "open"
    if high_col:
        mapping[high_col] = "high"
    if low_col:
        mapping[low_col] = "low"
    if volume_col:
        mapping[volume_col] = "volume"

    available = [col for col in mapping if col in df.columns]
    if not available:
        raise ValueError("No se encuentran columnas suficientes para estandarizar.")

    out = df[available].rename(columns=mapping).copy()
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    for column in [c for c in ["open", "high", "low", "close", "adj close", "volume"] if c in out.columns]:
        out[column] = pd.to_numeric(out[column], errors="coerce")

    if "adj close" not in out.columns:
        out["adj close"] = out.get("close")

    out = out.sort_values("date").dropna(subset=["date"]).reset_index(drop=True)
    return out


def infer_and_standardize_price_df(df: pd.DataFrame) -> pd.DataFrame:
    """Intenta detectar las columnas más comunes y estandariza el DataFrame."""

    candidates_date = ["date", "Date", "timestamp", "time", "datetime"]
    candidates_close = ["adj close", "Adj Close", "close", "Close", "price", "Price"]
    candidates_adj = ["adj close", "Adj Close"]

    date_col = next((col for col in candidates_date if col in df.columns), None)
    close_col = next((col for col in candidates_close if col in df.columns), None)
    adj_col = next((col for col in candidates_adj if col in df.columns), None)

    if date_col is None or close_col is None:
        raise ValueError("No se han encontrado columnas de fecha o cierre reconocibles.")

    return standardize_price_df(df, date_col=date_col, close_col=close_col, adjclose_col=adj_col)


def _resample_with_fill(df: pd.DataFrame, freq: str) -> pd.DataFrame:
    """Resample auxiliar que rellena usando forward-fill tras el muestreo."""

    resampled = df.set_index("date").resample(freq).last()
    numeric_cols = resampled.select_dtypes(include=[np.number]).columns
    resampled[numeric_cols] = resampled[numeric_cols].ffill()
    return resampled.reset_index()


@dataclass
class DataCleaner:
    """Encapsula operaciones de limpieza configurable sobre series de precios."""

    df: pd.DataFrame

    def drop_duplicate_dates(self) -> "DataCleaner":
        """Elimina fechas duplicadas conservando la última aparición."""

        self.df = self.df.drop_duplicates(subset=["date"], keep="last").reset_index(drop=True)
        return self

    def ensure_numeric_prices(self) -> "DataCleaner":
        """Garantiza que las columnas de precio sean numéricas."""

        for column in ["open", "high", "low", "close", "adj close"]:
            if column in self.df.columns:
                self.df[column] = pd.to_numeric(self.df[column], errors="coerce")
        return self

    def handle_missing_values(self, method: str = "ffill") -> "DataCleaner":
        """Gestiona valores faltantes según el método indicado."""

        price_cols = [col for col in ["open", "high", "low", "close", "adj close"] if col in self.df.columns]

        if method == "ffill":
            self.df[price_cols] = self.df[price_cols].ffill()
        elif method == "bfill":
            self.df[price_cols] = self.df[price_cols].bfill()
        elif method == "linear":
            self.df[price_cols] = self.df[price_cols].interpolate(method="linear", limit_direction="both")
        elif method == "spline":
            try:
                self.df[price_cols] = self.df[price_cols].interpolate(method="spline", order=3, limit_direction="both")
            except Exception:
                # Si SciPy no está disponible, degradar a interpolación lineal.
                self.df[price_cols] = self.df[price_cols].interpolate(method="linear", limit_direction="both")
        elif method == "drop":
            self.df = self.df.dropna(subset=price_cols).reset_index(drop=True)
        else:
            raise ValueError(f"Método de imputación no soportado: {method}")

        return self

    def normalize_dates(
        self,
        *,
        timezone: str = "UTC",
        fill_missing: bool = True,
        freq: str = "B",
    ) -> "DataCleaner":
        """Normaliza las fechas a la zona horaria y rellena días faltantes."""

        dates = pd.to_datetime(self.df["date"], errors="coerce")
        if timezone:
            if dates.dt.tz is None:
                dates = dates.dt.tz_localize(timezone)
            else:
                dates = dates.dt.tz_convert(timezone)
        self.df["date"] = dates

        if fill_missing:
            # Convertir a naive para el reindexado, se mantiene la información al final.
            naive = dates.dt.tz_convert(timezone).dt.tz_localize(None)
            full_range = pd.date_range(start=naive.min(), end=naive.max(), freq=freq)
            reindexed = self.df.set_index(naive).reindex(full_range)
            reindexed["date"] = full_range.tz_localize(timezone)
            self.df = reindexed.reset_index(drop=True)

        return self

    def adjust_for_corporate_actions(
        self,
        *,
        split_col: str = "split_coefficient",
        dividend_col: str = "dividend",
        price_col: str = "adj close",
    ) -> "DataCleaner":
        """Aplica ajustes por splits y dividendos si existen las columnas."""

        if split_col in self.df.columns:
            factors = pd.to_numeric(self.df[split_col], errors="coerce").replace({0: np.nan}).fillna(1.0)
            self.df[price_col] = self.df[price_col] / factors.cumprod()

        if dividend_col in self.df.columns:
            dividends = pd.to_numeric(self.df[dividend_col], errors="coerce").fillna(0.0)
            self.df[price_col] = self.df[price_col] - dividends.cumsum()

        return self

    def normalize_base(self, base: float = 100.0, price_col: str = "adj close") -> "DataCleaner":
        """Normaliza la serie a una base fija (por ejemplo, 100)."""

        if price_col not in self.df.columns:
            raise ValueError(f"No se encuentra la columna de precio '{price_col}' para normalizar.")

        initial = self.df[price_col].iloc[0]
        self.df[f"{price_col}_base_{int(base)}"] = (self.df[price_col] / initial) * base
        return self

    def filter_outliers(
        self,
        *,
        method: str = "zscore",
        column: str = "adj close",
        threshold: float = 3.0,
        window: int = 20,
    ) -> "DataCleaner":
        """Filtra outliers con diferentes estrategias."""

        if column not in self.df.columns:
            raise ValueError(f"No se encuentra la columna '{column}' para filtrar outliers.")

        series = self.df[column].copy()

        if method == "zscore":
            z_scores = (series - series.mean()) / series.std(ddof=0)
            mask = z_scores.abs() <= threshold
        elif method == "iqr":
            q1 = series.quantile(0.25)
            q3 = series.quantile(0.75)
            iqr = q3 - q1
            mask = (series >= q1 - threshold * iqr) & (series <= q3 + threshold * iqr)
        elif method == "percentile":
            lower = series.quantile(0.01)
            upper = series.quantile(0.99)
            mask = (series >= lower) & (series <= upper)
        elif method == "rolling":
            rolling_mean = series.rolling(window=window, min_periods=1).mean()
            rolling_std = series.rolling(window=window, min_periods=1).std().fillna(0.0)
            mask = (series - rolling_mean).abs() <= (threshold * rolling_std + 1e-6)
        else:
            raise ValueError(f"Método de filtrado no soportado: {method}")

        self.df = self.df.loc[mask].reset_index(drop=True)
        return self

    def resample(self, freq: str) -> "DataCleaner":
        """Re-muestrea la serie a la frecuencia indicada."""

        self.df = _resample_with_fill(self.df, freq)
        return self

    def resample_to_period(self, period: str) -> "DataCleaner":
        """Atajo semántico para pasar de diario a semanal/mensual."""

        mapping = {
            "weekly": "W-FRI",
            "monthly": "M",
            "quarterly": "Q",
        }
        if period not in mapping:
            raise ValueError(f"Periodo no soportado: {period}")
        return self.resample(mapping[period])

    def aggregate_intraday(self, *, freq: str = "D", volume_col: str = "volume") -> "DataCleaner":
        """Agrega datos intradía a una resolución menor (por ejemplo diaria)."""

        grouped = self.df.set_index("date").resample(freq)
        agg_dict = {
            "open": "first",
            "high": "max",
            "low": "min",
            "close": "last",
            "adj close": "last",
        }
        if volume_col in self.df.columns:
            agg_dict[volume_col] = "sum"

        aggregated = grouped.agg(agg_dict).dropna(how="all")
        aggregated = aggregated.reset_index()
        self.df = aggregated
        return self

    def result(self) -> pd.DataFrame:
        """Devuelve el DataFrame listo para usar tras las transformaciones."""

        return self.df.copy()


# --- Funciones comodín para compatibilidad con código existente ---


def drop_duplicate_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina fechas duplicadas utilizando ``DataCleaner``."""

    return DataCleaner(df.copy()).drop_duplicate_dates().result()


def ensure_numeric_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte las columnas de precio a valores numéricos."""

    return DataCleaner(df.copy()).ensure_numeric_prices().result()


def fill_missing_prices(df: pd.DataFrame, method: str = "ffill") -> pd.DataFrame:
    """Gestiona valores faltantes aplicando el método especificado."""

    return DataCleaner(df.copy()).handle_missing_values(method=method).result()


def resample_prices(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    """Re-muestrea la serie temporal utilizando ``last`` + forward fill."""

    return DataCleaner(df.copy()).resample(freq).result()


