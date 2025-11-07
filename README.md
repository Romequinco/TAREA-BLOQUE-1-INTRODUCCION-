# Tarea Bloque 1

Toolkit completo para extracción, limpieza, análisis y reporting de datos bursátiles. Este documento explica paso a paso cómo funciona cada componente del sistema.

## Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Cómo Funciona el Sistema](#cómo-funciona-el-sistema)
3. [Componentes Principales](#componentes-principales)
4. [Flujo de Trabajo Completo](#flujo-de-trabajo-completo)
5. [Ejemplos de Uso](#ejemplos-de-uso)
6. [Ejemplos de Uso Real](#ejemplos-de-uso-real)
7. [Testing](#testing)

---

## Visión General

Este sistema procesa datos financieros en 5 etapas principales:

1. **Extracción** → Obtiene datos históricos de APIs externas
2. **Preprocessing** → Valida, limpia y transforma los datos
3. **Data Classes** → Crea objetos estructurados con estadísticas
4. **Análisis** → Ejecuta simulaciones Monte Carlo
5. **Reporting** → Genera reportes y visualizaciones

---

## Cómo Funciona el Sistema

### Paso 1: Extracción de Datos

**¿Qué hace?**
- Se conecta a Yahoo Finance o Alpha Vantage
- Descarga datos históricos de precios (OHLC, volumen)
- Normaliza los datos a un formato estándar

**¿Cómo funciona?**
```python
# 1. Crear extractor
extractor = YFinanceExtractor()

# 2. Descargar datos
price_series = extractor.fetch_historical_prices(
    ticker="AAPL",
    start_date=datetime(2023, 1, 1)
)

# Resultado: PriceSeries con datos estandarizados
```

**Proceso interno:**
1. El extractor hace una petición HTTP a la API
2. Recibe datos en formato JSON/CSV
3. Convierte a DataFrame de pandas
4. Estandariza columnas (date, close, adj close, etc.)
5. Crea objeto `PriceSeries` con metadatos

---

### Paso 2: Preprocessing (Validación y Limpieza)

**¿Qué hace?**
- Valida que los datos sean correctos
- Limpia errores (duplicados, valores faltantes)
- Transforma datos (retornos, indicadores técnicos)

**¿Cómo funciona?**

#### 2.1 Validación
```python
# Validar completitud temporal
report = validate_time_series_completeness(df)
# Detecta: fechas faltantes, duplicados, gaps grandes

# Validar rangos de precios
report = validate_price_ranges(df)
# Detecta: precios negativos, inconsistencias OHLC, outliers

# Validar volumen
report = validate_volume_information(df)
# Detecta: volúmenes nulos, valores extremos
```

#### 2.2 Limpieza
```python
# Usar DataCleaner para limpiar
cleaner = DataCleaner(df)
cleaned_df = (cleaner
    .drop_duplicate_dates()      # Elimina fechas duplicadas
    .ensure_numeric_prices()     # Convierte a numérico
    .handle_missing_values()     # Rellena valores faltantes
    .result()
)
```

#### 2.3 Transformaciones
```python
# Calcular retornos
returns = compute_returns(df)              # Retornos simples
log_returns = compute_log_returns(df)      # Retornos logarítmicos

# Indicadores técnicos
sma = rolling_mean(df, window=20)         # Media móvil simple
ema = exponential_moving_average(df, span=12)  # Media móvil exponencial
rsi = rsi(df, periods=14)                 # RSI
macd_result = macd(df)                    # MACD
bb = bollinger_bands(df)                   # Bandas de Bollinger
```

**Proceso interno:**
1. Validadores revisan cada aspecto de los datos
2. Generan un `ValidationReport` con issues encontrados
3. DataCleaner aplica limpieza paso a paso (método builder)
4. Transformaciones calculan métricas financieras estándar

---

### Paso 3: Data Classes (PriceSeries y Portfolio)

**¿Qué hace?**
- Encapsula datos con métodos útiles
- Calcula estadísticas automáticamente
- Proporciona interfaz unificada para análisis

**¿Cómo funciona?**

#### 3.1 PriceSeries
```python
# Crear PriceSeries
series = PriceSeries(
    ticker="AAPL",
    data=df,  # DataFrame con columnas: date, adj close, etc.
    name="Apple Inc."
)

# Estadísticas automáticas
print(series.mean_price)      # Precio promedio
print(series.volatility())     # Volatilidad anualizada
print(series.get_returns())    # Retornos diarios
print(series.summary_stats())  # Resumen completo
```

**Proceso interno:**
1. Al crear PriceSeries, se calculan estadísticas básicas
2. Métodos como `get_returns()` calculan métricas bajo demanda
3. Validación y limpieza integradas con `.clean()` y `.validate()`

#### 3.2 Portfolio
```python
# Crear portfolio
portfolio = Portfolio(
    holdings={
        "AAPL": series_aapl,
        "MSFT": series_msft
    },
    weights={"AAPL": 0.6, "MSFT": 0.4}
)

# Métricas del portfolio
returns = portfolio.get_portfolio_returns()      # Retornos ponderados
volatility = portfolio.portfolio_volatility()    # Volatilidad del portfolio
correlation = portfolio.correlation_matrix()     # Matriz de correlación
```

**Proceso interno:**
1. Combina múltiples PriceSeries
2. Calcula retornos ponderados según pesos
3. Considera correlaciones entre activos
4. Proporciona métricas agregadas

---

### Paso 4: Análisis Monte Carlo

**¿Qué hace?**
- Simula escenarios futuros de precios
- Calcula métricas de riesgo (VaR, CVaR)
- Genera distribuciones de resultados

**¿Cómo funciona?**
```python
# Configurar simulador
simulator = MonteCarloSimulator(
    method="gbm",              # Geometric Brownian Motion
    horizon=252,               # 1 año (días de trading)
    num_simulations=1000,      # Número de simulaciones
    seed=42                    # Semilla para reproducibilidad
)

# Ejecutar simulación
result = simulator.simulate_price_series(series)

# Analizar resultados
percentiles = result.percentile([5, 50, 95])  # Percentiles
var = result.value_at_risk(alpha=0.05)        # VaR 5%
cvar = result.conditional_value_at_risk(alpha=0.05)  # CVaR 5%
```

**Métodos disponibles:**
- **GBM (Geometric Brownian Motion)**: Modelo estándar de Black-Scholes
- **Historical Bootstrap**: Re-muestreo de retornos históricos
- **Stochastic Volatility**: Modelo con volatilidad variable (GARCH)

**Proceso interno:**
1. Calcula parámetros (media, volatilidad) de datos históricos
2. Genera trayectorias aleatorias según el método elegido
3. Almacena todas las simulaciones en `MonteCarloResult`
4. Calcula métricas estadísticas sobre las simulaciones

---

### Paso 5: Reporting

**¿Qué hace?**
- Genera reportes en Markdown con métricas clave
- Crea visualizaciones profesionales
- Exporta a diferentes formatos

**¿Cómo funciona?**

#### 5.1 Reportes Markdown
```python
# Generar reporte
generator = MarkdownReportGenerator()
report = generator.price_series_report(series)

# Contenido del reporte:
# - Resumen ejecutivo
# - Métricas clave (retorno, volatilidad, Sharpe)
# - Análisis de riesgo
# - Recomendaciones
```

#### 5.2 Visualizaciones
```python
# Crear visualizaciones
viz = VisualizationReport(theme="light")
figures = viz.price_series_plots(series)

# Gráficos generados:
# - Precio histórico con bandas
# - Distribución de retornos
# - Volatilidad rolling
# - Drawdowns
```

**Proceso interno:**
1. MarkdownReportGenerator recopila métricas de PriceSeries/Portfolio
2. Formatea datos en tablas y secciones Markdown
3. VisualizationReport usa matplotlib/seaborn para gráficos
4. Se pueden exportar a HTML, PDF, o guardar imágenes

---

## Componentes Principales

### src/extractors/
- **BaseExtractor**: Clase abstracta base
- **YFinanceExtractor**: Extracción desde Yahoo Finance
- **AlphaVantageExtractor**: Extracción desde Alpha Vantage
- **Características**: Descarga paralela, caché, rate limiting

### src/preprocessing/
- **validators.py**: Validación de calidad de datos
- **data_cleaner.py**: Limpieza avanzada (DataCleaner)
- **transformations.py**: Transformaciones y indicadores técnicos

### src/data_classes/
- **price_series.py**: Objeto PriceSeries con métodos integrados
- **portfolio.py**: Objeto Portfolio para múltiples activos

### src/analysis/
- **monte_carlo.py**: Motor de simulación Monte Carlo
- **Métodos**: GBM, histórico, volatilidad estocástica

### src/reporting/
- **markdown_report.py**: Generación de reportes Markdown
- **visualizations.py**: Creación de gráficos profesionales

### src/utils/
- **logger.py**: Sistema de logging centralizado
- **config.py**: Gestión de configuración
- **cache.py**: Sistema de caché para APIs
- **exceptions.py**: Excepciones personalizadas

---

## Flujo de Trabajo Completo

### Ejemplo: Análisis Completo de un Activo

```python
from datetime import datetime
from src.extractors import YFinanceExtractor
from src.data_classes import PriceSeries

# PASO 1: Extracción
print("Paso 1: Descargando datos...")
extractor = YFinanceExtractor()
series = extractor.fetch_historical_prices(
    ticker="AAPL",
    start_date=datetime(2023, 1, 1)
)
print(f"✓ Datos descargados: {len(series.data)} puntos")

# PASO 2: Preprocessing
print("\nPaso 2: Validando y limpiando datos...")
validation = series.validate()
if validation.has_errors:
    print("⚠ Errores encontrados, limpiando...")
    series.clean()
print("✓ Datos validados y limpios")

# PASO 3: Análisis
print("\nPaso 3: Ejecutando simulación Monte Carlo...")
mc_result = series.monte_carlo(
    method="gbm",
    num_simulations=1000,
    horizon=252,
    seed=42
)
print(f"✓ Simulación completada: {mc_result.paths.shape}")

# PASO 4: Reporting
print("\nPaso 4: Generando reportes...")
report_md = series.report()
figures = series.plots_report()
print("✓ Reportes generados")

# PASO 5: Resultados
print("\nPaso 5: Mostrando resultados...")
summary = mc_result.scenario_summary()
print(f"Escenario base (50%): ${summary['base_case']:.2f}")
print(f"Escenario peor (5%): ${summary['worst_case']:.2f}")
print(f"Escenario mejor (95%): ${summary['best_case']:.2f}")
```

---

## Ejemplos de Uso

### Ejemplo 1: Análisis Simple de un Activo

```python
from src.extractors import YFinanceExtractor
from datetime import datetime

extractor = YFinanceExtractor()
series = extractor.fetch_historical_prices("AAPL", start_date=datetime(2023, 1, 1))

# Limpiar y validar
series.clean().validate()

# Estadísticas básicas
stats = series.summary_stats()
print(f"Retorno total: {stats['total_return']*100:.2f}%")
print(f"Volatilidad: {stats['volatility']*100:.2f}%")
```

### Ejemplo 2: Análisis de Portfolio

```python
from src.data_classes import Portfolio
from src.extractors import YFinanceExtractor

extractor = YFinanceExtractor()

# Descargar múltiples activos
aapl = extractor.fetch_historical_prices("AAPL", start_date=datetime(2023, 1, 1))
msft = extractor.fetch_historical_prices("MSFT", start_date=datetime(2023, 1, 1))

# Crear portfolio
portfolio = Portfolio(
    holdings={"AAPL": aapl, "MSFT": msft},
    weights={"AAPL": 0.6, "MSFT": 0.4}
)

# Métricas del portfolio
print(f"Volatilidad del portfolio: {portfolio.portfolio_volatility()*100:.2f}%")
print(f"Correlación: {portfolio.correlation_matrix()}")
```

### Ejemplo 3: Simulación Monte Carlo

```python
from src.analysis import MonteCarloSimulator

simulator = MonteCarloSimulator(
    method="gbm",
    horizon=252,
    num_simulations=1000,
    seed=42
)

result = simulator.simulate_price_series(series)

# Análisis de riesgo
var_5 = result.value_at_risk(alpha=0.05)
cvar_5 = result.conditional_value_at_risk(alpha=0.05)

print(f"VaR 5%: ${var_5:.2f}")
print(f"CVaR 5%: ${cvar_5:.2f}")
```

---

## Testing

Todos los tests muestran el proceso paso a paso, demostrando el flujo completo del sistema.

```bash
# Test de extracción (descarga datos)
python tests/test_extractors.py

# Test de data models
python tests/test_data_models.py

# Test de preprocessing
python tests/test_preprocessing.py

# Test de análisis (usa datos descargados)
python tests/test_analysis.py

# Test de reporting (usa datos descargados)
python tests/test_reporting.py

# Test de flujo completo end-to-end (extracción → preprocessing → análisis → reporting)
python tests/test_flujo_completo.py

# Ejecutar todos los tests
python tests/run_all_tests.py
```

**Flujo de datos en los tests:**
1. **Extracción**: Los tests descargan datos reales desde Yahoo Finance
2. **Preprocessing**: Los datos descargados se validan y limpian
3. **Análisis**: Los mismos datos se usan para simulaciones Monte Carlo
4. **Reporting**: Los mismos datos se usan para generar reportes y visualizaciones

Cada test muestra:
- Qué paso se está ejecutando
- Qué datos se están procesando (descargados o generados)
- Resultados de cada operación
- Separadores visuales para claridad

---

## Ejemplos de Uso Real

El proyecto incluye scripts de ejemplo que demuestran el uso completo del sistema con datos reales:

### Ejemplo Real (Recomendado)

**`ejemplo_real.py`** 

```bash
python ejemplo_real.py
```

**Características:**
- Descarga 5 activos reales (AAPL, MSFT, GOOGL, AMZN, TSLA)
- Crea 10 portfolios diferentes con diferentes estrategias de pesos
- Usa métodos integrados: `portfolio.report()`, `portfolio.plots_report()`, `portfolio.monte_carlo()`
- Genera outputs completos en `ejemplos_output/`:
  - Resumen de activos descargados
  - 10 carpetas (una por portfolio) con reportes y visualizaciones
  - 7 gráficos comparativos mostrando todos los portfolios juntos
  - Resumen comparativo con rankings

**Outputs generados:**
- `00_EXTRACCION_resumen_activos.txt` - Resumen de los 5 activos
- `RESUMEN_COMPARATIVO_todos_los_portfolios.txt` - Comparación completa
- `Portfolio_01_*/` hasta `Portfolio_10_*/` - Carpetas individuales con:
  - `resumen_portfolio.txt` - Métricas y composición
  - `reporte_markdown.md` - Reporte completo generado automáticamente
  - `visualizacion_*.png` - Gráficos generados automáticamente
- `COMPARATIVO_*.png` - 7 gráficos comparativos:
  - Evolución de valor de todas las carteras
  - Retornos acumulados
  - Retorno vs Volatilidad
  - Sharpe Ratio
  - Distribución de pesos (heatmap)
  - Escenarios Monte Carlo
  - VaR y CVaR

## Conceptos Clave

### PriceSeries
Objeto que encapsula una serie temporal de precios con:
- Datos históricos (DataFrame)
- Métodos de análisis (retornos, volatilidad)
- Validación y limpieza integradas
- Simulación Monte Carlo
- Generación de reportes

### Portfolio
Objeto que combina múltiples PriceSeries:
- Gestión de pesos por activo
- Cálculo de métricas agregadas
- Consideración de correlaciones
- Simulación conjunta

### MonteCarloResult
Resultado de una simulación con:
- Trayectorias simuladas (array numpy)
- Fechas futuras
- Métodos de análisis (percentiles, VaR, CVaR)

### ValidationReport
Reporte de validación con:
- Lista de issues encontrados
- Severidad (error, warning, info)
- Contexto de cada issue

---

## 🔍 Detalles Técnicos

### Semilla para Reproducibilidad
Todos los tests y simulaciones usan `seed=42` para garantizar resultados reproducibles.

### Detección Automática de Paths
Los tests detectan automáticamente el directorio raíz del proyecto, funcionando desde cualquier ubicación.

### Manejo de Errores
- Validación previa a operaciones críticas
- Mensajes de error claros y descriptivos
- Fallbacks cuando APIs no están disponibles

### Optimizaciones
- Caché de peticiones API
- Descarga paralela de múltiples tickers
- Cálculos vectorizados con numpy/pandas

---

Para más detalles sobre instalación, ver `GUIA_INSTALACION.md`.
Para ver el diagrama del sistema, ver `diagram.md`.
