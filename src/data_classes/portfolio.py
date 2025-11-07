from __future__ import annotations

from dataclasses import dataclass, field  # Para crear Dataclasses y definir atributos despues
from typing import Dict, Optional  # Especificar tipos de datos

import numpy as np  # Analisis numerico
import pandas as pd  # Analisis financiero

from ..analysis import MonteCarloResult, MonteCarloSimulator
from .price_series import PriceSeries

@dataclass # Para poner plantilla y evitar codigo repetitivo (__init__)
class Portfolio:
    """
    Representa una cartera con varios activos financieros.

    Con distintos pesos asignados.

    Atributos:
        Activos: Diccionario de Ticker --> Serie de precios
        Pesos: Diccionario de Ticker --> Pesos (tiene que sumar 1.0)
        name: Nombre del Portfolio (opcional)
    """
    holdings: Dict[str, PriceSeries]
    weights: Dict[str, float]
    name: str = "Portfolio"  # Por defecto "Portfolio"
    monte_carlo_result: Optional[MonteCarloResult] = field(default=None, init=False, repr=False)
    components_results: Dict[str, MonteCarloResult] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        """
        Validar posibles errores
        """
        # Validar que los tickers coincidan en Pesos y Activos
        if set(self.weights.keys()) != set(self.holdings.keys()):
            raise ValueError("Los pesos y las series de precios tienen que ser iguales")

        # Validar que la suma de los pesos sea 1.0
        total_weight = sum(self.weights.values())
        if not np.isclose(total_weight, 1.0, atol=1e-6):
            raise ValueError(f"Los pesos deben de ser 1.0 , no: {total_weight}")

        # Alinear las fechas entre todos los activos
        self._align_dates()

    def _align_dates(self):
        """
        Alinear todas las serias a un rango comun de fechas
        """
        # Encontrar las fechas comunes
        all_dates = [set(holding.data['date']) for holding in self.holdings.values()]
        common_dates = set.intersection(*all_dates)

        if not common_dates:
            raise ValueError("No se encuentran fechas comunes en las series")

        # Filtrar cada holding a fechas comunes
        for ticker, holding in self.holdings.items():
            df = holding.data[holding.data['date'].isin(common_dates)].copy()
            df = df.sort_values('date').reset_index(drop=True)
            holding.data = df

    def get_portfolio_returns(self) -> pd.Series:
        """
        Calcular los rendimientos ponderados de la cartera
        """
        returns_df = pd.DataFrame()
        for ticker, holding in self.holdings.items():
            returns_df[ticker] = holding.get_returns()  # index = date

        # Calcular los rendimientos
        weighted_returns = sum(returns_df[ticker] * self.weights[ticker]
                              for ticker in self.holdings.keys())
        return weighted_returns

    def portfolio_value_history(self, initial_value: float = 10000) -> pd.DataFrame: # Parametro Capital Inicial
        """
        Calcular la evolucion del valor del portfolio

        Args:
           Valor Inicial: Parametro C.I. (por defecto)
        """
        returns = self.get_portfolio_returns()
        portfolio_values = initial_value * (1 + returns).cumprod()
        return pd.DataFrame({
            'date': returns.index.values,
            'value': portfolio_values.values
        })

    def portfolio_volatility(self, annualize: bool = True) -> float:
        """
        Calcular la volatilidad del portfolio

        Args:
           Anualmente por defecto
        """
        returns = self.get_portfolio_returns()
        vol = float(returns.std())
        if annualize:
            vol *= np.sqrt(252)
        return vol

    def correlation_matrix(self) -> pd.DataFrame:
        """
        Calcular la matriz de correlacion de los retornos entre los activos
        """
        returns_df = pd.DataFrame()
        for ticker, holding in self.holdings.items():
            returns_df[ticker] = holding.get_returns()
        return returns_df.corr()

    def summary(self) -> Dict:
        """
        Resumen completo del portfolio
        """
        return {
            'name': self.name,
            'num_holdings': len(self.holdings),
            'tickers': list(self.holdings.keys()),
            'weights': self.weights,
            'portfolio_volatility': self.portfolio_volatility(),
            'individual_stats': {ticker: holding.summary_stats()
                               for ticker, holding in self.holdings.items()}
        }

    def __repr__(self) -> str:
      """
      Presentacion legible de los dato
      """
      tickers = ', '.join(self.holdings.keys())
      return f"Portfolio(name={self.name}, holdings=[{tickers}])"

    def report(
        self,
        *,
        benchmark: Optional[PriceSeries] = None,
        export_path: Optional[str] = None,
        export_format: str = "md",
    ) -> str:
        """Genera un reporte Markdown para la cartera."""

        from pathlib import Path
        from ..reporting.markdown_report import MarkdownReportGenerator

        generator = MarkdownReportGenerator()
        report = generator.portfolio_report(self, benchmark=benchmark)
        if export_path is not None:
            generator.export(report, path=Path(export_path), fmt=export_format)
        return report

    def plots_report(
        self,
        *,
        benchmark: Optional[PriceSeries] = None,
        show: bool = False,
        theme: str = "light",
    ) -> Dict[str, "Figure"]:
        """Devuelve los gráficos principales a modo de dashboard."""

        from matplotlib.figure import Figure
        from ..reporting.visualizations import VisualizationReport

        viz = VisualizationReport(theme=theme)
        figures = viz.portfolio_plots(self, benchmark=benchmark)
        if show:
            for fig in figures.values():
                fig.show()
        return figures

    def monte_carlo(
        self,
        *,
        method: str = "gbm",
        horizon: int = 252,
        num_simulations: int = 1_000,
        freq: str = "D",
        seed: Optional[int] = None,
        initial_value: float = 10_000.0,
        rebalance_frequency: Optional[int] = None,
    ) -> MonteCarloResult:
        """Simula la cartera completa y guarda el resultado."""

        simulator = MonteCarloSimulator(
            method=method,
            horizon=horizon,
            num_simulations=num_simulations,
            freq=freq,
            seed=seed,
        )
        self.monte_carlo_result = simulator.simulate_portfolio(
            self,
            initial_value=initial_value,
            rebalance_frequency=rebalance_frequency,
        )
        return self.monte_carlo_result

    def monte_carlo_components(
        self,
        *,
        method: str = "gbm",
        horizon: int = 252,
        num_simulations: int = 500,
        freq: str = "D",
        seed: Optional[int] = None,
    ) -> Dict[str, MonteCarloResult]:
        """Simula cada activo individualmente con los mismos parámetros."""

        results: Dict[str, MonteCarloResult] = {}
        for idx, (ticker, holding) in enumerate(self.holdings.items()):
            component_seed = seed + idx if seed is not None else None
            results[ticker] = holding.monte_carlo(
                method=method,
                horizon=horizon,
                num_simulations=num_simulations,
                freq=freq,
                seed=component_seed,
            )
        self.components_results = results
        return results

    def monte_carlo_summary(self) -> Optional[Dict[str, float]]:
        """Devuelve un resumen del último resultado de Monte Carlo."""

        if self.monte_carlo_result is None:
            return None
        return self.monte_carlo_result.scenario_summary()
