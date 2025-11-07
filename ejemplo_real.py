"""
Script de ejemplo real que usa al máximo el código existente en src.
Crea 10 portfolios diferentes con 5 activos cada uno, con diferentes pesos.

Este script reutiliza los métodos integrados de Portfolio y PriceSeries
en lugar de duplicar lógica.

Ejecutar: python ejemplo_real.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Configurar path
current_dir = Path(__file__).resolve().parent
project_root = current_dir
for potential_root in [current_dir, current_dir.parent]:
    if (potential_root / "src").exists() and (potential_root / "tests").exists():
        project_root = potential_root
        break

sys.path.insert(0, str(project_root))
os.chdir(project_root)

# Semilla para reproducibilidad
np.random.seed(42)

try:
    from src.extractors import YFinanceExtractor
    from src.data_classes import PriceSeries, Portfolio
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)

# Crear directorio para outputs
output_dir = project_root / "ejemplos_output"

# Limpiar carpeta de ejemplos_output antes de empezar
if output_dir.exists():
    import shutil
    print("Limpiando carpeta ejemplos_output...")
    for item in output_dir.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    print("✓ Carpeta limpiada\n")

output_dir.mkdir(exist_ok=True)

print("=" * 80)
print("EJEMPLO REAL - USANDO CÓDIGO EXISTENTE DE src")
print("=" * 80)
print(f"Los archivos se guardarán en: {output_dir}\n")

# ============================================================================
# ETAPA 1: EXTRACCIÓN DE MÚLTIPLES ACTIVOS
# ============================================================================
print("ETAPA 1: EXTRACCIÓN DE 5 ACTIVOS")
print("-" * 80)

extractor = YFinanceExtractor()
tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
holdings_data = {}

print("Descargando datos de los activos...")
for ticker in tickers:
    try:
        print(f"  Descargando {ticker}...", end=" ")
        price_series = extractor.fetch_historical_prices(
            ticker=ticker,
            start_date=datetime.now() - timedelta(days=365)
        )
        # Usar método integrado de limpieza
        price_series.clean()
        holdings_data[ticker] = price_series
        print(f"✓ {len(price_series.data)} puntos")
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

print(f"\n✓ Todos los activos descargados y limpiados\n")

# Guardar resumen usando métodos integrados
output_file = output_dir / "00_EXTRACCION_resumen_activos.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("ETAPA 1: EXTRACCIÓN DE ACTIVOS\n")
    f.write("=" * 80 + "\n\n")
    f.write(f"Total de activos descargados: {len(holdings_data)}\n")
    f.write(f"Activos: {', '.join(tickers)}\n\n")
    
    for ticker, ps in holdings_data.items():
        # Usar summary_stats() integrado
        stats = ps.summary_stats()
        f.write(f"{ticker} - {stats['name']}:\n")
        f.write(f"  - Puntos de datos: {stats['data_points']}\n")
        f.write(f"  - Rango: {stats['start_date'].date()} a {stats['end_date'].date()}\n")
        f.write(f"  - Precio promedio: ${stats['mean_price']:.2f}\n")
        f.write(f"  - Volatilidad anualizada: {stats['volatility']*100:.2f}%\n")
        f.write(f"  - Retorno total: {stats['total_return']*100:.2f}%\n\n")

print(f"✓ Resumen de extracción guardado en: {output_file}\n")

# ============================================================================
# ETAPA 2: CREACIÓN DE 10 PORTFOLIOS CON DIFERENTES PESOS
# ============================================================================
print("ETAPA 2: CREACIÓN DE 10 PORTFOLIOS CON DIFERENTES PESOS")
print("-" * 80)

# Generar 10 combinaciones diferentes de pesos
portfolios_config = [
    {'name': 'Portfolio 1 - Equiponderado', 'weights': {ticker: 0.20 for ticker in tickers}},
    {'name': 'Portfolio 2 - Concentrado en AAPL', 'weights': {ticker: 0.125 if ticker != 'AAPL' else 0.50 for ticker in tickers}},
    {'name': 'Portfolio 3 - Concentrado en MSFT', 'weights': {ticker: 0.125 if ticker != 'MSFT' else 0.50 for ticker in tickers}},
    {'name': 'Portfolio 4 - Concentrado en GOOGL', 'weights': {ticker: 0.125 if ticker != 'GOOGL' else 0.50 for ticker in tickers}},
    {'name': 'Portfolio 5 - Concentrado en AMZN', 'weights': {ticker: 0.125 if ticker != 'AMZN' else 0.50 for ticker in tickers}},
    {'name': 'Portfolio 6 - Concentrado en TSLA', 'weights': {ticker: 0.125 if ticker != 'TSLA' else 0.50 for ticker in tickers}},
    {'name': 'Portfolio 7 - Tech Pesado', 'weights': {'AAPL': 0.30, 'MSFT': 0.30, 'GOOGL': 0.20, 'AMZN': 0.10, 'TSLA': 0.10}},
    {'name': 'Portfolio 8 - Crecimiento', 'weights': {'AAPL': 0.15, 'MSFT': 0.15, 'GOOGL': 0.10, 'AMZN': 0.30, 'TSLA': 0.30}},
    {'name': 'Portfolio 9 - Conservador', 'weights': {'AAPL': 0.35, 'MSFT': 0.35, 'GOOGL': 0.15, 'AMZN': 0.10, 'TSLA': 0.05}},
    {'name': 'Portfolio 10 - Agresivo', 'weights': {'AAPL': 0.15, 'MSFT': 0.15, 'GOOGL': 0.15, 'AMZN': 0.15, 'TSLA': 0.40}},
]

print(f"✓ Configurados {len(portfolios_config)} portfolios diferentes\n")

# ============================================================================
# ETAPA 3: PROCESAR CADA PORTFOLIO USANDO MÉTODOS INTEGRADOS
# ============================================================================
print("ETAPA 3: PROCESANDO CADA PORTFOLIO (usando métodos de src)")
print("=" * 80)

portfolios_list = []
resumen_portfolios = []

for idx, config in enumerate(portfolios_config, 1):
    print(f"\nProcesando {config['name']}...")
    print("-" * 80)
    
    # Crear portfolio (usa métodos integrados automáticamente)
    portfolio = Portfolio(
        holdings=holdings_data.copy(),
        weights=config['weights'],
        name=config['name']
    )
    portfolios_list.append(portfolio)
    
    # Usar método integrado de Monte Carlo
    print("  Ejecutando simulación Monte Carlo (método integrado)...")
    mc_result = portfolio.monte_carlo(
        method="gbm",
        horizon=252,
        num_simulations=100,
        seed=42,
        initial_value=10000
    )
    
    # Usar método integrado para obtener resumen
    mc_summary = portfolio.monte_carlo_summary()
    
    # Usar método integrado summary()
    portfolio_summary = portfolio.summary()
    
    # Guardar output individual usando métodos integrados
    portfolio_dir = output_dir / f"Portfolio_{idx:02d}_{config['name'].replace(' ', '_').replace('-', '_')}"
    portfolio_dir.mkdir(exist_ok=True)
    
    # Resumen usando métodos integrados
    output_file = portfolio_dir / "resumen_portfolio.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write(f"{config['name'].upper()}\n")
        f.write("=" * 80 + "\n\n")
        
        f.write("COMPOSICIÓN DEL PORTFOLIO:\n")
        f.write("-" * 80 + "\n")
        for ticker, weight in sorted(config['weights'].items(), key=lambda x: x[1], reverse=True):
            f.write(f"  {ticker}: {weight*100:.2f}%\n")
        f.write(f"  Total: {sum(config['weights'].values())*100:.2f}%\n\n")
        
        f.write("MÉTRICAS DEL PORTFOLIO (usando summary()):\n")
        f.write("-" * 80 + "\n")
        f.write(f"Número de holdings: {portfolio_summary['num_holdings']}\n")
        f.write(f"Volatilidad del portfolio: {portfolio_summary['portfolio_volatility']*100:.2f}%\n\n")
        
        # Usar métodos integrados para métricas
        returns = portfolio.get_portfolio_returns()
        f.write(f"Retorno medio diario: {returns.mean()*100:.4f}%\n")
        f.write(f"Retorno anualizado: {returns.mean()*252*100:.2f}%\n")
        f.write(f"Volatilidad anualizada: {portfolio.portfolio_volatility()*100:.2f}%\n")
        sharpe = (returns.mean()*252) / portfolio.portfolio_volatility() if portfolio.portfolio_volatility() > 0 else 0
        f.write(f"Sharpe Ratio: {sharpe:.2f}\n\n")
        
        f.write("MATRIZ DE CORRELACIÓN (usando correlation_matrix()):\n")
        f.write("-" * 80 + "\n")
        f.write(portfolio.correlation_matrix().to_string() + "\n\n")
        
        f.write("RESULTADOS MONTE CARLO (usando monte_carlo_summary()):\n")
        f.write("-" * 80 + "\n")
        if mc_summary:
            for key, value in mc_summary.items():
                f.write(f"{key}: ${value:.2f}\n")
    
    # Usar método integrado report() para generar reporte Markdown
    print("  Generando reporte Markdown (método integrado)...")
    report_md = portfolio.report()
    output_file = portfolio_dir / "reporte_markdown.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report_md)
    
    # Usar método integrado plots_report() para generar visualizaciones
    print("  Generando visualizaciones (método integrado)...")
    try:
        figures = portfolio.plots_report(theme="light")
        for name, fig in figures.items():
            output_file = portfolio_dir / f"visualizacion_{name}.png"
            fig.savefig(output_file, dpi=150, bbox_inches='tight')
            plt.close(fig)
    except Exception as e:
        print(f"    ⚠ Error en visualizaciones: {e}")
    
    # Guardar datos para resumen comparativo
    resumen_portfolios.append({
        'portfolio': idx,
        'name': config['name'],
        'weights': config['weights'],
        'retorno_anual': returns.mean() * 252,
        'volatilidad': portfolio.portfolio_volatility(),
        'sharpe': sharpe,
        'base_case': mc_summary['base_case'] if mc_summary else 0,
        'worst_case': mc_summary['worst_case'] if mc_summary else 0,
        'best_case': mc_summary['best_case'] if mc_summary else 0,
        'var_5': mc_summary['var_5'] if mc_summary else 0,
        'cvar_5': mc_summary['cvar_5'] if mc_summary else 0
    })
    
    print(f"  ✓ Portfolio {idx} procesado completamente")

# ============================================================================
# ETAPA 4: RESUMEN COMPARATIVO
# ============================================================================
print("\n" + "=" * 80)
print("ETAPA 4: GENERANDO RESUMEN COMPARATIVO")
print("=" * 80)

df_comparativo = pd.DataFrame(resumen_portfolios)

output_file = output_dir / "RESUMEN_COMPARATIVO_todos_los_portfolios.txt"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("=" * 80 + "\n")
    f.write("RESUMEN COMPARATIVO DE TODOS LOS PORTFOLIOS\n")
    f.write("=" * 80 + "\n\n")
    
    f.write("COMPARACIÓN DE MÉTRICAS:\n")
    f.write("-" * 80 + "\n")
    f.write(f"{'Portfolio':<30} {'Retorno':<12} {'Volatilidad':<12} {'Sharpe':<10} {'VaR 5%':<12}\n")
    f.write("-" * 80 + "\n")
    for row in resumen_portfolios:
        f.write(f"{row['name']:<30} {row['retorno_anual']*100:>10.2f}% {row['volatilidad']*100:>10.2f}% "
                f"{row['sharpe']:>8.2f} ${row['var_5']:>10.2f}\n")
    
    f.write("\n" + "=" * 80 + "\n\n")
    f.write("COMPARACIÓN DE ESCENARIOS MONTE CARLO:\n")
    f.write("-" * 80 + "\n")
    f.write(f"{'Portfolio':<30} {'Base (50%)':<15} {'Peor (5%)':<15} {'Mejor (95%)':<15}\n")
    f.write("-" * 80 + "\n")
    for row in resumen_portfolios:
        f.write(f"{row['name']:<30} ${row['base_case']:>12.2f} ${row['worst_case']:>12.2f} "
                f"${row['best_case']:>12.2f}\n")
    
    f.write("\n" + "=" * 80 + "\n\n")
    f.write("RANKING POR SHARPE RATIO:\n")
    f.write("-" * 80 + "\n")
    sorted_by_sharpe = sorted(resumen_portfolios, key=lambda x: x['sharpe'], reverse=True)
    for i, row in enumerate(sorted_by_sharpe, 1):
        f.write(f"{i}. {row['name']:<30} Sharpe: {row['sharpe']:.2f}\n")

print(f"✓ Resumen comparativo guardado en: {output_file}")

# ============================================================================
# ETAPA 5: VISUALIZACIONES COMPARATIVAS USANDO MÉTODOS INTEGRADOS
# ============================================================================
print("\n" + "=" * 80)
print("ETAPA 5: GENERANDO VISUALIZACIONES COMPARATIVAS")
print("=" * 80)

# Gráfico 1: Evolución del valor usando portfolio_value_history()
print("Generando gráfico de evolución de valor...")
fig, ax = plt.subplots(figsize=(14, 8))
initial_value = 10000

for portfolio in portfolios_list:
    # Usar método integrado portfolio_value_history()
    value_history = portfolio.portfolio_value_history(initial_value=initial_value)
    ax.plot(value_history['date'], value_history['value'], 
            label=portfolio.name, linewidth=2, alpha=0.8)

ax.set_xlabel('Fecha', fontsize=12)
ax.set_ylabel('Valor del Portfolio ($)', fontsize=12)
ax.set_title('Evolución del Valor - Comparación de Todos los Portfolios', fontsize=14, fontweight='bold')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
output_file = output_dir / "COMPARATIVO_evolucion_valor_todos_portfolios.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

# Gráfico 2: Retornos acumulados usando get_portfolio_returns()
print("Generando gráfico de retornos acumulados...")
fig, ax = plt.subplots(figsize=(14, 8))

for portfolio in portfolios_list:
    # Usar método integrado get_portfolio_returns()
    returns = portfolio.get_portfolio_returns()
    cum_returns = (1 + returns).cumprod() - 1
    ax.plot(cum_returns.index, cum_returns.values * 100, 
            label=portfolio.name, linewidth=2, alpha=0.8)

ax.set_xlabel('Fecha', fontsize=12)
ax.set_ylabel('Retorno Acumulado (%)', fontsize=12)
ax.set_title('Retornos Acumulados - Comparación de Todos los Portfolios', fontsize=14, fontweight='bold')
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
ax.grid(True, alpha=0.3)
plt.tight_layout()
output_file = output_dir / "COMPARATIVO_retornos_acumulados_todos_portfolios.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

# Gráfico 3: Retorno vs Volatilidad usando métodos integrados
print("Generando gráfico Retorno vs Volatilidad...")
fig, ax = plt.subplots(figsize=(12, 8))

retornos = []
volatilidades = []
nombres = []

for portfolio in portfolios_list:
    # Usar métodos integrados
    returns = portfolio.get_portfolio_returns()
    retornos.append(returns.mean() * 252 * 100)
    volatilidades.append(portfolio.portfolio_volatility() * 100)
    nombres.append(portfolio.name)

scatter = ax.scatter(volatilidades, retornos, s=200, alpha=0.6, c=range(len(retornos)), cmap='viridis')

for i, nombre in enumerate(nombres):
    ax.annotate(f"P{i+1}", (volatilidades[i], retornos[i]), 
                xytext=(5, 5), textcoords='offset points', fontsize=9)

ax.set_xlabel('Volatilidad Anualizada (%)', fontsize=12)
ax.set_ylabel('Retorno Anualizado (%)', fontsize=12)
ax.set_title('Retorno vs Volatilidad - Todos los Portfolios', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)

legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                              markerfacecolor=plt.cm.viridis(i/len(nombres)), 
                              markersize=10, label=f"P{i+1}: {nombre[:30]}") 
                   for i, nombre in enumerate(nombres)]
ax.legend(handles=legend_elements, bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=8)
plt.tight_layout()
output_file = output_dir / "COMPARATIVO_retorno_vs_volatilidad.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

# Gráfico 4: Sharpe Ratio
print("Generando gráfico de Sharpe Ratio...")
fig, ax = plt.subplots(figsize=(14, 8))

sharpe_ratios = [row['sharpe'] for row in resumen_portfolios]
nombres_cortos = [f"P{i+1}" for i in range(len(resumen_portfolios))]

bars = ax.barh(nombres_cortos, sharpe_ratios, color=plt.cm.viridis(np.linspace(0, 1, len(sharpe_ratios))))
ax.set_xlabel('Sharpe Ratio', fontsize=12)
ax.set_ylabel('Portfolio', fontsize=12)
ax.set_title('Sharpe Ratio - Comparación de Todos los Portfolios', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3, axis='x')

for i, (bar, ratio) in enumerate(zip(bars, sharpe_ratios)):
    ax.text(ratio, i, f' {ratio:.2f}', va='center', fontsize=9)

legend_text = '\n'.join([f"P{i+1}: {row['name']}" for i, row in enumerate(resumen_portfolios)])
ax.text(1.02, 0.5, legend_text, transform=ax.transAxes, fontsize=8,
        verticalalignment='center', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))

plt.tight_layout()
output_file = output_dir / "COMPARATIVO_sharpe_ratio_todos_portfolios.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

# Gráfico 5: Distribución de pesos (Heatmap)
print("Generando heatmap de distribución de pesos...")
fig, ax = plt.subplots(figsize=(14, 10))

pesos_matrix = []
nombres_portfolios = []
for row in resumen_portfolios:
    pesos_fila = [row['weights'].get(ticker, 0) * 100 for ticker in tickers]
    pesos_matrix.append(pesos_fila)
    nombres_portfolios.append(f"P{row['portfolio']}")

pesos_df = pd.DataFrame(pesos_matrix, index=nombres_portfolios, columns=tickers)

im = ax.imshow(pesos_df.values, cmap='YlOrRd', aspect='auto', vmin=0, vmax=100)
ax.set_xticks(range(len(tickers)))
ax.set_xticklabels(tickers, fontsize=10)
ax.set_yticks(range(len(nombres_portfolios)))
ax.set_yticklabels(nombres_portfolios, fontsize=9)
ax.set_xlabel('Activos', fontsize=12)
ax.set_ylabel('Portfolios', fontsize=12)
ax.set_title('Distribución de Pesos (%) - Todos los Portfolios', fontsize=14, fontweight='bold')

for i in range(len(nombres_portfolios)):
    for j in range(len(tickers)):
        text = ax.text(j, i, f'{pesos_df.iloc[i, j]:.1f}%',
                      ha="center", va="center", color="black", fontsize=8, fontweight='bold')

cbar = plt.colorbar(im, ax=ax)
cbar.set_label('Peso (%)', fontsize=10)

plt.tight_layout()
output_file = output_dir / "COMPARATIVO_distribucion_pesos_heatmap.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

# Gráfico 6: Escenarios Monte Carlo usando monte_carlo_summary()
print("Generando gráfico de escenarios Monte Carlo...")
fig, ax = plt.subplots(figsize=(14, 8))

x_pos = np.arange(len(resumen_portfolios))
width = 0.25

base_cases = [row['base_case'] for row in resumen_portfolios]
worst_cases = [row['worst_case'] for row in resumen_portfolios]
best_cases = [row['best_case'] for row in resumen_portfolios]

bars1 = ax.bar(x_pos - width, base_cases, width, label='Base (50%)', alpha=0.8, color='blue')
bars2 = ax.bar(x_pos, worst_cases, width, label='Peor (5%)', alpha=0.8, color='red')
bars3 = ax.bar(x_pos + width, best_cases, width, label='Mejor (95%)', alpha=0.8, color='green')

ax.set_xlabel('Portfolio', fontsize=12)
ax.set_ylabel('Valor Final ($)', fontsize=12)
ax.set_title('Escenarios Monte Carlo - Comparación de Todos los Portfolios', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels([f"P{i+1}" for i in range(len(resumen_portfolios))], fontsize=9)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
output_file = output_dir / "COMPARATIVO_escenarios_monte_carlo.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

# Gráfico 7: VaR y CVaR comparativo
print("Generando gráfico de VaR y CVaR...")
fig, ax = plt.subplots(figsize=(14, 8))

x_pos = np.arange(len(resumen_portfolios))
width = 0.35

var_values = [abs(row['var_5']) for row in resumen_portfolios]
cvar_values = [abs(row['cvar_5']) for row in resumen_portfolios]

bars1 = ax.bar(x_pos - width/2, var_values, width, label='VaR 5%', alpha=0.8, color='orange')
bars2 = ax.bar(x_pos + width/2, cvar_values, width, label='CVaR 5%', alpha=0.8, color='purple')

ax.set_xlabel('Portfolio', fontsize=12)
ax.set_ylabel('Riesgo ($)', fontsize=12)
ax.set_title('Métricas de Riesgo (VaR y CVaR) - Comparación de Todos los Portfolios', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels([f"P{i+1}" for i in range(len(resumen_portfolios))], fontsize=9)
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
output_file = output_dir / "COMPARATIVO_var_cvar_todos_portfolios.png"
fig.savefig(output_file, dpi=150, bbox_inches='tight')
plt.close(fig)
print(f"  ✓ Guardado: {output_file.name}")

print(f"\n✓ {7} gráficos comparativos generados")

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "=" * 80)
print("RESUMEN DE ARCHIVOS GENERADOS")
print("=" * 80)
print(f"\nTodos los archivos se encuentran en: {output_dir}\n")

print("Archivos principales:")
print(f"  ✓ 00_EXTRACCION_resumen_activos.txt")
print(f"  ✓ RESUMEN_COMPARATIVO_todos_los_portfolios.txt\n")

print("Carpetas por portfolio (10 portfolios):")
for idx in range(1, 11):
    portfolio_dirs = list(output_dir.glob(f"Portfolio_{idx:02d}_*"))
    if portfolio_dirs:
        print(f"  ✓ Portfolio {idx}: {portfolio_dirs[0].name}/")

print("\nGráficos comparativos (7 archivos):")
comparativos = list(output_dir.glob("COMPARATIVO_*.png"))
for comp in sorted(comparativos):
    print(f"  ✓ {comp.name}")

print("\n" + "=" * 80)
print("PROCESO COMPLETADO")
print("=" * 80)
print(f"\n✓ {len(holdings_data)} activos descargados")
print(f"✓ {len(portfolios_config)} portfolios creados y procesados")
print(f"✓ Todos los portfolios usan los mismos datos descargados")
print(f"✓ Script usa métodos integrados de src (portfolio.report(), portfolio.plots_report(), etc.)\n")

