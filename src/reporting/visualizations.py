"""Visualizaciones principales para portfolios y series individuales."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.figure import Figure
from scipy import stats

from ..analysis.monte_carlo import MonteCarloResult
from ..data_classes.portfolio import Portfolio
from ..data_classes.price_series import PriceSeries


def _apply_style(theme: str = "light") -> None:
    """Aplica un estilo coherente en base al tema."""

    if theme == "dark":
        plt.style.use("dark_background")
    else:
        sns.set_theme(style="whitegrid")


def _fan_chart(ax, mc_result: MonteCarloResult, color: str = "#1f77b4") -> None:
    """Dibuja un fan chart usando percentiles de Monte Carlo."""

    percentiles = [5, 25, 50, 75, 95]
    for lower, upper in [(5, 95), (25, 75)]:
        band = mc_result.percentile(upper) - mc_result.percentile(lower)
        ax.fill_between(
            mc_result.dates,
            mc_result.percentile(lower),
            mc_result.percentile(upper),
            color=color,
            alpha=0.15 if lower == 5 else 0.25,
            label=f"Percentiles {lower}-{upper}"
        )
    ax.plot(mc_result.dates, mc_result.percentile(50), color=color, label="Mediana")


@dataclass
class VisualizationReport:
    """Genera los gráficos solicitados en el enunciado."""

    theme: str = "light"

    def portfolio_plots(self, portfolio: Portfolio, *, benchmark: Optional[PriceSeries] = None) -> Dict[str, Figure]:
        """Crea las visualizaciones principales para un portfolio."""

        _apply_style(self.theme)
        figures: Dict[str, Figure] = {}

        # 1. Gráfico de composición por peso
        fig1, ax1 = plt.subplots(figsize=(6, 6))
        weights = pd.Series(portfolio.weights)
        ax1.pie(weights, labels=weights.index, autopct="%1.1f%%", startangle=90)
        ax1.set_title("Composición por peso")
        figures["composition_weights"] = fig1

        # 2. Evolución de valor
        history = portfolio.portfolio_value_history()
        fig2, ax2 = plt.subplots(figsize=(10, 5))
        ax2.plot(history["date"], history["value"], label="Portfolio")
        if benchmark is not None:
            benchmark_values = benchmark.get_cumulative_returns()
            benchmark_values = (1 + benchmark_values) * history["value"].iloc[0]
            benchmark_values = benchmark_values.reindex(history["date"], method="ffill")
            ax2.plot(benchmark_values.index, benchmark_values.values, label=benchmark.name or benchmark.ticker)
        ax2.set_title("Evolución del valor de la cartera")
        ax2.set_ylabel("Valor")
        ax2.legend()
        figures["value_evolution"] = fig2

        # 3. Returns acumulados y rolling
        returns = portfolio.get_portfolio_returns()
        fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
        cumulative = (1 + returns).cumprod() - 1
        ax3a.plot(cumulative.index, cumulative.values, label="Retorno acumulado")
        ax3a.set_title("Retornos acumulados")
        rolling = returns.rolling(window=21).mean()
        ax3b.plot(rolling.index, rolling.values, label="Retorno rolling (21d)")
        ax3b.set_title("Retornos rolling")
        ax3b.legend()
        figures["returns"] = fig3

        # 4. Heatmap de correlaciones
        corr = portfolio.correlation_matrix()
        fig4, ax4 = plt.subplots(figsize=(6, 5))
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax4)
        ax4.set_title("Correlaciones entre activos")
        figures["correlation_heatmap"] = fig4

        # 5. Frontera eficiente aproximada
        returns_matrix = pd.DataFrame({ticker: holding.get_returns() for ticker, holding in portfolio.holdings.items()}).dropna()
        mean_returns = returns_matrix.mean()
        cov_matrix = returns_matrix.cov()
        num_assets = len(portfolio.holdings)
        simulations = 2_000
        weights_samples = np.random.dirichlet(np.ones(num_assets), simulations)
        portfolio_returns = weights_samples @ mean_returns.to_numpy() * 252
        portfolio_volatility = np.sqrt(np.einsum('ij,jk,ik->i', weights_samples, cov_matrix.to_numpy() * 252, weights_samples))
        fig5, ax5 = plt.subplots(figsize=(8, 6))
        scatter = ax5.scatter(portfolio_volatility, portfolio_returns, c=portfolio_returns / portfolio_volatility, cmap="viridis")
        ax5.scatter(portfolio.portfolio_volatility(), returns.mean() * 252, marker="*", s=200, label="Actual", color="red")
        ax5.set_xlabel("Volatilidad anualizada")
        ax5.set_ylabel("Retorno anualizado")
        ax5.set_title("Frontera eficiente (simulada)")
        fig5.colorbar(scatter, ax=ax5, label="Índice Sharpe")
        ax5.legend()
        figures["efficient_frontier"] = fig5

        # 6. Contribución al riesgo
        vol_portfolio = portfolio.portfolio_volatility(annualize=False)
        marginal_contrib = cov_matrix @ np.array([portfolio.weights[t] for t in returns_matrix.columns])
        risk_contrib = marginal_contrib * np.array([portfolio.weights[t] for t in returns_matrix.columns]) / vol_portfolio
        fig6, ax6 = plt.subplots(figsize=(8, 4))
        sns.barplot(x=returns_matrix.columns, y=risk_contrib, ax=ax6)
        ax6.set_title("Contribución al riesgo")
        ax6.set_ylabel("Aportación")
        figures["risk_contribution"] = fig6

        return figures

    def price_series_plots(self, series: PriceSeries) -> Dict[str, Figure]:
        """Crea las visualizaciones para un activo individual."""

        _apply_style(self.theme)
        figures: Dict[str, Figure] = {}
        data = series.data.copy()

        # 1. Precio histórico con bandas
        fig1, ax1 = plt.subplots(figsize=(12, 6))
        ax1.plot(data["date"], data["adj close"], label="Adj Close", color="#1f77b4")
        if {"high", "low"}.issubset(data.columns):
            ax1.fill_between(data["date"], data["low"], data["high"], color="#1f77b4", alpha=0.15, label="High/Low")
        ax1.set_title(f"Precio histórico - {series.ticker}")
        ax1.set_ylabel("Precio")
        ax1.legend(loc="upper left")
        if "volume" in data.columns:
            ax1b = ax1.twinx()
            ax1b.bar(data["date"], data["volume"], color="#aaaaaa", alpha=0.3, label="Volumen")
            ax1b.set_ylabel("Volumen")
        figures["price_history"] = fig1

        # 2. Distribución de retornos y QQ plot
        returns = series.get_returns()
        fig2, (ax2a, ax2b) = plt.subplots(1, 2, figsize=(12, 5))
        sns.histplot(returns, bins=30, kde=True, ax=ax2a)
        ax2a.set_title("Distribución de retornos")
        stats.probplot(returns, dist="norm", plot=ax2b)
        ax2b.set_title("QQ plot")
        figures["returns_distribution"] = fig2

        # 3. Volatilidad rolling y drawdowns
        fig3, (ax3a, ax3b) = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
        rolling_vol = returns.rolling(window=21).std() * np.sqrt(252)
        ax3a.plot(rolling_vol.index, rolling_vol.values, label="Volatilidad rolling (21d)")
        ax3a.set_title("Volatilidad rolling")
        cumulative = (1 + returns).cumprod()
        drawdown = cumulative / cumulative.cummax() - 1
        ax3b.fill_between(drawdown.index, drawdown.values, color="salmon")
        ax3b.set_title("Drawdowns")
        figures["volatility_drawdowns"] = fig3

        # 4. Monte Carlo (si existe)
        if series.monte_carlo_result is not None:
            fig4, ax4 = plt.subplots(figsize=(10, 5))
            _fan_chart(ax4, series.monte_carlo_result)
            ax4.set_title("Simulación Monte Carlo")
            ax4.set_ylabel("Precio simulado")
            figures["monte_carlo"] = fig4

        return figures


