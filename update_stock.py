Automatisierte Finanzwebsite
Ich entwickle derzeit eine vollautomatische Finanz-, Aktien- und Kryptowährungs-Website namens "Jahdo". Das Projekt ist darauf ausgelegt, passives Einkommen durch Affiliate-Empfehlungen (z.B. Broker mit 1% Saveback) und digitale Tools zu generieren, ohne manuellen Pflegeaufwand.
Hier sind die technischen Details und der aktuelle Stack:
1. Hosting & Deployment: GitHub Pages (unter eigener Domain, Repository ist public).
2. Automatisierung (Backend): Ein Python-Skript (läuft über GitHub Actions Mo-Fr nach Börsenschluss), das Kursdaten über yfinance lädt, technische Indikatoren (RSI nach Wilder, SMA 50, SMA 200), historische Zeiträume (7T, 1M, 3M, 6M, 1Y, 2Y, MAX) und tägliche KI-Marktkommentare (über die Google Gemini API, Modell gemini-2.5-flash) generiert. Die Ergebnisse werden in einer JSON-Datei (data/latest_analysis.json) gespeichert.
3. Frontend: Eine moderne, dunkle FinTech-Single-Page-Anwendung (HTML5, Tailwind CSS, Plus Jakarta Sans, Chart.js) mit:
   - Kategoriefiltern (Alle, ETF, Aktien, Krypto, Edelmetalle)
   - Einer Live-Suche, mit der Nutzer über die Yahoo Finance API jede beliebige Aktie oder Krypto-Währung (z.B. Krypto mit -USD Suffix, deutsche Aktien mit .DE) weltweit live abrufen können.
   - Einem interaktiven Zinseszins- und Sparplan-Simulator (mit Reglern für Startkapital, monatliche Sparrate, Laufzeit und Rendite).
   - Einem rechtssicheren Footer und integrierten Affiliate-Empfehlungen.
Deine Aufgabe:
Bitte analysiere diesen Projekt-Setup auf folgende Punkte und schlage konkrete Verbesserungen, Optimierungen oder potenzielle Fehlerquellen vor:
1. Performance & Skalierbarkeit: Wie stabil ist der Ansatz, Kursdaten per Frontend-Fetch (über CORS-Proxy) oder per statischem JSON zu laden?
2. Code-Qualität & Robustheit: Gibt es Optimierungspotenziale im Python-Skript (Fehlerbehandlung bei yfinance, Ratenbegrenzung) oder im JavaScript-Code?
3. Monetarisierungs- und UX-Erweiterungen: Welche smarten Features könnten die Conversion-Rate (Affiliate-Klicks) oder den Nutzerwert noch weiter steigern?
Show more

Die Architekturprüfung mit konkreten Verbesserungen und einem priorisierten Umsetzungs-Playbook ist fertig. Sie behandelt Datenquellen und CORS-Proxy, Pipeline und Frontend, Monetarisierung, Risiken sowie sinnvolle Betriebskennzahlen.

Hinweis: Da ich keinen Zugriff auf dein Repository oder den tatsächlichen Code hatte, bewertet sie den beschriebenen Aufbau und ist kein zeilenweises Code-Audit.

Jahdo architektur review

Document

gemini-code-1794087803235.html

HTML file

das ist update stock

Verstanden — ich habe den hochgeladenen Stock-Code konkret geprüft und die Review ergänzt. Die Inline-JavaScript-Syntax ist parsebar; wichtige Funktionsprobleme bleiben aber:

Affiliate-CTA: Der Link zeigt auf #depot statt auf einen Partner. So führt der Klick nicht zum Depot.
Indikatoren: Der Live-RSI ist nicht nach Wilder berechnet; bei kurzer Historie werden Kurswerte als SMA 50/200 ausgegeben.
Datenversprechen: Die Suche ruft Tagesdaten mit maximal zehn Jahren Historie ab. Das belegt weder Echtzeit noch „seit Börsenstart“.
Robustheit: Der Proxy-Fetch prüft HTTP-Status und Antwortstruktur nicht und hat keinen Timeout.
Caching: Der Zeitstempel als Query-Parameter beim JSON-Aufruf verhindert wirksames Browser-/CDN-Caching.

