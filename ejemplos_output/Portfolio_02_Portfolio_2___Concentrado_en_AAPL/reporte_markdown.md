# Reporte de Cartera: Portfolio 2 - Concentrado en AAPL

## Composición
| Ticker   | Peso   | Tipo   |
|----------|--------|--------|
| AAPL     | 50.00% | equity |
| MSFT     | 12.50% | equity |
| GOOGL    | 12.50% | equity |
| AMZN     | 12.50% | equity |
| TSLA     | 12.50% | equity |

## Estadísticas Clave
| Métrica                | Valor   |
|------------------------|---------|
| Retorno total          | 28.71%  |
| Retorno anualizado     | 29.24%  |
| Volatilidad anualizada | 29.42%  |
| Sharpe Ratio           | 1.02    |
| Max Drawdown           | -31.95% |

## Matriz de Correlación
| Ticker   |     AAPL |     MSFT |    GOOGL |     AMZN |     TSLA |
|----------|----------|----------|----------|----------|----------|
| AAPL     | 1        | 0.51451  | 0.494447 | 0.566176 | 0.510677 |
| MSFT     | 0.51451  | 1        | 0.474829 | 0.625532 | 0.475563 |
| GOOGL    | 0.494447 | 0.474829 | 1        | 0.54711  | 0.513981 |
| AMZN     | 0.566176 | 0.625532 | 0.54711  | 1        | 0.509656 |
| TSLA     | 0.510677 | 0.475563 | 0.513981 | 0.509656 | 1        |

## Advertencias
- **AAPL**: Alta concentración superior al 35%.

## Recomendaciones
- Considera reducir la volatilidad rebalanceando hacia activos defensivos.
- Revisa estrategias de cobertura para mitigar drawdowns profundos.

## Escenarios Monte Carlo
| Escenario | Valor |
|-----------|-------|
| worst_case | 7,936.37 |
| base_case | 13,361.13 |
| best_case | 20,946.10 |
| var_5 | 7,936.37 |
| cvar_5 | 6,877.29 |