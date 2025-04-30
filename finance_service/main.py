from fastapi import FastAPI, HTTPException
import yfinance as yf
import pandas as pd

from shared.schemas import StockData, HistoricalData
from typing import List

app = FastAPI()


@app.get("/stock/{symbol}", response_model=StockData)
def get_stock_data(symbol: str):

    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
        previous_close = info.get('previousClose', current_price)
        change_amount = current_price - previous_close
        change_percent = (change_amount / previous_close) * 100 if previous_close else 0
        
        return StockData(
            symbol=symbol,
            current_price=current_price,
            change_percent=change_percent,
            change_amount=change_amount,
            volume=info.get('volume', 0),
            market_cap=info.get('marketCap'),
            pe_ratio=info.get('trailingPE'),
            dividend_yield=info.get('dividendYield')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{symbol}/history", response_model=List[HistoricalData])
def get_stock_history(symbol: str,
                      period: str = "1mo",
                      interval: str = "1d"):
    
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period=period, interval=interval)
        
        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for {symbol}")
        
        # Convert DataFrame to list of HistoricalData objects
        history_data = []

        for index, row in hist.iterrows():

            history_data.append(HistoricalData(
                date=index.strftime("%Y-%m-%d"),
                open=row['Open'],
                high=row['High'],
                low=row['Low'],
                close=row['Close'],
                volume=int(row['Volume'])
            ))
        
        return history_data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{symbol}/search")
def search_stock(symbol: str):

    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        
        if not info:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        return {
            "symbol": symbol,
            "name": info.get('longName', info.get('shortName', '')),
            "exchange": info.get('exchange', ''),
            "currency": info.get('currency', ''),
            "sector": info.get('sector', ''),
            "industry": info.get('industry', '')
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