Die aktualisierte Review enthält außerdem konkrete Abhilfen und eine priorisierte Reihenfolge:

Jahdo architektur review

Document

gemini-code-1794087920779.html

HTML file

Verbesere den Code

Die überarbeitete HTML-Version ist fertig. Sie behandelt fehlende oder fehlerhafte Daten sauber, zeigt Kennzahlen nur bei ausreichender Datenlage an und lässt im Simulator auch Verlustszenarien zu. Der Affiliate-CTA bleibt deaktiviert, bis eine geprüfte HTTPS-Partner-URL eingetragen ist; Demo-Kurse werden nicht als echte Marktdaten ausgegeben.

Vor dem Deployment musst du noch die Datenquelle und die Partner-URL konfigurieren. Live-Daten konnte ich ohne deinen tatsächlichen Datensatz nicht testen.

jahdo-verbesserte-version.html

HTML file · 31 KB

mir gefellt die Farben nicht, bitte modernisiere das kompletten Design

Das komplette Design ist jetzt auf ein helles, modernes Fintech-Dashboard umgestellt: warmes Off-White, tiefes Waldgrün und gezielte Limetten-Akzente. Navigation, Karten, Charts, Simulator und Partnerbereich sind visuell darauf abgestimmt und für Mobilgeräte angepasst. Die Daten- und Simulatorfunktionen bleiben erhalten.

Die aktualisierte Version ist beigefügt.

jahdo-verbesserte-version.html

HTML file · 35 KB

mach die Grunne farbe weg

Erledigt — die grünen Akzente sind durch Indigo und Blau ersetzt; positive Kursbewegungen sind jetzt ebenfalls blau dargestellt. Die aktualisierte Version ist beigefügt.

jahdo-verbesserte-version.html

HTML file · 38 KB

gefelt mir nicht

Verstanden — ich frage kurz nach der gewünschten Richtung, damit ich nicht noch einmal an deinem Geschmack vorbeidesigne.

Ich habe das Design auf ein kompaktes Schwarz-Gold-Dashboard umgestellt – inklusive goldener Kurslinie und goldenen positiven Werten. Die aktualisierte Version ist beigefügt.

jahdo-verbesserte-version.html

HTML file · 40 KB

verbessere den code : import os, json
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

def calc_rsi(s, p=14):
    d = s.diff()
    g = d.where(d > 0, 0.0).ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    l = (-d.where(d < 0, 0.0)).ewm(alpha=1/p, min_periods=p, adjust=False).mean()
    return 100 - (100 / (1 + (g / l)))

def get_ai_text(client, d):
    fb = f"{d['name']} notiert bei {d['price']} {d['currency']} (RSI: {d['indicators']['rsi']}, Trend: {d['trend']})."
    if not client:
        return fb
    prompt = f"Kurze deutsche Aktienanalyse (max 3 Sätze, reiner Text) für {d['name']}: Kurs {d['price']} {d['currency']}, RSI {d['indicators']['rsi']}, SMA50 {d['indicators']['sma_50']}, Trend {d['trend']}."
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
            if df.empty or len(df) < 30:
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
                "ticker": t["symbol"], "name": t["name"], "currency": t["currency"],
                "price": round(price, 2), "change_pct": round(chg, 2), "pe_ratio": "-", "trend": trend,
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
Show more

Ich habe die Pipeline überarbeitet. Syntax und RSI-Sonderfälle sind geprüft: nur steigende Kurse ergeben RSI 100, nur fallende 0, konstante 50; bei zu wenig Historie bleibt der RSI nicht verfügbar. Echte Yahoo- und Gemini-Requests habe ich nicht ausgeführt.

Wesentliche Änderungen:

