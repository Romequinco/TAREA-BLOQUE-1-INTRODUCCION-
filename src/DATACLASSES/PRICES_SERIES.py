
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
        # Verificar columnas
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

