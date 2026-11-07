"""Jahdo market-data pipeline.


Dependencies: pandas, yfinance, google-genai (optional when Gemini is disabled).
Set GEMINI_API_KEY as a CI secret; never commit it to the repository.
"""


from __future__ import annotations


import json
import logging
import math
import os
import random
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


import pandas as pd
import yfinance as yf


try:
    from google import genai
except ImportError:  # The market-data job can still run without AI commentary.
    genai = None  # type: ignore[assignment]




TICKERS: list[dict[str, str]] = [
    {"symbol": "VWCE.DE", "name": "Vanguard FTSE All-World ETF", "currency": "EUR"},
    {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD"},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "currency": "USD"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "currency": "USD"},
    {"symbol": "SAP.DE", "name": "SAP SE", "currency": "EUR"},
]


OUTPUT_PATH = Path(os.environ.get("OUTPUT_PATH", "data/latest_analysis.json"))
GEMINI_MODEL = "gemini-2.5-flash"
RSI_PERIOD = 14
MIN_HISTORY = RSI_PERIOD + 1
MAX_CHART_POINTS = 180
YF_TIMEOUT_SECONDS = 20
YF_RETRIES = 3
GEMINI_RETRIES = 2
SYMBOL_PAUSE_SECONDS = 0.8
RETRY_BASE_SECONDS = 1.0


LOGGER = logging.getLogger("jahdo_pipeline")




def configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )




def _rsi_from_averages(avg_gain: float, avg_loss: float) -> float:
    """Return RSI for Wilder-smoothed average gains and losses."""
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    relative_strength = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + relative_strength))




def calc_rsi(prices: pd.Series, period: int = RSI_PERIOD) -> pd.Series:
    """Calculate RSI with Wilder's initial simple average and recursive smoothing.


    The first valid RSI requires ``period`` actual price changes. Earlier values
    remain NaN instead of being replaced with a made-up neutral value.
    """
    if period < 1:
        raise ValueError("period must be >= 1")


    close = pd.to_numeric(prices, errors="coerce").astype("float64")
    result = pd.Series(float("nan"), index=close.index, dtype="float64")
    if len(close) <= period:
        return result


    delta = close.diff()
    gains = delta.clip(lower=0.0)
    losses = -delta.clip(upper=0.0)


    avg_gain = float(gains.iloc[1 : period + 1].mean())
    avg_loss = float(losses.iloc[1 : period + 1].mean())
    result.iloc[period] = _rsi_from_averages(avg_gain, avg_loss)


    for index in range(period + 1, len(close)):
        gain = float(gains.iloc[index]) if pd.notna(gains.iloc[index]) else 0.0
        loss = float(losses.iloc[index]) if pd.notna(losses.iloc[index]) else 0.0
        avg_gain = ((avg_gain * (period - 1)) + gain) / period
        avg_loss = ((avg_loss * (period - 1)) + loss) / period
        result.iloc[index] = _rsi_from_averages(avg_gain, avg_loss)


    return result




def _finite_number(value: Any) -> float | None:
    """Convert a value to a finite float, otherwise return None for JSON null."""
    if value is None or pd.isna(value):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None




def _rounded(value: Any, digits: int = 2) -> float | None:
    number = _finite_number(value)
    return round(number, digits) if number is not None else None




def _chart_points(series: pd.Series, step: int = 1, date_format: str = "%d.%m.%y") -> dict[str, list[Any]]:
    clean = pd.to_numeric(series, errors="coerce").dropna().sort_index()
    if clean.empty:
        return {"labels": [], "prices": []}


    step = max(1, int(step))
    sampled = clean.iloc[::step]
    if sampled.index[-1] != clean.index[-1]:
        sampled = pd.concat([sampled, clean.iloc[[-1]]])


    labels = [pd.Timestamp(index).strftime(date_format) for index in sampled.index]
    prices = [round(float(value), 8) for value in sampled]
    return {"labels": labels, "prices": prices}




def build_charts(close: pd.Series) -> dict[str, dict[str, list[Any]]]:
    """Build period charts without filling short windows with older prices."""
    clean = pd.to_numeric(close, errors="coerce").dropna().sort_index()
    if clean.empty:
        return {key: {"labels": [], "prices": []} for key in ("7d", "1m", "3m", "6m", "1y", "2y", "max")}


    end = clean.index[-1]


    def period(days: int | None) -> pd.Series:
        if days is None:
            return clean
        cutoff = end - pd.Timedelta(days=days)
        return clean.loc[clean.index >= cutoff]


    def pack_period(days: int | None, date_format: str) -> dict[str, list[Any]]:
        subset = period(days)
        step = max(1, math.ceil(len(subset) / MAX_CHART_POINTS))
        return _chart_points(subset, step=step, date_format=date_format)


    return {
        "7d": pack_period(7, "%d.%m."),
        "1m": pack_period(30, "%d.%m."),
        "3m": pack_period(90, "%d.%m."),
        "6m": pack_period(180, "%d.%m.%y"),
        "1y": pack_period(365, "%d.%m.%y"),
        "2y": pack_period(730, "%m/%Y"),
        "max": pack_period(None, "%m/%Y"),
    }




