import os, json
from datetime import datetime
import pandas as pd
import yfinance as yf
from google import genai

TICKERS = [
    {"symbol": "VWCE.DE", "name": "Vanguard FTSE All-World", "currency": "EUR", "cat": "ETF"},
    {"symbol": "EUNL.DE", "name": "iShares Core MSCI World", "currency": "EUR", "cat": "ETF"},
    {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SAP.DE", "name": "SAP SE", "currency": "EUR", "cat": "Aktien"},
    {"symbol": "BTC-USD", "name": "Bitcoin", "currency": "USD", "cat": "Krypto"},
    {"symbol": "ETH-USD", "name": "Ethereum", "currency": "USD", "cat": "Krypto"},
    {"symbol": "SOL-USD", "name": "Solana", "currency": "USD", "cat": "Krypto"},
    {"symbol": "XRP-USD", "name": "XRP (Ripple)", "currency": "USD", "cat": "Krypto"},
    {"symbol": "GC=F", "name": "Gold (Feinunze)", "currency": "USD", "cat": "Edelmetalle"},
    {"symbol": "SI=F", "name": "Silber (Feinunze)", "currency": "USD", "cat": "Edelmetalle"}
]

def calc_rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0.0).ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    l = (-d.where(d < 0, 0.0)).ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    return 100 - (100 / (1 + (g / l)))

def get_ai_text(client, d):
    fb = f"{d['name']} ({d['ticker']}) notiert aktuell bei {d['price']} {d['currency']} (RSI: {d['indicators']['rsi']}, übergeordneter Trend: {d['trend']})."
    if not client:
        return fb
    prompt = f"Kurze deutsche Marktanalyse (max 3 Sätze, reiner Text) für {d['name']} ({d['cat']}): Kurs {d['price']} {d['currency']}, RSI {d['indicators']['rsi']}, SMA50 {d['indicators']['sma_50']}, Trend {d['trend']}."
    try:
        r = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        return r.text.strip() if (r and r.text) else fb
    except Exception:
        return fb

def pack(series, step=1, fmt="%d.%m.%y"):
    s = series.iloc[::step]
    if len(series) > 0 and s.index[-1] != series.index[-1]:
        s = pd.concat([s, series.iloc[[-1]]])
    return {
        "labels": [x.strftime(fmt) for x in s.index],
        "prices": [round(float(x), 2) for x in s]
    }

def build_charts(c):
    end = c.index[-1]
    def sub(days):
        cut = c[c.index >= (end - pd.Timedelta(days=days))]
        return cut if len(cut) >= 2 else c.tail(5)
    max_step = max(1, len(c) // 180)
    return {
        "7d": pack(sub(7), 1, "%d.%m."),
        "1m": pack(sub(30), 1, "%d.%m."),
        "3m": pack(sub(90), 1, "%d.%m."),
        "6m": pack(sub(180), 2, "%d.%m.%y"),
        "1y": pack(sub(365), 3, "%d.%m.%y"),
        "2y": pack(sub(730), 5, "%m/%Y"),
        "max": pack(c, max_step, "%m/%Y")
    }

def main():
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    client = genai.Client(api_key=key) if key else None
    res = {"last_updated": datetime.now().strftime("%d.%m.%Y %H:%M"), "stocks": []}

    for t in TICKERS:
        try:
            df = yf.Ticker(t["symbol"]).history(period="max", auto_adjust=True)
            if df.empty or len(df) < 15:
                continue
            c = df["Close"].dropna()
            price = float(c.iloc[-1])
            prev = float(c.iloc[-2]) if len(c) > 1 else price
            chg = ((price - prev) / prev) * 100 if prev else 0.0
            s50 = float(c.rolling(50).mean().iloc[-1]) if len(c) >= 50 else price
            s200 = float(c.rolling(200).mean().iloc[-1]) if len(c) >= 200 else price
            rsi_s = calc_rsi(c)
            rsi = float(rsi_s.iloc[-1]) if not pd.isna(rsi_s.iloc[-1]) else 50.0
            trend = "Bullish" if (price > s50 and s50 >= s200) else ("Bearish" if (price < s50 and s50 < s200) else "Neutral")
            item = {
                "ticker": t["symbol"], "name": t["name"], "currency": t["currency"], "cat": t["cat"],
                "price": round(price, 2), "change_pct": round(chg, 2), "trend": trend,
                "indicators": {"rsi": round(rsi, 1), "sma_50": round(s50, 2), "sma_200": round(s200, 2)},
                "charts": build_charts(c)
            }
            item["ai_commentary"] = get_ai_text(client, item)
            res["stocks"].append(item)
        except Exception as e:
            print("Skip", t["symbol"], e)

    os.makedirs("data", exist_ok=True)
    with open("data/latest_analysis.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print("DONE")

if __name__ == "__main__":
    main()
