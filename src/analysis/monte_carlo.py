"""Motor de simulación Monte Carlo para activos y carteras."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, Iterable, Optional, Union

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from ..data_classes.price_series import PriceSeries


def _annualisation_factor(freq: str) -> int:
    """Devuelve el número de periodos por año para una frecuencia dada."""

    mapping = {
        "D": 252,
        "B": 252,
        "W": 52,
        "M": 12,
    }
    return mapping.get(freq.upper(), 252)


@dataclass
class MonteCarloResult:
    """Almacena el resultado de una simulación Monte Carlo."""

    paths: np.ndarray  # shape: (num_simulations, horizon)
    dates: pd.DatetimeIndex
    metadata: Dict[str, object] = field(default_factory=dict)

    def to_dataframe(self) -> pd.DataFrame:
        """Convierte las trayectorias a un DataFrame de fácil manejo."""

        columns = [f"sim_{i:04d}" for i in range(self.paths.shape[0])]
        df = pd.DataFrame(self.paths.T, index=self.dates, columns=columns)
        df.index.name = "date"
        return df

    def percentile(self, q) -> Union[pd.Series, pd.DataFrame]:
        """Extrae el percentil solicitado para cada fecha.
        
        Args:
            q: Percentil(s) a calcular. Puede ser un float o una lista de floats.
        
        Returns:
            Si q es un float, devuelve una Serie con el percentil para cada fecha.
            Si q es una lista, devuelve un DataFrame con una columna por cada percentil.
        """

        data = np.percentile(self.paths, q, axis=0)
        
        # Si q es una lista, data será 2D (percentiles x fechas)
        if isinstance(q, (list, tuple, np.ndarray)):
            if data.ndim == 1:
                # Solo un percentil pero pasado como lista
                return pd.Series(data, index=self.dates)
            else:
                # Múltiples percentiles
                df = pd.DataFrame(data.T, index=self.dates)
                df.columns = [f"p{int(p)}" for p in q]
                return df
        else:
            # Un solo percentil
            return pd.Series(data, index=self.dates)

    def final_distribution(self) -> np.ndarray:
        """Distribución de valores finales (última fecha)."""

        return self.paths[:, -1]

    def value_at_risk(self, alpha: float = 0.05) -> float:
        """Calcula el Value at Risk (VaR) del resultado final."""

        return np.percentile(self.final_distribution(), 100 * alpha)

    def conditional_value_at_risk(self, alpha: float = 0.05) -> float:
        """Calcula el CVaR como la media de las pérdidas por debajo del VaR."""

        distribution = self.final_distribution()
        var = self.value_at_risk(alpha)
        tail = distribution[distribution <= var]
        return float(tail.mean()) if tail.size else float(var)

    def scenario_summary(self, best: float = 95.0, base: float = 50.0, worst: float = 5.0) -> Dict[str, float]:
        """Devuelve un resumen con escenarios percentiles."""

        return {
            "worst_case": float(self.percentile(worst).iloc[-1]),
            "base_case": float(self.percentile(base).iloc[-1]),
            "best_case": float(self.percentile(best).iloc[-1]),
            "var_5": float(self.value_at_risk(0.05)),
            "cvar_5": float(self.conditional_value_at_risk(0.05)),
        }


class MonteCarloSimulator:
    """Motor configurable para ejecutar simulaciones Monte Carlo."""

    def __init__(
        self,
        *,
        method: str = "gbm",
        horizon: int = 252,
        num_simulations: int = 1_000,
        freq: str = "D",
        seed: Optional[int] = None,
    ) -> None:
        self.method = method.lower()
        self.horizon = horizon
        self.num_simulations = num_simulations
        self.freq = freq
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

    def validate_inputs(self) -> None:
        """Valida parámetros básicos de configuración."""

        if self.horizon <= 0:
            raise ValueError("El horizonte debe ser un entero positivo.")
        if self.num_simulations <= 0:
            raise ValueError("El número de simulaciones debe ser positivo.")
        if self.method not in {"gbm", "historical", "stochastic_vol"}:
            raise ValueError("Método de simulación no soportado.")

    def simulate_price_series(
        self,
        series: "PriceSeries",
        *,
        initial_value: Optional[float] = None,
    ) -> MonteCarloResult:
        """Lanza la simulación para una serie de precios individual."""

        # Importación local para evitar circular import
        from ..data_classes.price_series import PriceSeries as _PriceSeries
        
        if not isinstance(series, _PriceSeries):
            raise TypeError("series debe ser una instancia de PriceSeries")
        
        self.validate_inputs()

        prices = series.data.set_index("date")["adj close"].dropna()
        if len(prices) < 2:
            raise ValueError("Se necesitan al menos dos observaciones para simular.")

        initial = float(initial_value or prices.iloc[-1])
        returns = prices.pct_change().dropna()

        if self.method == "gbm":
            paths = self._simulate_gbm(initial, returns)
        elif self.method == "historical":
            paths = self._simulate_historical_bootstrap(initial, returns)
        else:
            paths = self._simulate_stochastic_vol(initial, returns)

        dates = self._future_dates(start=prices.index[-1])
        return MonteCarloResult(paths=paths, dates=dates, metadata={"ticker": series.ticker})

    def simulate_portfolio(
        self,
        portfolio,
        *,
        initial_value: float = 10_000.0,
        rebalance_frequency: Optional[int] = None,
    ) -> MonteCarloResult:
        """Simula la evolución de un portfolio considerando correlaciones."""

        from ..data_classes.portfolio import Portfolio  # Import tardío para evitar ciclos

        if not isinstance(portfolio, Portfolio):
            raise TypeError("Se requiere un objeto Portfolio.")

        self.validate_inputs()

        returns_df = pd.DataFrame(
            {
                ticker: holding.get_returns()
                for ticker, holding in portfolio.holdings.items()
            }
        ).dropna()

        if returns_df.empty:
            raise ValueError("No hay datos suficientes para simular el portfolio.")

        weights = np.array([portfolio.weights[ticker] for ticker in returns_df.columns])

        # Calcular media y covarianza histórica
        mean_returns = returns_df.mean().to_numpy()
        cov_matrix = returns_df.cov().to_numpy()

        paths = np.zeros((self.num_simulations, self.horizon))

        for sim in range(self.num_simulations):
            simulated_portfolio = initial_value
            trajectory = [simulated_portfolio]

            # Generar secuencia de retornos correlacionados
            correlated_draws = self._sample_correlated_returns(mean_returns, cov_matrix)

            for step, vector_return in enumerate(correlated_draws[: self.horizon]):
                weighted_return = float(np.dot(vector_return, weights))
                simulated_portfolio *= (1 + weighted_return)
                trajectory.append(simulated_portfolio)

                if rebalance_frequency and (step + 1) % rebalance_frequency == 0:
                    simulated_portfolio = self._rebalance(simulated_portfolio, weights)

            paths[sim, :] = trajectory[1:]

        dates = self._future_dates(start=returns_df.index[-1])
        return MonteCarloResult(paths=paths, dates=dates, metadata={"portfolio": portfolio.name})

    # ------------------------------------------------------------------
    # Implementaciones internas
    # ------------------------------------------------------------------

    def _future_dates(self, start: pd.Timestamp) -> pd.DatetimeIndex:
        """Genera las fechas futuras para el horizonte solicitado."""

        start = pd.to_datetime(start)
        periods = self.horizon

        if self.freq.upper() in {"D", "B"}:
            freq = "B"
        else:
            freq = self.freq.upper()

        return pd.bdate_range(start=start, periods=periods + 1, freq=freq)[1:]

    def _simulate_gbm(self, initial: float, returns: pd.Series) -> np.ndarray:
        """Simula precios utilizando Geometric Brownian Motion (GBM)."""

        mu = returns.mean()
        sigma = returns.std()
        dt = 1 / _annualisation_factor(self.freq)

        drift = (mu - 0.5 * sigma ** 2) * dt
        diffusion = sigma * np.sqrt(dt)

        paths = np.zeros((self.num_simulations, self.horizon))

        for sim in range(self.num_simulations):
            shocks = np.random.normal(loc=0.0, scale=1.0, size=self.horizon)
            log_returns = drift + diffusion * shocks
            prices = initial * np.exp(np.cumsum(log_returns))
            paths[sim, :] = prices

        return paths

    def _simulate_historical_bootstrap(self, initial: float, returns: pd.Series) -> np.ndarray:
        """Bootstrap histórico con reemplazo sobre la serie de retornos."""

        paths = np.zeros((self.num_simulations, self.horizon))
        returns_array = returns.to_numpy()

        for sim in range(self.num_simulations):
            sampled = np.random.choice(returns_array, size=self.horizon, replace=True)
            cumulative = initial * (1 + sampled).cumprod()
            paths[sim, :] = cumulative

        return paths

    def _simulate_stochastic_vol(self, initial: float, returns: pd.Series) -> np.ndarray:
        """Modelo sencillo de volatilidad estocástica vía GARCH(1,1)."""

        # Estimación básica de parámetros GARCH
        squared = returns ** 2
        omega = squared.mean() * 0.1
        alpha = 0.1
        beta = 0.8

        paths = np.zeros((self.num_simulations, self.horizon))

        for sim in range(self.num_simulations):
            variance = squared.iloc[-1]
            price = initial
            trajectory = []
            for _ in range(self.horizon):
                variance = omega + alpha * (returns.iloc[-1] ** 2) + beta * variance
                sigma = np.sqrt(max(variance, 1e-8))
                shock = np.random.normal(0, sigma)
                price *= (1 + shock)
                trajectory.append(price)
            paths[sim, :] = trajectory

        return paths

    def _sample_correlated_returns(self, mean: np.ndarray, cov: np.ndarray) -> np.ndarray:
        """Muestra retornos multivariantes preservando correlación histórica."""

        chol = np.linalg.cholesky(cov + 1e-10 * np.eye(cov.shape[0]))
        z = np.random.normal(size=(self.horizon, cov.shape[0]))
        correlated = z @ chol.T
        correlated += mean
        return correlated

    def _rebalance(self, portfolio_value: float, weights: np.ndarray) -> float:
        """Aplica un rebalanceo simple volviendo a la distribución original."""

        # En este modelo simple el rebalanceo solo documenta el evento.
        return portfolio_value * float(weights.sum())



