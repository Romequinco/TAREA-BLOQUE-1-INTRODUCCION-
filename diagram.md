# Diagrama del Sistema

Diagrama visual del flujo completo del Sistema de Análisis Financiero.

## 📊 Flujo Principal del Sistema

```mermaid
graph TD
    Start([Inicio]) --> Extract[1. Extracción<br/>YFinance/AlphaVantage]
    Extract -->|Datos Históricos| Validate[2. Validación<br/>Completitud, Rangos, Volumen]
    Validate -->|Datos Válidos| Clean[3. Limpieza<br/>Duplicados, Faltantes, Outliers]
    Clean -->|Datos Limpios| Transform[4. Transformaciones<br/>Retornos, Indicadores Técnicos]
    Transform -->|Datos Transformados| PriceSeries[5. PriceSeries<br/>Objeto con Estadísticas]
    
    PriceSeries -->|Análisis| MonteCarlo[6. Monte Carlo<br/>Simulaciones GBM/Histórico]
    MonteCarlo -->|Resultados| Metrics[7. Métricas de Riesgo<br/>VaR, CVaR, Percentiles]
    
    PriceSeries -->|Reportes| Markdown[8. Reporte Markdown<br/>Métricas y Análisis]
    PriceSeries -->|Visualizaciones| Charts[9. Gráficos<br/>Precios, Retornos, Distribuciones]
    
    Metrics --> End([Resultados Finales])
    Markdown --> End
    Charts --> End
    
    style Extract fill:#e1f5ff
    style Validate fill:#fff4e1
    style Clean fill:#fff4e1
    style Transform fill:#fff4e1
    style PriceSeries fill:#e8f5e9
    style MonteCarlo fill:#f3e5f5
    style Metrics fill:#f3e5f5
    style Markdown fill:#fce4ec
    style Charts fill:#fce4ec
```

## 🔄 Flujo Detallado por Componente

### Extracción → Preprocessing

```mermaid
sequenceDiagram
    participant User
    participant Extractor
    participant API
    participant Validator
    participant Cleaner
    
    User->>Extractor: fetch_historical_prices(ticker)
    Extractor->>API: HTTP Request
    API-->>Extractor: Datos JSON/CSV
    Extractor->>Extractor: Normalizar a DataFrame
    Extractor-->>User: PriceSeries
    
    User->>PriceSeries: validate()
    PriceSeries->>Validator: validate_time_series_completeness()
    PriceSeries->>Validator: validate_price_ranges()
    Validator-->>PriceSeries: ValidationReport
    
    User->>PriceSeries: clean()
    PriceSeries->>Cleaner: DataCleaner()
    Cleaner->>Cleaner: drop_duplicate_dates()
    Cleaner->>Cleaner: ensure_numeric_prices()
    Cleaner->>Cleaner: handle_missing_values()
    Cleaner-->>PriceSeries: DataFrame limpio
```

### Análisis Monte Carlo

```mermaid
graph LR
    A[PriceSeries<br/>Datos Históricos] -->|Calcular| B[Parámetros<br/>μ, σ]
    B -->|Configurar| C[MonteCarloSimulator<br/>method, horizon, simulations]
    C -->|Generar| D[Trayectorias<br/>1000 simulaciones]
    D -->|Analizar| E[MonteCarloResult<br/>Percentiles, VaR, CVaR]
    E -->|Visualizar| F[Fan Chart<br/>Gráfico de Escenarios]
    
    style A fill:#e8f5e9
    style B fill:#fff4e1
    style C fill:#f3e5f5
    style D fill:#f3e5f5
    style E fill:#f3e5f5
    style F fill:#fce4ec
```

### Portfolio Multi-Activo

```mermaid
graph TD
    A[Extractor] -->|AAPL| B[PriceSeries AAPL]
    A -->|MSFT| C[PriceSeries MSFT]
    A -->|GOOGL| D[PriceSeries GOOGL]
    
    B --> E[Portfolio]
    C --> E
    D --> E
    
    E -->|Pesos| F[Retornos Ponderados]
    E -->|Correlaciones| G[Matriz de Correlación]
    E -->|Simulación| H[Monte Carlo Portfolio]
    
    F --> I[Reporte Portfolio]
    G --> I
    H --> I
    
    style A fill:#e1f5ff
    style B fill:#e8f5e9
    style C fill:#e8f5e9
    style D fill:#e8f5e9
    style E fill:#e8f5e9
    style F fill:#fff4e1
    style G fill:#fff4e1
    style H fill:#f3e5f5
    style I fill:#fce4ec
```

