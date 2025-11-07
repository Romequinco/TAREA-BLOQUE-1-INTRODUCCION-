# Reporte de Cartera: Portfolio 10 - Agresivo

## Composición
| Ticker   | Peso   | Tipo   |
|----------|--------|--------|
| AAPL     | 15.00% | equity |
| MSFT     | 15.00% | equity |
| GOOGL    | 15.00% | equity |
| AMZN     | 15.00% | equity |
| TSLA     | 40.00% | equity |

## Estadísticas Clave
| Métrica                | Valor   |
|------------------------|---------|
| Retorno total          | 38.72%  |
| Retorno anualizado     | 39.45%  |
| Volatilidad anualizada | 38.07%  |
| Sharpe Ratio           | 1.06    |
| Max Drawdown           | -38.01% |

## Matriz de Correlación
| Ticker   |     AAPL |     MSFT |    GOOGL |     AMZN |     TSLA |
|----------|----------|----------|----------|----------|----------|
| AAPL     | 1        | 0.51451  | 0.494447 | 0.566176 | 0.510677 |
| MSFT     | 0.51451  | 1        | 0.474829 | 0.625532 | 0.475563 |
| GOOGL    | 0.494447 | 0.474829 | 1        | 0.54711  | 0.513981 |
| AMZN     | 0.566176 | 0.625532 | 0.54711  | 1        | 0.509656 |
| TSLA     | 0.510677 | 0.475563 | 0.513981 | 0.509656 | 1        |

## Advertencias
- **TSLA**: Alta concentración superior al 35%.

## Recomendaciones
- Considera reducir la volatilidad rebalanceando hacia activos defensivos.
- Revisa estrategias de cobertura para mitigar drawdowns profundos.

## Escenarios Monte Carlo
| Escenario | Valor |
|-----------|-------|
| worst_case | 7,484.22 |
| base_case | 14,799.80 |
| best_case | 26,129.07 |
| var_5 | 7,484.22 |
| cvar_5 | 6,520.91 |