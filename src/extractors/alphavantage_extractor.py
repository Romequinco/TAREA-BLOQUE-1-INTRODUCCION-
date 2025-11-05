from typing import Optional
from datetime import datetime, timedelta
import pandas as pd
import requests
import time
import logging

from .base_extractor import BaseExtractor
from ..data_classes import PriceSeries  # corregir import

logger = logging.getLogger(__name__)


class AlphaVantageExtractor(BaseExtractor):
    """
    Extractor de datos financieros desde la API de Alpha Vantage.
    
    Características:
    - Requiere API key gratuita (25 requests/día)
    - Rate limiting automático (respeta 5 requests/minuto)
    """
    
    # URL base para todas las peticiones a la API
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: str):
        """
        Inicializa el extractor de Alpha Vantage.
        
        Args:
            api_key:  API de Alpha Vantage 
            
        Raises:
            ValueError: Si no se proporciona una API key
        """
        # Verificar que se proporcionó una API key
        if not api_key:
            raise ValueError(
                "Alpha Vantage requiere una API key. "
                "Obtén una gratis en: https://www.alphavantage.co/support/#api-key"
            )
        
        # Inicializar la clase padre con la API key
        super().__init__(api_key=api_key)
        
        # Variables para controlar el rate limiting
        self._last_request_time = 0  # Timestamp de la última petición
        self._min_request_interval = 12  # segundos entre peticiones (5 req/min = cada 12s)
    
    def _rate_limit(self):
        """
        Respetar los límites de la API.
        
        Cálculo: 60 segundos / 5 requests = 12 segundos entre requests
        """
        # Calcular cuánto tiempo ha pasado desde la última petición
        elapsed = time.time() - self._last_request_time
        
        # Si no ha pasado suficiente tiempo, esperar
        if elapsed < self._min_request_interval:
            sleep_time = self._min_request_interval - elapsed
            logger.debug(f"Rate limiting: esperando {sleep_time:.1f}s antes del siguiente request")
            time.sleep(sleep_time)
        
        # Actualizar el tiempo de la última petición
        self._last_request_time = time.time()
    
    def _make_request(self, params: dict) -> dict:
        """
        Realiza una petición HTTP a la API de Alpha Vantage con manejo de errores.
        
        Args:
            params: Diccionario con los parámetros de la query (function, symbol, etc.)
            
        Returns:
            Respuesta JSON como diccionario
            
        Raises:
            ValueError: Si la API retorna un error o se alcanzó el límite de requests
        """
        # Aplicar rate limiting antes de hacer la petición
        self._rate_limit()
        
        # Añadir la API key a los parámetros
        params['apikey'] = self.api_key
        
        try:
            # Realizar petición GET con timeout de 30 segundos
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            
            # Verificar que la petición fue exitosa 
            response.raise_for_status()
            
            # Convertir a JSON
            data = response.json()
            
            # Verificar si hay un mensaje de error
            if 'Error Message' in data:
                raise ValueError(f"Error de la API: {data['Error Message']}")
            
            # Verificar si se alcanzó el límite de requests
            if 'Note' in data:
                raise ValueError(
                    f"Límite de requests alcanzado: {data['Note']}. "
                    f"Plan gratuito: 25 requests/día, 5 requests/minuto."
                )
            
            return data
            
        except requests.exceptions.RequestException as e:
            # Error de conexión o HTTP
            logger.error(f"Fallo en la petición HTTP: {str(e)}")
            raise
    
    def fetch_historical_prices(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        outputsize: str = 'full',
        **kwargs
    ) -> PriceSeries:
        """
        Obtiene datos históricos diarios de una acción desde Alpha Vantage.
        
        Args:
            ticker: Símbolo de la acción 
            start_date: Fecha inicial 
            end_date: Fecha final 
            outputsize: Tamaño de salida:
                - 'compact': Últimos 100 puntos de datos (~4 meses)
                - 'full': Más de 20 años de datos históricos completos
            
        Returns:
            PriceSeries con datos en formato estandarizado
        """
        logger.info(f"Obteniendo {ticker} desde Alpha Vantage")
        
        try:
            # Parámetros para la API
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',  # Función de series temporales diarias ajustadas
                'symbol': ticker,
                'outputsize': outputsize,
                'datatype': 'json'  # Formato de respuesta
            }
            
            # Realizar la petición a la API
            data = self._make_request(params)
            
            # Verificar que la respuesta contiene datos de series temporales
            if 'Time Series (Daily)' not in data:
                raise ValueError(
                    f"No se encontraron datos de series temporales para {ticker}. "
                    f"Verifica que el símbolo sea correcto."
                )
            
            # Extraer los datos de series temporales del JSON
            time_series = data['Time Series (Daily)']
            
            # Convertir de dict a DataFrame
            # El JSON tiene fechas como keys, necesitamos convertirlo
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'date'}, inplace=True)
            
            # Alpha Vantage usa claves numeradas para las columnas:
            # '1. open', '2. high', '3. low', '4. close', '5. adjusted close', '6. volume'
            df_standardized = self._standardize_dataframe(
                df,
                date_col='date',
                close_col='4. close',
                adjclose_col='5. adjusted close',
            )
            
            # Filtrar por rango de fechas si se proporcionaron
            if start_date:
                df_standardized = df_standardized[df_standardized['date'] >= start_date]
            if end_date:
                df_standardized = df_standardized[df_standardized['date'] <= end_date]
            
            # Validar que hay datos después del filtrado
            self.validate_data(df_standardized, ticker)
            
            # Intentar obtener el nombre desde los metadatos
            name = ticker
            if 'Meta Data' in data:
                name = data['Meta Data'].get('2. Symbol', ticker)
            
            # Crear objeto PriceSeries
            price_series = PriceSeries(
                ticker=ticker,
                data=df_standardized,
                name=name,
                asset_type='stock'
            )
            
            logger.info(f"Descarga exitosa de {ticker}: {len(df_standardized)} puntos de datos")
            return price_series
            
        except Exception as e:
            logger.error(f"Error al obtener {ticker} desde Alpha Vantage: {str(e)}")
            raise
    
    def fetch_index_prices(
        self,
        index_symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> PriceSeries:
        """
        Obtiene datos históricos de un índice bursátil.
        
        IMPORTANTE: Alpha Vantage tiene soporte limitado para índices.
        Se recomienda usar ETFs como proxies de los índices:
        
        Args:
            index_symbol: Símbolo del índice o ETF proxy
            start_date: Fecha inicial
            end_date: Fecha final
            
        Returns:
            PriceSeries marcado como tipo 'index'
        """
        # Usar el mismo método que para acciones
        price_series = self.fetch_historical_prices(
            ticker=index_symbol,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
        # Marcar como índice
        price_series.asset_type = 'index'
        return price_series
    
    def fetch_intraday_prices(
        self,
        ticker: str,
        interval: str = '5min',
        outputsize: str = 'compact'
    ) -> pd.DataFrame:
        """
        Obtiene datos de precios intraday (dentro del día).
        
        Args:
            ticker: Símbolo de la acción
            interval: Intervalo temporal entre datos:
                - '1min': Cada minuto (mucha información)
                - '5min': Cada 5 minutos (recomendado)
                - '15min': Cada 15 minutos
                - '30min': Cada 30 minutos
                - '60min': Cada hora
            outputsize: Tamaño de salida:
                - 'compact': Últimos 100 puntos de datos
                - 'full': Últimos 30 días completos de trading
                
        Returns:
            DataFrame con datos intraday estandarizados
        """
        logger.info(f"Obteniendo datos intraday para {ticker} (intervalo: {interval})")
        
        try:
            # Configurar parámetros para datos intraday
            params = {
                'function': 'TIME_SERIES_INTRADAY',
                'symbol': ticker,
                'interval': interval,
                'outputsize': outputsize,
                'datatype': 'json'
            }
            
            # Realizar petición
            data = self._make_request(params)
            
            # La clave de los datos cambia según el intervalo
            time_series_key = f'Time Series ({interval})'
            if time_series_key not in data:
                raise ValueError(f"No se encontraron datos intraday para {ticker}")
            
            # Extraer series temporales
            time_series = data[time_series_key]
            
            # Convertir a DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.reset_index(inplace=True)
            df.rename(columns={'index': 'datetime'}, inplace=True)
            
            # Estandarizar formato
            df_standardized = self._standardize_dataframe(
                df,
                date_col='datetime',
                open_col='1. open',
                high_col='2. high',
                low_col='3. low',
                close_col='4. close',
                volume_col='5. volume'
            )
            
            return df_standardized
            
        except Exception as e:
            logger.error(f"Error al obtener datos intraday para {ticker}: {str(e)}")
            raise
    
    def fetch_global_quote(self, ticker: str) -> dict:
        """
        Obtiene la cotización más reciente de una acción (quote en tiempo real).
        
        Esta función retorna el precio actual, cambio del día, volumen, etc.
        Útil para obtener datos rápidos sin descargar historial completo.
        
        Args:
            ticker: Símbolo de la acción
            
        Returns:
            Diccionario con datos actuales:
                - ticker: Símbolo
                - price: Precio actual
                - change: Cambio absoluto del día
                - change_percent: Cambio porcentual del día
                - volume: Volumen de transacciones del día
                - latest_trading_day: Última fecha de trading
                - previous_close: Precio de cierre anterior
                - open, high, low: Precios del día
        """
        logger.info(f"Obteniendo cotización actual para {ticker}")
        
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': ticker
            }
            
            data = self._make_request(params)
            
            if 'Global Quote' not in data:
                raise ValueError(f"No se encontraron datos de cotización para {ticker}")
            
            quote = data['Global Quote']
            
            # Extraer y limpiar los datos relevantes
            quote_data = {
                'ticker': ticker,
                'price': float(quote.get('05. price', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%'),
                'volume': int(quote.get('06. volume', 0)),
                'latest_trading_day': quote.get('07. latest trading day', None),
                'previous_close': float(quote.get('08. previous close', 0)),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0))
            }
            
            return quote_data
            
        except Exception as e:
            logger.error(f"Error al obtener cotización para {ticker}: {str(e)}")
            return {'ticker': ticker, 'error': str(e)}
    
    def search_symbol(self, keywords: str) -> pd.DataFrame:
        """
        Busca símbolos de acciones que coincidan con palabras clave
        
        Args:
            keywords: Palabras clave para buscar (nombre de empresa, símbolo, etc.)
            
        Returns:
            DataFrame con resultados de búsqueda:
                - symbol: Símbolo de la acción
                - name: Nombre de la empresa
                - type: Tipo de activo (Equity, ETF, etc.)
                - region: Región/país
                - currency: Moneda de cotización
                - matchScore: Puntuación de coincidencia (0-1)
        """
        logger.info(f"Buscando símbolos para: {keywords}")
        
        try:
            params = {
                'function': 'SYMBOL_SEARCH',
                'keywords': keywords
            }
            
            data = self._make_request(params)
            
            # Verificar si hay resultados
            if 'bestMatches' not in data or not data['bestMatches']:
                logger.warning(f"No se encontraron coincidencias para: {keywords}")
                return pd.DataFrame()
            
            # Convertir resultados a DataFrame
            matches = pd.DataFrame(data['bestMatches'])
            
            # Limpiar nombres de columnas (Alpha Vantage usa formato "1. symbol", etc.)
            matches.columns = [
                col.split('. ')[1] if '. ' in col else col 
                for col in matches.columns
            ]
            
            return matches
            
        except Exception as e:
            logger.error(f"Error al buscar {keywords}: {str(e)}")
            return pd.DataFrame()