Wilder-RSI mit korrekter Startglättung.
Keine erfundenen Ersatzwerte mehr für fehlende SMA 50/200.
Begrenzte Wiederholungen und Timeouts für Kursabrufe; Gemini-Fehler verhindern nicht den Datenlauf.
JSON-Validierung und atomare Veröffentlichung; bei komplett fehlgeschlagenem Lauf bleibt die letzte Datei unangetastet.
UTC-Zeitstempel und Datenstand je Symbol.

Vor dem Einbau:GEMINI_API_KEY als GitHub Actions Secret setzen und prüfen, dass das Frontend fehlende RSI-/SMA-Werte als „nicht verfügbar“ darstellen kann.

jahdo_market_pipeline.py

PY file · 15 KB

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
kursverlauf ist sichtbar nur für 7 Tage?

Nein. Das überarbeitete Skript erzeugt 7T, 1M, 3M, 6M, 1J, 2J und MAX. Die Begrenzung auf höchstens 180 Punkte pro Zeitraum reduziert nur die Chart-Dichte, nicht die Zeitspanne.

Wenn alle Ansichten trotzdem nur sieben Tage zeigen, prüfe:

In data/latest_analysis.json unter stocks[0].charts müssen auch 1m, 3m usw. vorhanden sein und jeweils längere Datumsreihen enthalten.
Prüfe, ob GitHub Actions die neu erzeugte JSON-Datei tatsächlich veröffentlicht hat.
Stelle sicher, dass die Buttons im Frontend dieselben Schlüssel verwenden: 7d, 1m, 3m, 6m, 1y, 2y, max.

Wenn du mir den charts-Abschnitt aus der JSON-Datei schickst, kann ich erkennen, ob die Ursache in der Datenpipeline oder im Frontend liegt.

last.txt

Text file

