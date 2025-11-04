from dataclasses import dataclass, field # Para crear Dataclasses y definir atributos despues
from datetime import datetime # Para manejar fechas
from typing import List, Dict, Optional # Especificar tipos de datos
import pandas as pd # Analisis financiero
import numpy as np # Analisis numerico


@dataclass # Para poner plantilla y evitar codigo repetitivo (__init__)
class PriceSeries:
    """
    Representar una serie temporal de precios de un activo.

    Atributos:
        ticker: Ticker (AAPL)
        data: Datos históricos en DataFrame
        asset_type: Tipo de activo
    """
    ticker: str
    data: pd.DataFrame
    asset_type: str = "stock" # Por defecto accion

    # Media y desviacion estandar, se calcularan despues de crear el objeto
    mean_price: float = field(init=False)
    std_dev: float = field(init=False)

    def __post_init__(self): # Activar despues del __init__
        """
        Verifica las columnas. Se asegura el date sea datetime,
        Ordena por fecha y Calcula estadisticas basicas
        """
        # Estandarizar columnas antes de verificar nada
        self._standardize_columns()

        # Verificar columnas requeridas
        required_cols = ['date', 'Adj close']
        if not all(col in self.data.columns for col in required_cols):
            raise ValueError(f"Faltan columnas de los datos: {required_cols}")

        # Asegurar que 'date' sea tipo datetime
        if not pd.api.types.is_datetime64_any_dtype(self.data['date']):
            self.data['date'] = pd.to_datetime(self.data['date'])

        # Ordenar por fechas
        self.data = self.data.sort_values('date').reset_index(drop=True)

        # Calcular estadisticas
        self.mean_price = float(self.data['Adj close'].mean())
        self.std_dev = float(self.data['Adj close'].std())

    def _standardize_columns(self):
        """
        Garantiza que las columnas principales existan.
        Si 'Adj close' falta, intenta usar valores previos o 'close'.
        """
        standard_cols = ['date', 'close', 'Adj close']

        # Crear las columnas que falten con NaN
        for col in standard_cols:
            if col not in self.data.columns:
                self.data[col] = np.nan

        # 🔹 Si falta 'Adj close' o tiene muchos NaN, intentar rellenar
        if self.data['Adj close'].isna().all():
            # Si toda la columna está vacía → usar 'close'
            self.data['Adj close'] = self.data['close']
        else:
            # Rellenar huecos con el valor anterior (forward fill)
            self.data['Adj close'] = self.data['Adj close'].fillna(method='ffill')

        # Reordenar columnas
        self.data = self.data[standard_cols]

    def get_returns(self) -> pd.Series:
        """
        Calcular rendimientos diarios porcentuales
        """
        return self.data['close'].pct_change().dropna()

    def get_cumulative_returns(self) -> pd.Series:
        """
        Calcular rendimiento acumulado
        """
        returns = self.get_returns()
        return (1 + returns).cumprod() - 1

    def volatility(self, annualize: bool = True) -> float:
        """
        Calcular la volatilidad (Desviacion estandar de los retornos).

        Args:
            Anual: If True, (se asumen 252 dias de cotizacion)
        """
        returns = self.get_returns()
        vol = float(returns.std())
        if annualize:
            vol *= np.sqrt(252)
        return vol

    def summary_stats(self) -> Dict:
        """
        Devolver todas las metricas
        """
        return {
            'ticker': self.ticker,
            'mean_price': self.mean_price,
            'std_dev': self.std_dev,
            'volatility': self.volatility(),
            'total_return': float(self.get_cumulative_returns().iloc[-1]) if len(self.data) > 1 else 0.0,
            'data_points': len(self.data),
            'start_date': self.data['date'].min(),
            'end_date': self.data['date'].max()
        }

    def __repr__(self) -> str:
      """
      Como se muestra el objeto
      """
      return (f"PriceSeries(ticker={self.ticker}, "
              f"points={len(self.data)}, mean={self.mean_price:.2f}, "
              f"std={self.std_dev:.2f})")


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
    name: str = "Portfolio" # Por defecto "Portfolio"

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
            holding.data = holding.data[holding.data['date'].isin(common_dates)].reset_index(drop=True)

    def get_portfolio_returns(self) -> pd.Series:
        """
        Calcular los rendimientos ponderados de la cartera
        """
        returns_df = pd.DataFrame()

        for ticker, holding in self.holdings.items():
            returns_df[ticker] = holding.get_returns()

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

        # Index de cualquier activo
        dates = list(self.holdings.values())[0].data['date'][1:]  # Nos saltamos el primer dia (no tiene retorno)

        return pd.DataFrame({
            'date': dates.values,
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
