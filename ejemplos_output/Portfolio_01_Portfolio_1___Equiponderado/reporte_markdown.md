# Reporte de Cartera: Portfolio 1 - Equiponderado

## Composición
| Ticker   | Peso   | Tipo   |
|----------|--------|--------|
| AAPL     | 20.00% | equity |
| MSFT     | 20.00% | equity |
| GOOGL    | 20.00% | equity |
| AMZN     | 20.00% | equity |
| TSLA     | 20.00% | equity |

## Estadísticas Clave
| Métrica                | Valor   |
|------------------------|---------|
| Retorno total          | 33.72%  |
| Retorno anualizado     | 34.35%  |
| Volatilidad anualizada | 30.40%  |
| Sharpe Ratio           | 1.12    |
| Max Drawdown           | -32.21% |

## Matriz de Correlación
| Ticker   |     AAPL |     MSFT |    GOOGL |     AMZN |     TSLA |
|----------|----------|----------|----------|----------|----------|
| AAPL     | 1        | 0.51451  | 0.494447 | 0.566176 | 0.510677 |
| MSFT     | 0.51451  | 1        | 0.474829 | 0.625532 | 0.475563 |
| GOOGL    | 0.494447 | 0.474829 | 1        | 0.54711  | 0.513981 |
| AMZN     | 0.566176 | 0.625532 | 0.54711  | 1        | 0.509656 |
| TSLA     | 0.510677 | 0.475563 | 0.513981 | 0.509656 | 1        |

## Advertencias
- No se detectaron advertencias destacables.

## Recomendaciones
- Considera reducir la volatilidad rebalanceando hacia activos defensivos.
- Revisa estrategias de cobertura para mitigar drawdowns profundos.

## Escenarios Monte Carlo
| Escenario | Valor |
|-----------|-------|
| worst_case | 8,161.69 |
| base_case | 13,597.49 |
| best_case | 21,611.85 |
| var_5 | 8,161.69 |
| cvar_5 | 7,249.19 |