def _fallback_comment(data: dict[str, Any]) -> str:
    rsi = data["indicators"]["rsi"]
    rsi_text = f"{rsi:.1f}" if rsi is not None else "nicht verfügbar"
    trend = data["trend"] or "nicht berechenbar"
    return (
        f"{data['name']} notiert bei {data['price']:.2f} {data['currency']}. "
        f"Der RSI (14) beträgt {rsi_text}; der technische Trend ist {trend}."
    )




def get_ai_text(client: Any, data: dict[str, Any]) -> str:
    """Generate a short, metrics-only commentary; safely fall back on errors."""
    fallback = _fallback_comment(data)
    if client is None:
        return fallback


    indicators = data["indicators"]
    prompt_data = {
        "name": data["name"],
        "price": data["price"],
        "currency": data["currency"],
        "change_pct": data["change_pct"],
        "rsi_14": indicators["rsi"],
        "sma_50": indicators["sma_50"],
        "sma_200": indicators["sma_200"],
        "trend": data["trend"],
    }
    prompt = (
        "Schreibe eine kurze, sachliche Einordnung auf Deutsch mit höchstens drei Sätzen. "
        "Nutze ausschließlich die folgenden Kennzahlen. Erfinde keine Nachrichten, Ursachen, "
        "Prognosen oder weiteren Fakten. Gib keine Kauf-, Verkaufs- oder persönliche "
        "Anlageempfehlung. Wenn Werte fehlen, benenne sie als nicht verfügbar. Reiner Text, "
        "kein Markdown.\nKennzahlen: "
        + json.dumps(prompt_data, ensure_ascii=False, allow_nan=False)
    )


    for attempt in range(1, GEMINI_RETRIES + 1):
        try:
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )
            text = " ".join((response.text or "").split()) if response else ""
            if text:
                return text[:700].rstrip()
            LOGGER.warning("Gemini returned an empty response for %s", data["ticker"])
        except Exception as exc:  # Keep a provider failure from breaking market data.
            LOGGER.warning(
                "Gemini request failed for %s (attempt %d/%d): %s",
                data["ticker"], attempt, GEMINI_RETRIES, exc,
            )
        if attempt < GEMINI_RETRIES:
            time.sleep(RETRY_BASE_SECONDS * attempt + random.uniform(0.0, 0.4))


    return fallback




def create_gemini_client() -> Any | None:
    api_key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if not api_key:
        LOGGER.info("GEMINI_API_KEY is not set; using deterministic commentary fallback")
        return None
    if genai is None:
        LOGGER.warning("google-genai is unavailable; using deterministic commentary fallback")
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as exc:
        # Do not print the key or the client configuration.
        LOGGER.warning("Could not initialize Gemini client: %s", exc)
        return None




def download_history(symbol: str) -> pd.DataFrame:
    """Fetch one symbol with bounded retries and a request timeout."""
    last_error: Exception | None = None
    for attempt in range(1, YF_RETRIES + 1):
        try:
            history = yf.Ticker(symbol).history(
                period="max",
                interval="1d",
                auto_adjust=True,
                timeout=YF_TIMEOUT_SECONDS,
                raise_errors=True,
            )
            if history is None or history.empty:
                raise ValueError("empty price history")
            return history
        except Exception as exc:
            last_error = exc
            LOGGER.warning(
                "Price download failed for %s (attempt %d/%d): %s",
                symbol, attempt, YF_RETRIES, exc,
            )
            if attempt < YF_RETRIES:
                delay = RETRY_BASE_SECONDS * (2 ** (attempt - 1)) + random.uniform(0.0, 0.5)
                time.sleep(delay)


    raise RuntimeError(f"Could not download history for {symbol}") from last_error