{
"schema_version": 1,
"generated_at": "2026-11-07T22:16:49Z",
"last_updated": "07.11.2026 22:16 UTC",
"stocks": [
{
"ticker": "VWCE.DE",
"name": "Vanguard FTSE All-World ETF",
"currency": "EUR",
"price": 165.83999634,
"change_pct": -0.0843,
"trend": "Neutral",
"data_as_of": "2026-11-06T00:00:00+01:00",
"price_basis": "auto_adjusted_close",
"indicators": {
"rsi": 37.2,
"sma_50": 169.36439972,
"sma_200": 160.14060005
},
"charts": {

Die JSON ist nicht auf sieben Tage begrenzt. Für VWCE enthält sie mehrere Zeiträume: 7d hat 6 Kurspunkte, 1m reicht vom 08.10. bis 06.11., 3m vom 10.08. bis 06.11.; außerdem sind 6m, 1y, 2y und max vorhanden. max beginnt 2019.

Damit liegt der Fehler wahrscheinlich im Frontend oder Deployment, nicht in der Datenpipeline. In der überarbeiteten HTML-Version ist 1m der Standardzeitraum. Prüfe, ob die veröffentlichte Seite wirklich diese HTML-Version lädt und ob ein Klick auf „1M“ den Zeitraum auf den Schlüssel 1m setzt und den Chart neu rendert. Im Browser-Netzwerk-Tab kannst du außerdem kontrollieren, ob die Seite genau die JSON-Datei lädt, die du geschickt hast.

ja nur 1 monat

Die Startansicht ist jetzt auf MAX gesetzt, damit beim Öffnen die gesamte verfügbare Historie erscheint. Die Zeiträume von 7 Tagen bis 2 Jahren bleiben auswählbar. Die aktualisierte Seite ist beigefügt; veröffentliche sie erneut, damit die Änderung live sichtbar wird.

jahdo-verbesserte-version.html

HTML file · 40 KB

okay jetzt funktioniert, aber verbessere den kompleten HTML: 1. zu wenig Stocks; 2.Unotig gross Marktaden analyse; 3. Verbessere den Symulator 4. Analysiere den Chart

Die Überarbeitung ist fertig. Wichtig: Für die zusätzlichen Basiswerte muss auch die Python-Pipeline ersetzt und danach erneut ausgeführt werden; die HTML-Seite zeigt nur Werte, die in der erzeugten JSON-Datei stehen.

Mehr Assets: Die Pipeline ist von 5 auf 24 Einträge erweitert: 16 Aktien, 4 ETFs, 2 Kryptowährungen und 2 Edelmetall-Futures. Suche und Kategorien filtern die geladenen Daten. Die Gold-/Silberwerte sind Futures, keine Spotpreise.
Kompaktere Marktanalyse: Weniger Platz für die Auswahl; Suche, Kategorie-Filter und Asset-Liste sind gebündelt.
Simulator: Gebühren- und Inflationsannahme ergänzt; angezeigt werden Einzahlungen, Wertänderung nach Gebühren, nominaler Endwert und Kaufkraft in heutigen Euro. Gebühren werden vereinfacht als jährlicher Renditeabschlag modelliert; Steuern sind nicht enthalten.
Chartanalyse: Zeigt Performance, Hoch/Tief, größten Rückgang vom Hoch sowie eine sachliche Einordnung von Trend und RSI. Das ist keine Prognose oder Anlageempfehlung.

Nächste Schritte: HTML und Pipeline übernehmen, dann den GitHub-Action-Lauf starten und die aktualisierte JSON-Datei veröffentlichen. Mit gesetztem Gemini-Schlüssel sind bis zu 24 KI-Aufrufe pro Lauf möglich. Python-Syntax sowie RSI-Sonderfälle und Chart-Zeiträume wurden geprüft; externe Datenabrufe wurden nicht ausgeführt.

Überarbeitete HTML-Seite
Erweiterte Python-Pipeline

jahdo-verbesserte-version.html

HTML file · 51 KB

jahdo_market_pipeline.py

PY file · 17 KB

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
wo kommt jado pipeline

Die Pipeline-Datei kommt ins Repository, am besten nach scripts/. Der Workflow liegt separat im GitHub-Actions-Ordner; die erzeugte JSON-Datei bleibt unter data/.

Copy
text
dein-repository/
├── index.html
├── requirements.txt
├── data/
│   └── latest_analysis.json       # wird von der Pipeline erzeugt
├── scripts/
│   └── jahdo_market_pipeline.py    # die Pipeline
└── .github/
    └── workflows/
        └── update-market-data.yml # startet die Pipeline

Wichtig: Das Skript schreibt standardmäßig relativ zum Repository-Hauptverzeichnis nach data/latest_analysis.json. Im Workflow also von dort aus starten:

Copy
yaml
- run: python scripts/jahdo_market_pipeline.py

Lege in requirements.txt die Abhängigkeiten pandas, yfinance und google-genai ab; pinne die getesteten Versionen, damit spätere Updates den Workflow nicht unerwartet brechen.

Falls Gemini-Kommentare aktiv sein sollen, speichere GEMINI_API_KEY unter GitHub → Settings → Secrets and variables → Actions als Repository Secret. Nicht in die Datei oder den Workflow-Text schreiben. Ohne Schlüssel läuft die Pipeline mit dem Text-Fallback.

Danach: Workflow starten und prüfen, ob data/latest_analysis.json aktualisiert und veröffentlicht wird. Bei GitHub Pages aus dem Repository-Branch muss der Commit der JSON-Datei auf diesem Branch landen. Wenn Pages über einen separaten Deployment-Workflow gebaut wird, muss dieser die aktualisierte Datei ebenfalls übernehmen.

schon wieder Marktdanetklar sehen zu gross, lieber kleiner Machen und dan top 5 Stocks auflisten

Erledigt: Die große „Marktdaten klar sehen“-Überschrift ist kleiner, und direkt darunter listet die Seite die Top 5 Aktien nach Tagesperformance auf — ohne dies als Anlageempfehlung darzustellen. Außerdem sind Suche und Kategorien für die Asset-Auswahl, der kompaktere Analysebereich, der erweiterte Simulator und die Chart-Einordnung enthalten.

Die Top-5-Liste nutzt die Daten aus der JSON-Datei. Führe die aktualisierte Pipeline einmal aus, damit die zusätzlichen Werte geladen werden. Bis dahin kann die Liste weniger als fünf Aktien anzeigen.

Aktualisierte Jahdo-Seite
Aktualisierte Datenpipeline

jahdo-verbesserte-version.html

HTML file · 56 KB

jahdo_market_pipeline.py

PY file · 17 KB

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
ich will alle stocks haben

Erledigt: Die Übersicht zeigt jetzt alle Aktien aus dem Datensatz, nach Tagesperformance sortiert — nicht mehr nur fünf. Die Pipeline-Watchlist enthält 16 Aktien sowie ETFs, Kryptowährungen und Edelmetall-Futures.

Damit alle Aktien erscheinen, musst du die aktualisierte Pipeline ausführen und die neue JSON-Datei veröffentlichen. Bis dahin zeigt die Seite nur die Aktien, die in deiner aktuellen JSON-Datei stehen. „Alle“ meint hier die Watchlist, nicht sämtliche weltweit börsennotierten Aktien.

Aktualisierte Jahdo-Seite
Datenpipeline für die erweiterte Watchlist

jahdo-verbesserte-version.html

HTML file · 56 KB

jahdo_market_pipeline.py

PY file · 17 KB

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
ich will 100 stocks haben

Erledigt: Die Watchlist enthält jetzt 100 ausgewählte Aktien. Die Seite zeigt alle Aktien aus der JSON-Datei in einer scrollbaren Liste, sortiert nach Tagesperformance; Suche und Kategorie-Filter bleiben verfügbar. Zusätzlich bleiben 4 ETFs, 2 Kryptowährungen und 2 Edelmetall-Futures enthalten. Es ist eine kuratierte Auswahl, nicht jede weltweit börsennotierte Aktie.

Nächste Schritte

Beide aktualisierten Dateien ins Repository übernehmen.
GitHub Action ausführen, damit die JSON-Datei mit den 100 Aktien neu erzeugt wird.
Die aktualisierte JSON-Datei veröffentlichen.

Die Pipeline erstellt standardmäßig höchstens 10 KI-Kommentare pro Lauf; für die übrigen Werte erzeugt sie Kennzahlen-Kurztexte. Für KI-Kommentare zu allen 100 Aktien kannst du in der Action MAX_AI_COMMENTARIES_PER_RUN: "100" setzen.

Aktualisierte HTML-Seite
Pipeline mit 100 Aktien

Die Python-Syntax, die Anzahl der Symbole und doppelte Ticker wurden geprüft. Den Live-Abruf der Kurse habe ich nicht ausgeführt.

jahdo-verbesserte-version.html

HTML file · 56 KB

jahdo_market_pipeline.py

PY file · 25 KB

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
mach den Simulator kleiner, und erstelle den Design wie ein Spiderman netz die pulsiert

Der Simulator ist jetzt kompakter: Auf größeren Bildschirmen stehen Eingaben und Ergebnisse nebeneinander. Dazu kommt ein dezentes, pulsierendes Spinnennetz-Muster im Hintergrund; bei aktivierter Einstellung für reduzierte Bewegung bleibt die Animation stehen.

Playbook: Ersetze die bisherige HTML-Datei durch die aktualisierte Version und veröffentliche die Seite erneut. Den echten Kursdatenabruf habe ich nicht ausgeführt.

jahdo-verbesserte-version.html

HTML file · 59 KB

die Netz auch als Design komplete Website

Erledigt: Das Spinnennetz-Design zieht sich jetzt als dezenter, pulsierender Hintergrund über die gesamte Website und bleibt auch im Simulator sichtbar. Bei aktivierter Einstellung „Bewegung reduzieren“ wird die Animation angehalten.

Playbook

Ersetze die bisherige HTML-Datei durch die aktualisierte Version.
Veröffentliche bzw. deploye die Seite erneut.
Prüfe Desktop und Mobilansicht sowie die reduzierte Bewegungsoption.

jahdo-verbesserte-version.html

HTML file · 60 KB

sehe nur 4 stocks

Der Screenshot zeigt nur AAPL, NVDA, MSFT und SAP.DE, weil die veröffentlichte Website noch eine alte data/latest_analysis.json lädt. Die HTML-Datei zeigt die Werte aus dieser Datendatei an; sie erzeugt selbst keine neuen Aktien- oder Kursdaten. Die Pipeline enthält zwar 100 ausgewählte Aktien, wurde aber noch nicht ausgeführt und veröffentlicht.

Playbook

Übernimm die aktualisierte 
Pipeline mit 100 Aktien
 ins Repository.
Führe die Pipeline im Repository aus – oder starte den entsprechenden GitHub-Actions-Workflow.
Prüfe die neu erzeugte data/latest_analysis.json. Sie sollte 100 Einträge mit cat: "Aktien" enthalten. Wenn weniger vorhanden sind, prüfe failed_symbols.
Veröffentliche die neue JSON-Datei zusammen mit der HTML-Seite und lade die Website mit einem harten Refresh neu.

Wenn die JSON-Datei bereits 100 Aktien enthält und die Seite trotzdem vier zeigt, schick mir bitte diese Datei oder die veröffentlichte Seiten-URL; dann lässt sich prüfen, ob die Seite noch eine alte Datenquelle lädt.

wo ist die

Die JSON-Datei liegt im Repository unter data/latest_analysis.json. Sie wurde hier noch nicht erzeugt oder mitgeliefert, weil die Pipeline nicht ausgeführt wurde. Nach dem Lauf sollte sie im Ordner data erscheinen.

1
 document

wo ist die 

jahdo_market_pipeline.py

PY file

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
    # ETFs
    {"symbol": "VWCE.DE", "name": "Vanguard FTSE All-World ETF", "currency": "EUR", "cat": "ETF"},
    {"symbol": "IWDA.AS", "name": "iShares Core MSCI World UCITS ETF", "currency": "EUR", "cat": "ETF"},
    {"symbol": "VOO", "name": "Vanguard S&P 500 ETF", "currency": "USD", "cat": "ETF"},
    {"symbol": "QQQ", "name": "Invesco QQQ Trust", "currency": "USD", "cat": "ETF"},
    # 100 ausgewählte US- und internationale Aktien; keine Rangliste oder Empfehlung.
    # US-Unternehmen (80)
    {"symbol": "AAPL", "name": "Apple Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MSFT", "name": "Microsoft Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "NVDA", "name": "NVIDIA Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "GOOGL", "name": "Alphabet Inc. Class A", "currency": "USD", "cat": "Aktien"},
    {"symbol": "META", "name": "Meta Platforms Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BRK-B", "name": "Berkshire Hathaway Inc. Class B", "currency": "USD", "cat": "Aktien"},
    {"symbol": "AVGO", "name": "Broadcom Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "LLY", "name": "Eli Lilly and Company", "currency": "USD", "cat": "Aktien"},
    {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "V", "name": "Visa Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MA", "name": "Mastercard Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "WMT", "name": "Walmart Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "XOM", "name": "Exxon Mobil Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ORCL", "name": "Oracle Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "COST", "name": "Costco Wholesale Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "JNJ", "name": "Johnson & Johnson", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ABBV", "name": "AbbVie Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "NFLX", "name": "Netflix Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "PG", "name": "Procter & Gamble Co.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BAC", "name": "Bank of America Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "KO", "name": "The Coca-Cola Company", "currency": "USD", "cat": "Aktien"},
    {"symbol": "HD", "name": "The Home Depot Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "GE", "name": "GE Aerospace", "currency": "USD", "cat": "Aktien"},
    {"symbol": "CVX", "name": "Chevron Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MRK", "name": "Merck & Co. Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "CRM", "name": "Salesforce Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "PEP", "name": "PepsiCo Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "CAT", "name": "Caterpillar Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "CSCO", "name": "Cisco Systems Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "IBM", "name": "International Business Machines Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MCD", "name": "McDonald's Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "LIN", "name": "Linde plc", "currency": "USD", "cat": "Aktien"},
    {"symbol": "NOW", "name": "ServiceNow Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "AMGN", "name": "Amgen Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "GS", "name": "The Goldman Sachs Group Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "RTX", "name": "RTX Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "DIS", "name": "The Walt Disney Company", "currency": "USD", "cat": "Aktien"},
    {"symbol": "QCOM", "name": "QUALCOMM Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TMO", "name": "Thermo Fisher Scientific Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TXN", "name": "Texas Instruments Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ABT", "name": "Abbott Laboratories", "currency": "USD", "cat": "Aktien"},
    {"symbol": "PM", "name": "Philip Morris International Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "VZ", "name": "Verizon Communications Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SPGI", "name": "S&P Global Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ISRG", "name": "Intuitive Surgical Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "C", "name": "Citigroup Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "INTU", "name": "Intuit Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MU", "name": "Micron Technology Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "AMAT", "name": "Applied Materials Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "PFE", "name": "Pfizer Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BKNG", "name": "Booking Holdings Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ADI", "name": "Analog Devices Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TJX", "name": "The TJX Companies Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "UNH", "name": "UnitedHealth Group Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "NEE", "name": "NextEra Energy Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BA", "name": "The Boeing Company", "currency": "USD", "cat": "Aktien"},
    {"symbol": "DE", "name": "Deere & Company", "currency": "USD", "cat": "Aktien"},
    {"symbol": "UPS", "name": "United Parcel Service Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "LRCX", "name": "Lam Research Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BLK", "name": "BlackRock Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SCHW", "name": "The Charles Schwab Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "PANW", "name": "Palo Alto Networks Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TGT", "name": "Target Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MDT", "name": "Medtronic plc", "currency": "USD", "cat": "Aktien"},
    {"symbol": "PLTR", "name": "Palantir Technologies Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ANET", "name": "Arista Networks Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SYK", "name": "Stryker Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "COP", "name": "ConocoPhillips", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SO", "name": "The Southern Company", "currency": "USD", "cat": "Aktien"},
    {"symbol": "DHR", "name": "Danaher Corp.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "GILD", "name": "Gilead Sciences Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "CME", "name": "CME Group Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ICE", "name": "Intercontinental Exchange Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ADP", "name": "Automatic Data Processing Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "MMC", "name": "Marsh & McLennan Companies Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "FI", "name": "Fiserv Inc.", "currency": "USD", "cat": "Aktien"},
    {"symbol": "ETN", "name": "Eaton Corp. plc", "currency": "USD", "cat": "Aktien"},
    {"symbol": "APH", "name": "Amphenol Corp.", "currency": "USD", "cat": "Aktien"},
    # Internationale Unternehmen (20; ADRs in USD, soweit angegeben)
    {"symbol": "SAP.DE", "name": "SAP SE", "currency": "EUR", "cat": "Aktien"},
    {"symbol": "ASML.AS", "name": "ASML Holding N.V.", "currency": "EUR", "cat": "Aktien"},
    {"symbol": "SIE.DE", "name": "Siemens AG", "currency": "EUR", "cat": "Aktien"},
    {"symbol": "ALV.DE", "name": "Allianz SE", "currency": "EUR", "cat": "Aktien"},
    {"symbol": "MC.PA", "name": "LVMH Moet Hennessy Louis Vuitton SE", "currency": "EUR", "cat": "Aktien"},
    {"symbol": "NESN.SW", "name": "Nestle S.A.", "currency": "CHF", "cat": "Aktien"},
    {"symbol": "NOVO-B.CO", "name": "Novo Nordisk A/S Class B", "currency": "DKK", "cat": "Aktien"},
    {"symbol": "AZN", "name": "AstraZeneca PLC ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TSM", "name": "Taiwan Semiconductor Manufacturing Co. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "INFY", "name": "Infosys Ltd. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "TM", "name": "Toyota Motor Corp. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SONY", "name": "Sony Group Corp. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BABA", "name": "Alibaba Group Holding Ltd. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "HDB", "name": "HDFC Bank Ltd. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "NVS", "name": "Novartis AG ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BHP", "name": "BHP Group Ltd. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "SHEL", "name": "Shell plc ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "BP", "name": "BP p.l.c. ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "RELX", "name": "RELX PLC ADR", "currency": "USD", "cat": "Aktien"},
    {"symbol": "UL", "name": "Unilever PLC ADR", "currency": "USD", "cat": "Aktien"},
    # Krypto
    {"symbol": "BTC-USD", "name": "Bitcoin", "currency": "USD", "cat": "Krypto"},
    {"symbol": "ETH-USD", "name": "Ethereum", "currency": "USD", "cat": "Krypto"},
    # Edelmetall-Futures, keine Spotpreise
    {"symbol": "GC=F", "name": "Gold-Future (COMEX)", "currency": "USD", "cat": "Edelmetalle"},
    {"symbol": "SI=F", "name": "Silber-Future (COMEX)", "currency": "USD", "cat": "Edelmetalle"},
]


OUTPUT_PATH = Path(os.environ.get("OUTPUT_PATH", "data/latest_analysis.json"))
GEMINI_MODEL = "gemini-2.5-flash"
RSI_PERIOD = 14
MIN_HISTORY = RSI_PERIOD + 1
MAX_CHART_POINTS = 180
YF_TIMEOUT_SECONDS = 20
YF_RETRIES = 3
GEMINI_RETRIES = 2
MAX_AI_COMMENTARIES_PER_RUN = max(0, int(os.environ.get("MAX_AI_COMMENTARIES_PER_RUN", "10")))
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




def get_ai_text(client: Any, data: dict[str, Any]) -> tuple[str, bool]:
    """Generate a short, metrics-only commentary; safely fall back on errors."""
    fallback = _fallback_comment(data)
    if client is None:
        return fallback, False


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
                return text[:700].rstrip(), True
            LOGGER.warning("Gemini returned an empty response for %s", data["ticker"])
        except Exception as exc:  # Keep a provider failure from breaking market data.
            LOGGER.warning(
                "Gemini request failed for %s (attempt %d/%d): %s",
                data["ticker"], attempt, GEMINI_RETRIES, exc,
            )
        if attempt < GEMINI_RETRIES:
            time.sleep(RETRY_BASE_SECONDS * attempt + random.uniform(0.0, 0.4))


    return fallback, False




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
        "cat": ticker["cat"],
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
    item["ai_commentary"], ai_used = get_ai_text(client, item)
    item["commentary_type"] = "ai" if ai_used else "metrics"
    return item




def validate_payload(payload: dict[str, Any]) -> None:
    stocks = payload.get("stocks")
    if not isinstance(stocks, list) or not stocks:
        raise ValueError("Refusing to publish an empty stocks list")


    for item in stocks:
        if not isinstance(item, dict):
            raise ValueError("Invalid stock record")
        for required in ("ticker", "name", "currency", "cat", "price", "indicators", "charts"):
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
    ai_targets_used = 0
    ai_successes = 0


    for index, ticker in enumerate(TICKERS):
        symbol = ticker["symbol"]
        ticker_client = None
        if (
            client is not None
            and ticker.get("cat") == "Aktien"
            and ai_targets_used < MAX_AI_COMMENTARIES_PER_RUN
        ):
            ticker_client = client
            ai_targets_used += 1


        try:
            item = process_ticker(ticker, ticker_client)
            stocks.append(item)
            if item.get("commentary_type") == "ai":
                ai_successes += 1
            LOGGER.info("Processed %s", symbol)
        except Exception as exc:
            if ticker_client is not None:
                ai_targets_used -= 1
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
        "ai_commentary_limit_per_run": MAX_AI_COMMENTARIES_PER_RUN,
        "ai_commentaries_generated": ai_successes,
    }
    validate_payload(payload)
    atomic_write_json(OUTPUT_PATH, payload)
    LOGGER.info(
        "Published %d symbols to %s (%d failed; %d AI commentaries)",
        len(stocks), OUTPUT_PATH, len(failed_symbols), ai_successes,
    )




if __name__ == "__main__":
    main()

