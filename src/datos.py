#primero importamos las librerias necesarias para la ejecucion del programa
import numpy as np
import yfinance as yf
import pandas as pd

#recordar importar las funciones del utils.py


#seleccionamos las apis de las que sacaremos informaciones





tickers_list = yf.ticker

datos2023_2024 = yf.download(list(tickers_list), start=2023-01-01, end=2024-01-01, auto_adjust=True)["Close"]
datos2023_2024.head()