def _clean_close(history: pd.DataFrame, symbol: str) -> pd.Series:
    if "Close" not in history.columns:
        raise ValueError(f"Close column missing for {symbol}")


    close = history["Close"]
    # Defensive handling in case a provider/library version returns a frame.
    if isinstance(close, pd.DataFrame):
        if close.shape[1] == 0:
            raise ValueError(f"Close data is empty for {symbol}")
        close = close.iloc[:, 0]


    close = pd.to_numeric(close, errors="coerce").dropna()
    close = close.loc[~close.index.duplicated(keep="last")].sort_index()
    close = close[close.map(lambda value: math.isfinite(float(value)) and float(value) > 0)]
    if len(close) < MIN_HISTORY:
        raise ValueError(f"not enough valid observations for {symbol}: {len(close)}")
    return close.astype("float64")




def process_ticker(ticker: dict[str, str], client: Any | None) -> dict[str, Any]:
    symbol = ticker["symbol"]
    history = download_history(symbol)
    close = _clean_close(history, symbol)


    price = float(close.iloc[-1])
    previous = float(close.iloc[-2]) if len(close) >= 2 else None
    change_pct = ((price - previous) / previous * 100.0) if previous else None


    sma_50 = close.rolling(window=50, min_periods=50).mean().iloc[-1] if len(close) >= 50 else None
    sma_200 = close.rolling(window=200, min_periods=200).mean().iloc[-1] if len(close) >= 200 else None
    rsi_series = calc_rsi(close, RSI_PERIOD)
    rsi = _finite_number(rsi_series.iloc[-1])
    sma_50 = _finite_number(sma_50)
    sma_200 = _finite_number(sma_200)


    if sma_50 is None or sma_200 is None:
        trend = None
    elif price > sma_50 and sma_50 >= sma_200:
        trend = "Bullish"
    elif price < sma_50 and sma_50 < sma_200:
        trend = "Bearish"
    else:
        trend = "Neutral"


    data_as_of = pd.Timestamp(close.index[-1]).isoformat()
    item: dict[str, Any] = {
        "ticker": symbol,
        "name": ticker["name"],
        "currency": ticker["currency"],
        "price": round(price, 8),
        "change_pct": _rounded(change_pct, 4),
        "trend": trend,
        "data_as_of": data_as_of,
        "price_basis": "auto_adjusted_close",
        "indicators": {
            "rsi": _rounded(rsi, 2),
            "sma_50": _rounded(sma_50, 8),
            "sma_200": _rounded(sma_200, 8),
        },
        "charts": build_charts(close),
    }
    item["ai_commentary"] = get_ai_text(client, item)
    return item




def validate_payload(payload: dict[str, Any]) -> None:
    stocks = payload.get("stocks")
    if not isinstance(stocks, list) or not stocks:
        raise ValueError("Refusing to publish an empty stocks list")


    for item in stocks:
        if not isinstance(item, dict):
            raise ValueError("Invalid stock record")
        for required in ("ticker", "name", "currency", "price", "indicators", "charts"):
            if required not in item:
                raise ValueError(f"Required field missing: {required}")
        price = _finite_number(item["price"])
        if price is None or price <= 0:
            raise ValueError(f"Invalid price for {item.get('ticker', 'unknown')}")
        # Fail before writing if any NaN/Infinity slipped into nested data.
        json.dumps(item, ensure_ascii=False, allow_nan=False)




def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write to a temporary file in the destination directory, then replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()




def main() -> None:
    configure_logging()
    client = create_gemini_client()
    generated_at = datetime.now(timezone.utc)
    stocks: list[dict[str, Any]] = []
    failed_symbols: list[str] = []


    for index, ticker in enumerate(TICKERS):
        symbol = ticker["symbol"]
        try:
            stocks.append(process_ticker(ticker, client))
            LOGGER.info("Processed %s", symbol)
        except Exception as exc:
            failed_symbols.append(symbol)
            LOGGER.exception("Skipping %s after processing failure: %s", symbol, exc)


        if index < len(TICKERS) - 1:
            time.sleep(SYMBOL_PAUSE_SECONDS + random.uniform(0.0, 0.3))


    if not stocks:
        # Do not replace the last known good file with an empty dataset.
        raise SystemExit("No symbols were processed successfully; existing JSON was left untouched.")


    timestamp = generated_at.isoformat(timespec="seconds").replace("+00:00", "Z")
    payload: dict[str, Any] = {
        "schema_version": 1,
        "generated_at": timestamp,
        "last_updated": generated_at.strftime("%d.%m.%Y %H:%M UTC"),
        "stocks": stocks,
        "failed_symbols": failed_symbols,
    }
    validate_payload(payload)
    atomic_write_json(OUTPUT_PATH, payload)
    LOGGER.info(
        "Published %d symbols to %s (%d failed)",
        len(stocks), OUTPUT_PATH, len(failed_symbols),
    )




if __name__ == "__main__":
    main()