## 🏗️ Arquitectura de Componentes

```mermaid
graph TB
    subgraph "Capa de Extracción"
        E1[BaseExtractor]
        E2[YFinanceExtractor]
        E3[AlphaVantageExtractor]
        E1 --> E2
        E1 --> E3
    end
    
    subgraph "Capa de Preprocessing"
        P1[Validators]
        P2[DataCleaner]
        P3[Transformations]
    end
    
    subgraph "Capa de Datos"
        D1[PriceSeries]
        D2[Portfolio]
    end
    
    subgraph "Capa de Análisis"
        A1[MonteCarloSimulator]
        A2[MonteCarloResult]
    end
    
    subgraph "Capa de Reporting"
        R1[MarkdownReportGenerator]
        R2[VisualizationReport]
    end
    
    subgraph "Utilidades"
        U1[Logger]
        U2[Config]
        U3[Cache]
    end
    
    E2 --> D1
    E3 --> D1
    P1 --> D1
    P2 --> D1
    P3 --> D1
    D1 --> D2
    D1 --> A1
    D2 --> A1
    A1 --> A2
    D1 --> R1
    D1 --> R2
    D2 --> R1
    D2 --> R2
    A2 --> R2
    
    E1 -.-> U1
    P1 -.-> U1
    A1 -.-> U1
    R1 -.-> U1
    
    E1 -.-> U3
```

## 📈 Flujo de Datos Completo

```mermaid
flowchart TD
    Start([Usuario inicia análisis]) --> Input{¿Qué tipo de análisis?}
    
    Input -->|Activo Individual| Single[Análisis de Activo]
    Input -->|Múltiples Activos| Multi[Análisis de Portfolio]
    
    Single --> S1[1. Extraer datos<br/>YFinance/AlphaVantage]
    S1 --> S2[2. Crear PriceSeries]
    S2 --> S3[3. Validar y limpiar]
    S3 --> S4[4. Calcular estadísticas]
    S4 --> S5[5. Simular Monte Carlo]
    S5 --> S6[6. Generar reportes]
    S6 --> End([Resultados])
    
    Multi --> M1[1. Extraer múltiples activos]
    M1 --> M2[2. Crear Portfolio]
    M2 --> M3[3. Calcular correlaciones]
    M3 --> M4[4. Simular portfolio]
    M4 --> M5[5. Generar reportes]
    M5 --> End
    
    style Start fill:#e1f5ff
    style Single fill:#e8f5e9
    style Multi fill:#e8f5e9
    style End fill:#fce4ec
```

## 🔑 Conceptos Clave Visualizados

### PriceSeries - Estructura Interna

```
PriceSeries
├── ticker: str              # Símbolo del activo
├── data: DataFrame          # Datos históricos
│   ├── date                # Fechas
│   ├── close               # Precio de cierre
│   ├── adj close           # Precio ajustado
│   └── volume              # Volumen
├── name: str               # Nombre del activo
├── asset_type: str         # Tipo (equity, index, etc.)
└── Métodos:
    ├── clean()             # Limpieza
    ├── validate()          # Validación
    ├── get_returns()       # Retornos
    ├── volatility()        # Volatilidad
    ├── monte_carlo()       # Simulación
    ├── report()            # Reporte Markdown
    └── plots_report()      # Gráficos
```

### Portfolio - Estructura Interna

```
Portfolio
├── holdings: Dict[str, PriceSeries]  # Activos
├── weights: Dict[str, float]         # Pesos
├── name: str                         # Nombre
└── Métodos:
    ├── get_portfolio_returns()       # Retornos ponderados
    ├── portfolio_volatility()        # Volatilidad del portfolio
    ├── correlation_matrix()          # Correlaciones
    ├── portfolio_value_history()     # Evolución del valor
    ├── monte_carlo()                 # Simulación
    ├── report()                      # Reporte
    └── plots_report()                # Gráficos
```

## 📝 Resumen del Flujo

1. **Extracción**: APIs externas → Datos normalizados
2. **Validación**: Verificar calidad y completitud
3. **Limpieza**: Eliminar errores y normalizar
4. **Transformación**: Calcular métricas financieras
5. **Data Classes**: Encapsular en objetos estructurados
6. **Análisis**: Simulaciones Monte Carlo
7. **Reporting**: Generar reportes y visualizaciones

Cada paso es independiente y puede ejecutarse por separado, pero juntos forman un pipeline completo de análisis financiero.

