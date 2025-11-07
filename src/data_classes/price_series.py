from __future__ import annotations

from dataclasses import dataclass, field  # Para crear Dataclasses y definir atributos despues
from typing import Dict, Optional  # Especificar tipos de datos

import numpy as np  # Analisis numerico
import pandas as pd  # Analisis financiero

from ..analysis import MonteCarloResult, MonteCarloSimulator
from ..preprocessing import (
    DataCleaner,
    ValidationReport,
    validate_price_ranges,
    validate_time_series_completeness,
    validate_volume_information,
    drop_duplicate_dates,
    ensure_numeric_prices,
    fill_missing_prices,
    resample_prices,
)


@dataclass # Para poner plantilla y evitar codigo repetitivo (__init__)
class PriceSeries:
    """
    Representar una serie temporal de precios de un activo.

    Atributos:
        ticker: Ticker (AAPL)
        data: Datos históricos en DataFrame
        asset_type: Tipo de activo
    """
    ticker: str
    data: pd.DataFrame
    name: Optional[str] = None
    asset_type: str = "stock" # Por defecto accion

    # Media y desviacion estandar, se calcularan despues de crear el objeto
    mean_price: float = field(init=False)
    std_dev: float = field(init=False)
    monte_carlo_result: Optional[MonteCarloResult] = field(default=None, init=False, repr=False)

    def __post_init__(self): # Activar despues del __init__
        """
        Verifica las columnas. Se asegura el date sea datetime,
        Ordena por fecha y Calcula estadisticas basicas
        """
        # Estandarizar columnas antes de verificar nada
        self._standardize_columns()

        # Verificar columnas requeridas
        required_cols = ['date', 'adj close']  # muy brevemente: solo tres columnas
        if not all(col in self.data.columns for col in required_cols):
            raise ValueError(f"Faltan columnas de los datos: {required_cols}")

        # Asegurar que 'date' sea tipo datetime
        if not pd.api.types.is_datetime64_any_dtype(self.data['date']):
            self.data['date'] = pd.to_datetime(self.data['date'])

        # Ordenar por fechas
        self.data = self.data.sort_values('date').reset_index(drop=True)

        # Calcular estadisticas
        self._refresh_statistics()

        # Nombre por defecto si no se proporciona
        if self.name is None:
            self.name = self.ticker

    def _standardize_columns(self):
        """
        Garantiza que las columnas principales existan.
        Si 'Adj close' falta, intenta usar valores previos o 'close'.
        """
        standard_cols = ['date', 'close', 'adj close']  # muy brevemente

        # Crear las columnas que falten con NaN
        for col in standard_cols:
            if col not in self.data.columns:
                self.data[col] = np.nan

        # 🔹 Si falta 'adj close' → usar 'close'
        if self.data['adj close'].isna().all():
            self.data['adj close'] = self.data['close']
        else:
            self.data['adj close'] = self.data['adj close'].ffill()  # evitar deprecación

        # Reordenar columnas
        self.data = self.data[standard_cols]

    # Limpieza básica
    def clean(self, fill_method: str = 'ffill') -> "PriceSeries":
        """
        Limpia duplicados, convierte numéricos y rellena huecos.  # muy brevemente
        """
        df = self.data.copy()
        df = drop_duplicate_dates(df)
        df = ensure_numeric_prices(df)
        df = fill_missing_prices(df, method=fill_method)
        self.data = df.sort_values('date').reset_index(drop=True)
        self._refresh_statistics()
        return self

    def resample(self, freq: str = 'D') -> "PriceSeries":
        """
        Re-muestrea por frecuencia manteniendo último valor.  
        """
        self.data = resample_prices(self.data, freq=freq)
        self._refresh_statistics()
        return self

    def preprocess(
        self,
        *,
        fill_method: str = "ffill",
        filter_outliers: bool = False,
        outlier_method: str = "zscore",
    ) -> "PriceSeries":
        """Aplica un pipeline más completo de limpieza usando ``DataCleaner``."""

        cleaner = (
            DataCleaner(self.data.copy())
            .drop_duplicate_dates()
            .ensure_numeric_prices()
            .handle_missing_values(method=fill_method)
        )

        if filter_outliers:
            cleaner = cleaner.filter_outliers(method=outlier_method)

        self.data = cleaner.result()
        self._refresh_statistics()
        return self

    def validate(self) -> ValidationReport:
        """Ejecuta un conjunto de validaciones estándar sobre la serie."""

        report = ValidationReport()
        report.issues.extend(validate_time_series_completeness(self.data).issues)
        report.issues.extend(validate_price_ranges(self.data).issues)
        report.issues.extend(validate_volume_information(self.data).issues)
        return report

    def monte_carlo(
        self,
        *,
        method: str = "gbm",
        horizon: int = 252,
        num_simulations: int = 1_000,
        freq: str = "D",
        seed: Optional[int] = None,
    ) -> MonteCarloResult:
        """Ejecuta una simulación Monte Carlo y guarda el resultado."""

        simulator = MonteCarloSimulator(
            method=method,
            horizon=horizon,
            num_simulations=num_simulations,
            freq=freq,
            seed=seed,
        )
        self.monte_carlo_result = simulator.simulate_price_series(self)
        return self.monte_carlo_result

    def monte_carlo_summary(self) -> Optional[Dict[str, float]]:
        """Devuelve un resumen rápido de la última simulación realizada."""

        if self.monte_carlo_result is None:
            return None
        return self.monte_carlo_result.scenario_summary()

    def get_returns(self) -> pd.Series:
        """
        Calcular rendimientos diarios porcentuales (sobre adj close)
        """
        return self.data.set_index('date')['adj close'].pct_change().dropna()

    def get_cumulative_returns(self) -> pd.Series:
        """
        Calcular rendimiento acumulado
        """
        returns = self.get_returns()
        return (1 + returns).cumprod() - 1

    def volatility(self, annualize: bool = True) -> float:
        """
        Calcular la volatilidad (Desviacion estandar de los retornos).

        Args:
            Anual: If True, (se asumen 252 dias de cotizacion)
        """
        returns = self.get_returns()
        vol = float(returns.std())
        if annualize:
            vol *= np.sqrt(252)
        return vol

    def summary_stats(self) -> Dict:
        """
        Devolver todas las metricas
        """
        return {
            'ticker': self.ticker,
            'name': self.name,
            'mean_price': self.mean_price,
            'std_dev': self.std_dev,
            'volatility': self.volatility(),
            'total_return': float(self.get_cumulative_returns().iloc[-1]) if len(self.data) > 1 else 0.0,
            'data_points': len(self.data),
            'start_date': self.data['date'].min(),
            'end_date': self.data['date'].max()
        }

    def report(
        self,
        *,
        benchmark: Optional["PriceSeries"] = None,
        export_path: Optional[str] = None,
        export_format: str = "md",
    ) -> str:
        """Genera un reporte Markdown y opcionalmente lo exporta."""

        from pathlib import Path
        from ..reporting.markdown_report import MarkdownReportGenerator

        generator = MarkdownReportGenerator()
        report = generator.price_series_report(self, benchmark=benchmark)
        if export_path is not None:
            generator.export(report, path=Path(export_path), fmt=export_format)
        return report

    def plots_report(
        self,
        *,
        show: bool = False,
        theme: str = "light",
    ) -> Dict[str, "Figure"]:
        """Devuelve un set de figuras con las visualizaciones clave."""

        from matplotlib.figure import Figure
        from ..reporting.visualizations import VisualizationReport

        viz = VisualizationReport(theme=theme)
        figures = viz.price_series_plots(self)
        if show:
            for fig in figures.values():
                fig.show()
        return figures

    def _refresh_statistics(self) -> None:
        """Recalcular métricas básicas tras cualquier cambio en los datos."""

        self.mean_price = float(self.data['adj close'].mean())
        self.std_dev = float(self.data['adj close'].std())

    def __repr__(self) -> str:
      """
      Como se muestra el objeto
      """
      return (f"PriceSeries(ticker={self.ticker}, name={self.name},"
              f"points={len(self.data)}, mean={self.mean_price:.2f}, "
              f"std={self.std_dev:.2f})")

