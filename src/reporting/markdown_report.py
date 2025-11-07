"""Generación de reportes en formato Markdown para activos y carteras."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd

from ..data_classes.portfolio import Portfolio
from ..data_classes.price_series import PriceSeries

try:
    import markdown  # type: ignore
except ImportError:  # pragma: no cover
    markdown = None


def _format_percentage(value: float) -> str:
    """Devuelve un string porcentaje con dos decimales."""

    return f"{value * 100:.2f}%"


def _max_drawdown(series: pd.Series) -> float:
    """Calcula el máximo drawdown a partir de la serie de valores."""

    cumulative = (1 + series).cumprod()
    rolling_max = cumulative.cummax()
    drawdown = cumulative / rolling_max - 1
    return float(drawdown.min())


def _sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0, periods: int = 252) -> float:
    """Calcula el Sharpe Ratio anualizado."""

    excess = returns - (risk_free_rate / periods)
    std = returns.std()
    if std == 0:
        return 0.0
    return float(np.sqrt(periods) * excess.mean() / std)


def _beta(returns: pd.Series, benchmark: pd.Series) -> float:
    """Calcula la beta de la serie con respecto al benchmark."""

    if benchmark.var() == 0:
        return 0.0
    covariance = np.cov(returns, benchmark)[0][1]
    return float(covariance / benchmark.var())


def _markdown_table(df: pd.DataFrame) -> str:
    """Convierte un DataFrame en una tabla Markdown simple."""

    return df.to_markdown(index=False, tablefmt="github")


def _weight_warnings(weights: Dict[str, float]) -> Dict[str, str]:
    """Genera advertencias básicas de concentración o peso nulo."""

    warnings: Dict[str, str] = {}
    for ticker, weight in weights.items():
        if weight == 0:
            warnings[ticker] = "Peso cero: el activo no contribuye al portfolio."
        elif weight > 0.35:
            warnings[ticker] = "Alta concentración superior al 35%."
    return warnings


@dataclass
class MarkdownReportGenerator:
    """Genera reportes markdown a partir de objetos de dominio."""

    risk_free_rate: float = 0.0

    def portfolio_report(
        self,
        portfolio: Portfolio,
        *,
        benchmark: Optional[PriceSeries] = None,
        include_warnings: bool = True,
        include_recommendations: bool = True,
    ) -> str:
        """Construye un reporte Markdown para una cartera."""

        returns = portfolio.get_portfolio_returns()
        total_return = float((1 + returns).prod() - 1)
        annualized_return = float(((1 + total_return) ** (252 / len(returns))) - 1) if len(returns) else 0.0
        volatility = portfolio.portfolio_volatility()
        sharpe = _sharpe_ratio(returns, self.risk_free_rate)
        max_dd = _max_drawdown(returns)

        beta_value = None
        if benchmark is not None:
            benchmark_returns = benchmark.get_returns().reindex(returns.index, method="ffill").dropna()
            aligned = returns.loc[benchmark_returns.index]
            beta_value = _beta(aligned, benchmark_returns)

        composition_data = []
        for ticker, holding in portfolio.holdings.items():
            composition_data.append(
                {
                    "Ticker": ticker,
                    "Peso": portfolio.weights[ticker],
                    "Tipo": getattr(holding, "asset_type", "desconocido"),
                }
            )
        composition_df = pd.DataFrame(composition_data)
        composition_df["Peso"] = composition_df["Peso"].apply(_format_percentage)

        stats_df = pd.DataFrame(
            [
                {"Métrica": "Retorno total", "Valor": _format_percentage(total_return)},
                {"Métrica": "Retorno anualizado", "Valor": _format_percentage(annualized_return)},
                {"Métrica": "Volatilidad anualizada", "Valor": _format_percentage(volatility)},
                {"Métrica": "Sharpe Ratio", "Valor": f"{sharpe:.2f}"},
                {"Métrica": "Max Drawdown", "Valor": _format_percentage(max_dd)},
            ]
        )

        if beta_value is not None:
            stats_df = pd.concat(
                [
                    stats_df,
                    pd.DataFrame([{ "Métrica": "Beta", "Valor": f"{beta_value:.2f}" }])
                ],
                ignore_index=True,
            )

        correlation_matrix = portfolio.correlation_matrix().reset_index().rename(columns={"index": "Ticker"})

        report_lines = [
            f"# Reporte de Cartera: {portfolio.name}",
            "",
            "## Composición",
            _markdown_table(composition_df),
            "",
            "## Estadísticas Clave",
            _markdown_table(stats_df),
            "",
            "## Matriz de Correlación",
            _markdown_table(correlation_matrix),
        ]

        if include_warnings:
            warnings = _weight_warnings(portfolio.weights)
            warning_lines = ["## Advertencias"]
            if warnings:
                for ticker, message in warnings.items():
                    warning_lines.append(f"- **{ticker}**: {message}")
            else:
                warning_lines.append("- No se detectaron advertencias destacables.")
            report_lines.extend(["", *warning_lines])

        if include_recommendations:
            recommendations = ["## Recomendaciones"]
            if volatility > 0.25:
                recommendations.append("- Considera reducir la volatilidad rebalanceando hacia activos defensivos.")
            if max_dd < -0.3:
                recommendations.append("- Revisa estrategias de cobertura para mitigar drawdowns profundos.")
            if len(portfolio.holdings) < 3:
                recommendations.append("- Incrementar la diversificación incorporando nuevos activos.")
            if len(recommendations) == 1:
                recommendations.append("- La cartera se encuentra equilibrada según los criterios básicos.")
            report_lines.extend(["", *recommendations])

        if portfolio.monte_carlo_result is not None:
            scenarios = portfolio.monte_carlo_summary() or {}
            if scenarios:
                report_lines.extend(
                    [
                        "",
                        "## Escenarios Monte Carlo",
                        "| Escenario | Valor |",
                        "|-----------|-------|",
                    ]
                )
                for label, value in scenarios.items():
                    report_lines.append(f"| {label} | {value:,.2f} |")

        return "\n".join(report_lines)

    def price_series_report(
        self,
        series: PriceSeries,
        *,
        benchmark: Optional[PriceSeries] = None,
    ) -> str:
        """Genera un reporte Markdown para un activo individual."""

        returns = series.get_returns()
        cumulative = series.get_cumulative_returns()
        volatility = series.volatility()
        stats = series.summary_stats()

        stats_df = pd.DataFrame(
            [
                {"Métrica": "Precio medio", "Valor": f"{stats['mean_price']:.2f}"},
                {"Métrica": "Precio final", "Valor": f"{series.data['adj close'].iloc[-1]:.2f}"},
                {"Métrica": "Retorno total", "Valor": _format_percentage(float(cumulative.iloc[-1]))},
                {"Métrica": "Volatilidad anualizada", "Valor": _format_percentage(volatility)},
            ]
        )

        trend = "Alcista" if cumulative.iloc[-1] > 0 else "Bajista"

        report_lines = [
            f"# Reporte del activo {series.name} ({series.ticker})",
            "",
            "## Resumen Ejecutivo",
            f"- **Periodo analizado:** {stats['start_date'].date()} → {stats['end_date'].date()}",
            f"- **Dirección de la tendencia:** {trend}",
            f"- **Puntos de datos:** {stats['data_points']}",
            "",
            "## Estadísticas Descriptivas",
            _markdown_table(stats_df),
        ]

        if benchmark is not None:
            benchmark_returns = benchmark.get_returns().reindex(returns.index, method="ffill").dropna()
            aligned = returns.loc[benchmark_returns.index]
            tracking_error = float(np.sqrt(252) * (aligned - benchmark_returns).std())
            report_lines.extend(
                [
                    "",
                    "## Comparativa con Benchmark",
                    f"- **Correlación:** {aligned.corr(benchmark_returns):.2f}",
                    f"- **Tracking error anualizado:** {tracking_error:.2%}",
                ]
            )

        if series.monte_carlo_result is not None:
            scenarios = series.monte_carlo_summary()
            if scenarios:
                report_lines.extend(
                    [
                        "",
                        "## Escenarios Monte Carlo",
                        "| Escenario | Valor |",
                        "|-----------|-------|",
                    ]
                )
                for label, value in scenarios.items():
                    report_lines.append(f"| {label} | {value:,.2f} |")

        return "\n".join(report_lines)

    def export(
        self,
        report: str,
        *,
        path: Path,
        fmt: str = "md",
        css: Optional[str] = None,
    ) -> Path:
        """Guarda el reporte en el formato deseado (md/html/pdf)."""

        fmt = fmt.lower()
        path = path.resolve()

        if fmt == "md":
            path.write_text(report, encoding="utf-8")
            return path

        if fmt == "html":
            if markdown is None:
                raise RuntimeError("El paquete 'markdown' es necesario para exportar a HTML.")
            html = markdown.markdown(report, extensions=["tables", "fenced_code"])
            if css:
                html = f"<style>{css}</style>\n{html}"
            path.write_text(html, encoding="utf-8")
            return path

        if fmt == "pdf":
            try:
                import pdfkit  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError(
                    "Para exportar a PDF se requiere instalar 'pdfkit' y wkhtmltopdf."
                ) from exc

            html_path = path.with_suffix(".html")
            self.export(report, path=html_path, fmt="html", css=css)
            pdfkit.from_file(str(html_path), str(path))
            return path

        raise ValueError(f"Formato de exportación no soportado: {fmt}")


