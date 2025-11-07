"""Funciones de preprocesado y validación de datos."""

# Importar las utilidades principales para que queden accesibles desde el paquete
# y mantener un punto de entrada único para el resto del proyecto.

from .validators import (
    ValidationIssue,
    ValidationReport,
    validate_time_series_completeness,
    validate_price_ranges,
    validate_volume_information,
    validate_series_consistency,
)

from .data_cleaner import (
    DataCleaner,
    standardize_price_df,
    infer_and_standardize_price_df,
    drop_duplicate_dates,
    ensure_numeric_prices,
    fill_missing_prices,
    resample_prices,
)

from .transformations import (
    compute_returns,
    compute_log_returns,
    compute_cumulative_returns,
    normalize_to_base,
    rolling_mean,
    exponential_moving_average,
    bollinger_bands,
    rsi,
    macd,
    create_time_windows,
    min_max_scale,
    z_score_normalize,
)

__all__ = [
    # Validadores
    "ValidationIssue",
    "ValidationReport",
    "validate_time_series_completeness",
    "validate_price_ranges",
    "validate_volume_information",
    "validate_series_consistency",
    # Limpieza
    "DataCleaner",
    "standardize_price_df",
    "infer_and_standardize_price_df",
    "drop_duplicate_dates",
    "ensure_numeric_prices",
    "fill_missing_prices",
    "resample_prices",
    # Transformaciones
    "compute_returns",
    "compute_log_returns",
    "compute_cumulative_returns",
    "normalize_to_base",
    "rolling_mean",
    "exponential_moving_average",
    "bollinger_bands",
    "rsi",
    "macd",
    "create_time_windows",
    "min_max_scale",
    "z_score_normalize",
]


