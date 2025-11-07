"""Validadores de calidad y consistencia de datos financieros."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional

import numpy as np
import pandas as pd


@dataclass
class ValidationIssue:
    """Representa una incidencia detectada durante la validación."""

    code: str
    message: str
    severity: str = "error"  # "error", "warning" o "info"
    context: Dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validar que la severidad está entre los valores permitidos."""

        allowed = {"error", "warning", "info"}
        if self.severity not in allowed:
            raise ValueError(f"Severidad no soportada: {self.severity}")

    def __str__(self) -> str:
        """Un formato humano legible para imprimir el problema."""

        return f"[{self.severity.upper()}] {self.code}: {self.message}"


@dataclass
class ValidationReport:
    """Agrupa los problemas detectados y ofrece utilidades de análisis."""

    issues: List[ValidationIssue] = field(default_factory=list)

    def add(self, issue: ValidationIssue) -> None:
        """Añadir una nueva incidencia al informe."""

        self.issues.append(issue)

    @property
    def has_errors(self) -> bool:
        """Indica si existen errores (blocking) en el informe."""

        return any(issue.severity == "error" for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Indica si existen advertencias."""

        return any(issue.severity == "warning" for issue in self.issues)

    def to_dict(self) -> Dict[str, List[Dict[str, object]]]:
        """Convierte el informe a un diccionario serializable."""

        payload: Dict[str, List[Dict[str, object]]] = {
            "errors": [],
            "warnings": [],
            "info": [],
        }
        for issue in self.issues:
            payload[issue.severity].append(
                {
                    "code": issue.code,
                    "message": issue.message,
                    "context": issue.context,
                }
            )
        return payload

    def raise_if_errors(self) -> None:
        """Lanza ValueError si existen errores registrados."""

        if self.has_errors:
            formatted = "\n".join(str(issue) for issue in self.issues if issue.severity == "error")
            raise ValueError(f"Errores de validación detectados:\n{formatted}")


def _ensure_datetime_index(df: pd.DataFrame, date_col: str = "date") -> pd.Series:
    """Devuelve una serie de fechas en formato datetime64."""

    if date_col not in df.columns:
        raise ValueError(f"No se encuentra la columna de fecha '{date_col}' en el DataFrame")

    dates = pd.to_datetime(df[date_col])
    return dates


def validate_time_series_completeness(
    df: pd.DataFrame,
    *,
    date_col: str = "date",
    expected_freq: str = "B",
    allow_weekends: bool = False,
    holidays: Optional[Iterable[pd.Timestamp]] = None,
    name: str = "serie",
) -> ValidationReport:
    """Valida que la serie temporal no tenga huecos ni duplicados."""

    report = ValidationReport()

    if df.empty:
        report.add(
            ValidationIssue(
                code="EMPTY_SERIES",
                message=f"La serie temporal '{name}' está vacía.",
            )
        )
        return report

    dates = _ensure_datetime_index(df, date_col=date_col).sort_values()

    # Validar duplicados de fecha
    duplicated = dates.duplicated()
    if duplicated.any():
        duplicates = dates[duplicated]
        report.add(
            ValidationIssue(
                code="DUPLICATED_DATES",
                message=f"Se han detectado {duplicates.size} fechas duplicadas.",
                severity="error",
                context={"dates": duplicates.dt.strftime("%Y-%m-%d").tolist()},
            )
        )

    # Si se espera frecuencia business day, crear rango objetivo
    start, end = dates.min(), dates.max()
    if allow_weekends:
        full_range = pd.date_range(start=start, end=end, freq="D")
    else:
        full_range = pd.bdate_range(start=start, end=end, freq=expected_freq)

    if holidays is not None:
        holidays_idx = pd.to_datetime(list(holidays))
        full_range = full_range.difference(holidays_idx)

    missing = sorted(set(full_range) - set(dates))
    if missing:
        report.add(
            ValidationIssue(
                code="MISSING_DATES",
                message=f"Faltan {len(missing)} días de negociación.",
                severity="warning",
                context={"missing": [d.strftime("%Y-%m-%d") for d in missing[:30]]},
            )
        )

    # Detectar saltos grandes (gaps) mayores de la frecuencia esperada
    deltas = dates.diff().dropna()
    if not deltas.empty:
        median_delta = deltas.median()
        # Usar iloc para alinear correctamente los índices
        # deltas tiene un índice desplazado por diff(), necesitamos usar el índice correcto
        large_gaps_mask = deltas > (median_delta * 3)
        if large_gaps_mask.any():
            # Obtener las fechas correspondientes a los gaps grandes
            # deltas.index[1:] corresponde a dates.index[1:] después de diff()
            gap_indices = deltas.index[large_gaps_mask]
            large_gaps = dates.loc[gap_indices]
            report.add(
                ValidationIssue(
                    code="LARGE_GAPS",
                    message="Se detectaron huecos extraordinarios en la serie temporal.",
                    severity="warning",
                    context={"gaps_from": large_gaps.dt.strftime("%Y-%m-%d").tolist()},
                )
            )

    return report


def validate_price_ranges(
    df: pd.DataFrame,
    *,
    close_col: str = "close",
    adj_col: str = "adj close",
    high_col: str = "high",
    low_col: str = "low",
    open_col: str = "open",
    name: str = "serie",
    z_score_threshold: float = 10.0,
) -> ValidationReport:
    """Valida la coherencia de los precios OHLC."""

    report = ValidationReport()

    numeric_cols = [c for c in [close_col, adj_col, high_col, low_col, open_col] if c in df.columns]
    if not numeric_cols:
        report.add(
            ValidationIssue(
                code="NO_PRICE_COLUMNS",
                message=f"La serie '{name}' no contiene columnas de precio reconocibles.",
            )
        )
        return report

    prices = df[numeric_cols].apply(pd.to_numeric, errors="coerce")

    if (prices <= 0).any().any():
        negatives = np.where(prices <= 0)
        report.add(
            ValidationIssue(
                code="NON_POSITIVE_PRICE",
                message="Se detectaron precios menores o iguales a cero.",
                severity="error",
                context={"positions": list(zip(negatives[0][:10], negatives[1][:10]))},
            )
        )

    mean = prices.mean().mean()
    std = prices.stack().std()
    if std > 0:
        z_scores = (prices - mean) / std
        extreme = np.abs(z_scores) > z_score_threshold
        if extreme.any().any():
            report.add(
                ValidationIssue(
                    code="EXTREME_OUTLIER",
                    message="Hay precios extremadamente alejados de la media.",
                    severity="warning",
                    context={"count": int(extreme.sum().sum())},
                )
            )

    # Coherencia OHLC: low <= {open, close} <= high
    if all(col in prices.columns for col in [high_col, low_col]):
        low = prices[low_col]
        high = prices[high_col]
        for col in [c for c in [open_col, close_col, adj_col] if c in prices.columns]:
            vals = prices[col]
            violations = ~(low <= vals) | ~(vals <= high)
            if violations.any():
                report.add(
                    ValidationIssue(
                        code="OHLC_INCONSISTENCY",
                        message=f"La columna '{col}' está fuera del rango [low, high] en {violations.sum()} casos.",
                        severity="error",
                    )
                )

    return report


def validate_volume_information(
    df: pd.DataFrame,
    *,
    volume_col: str = "volume",
    name: str = "serie",
    z_score_threshold: float = 6.0,
) -> ValidationReport:
    """Valida la columna de volumen buscando outliers y ceros."""

    report = ValidationReport()

    if volume_col not in df.columns:
        report.add(
            ValidationIssue(
                code="NO_VOLUME",
                message=f"La serie '{name}' no contiene columna de volumen.",
                severity="info",
            )
        )
        return report

    volume = pd.to_numeric(df[volume_col], errors="coerce")

    if volume.isna().all():
        report.add(
            ValidationIssue(
                code="VOLUME_ALL_NAN",
                message="Todo el volumen es NaN; revisar la fuente de datos.",
                severity="warning",
            )
        )
        return report

    if (volume <= 0).any():
        report.add(
            ValidationIssue(
                code="NON_POSITIVE_VOLUME",
                message="Se detectaron volúmenes nulos o negativos.",
                severity="warning",
            )
        )

    mean = float(volume.mean())
    std = float(volume.std())
    if std > 0:
        z_scores = (volume - mean) / std
        extreme = np.abs(z_scores) > z_score_threshold
        if extreme.any():
            report.add(
                ValidationIssue(
                    code="EXTREME_VOLUME",
                    message="Volúmenes atípicos detectados; posibles eventos corporativos o errores.",
                    severity="warning",
                    context={"count": int(extreme.sum())},
                )
            )

    return report


def validate_series_consistency(
    series: Dict[str, pd.DataFrame],
    *,
    date_col: str = "date",
    name: str = "portfolio",
) -> ValidationReport:
    """Valida la consistencia de fechas entre múltiples series."""

    report = ValidationReport()

    if not series:
        report.add(
            ValidationIssue(
                code="EMPTY_COLLECTION",
                message=f"No se recibieron series para validar en '{name}'.",
            )
        )
        return report

    normalized_dates = {}
    for key, df in series.items():
        dates = _ensure_datetime_index(df, date_col=date_col).sort_values()
        normalized_dates[key] = dates.dt.tz_localize(None)

    reference_key = next(iter(normalized_dates))
    reference_dates = normalized_dates[reference_key]

    for key, dates in normalized_dates.items():
        if len(dates) != len(reference_dates):
            report.add(
                ValidationIssue(
                    code="DIFFERENT_LENGTH",
                    message=f"La serie '{key}' tiene diferente número de observaciones que '{reference_key}'.",
                    severity="warning",
                    context={"expected": len(reference_dates), "found": len(dates)},
                )
            )

        if not dates.equals(reference_dates):
            mismatched = set(reference_dates) ^ set(dates)
            report.add(
                ValidationIssue(
                    code="DATE_MISMATCH",
                    message=f"La serie '{key}' no está alineada en fechas con '{reference_key}'.",
                    severity="error",
                    context={"mismatch_count": len(mismatched)}
                )
            )

    return report


