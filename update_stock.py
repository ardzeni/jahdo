import os
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
from google import genai

# Liste der Aktien & ETFs, die täglich analysiert werden sollen
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
    # Exponentieller Durchschnitt nach Wilder
    avg_gain = gain.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def generate_ai_analysis(client, stock_data):
    if not client:
        return "KI-Kommentar nicht verfügbar (Kein API-Key hinterlegt)."
        
    prompt = f"""
    Du bist ein erfahrener, sachlicher Finanzanalyst. Analysiere die aktuellen Daten für {stock_data['name']} ({stock_data['ticker']}):
    - Kurs: {stock_data['price']} {stock_data['currency']} ({stock_data['change_pct']}% heute)
    - RSI (14): {stock_data['indicators']['rsi']}
    - SMA 50: {stock_data['indicators']['sma_50']} {stock_data['currency']}
    - SMA 200: {stock_data['indicators']['sma_200']} {stock_data['currency']}
    - Trend-Status: {stock_data['trend']}

    Schreibe ein präzises, professionelles Tagesfazit auf Deutsch (maximal 3 Sätze). 
    Ordne den RSI und den Abstand zu den gleitenden Durchschnitten kurz ein. 
    Verwende reinen Fließtext ohne Markdown-Überschriften oder Aufzählungszeichen.
    """
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text.strip()
    except Exception as e:
        print(f"KI-Fehler bei {stock_data['ticker']}: {e}")
        return "Die automatische KI-Einschätzung wird beim nächsten Durchlauf aktualisiert."

def run_update():
    api_key = os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key) if api_key else None

    results = {
        "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "stocks": []
    }

    for item in TICKERS:
        symbol = item["symbol"]
        print(f"Lade Daten für {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            # 1 Jahr Historie laden, damit der SMA 200 sauber berechnet werden kann
            df = stock.history(period="1y")
            if df.empty or len(df) < 50:
                print(f"Zu wenig Daten für {symbol}, überspringe...")
                continue

            current_price = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            change_pct = ((current_price - prev_close) / prev_close) * 100

            df['SMA_50'] = df['Close'].rolling(window=50).mean()
            df['SMA_200'] = df['Close'].rolling(window=200).mean()
            df['RSI'] = calculate_rsi(df['Close'], 14)

            rsi_val = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50.0
            sma50_val = float(df['SMA_50'].iloc[-1]) if not pd.isna(df['SMA_50'].iloc[-1]) else current_price
            sma200_val = float(df['SMA_200'].iloc[-1]) if not pd.isna(df['SMA_200'].iloc[-1]) else current_price

            # Trend bestimmen
            if current_price > sma50_val and sma50_val > sma200_val:
                trend = "Bullish"
            elif current_price < sma50_val and sma50_val < sma200_val:
                trend = "Bearish"
            else:
                trend = "Neutral"

            # Letzte 30 Tage für das Frontend-Diagramm extrahieren
            recent_df = df.tail(30)
            history_dates = [d.strftime("%d.%m.") for d in recent_df.index]
            history_prices = [round(float(p), 2) for p in recent_df['Close']]

            info = stock.info
            pe_ratio = info.get("trailingPE", None)

            stock_data = {
                "ticker": symbol,
                "name": item["name"],
                "currency": item["currency"],
                "price": round(current_price, 2),
                "change_pct": round(change_pct, 2),
                "pe_ratio": round(float(pe_ratio), 1) if pe_ratio else "–",
                "trend": trend,
                "indicators": {
                    "rsi": round(rsi_val, 1),
                    "sma_50": round(sma50_val, 2),
                    "sma_200": round(sma200_val, 2)
                },
                "chart": {
                    "labels": history_dates,
                    "prices": history_prices
                }
            }

            stock_data["ai_commentary"] = generate_ai_analysis(client, stock_data)
            results["stocks"].append(stock_data)

        except Exception as e:
            print(f"Fehler bei {symbol}: {e}")

    os.makedirs("data", exist_ok=True)
    with open("data/latest_analysis.json
