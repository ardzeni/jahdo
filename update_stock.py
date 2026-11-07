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
            print(f"Konnte Gemini Client nicht initialisieren: {e}")

    results = {
        "last_updated": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "stocks": []
    }

    for item in TICKERS:
        symbol = item["symbol"]
        print(f"Lade Daten für {symbol}...")
        try:
            stock = yf.Ticker(symbol)
            df = stock.history(period="1y", auto_adjust=True)
            if df.empty or len(df) < 30:
                print(f"Zu wenig Daten für {symbol}, überspringe...")
                continue

            close_series = df["Close"].dropna()
            current_price = float(close_series.iloc[-1])
            prev_close = float(close_series.iloc[-2]) if len(close_series) > 1 else current_price
            change_pct = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0.0

            sma_50_series = close_series.rolling(window=50).mean()
            sma_200_series = close_series.rolling(window=200).mean()
            rsi_series = calculate_rsi(close_series, 14)

            rsi_val = float(rsi_series.iloc[-1]) if not pd.isna(rsi_series.iloc[-1]) else 50.0
            sma50_val = float(sma_50_series.iloc[-1]) if not pd.isna(sma_50_series.iloc[-1]) else current_price
            sma200_val = float(sma_200_series.iloc[-1]) if not pd.isna(sma_200_series.iloc[-1]) else current_price

            if current_price > sma50_val and sma50_val >= sma200_val:
                trend = "Bullish"
            elif current_price < sma50_val and sma50_val < sma200_val:
                trend = "Bearish"
            else:
                trend = "Neutral"

            recent_close = close_series.tail(30)
            history_dates = [d.strftime("%d.%m.") for d in recent_close.index]
            history_prices = [round(float(p), 2) for p in recent_close]

            stock_data = {
                "ticker": symbol,
                "name": item["name"],
                "currency": item["currency"],
                "price": round(current_price, 2),
                "change_pct": round(change_pct, 2),
                "pe_ratio": "–",
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
    output_path = os.path.join("data", "latest_analysis.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("Alle Analysen erfolgreich in data/latest_analysis.json gespeichert!")


if __name__ == "__main__":
    run_update()
