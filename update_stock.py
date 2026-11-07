import os
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
from google import genai

TICKERS = [
    {"symbol": "VWCE.DE", "name": "Vanguard FTSE All-World ETF", "currency": "EUR"},
    {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD"},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "currency": "USD"},
    {"symbol": "SAP.DE", "name": "SAP SE", "currency": "EUR"}
]


def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def generate_ai_analysis(client, stock_data):
    if not client:
        return (
            f"{stock_data['name']} notiert aktuell bei {stock_data['price']} {stock_data['currency']} "
            f"({stock_data['change_pct']}%). Der RSI (14) liegt bei {stock_data['indicators']['rsi']}, "
            f"während der übergeordnete Trend als {stock_data['trend']} eingestuft wird."
        )

    prompt = (
        f"Du bist ein erfahrener, sachlicher Finanzanalyst. Analysiere die aktuellen Daten für "
        f"{stock_data['name']} ({stock_data['ticker']}): "
        f"Kurs: {stock_data['price']} {stock_data['currency']} ({stock_data['change_pct']}% heute), "
        f"RSI (14): {stock_data['indicators']['rsi']}, "
        f"SMA 50: {stock_data['indicators']['sma_50']} {stock_data['currency']}, "
        f"SMA 200: {stock_data['indicators']['sma_200']} {stock_data['currency']}, "
        f"Trend-Status: {stock_data['trend']}. "
        f"Schreibe ein präzises, professionelles Tagesfazit auf Deutsch (maximal 3 Sätze). "
        f"Ordne den RSI und den Abstand zu den gleitenden Durchschnitten kurz ein. "
        f"Verwende reinen Fließtext ohne Markdown-Überschriften oder Aufzählungszeichen."
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        if response and response.text:
            return response.text.strip()
    except Exception as e:
        print(f"KI-Fehler bei {stock_data['ticker']}: {e}")

    return (
        f"{stock_data['name']} schloss bei {stock_data['price']} {stock_data['currency']}. "
        f"Mit einem RSI von {stock_data['indicators']['rsi']} und einem {stock_data['trend']}-Trend "
        f"bewegt sich der Wert im Rahmen seiner gleitenden Durchschnitte (SMA 50: {stock_data['indicators']['sma_50']})."
    )


def run_update():
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    client = None
    if api_key:
        try:
            client = genai.Client(api_key=api_key)
        except Exception as e:
            print(f"Kon
