"""
CLASE BASE PARA EXTRAER DATOS

Todos los extractores heredaran de esta clase para garantizar la estandarizacion
de los datos
"""
from abc import ABC, abstractmethod # Indicar que sera una clase base abstracta
from typing import List, Optional # Mayor claridad
from datetime import datetime # Fecha y tiempos
import pandas as pd # Datos tabulares
from concurrent.futures import ThreadPoolExecutor, as_completed # Ejecutar peticiones concurrentes
import logging # Registrar info/errores durante la ejecucion

from ..data_classes import PriceSeries # Importar nuestro PriceSeries
# .. indica que esta en el paquete padre

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# Crear un logger con el nombre del módulo; para info, 
# errores y advertencias dentro de la clase

class BaseExtractor(ABC):
    """
    Clase abstracta base para los extractores

    Todos los extractores debe implementar metodos para obtener datos 
    historicos y devolver PriceSeries estandarizados
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Iniciar el extractor.
        
        Args:
            api_key: API key si es necesaria, sino None
        """
        self.api_key = api_key
        logger.info(f"Initialized {self.__class__.__name__}")
    
    @abstractmethod # Plantilla para las clases hijas (ACTIVOS)
    def fetch_historical_prices(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> PriceSeries:
        """
        Obtener precios historicos de los activos/tickers.
        
        Args:
            ticker: Simbolo Ticker
            start_date: Fecha de Inicio
            end_date: Fecha de Fin
            **kwargs: Parametros adicionales especificos del extractor
            
        Returns:
            Priceseries con un output estandarizado
        """
        pass
    
    @abstractmethod # Plantilla para las clases hijas (INDICES)
    def fetch_index_prices(
        self,
        index_symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> PriceSeries:
        """
         Obtener precios historicos de los Indices.
        
        Args:
            ticker: Simbolo Indice
            start_date: Fecha de Inicio
            end_date: Fecha de Fin
            **kwargs: Parametros adicionales especificos del extractor
            
        Returns:
            Priceseries con un output estandarizado
        """
        pass
    
    def fetch_multiple(
        self,
        tickers: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        max_workers: int = 5,
        **kwargs
    ) -> List[PriceSeries]:
        """
        Obtener precios historicos para varios tickers en paralelo.
        
        Args:
            tickers: Lista de los tickers
            start_date: Fecha de Inicio
            end_date: Fecha de Fin
            max_workers: Maximo numero de requests a la vez, por defecto 5 (AlphaVantage)
            **kwargs: Parametros adicionales para fetch_historical_prices
            
        Returns:
            Lista de PriceSeries standarizado
        """
        logger.info(f"Fetching {len(tickers)} tickers concurrently (max_workers={max_workers})")
        
        results = []
        failed = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_ticker = {
                executor.submit(
                    self.fetch_historical_prices,
                    ticker,
                    start_date,
                    end_date,
                    **kwargs
                ): ticker for ticker in tickers
            }
            
            # Recolectar las tareas a medida que van terminando
            for future in as_completed(future_to_ticker):
                ticker = future_to_ticker[future]
                try:
                    price_series = future.result()
                    results.append(price_series)
                    logger.info(f"Exito en {ticker}")
                except Exception as e:
                    logger.error(f"Fracaso en {ticker}: {str(e)}")
                    failed.append(ticker)
        
        if failed:
            logger.warning(f"Fracaso al buscar {len(failed)} tickers: {failed}")
        
        logger.info(f"Exito en {len(results)}/{len(tickers)} tickers")
        return results
    
    def _standardize_dataframe(
        self,
        df: pd.DataFrame,
        date_col: str = 'date',
        close_col: str = 'close',
        adjclose_col: str = 'adj close'
    ) -> pd.DataFrame:
        """
        Recibir un DataFrame con  nombres diversos y devolver uno con columnas
        estandar.
        
        Args:
            df: Input en DataFrame
            date_col: Nombre col de date
            close_col: Nombre col de close
            adjclose_col: Nombre col de adj close
            
        Returns:
            DataFrame estandarizado con [date, close, adj close]
        """
        # Mapear, diccionario nombres de columnas de entrada a nombre estandar
        column_mapping = {
            date_col: 'date',
            close_col: 'close',
            adjclose_col: 'adj close'
        }
        
        # Elegir y renombrar columnas (solo las que si existen)
        available_cols = {k: v for k, v in column_mapping.items() if k in df.columns}
        df_standardized = df[list(available_cols.keys())].copy() # Copia con cols disponibles
        df_standardized.rename(columns=available_cols, inplace=True)
        
        # Crear 'adj close' si no existe (desde 'close')
        if 'adj close' not in df_standardized.columns:
            if 'close' in df_standardized.columns:
                df_standardized['adj close'] = df_standardized['close']
            else:
                raise ValueError("No se encontró 'close' para crear 'adj close'")
        
        # Asegurar que la fecha sea datetime
        if not pd.api.types.is_datetime64_any_dtype(df_standardized['date']):
            df_standardized['date'] = pd.to_datetime(df_standardized['date'])
        
        # Asegurar sean datos numericos float
        numeric_cols = ['open', 'close', 'adj close']
        for col in numeric_cols:
            if col in df_standardized.columns:
                df_standardized[col] = pd.to_numeric(df_standardized[col], errors='coerce')
        
        # Ordenar por fecha
        df_standardized = df_standardized.sort_values('date').reset_index(drop=True)
        
        return df_standardized
    
    def validate_data(self, df: pd.DataFrame, ticker: str) -> bool:
        """
        Validar que los datos cumplen los requisitos minimos antes de guardarlos
        
        Args:
            df: Datafram no esta vacio, existen las columnas necesarias
            ticker: El simbolo ticker (para logging)
            
        Returns:
            True si valido, sino lanza ValueError
        """
        if df.empty:
            raise ValueError(f"No hay datos para {ticker}")
        
        if 'close' not in df.columns:
            raise ValueError(f"Falta 'close' en {ticker}")

        if 'adj close' not in df.columns:
            raise ValueError(f"Falta 'adj close' en {ticker}")
        
        if df['close'].isna().all():
            raise ValueError(f"Todos los closes son NaN en {ticker}")
        
        return True
