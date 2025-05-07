import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import mplfinance as mpf

def plot_candlestick(df, ticker):
    df_candle = df[['Open', 'High', 'Low', 'Close', 'Volume']]
    df_candle.index.name = 'Date'
    
    mpf.plot(df_candle, type='candle', volume=True, title=f'{ticker} Candlestick Chart',
             style='yahoo', mav=(5, 10), figsize=(12, 6))

def plot_peaks_troughs(df, ticker):
    close = df['Close']
    maxima = argrelextrema(close.values, np.greater)[0]
    minima = argrelextrema(close.values, np.less)[0]

    plt.figure(figsize=(12, 6))
    plt.plot(df.index, close, label='Close Price', color='black')

    plt.scatter(df.index[maxima], close.iloc[maxima], color='red', label='Peaks', s=50)
    plt.scatter(df.index[minima], close.iloc[minima], color='blue', label='Troughs', s=50)

    plt.title(f"{ticker} Close Price with Peaks and Troughs")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def main():
    ticker = "AAPL"  # Change as needed
    df = yf.download(ticker, start="2023-01-01", end="2024-12-31")
    df.dropna(inplace=True)

    plot_candlestick(df, ticker)
    plot_peaks_troughs(df, ticker)

if __name__ == "__main__":
    main()
