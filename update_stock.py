import os
import json
from datetime import datetime
import pandas as pd
import yfinance as yf
from google import genai

def generate_ai_analysis(stock_data):
    # Nutzt den GitHub Secret GEMINI_API_KEY
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    prompt = f"""
    Du bist ein professioneller Finanzanalyst. Analysiere die folgenden heutigen Daten für {stock_data['company_name']} ({stock_data['ticker']}):
    - Aktueller Kurs: {stock_data['current_price']} USD
    - Tägliche Änderung: {stock_data['daily_change_pct']}%
    - RSI (14 Tage): {stock_data['indicators']['rsi_14']}
    - SMA 50: {stock_data['indicators']['sma_50']}
    - SMA 200: {stock_data['indicators']['sma_200']}
    
    Schreibe eine prägnante, sachliche tagesaktuelle Analyse auf Deutsch (ca. 3 Sätze). Formatiere das Ergebnis als reinen Text für eine Finanz-Webseite.
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"KI-Analyse derzeit nicht verfügbar."

def run_update():
    ticker_symbol = "AAPL" # Beispiel Apple, lässt sich auf ETFs/andere Aktien ausweiten
    stock = yf.Ticker(ticker_symbol)
    df = stock.history(period="6mo")
    
    if df.empty:
        print("Keine Daten gefunden.")
        return

    info = stock.info
    current_price = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2]
    daily_change_pct = ((current_price - prev_close) / prev_close) * 100
    
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['SMA_200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    analysis_result = {
        "ticker": ticker_symbol.upper(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "company_name": info.get("longName", ticker_symbol),
        "current_price": round(current_price, 2),
        "daily_change_pct": round(daily_change_pct, 2),
        "indicators": {
            "rsi_14": round(df['RSI'].iloc[-1], 2) if not pd.isna(df['RSI'].iloc[-1]) else 0,
            "sma_50": round(df['SMA_50'].iloc[-1], 2) if not pd.isna(df['SMA_50'].iloc[-1]) else 0,
            "sma_200": round(df['SMA_200'].iloc[-1], 2) if not pd.isna(df['SMA_200'].iloc[-1]) else 0
        }
    }
    
    analysis_result["ai_commentary"] = generate_ai_analysis(analysis_result)
    
    # Speichern als JSON im data-Ordner
    os.makedirs("data", exist_ok=True)
    with open("data/latest_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis_result, f, ensure_ascii=False, indent=4)
    print("Analyse erfolgreich aktualisiert und gespeichert.")

if __name__ == "__main__":
    run_update()