"""
Extractor de datos de Yahoo Finance.
"""
from typing import Optional # Claridad
from datetime import datetime, timedelta # Datetime
import pandas as pd
import yfinance as yf 
import logging # Errores e info

from .base_extractor import BaseExtractor
from ..data_classes import PriceSeries  # corregir import

# Configurar logger para registrar eventos y errores durante la ejecución
logger = logging.getLogger(__name__)


class YFinanceExtractor(BaseExtractor):
    """
    Extractor de datos financieros desde Yahoo Finance 

    Hereda de BaseExtractor para garantizar que todos los extractores
    devuelvan datos en el mismo formato.
    """
    
    def __init__(self):
        """
        Inicializa el extractor de Yahoo Finance.
        """
        # Llamar al constructor de la clase padre sin API key
        super().__init__(api_key=None)
    
    def fetch_historical_prices(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> PriceSeries:
        """
        Obtiene datos históricos de precios de una acción desde Yf.
        
        Args:
            ticker: Símbolo de la acción (
            start_date: Fecha de inicio (por defecto: 1 año)
            end_date: Fecha final (por defecto: hoy)
            **kwargs: Parámetros adicionales de yfinance:
            
        Returns:
            PriceSeries en formato estandarizado
        """
        # Establecer fechas por defecto si no se proporcionan
        if end_date is None:
            end_date = datetime.now()
       
        if start_date is None:
            start_date = end_date - timedelta(days=365)
        
        # Registrar en el log qué estamos descargando y para qué período
        logger.info(f"Obteniendo {ticker} desde Yahoo Finance "
                   f"({start_date.date()} hasta {end_date.date()})")
        
        try:
            # Crear objeto Ticker de yfinance para el símbolo 
            # Este objeto nos da acceso a todos los datos disponibles
            stock = yf.Ticker(ticker)
            
            # Descargar el historial de precios con .history()
            # Devuelve DataFrame columnas: Luego cogemos solo las necesarias
            df = stock.history(
                start=start_date,
                end=end_date,
                **kwargs  # Pasar cualquier parámetro adicional a yfinance
            )
            
            # Verificar que se obtuvieron datos o si el DataFrame está vacío
            if df.empty:
                raise ValueError(f"No se obtuvieron datos para {ticker}. "
                               "Verifica que el símbolo sea correcto.")
            
            # Convertir el índice a una columna normal llamada 'Date'
            df.reset_index(inplace=True)
            
            # Estandarizar los nombres de las columnas (yf usa nombres con mayúsculas)
            # El método _standardize_dataframe viene de la clase BaseExtractor 
            df_standardized = self._standardize_dataframe(
                df,
                date_col='Date',      # Nombre original en yfinance
                close_col='Close',    # Precio de cierre
                adjclose_col='Adj Close'   # Precio de cierre ajustado
            )
            
            # Validar que los datos cumplen los requisitos mínimos
            self.validate_data(df_standardized, ticker)
            
            # Intentar obtener información adicional del ticker (nombre completo, tipo, etc.)
            try:
                # El atributo .info contiene metadatos de la empresa
                info = stock.info
                # Nombre completo de la empresa 
                name = info.get('longName', ticker)
                # Tipo de activo (EQUITY para acciones, INDEX para índices, etc.)
                asset_type = info.get('quoteType', 'stock').lower() 
            except:
                # Si falla la obtención de info, usar valores por defecto
                name = ticker
                asset_type = 'stock'
            
            # Crear el objeto PriceSeries con los datos estandarizados
            price_series = PriceSeries(
                ticker=ticker,                    # Símbolo del activo
                data=df_standardized,             # DataFrame con datos estandarizados
                name=name,                        # Nombre completo del activo
                asset_type=asset_type             # Tipo de activo
            )
            
            # Registrar el éxito de la operación
            logger.info(f"Descarga exitosa de {ticker}: "
                       f"{len(df_standardized)} puntos de datos obtenidos")
            
            return price_series
            
        except Exception as e:
            # Si ocurre cualquier error, registrarlo y re-lanzar la excepción
            logger.error(f"Error al obtener {ticker} desde Yahoo Finance: {str(e)}")
            raise
    
    def fetch_index_prices(
        self,
        index_symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs
    ) -> PriceSeries:
        """
        Obtiene datos históricos de precios de un índice bursátil desde Yahoo Finance.
        
        Args:
            index_symbol: Símbolo del índice (normalmente empieza con ^)
            start_date: Fecha de inicio (por defecto: hace 1 año)
            end_date: Fecha final (por defecto: hoy)
            **kwargs: Parámetros adicionales para yfinance
            
        Returns:
            PriceSeries: Objeto con los datos del índice en formato estandarizado
       """
        # Para los índices, mismo método que para acciones
        # La diferencia, marcamos explícitamente el tipo como 'index'
        price_series = self.fetch_historical_prices(
            ticker=index_symbol,
            start_date=start_date,
            end_date=end_date,
            **kwargs
        )
        
        # Sobrescribir el tipo de activo para asegurarnos de que sea 'index'
        price_series.asset_type = 'index'
        
        return price_series
    
    def fetch_dividend_history(
        self,
        ticker: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Obtiene el historial de dividendos pagados por una acción.
        
        Args:
            ticker: Símbolo de la acción
            start_date: Fecha de inicio (por defecto: hace 5 años)
            end_date: Fecha final (por defecto: hoy)
            
        Returns:
            DataFrame con columnas:
                - date: Fecha del pago del dividendo
                - dividend: Cantidad del dividendo por acción
            
            Si no hay dividendos, retorna un DataFrame vacío
        """
        # Establecer fechas por defecto
        if end_date is None:
            end_date = datetime.now()
        if start_date is None:
            # Por defecto, obtener 5 años de historial de dividendos
            start_date = end_date - timedelta(days=365*5)
        
        logger.info(f"Obteniendo historial de dividendos para {ticker}")
        
        try:
            # Crear objeto Ticker
            stock = yf.Ticker(ticker)
            
            # El atributo .dividends contiene todos los dividendos históricos
            dividends = stock.dividends
            
            # Filtrar por el rango de fechas especificado
            # Booleanos para seleccionar solo las fechas en el rango
            dividends = dividends[
                (dividends.index >= start_date) & 
                (dividends.index <= end_date)
            ]
            
            # Verificar si se encontraron dividendos
            if dividends.empty:
                logger.warning(f"No se encontraron dividendos para {ticker} "
                             f"en el período especificado. La empresa podría no "
                             f"pagar dividendos o no hay datos disponibles.")
                return pd.DataFrame()
            
            # Convertir a DataFrame con formato estándar
            df = pd.DataFrame({
                'date': dividends.index,      # Fechas de pago
                'dividend': dividends.values  # Montos de dividendo
            })
            
            return df
            
        except Exception as e:
            logger.error(f"Error al obtener dividendos para {ticker}: {str(e)}")
            # En caso de error, retornar DataFrame vacío en lugar de lanzar excepción (No paga div)
            return pd.DataFrame()
    
    def fetch_company_info(self, ticker: str) -> dict:
        """
        Obtiene información detallada y metadatos sobre una empresa.
        
        Args:
            ticker: Símbolo de la acción
            
        Returns:
            Diccionario con la siguiente información (cuando está disponible):
                - ticker: Símbolo del activo
                - name: Nombre completo de la empresa
                - sector: Sector económico 
                - industry: Industria específica 
                - market_cap: Capitalización de mercado en USD
                - currency: Moneda de cotización
                - exchange: Bolsa donde cotiza 
                - country: País donde opera principalmente
                - website: Sitio web corporativo
                - description: Descripción del negocio
            
            Si ocurre un error, retorna un dict con el ticker y el mensaje de error
            
        """
        logger.info(f"Obteniendo información corporativa para {ticker}")
        
        try:
            # Crear objeto Ticker
            stock = yf.Ticker(ticker)
            
            # El atributo .info contiene un diccionario completo con toda
            # la información disponible sobre la empresa
            info = stock.info
            
            # Extraer y estructurar la información relevante
            # Usamos .get() con valores por defecto para evitar errores
            # si algún campo no está disponible ponemos algun valor por defecto
            company_info = {
                'ticker': ticker,
                
                # Información básica
                'name': info.get('longName', ticker),  # Nombre completo
                
                # Clasificación
                'sector': info.get('sector', 'Desconocido'),      # Sector económico
                'industry': info.get('industry', 'Desconocido'),  # Industria específica
                
                # Datos financieros
                'market_cap': info.get('marketCap', None),  # Capitalización de mercado
                'currency': info.get('currency', 'USD'),    # Moneda de cotización
                
                # Datos de cotización
                'exchange': info.get('exchange', 'Desconocido'),  # Bolsa
                
                # Ubicación
                'country': info.get('country', 'Desconocido'),  # País de origen
                
                # Información adicional
                'website': info.get('website', None),  # Sitio web corporativo
                
                # Descripción del negocio
                # Puede ser un texto largo explicando a qué se dedica la empresa
                'description': info.get('longBusinessSummary', None)
            }
            
            return company_info
            
        except Exception as e:
            # Si hay algún error al obtener la información, 
            # retornar un diccionario con el error en lugar de fallar completamente
            logger.error(f"Error al obtener información para {ticker}: {str(e)}")
            return {
                'ticker': ticker, 
                'error': str(e)
            }
