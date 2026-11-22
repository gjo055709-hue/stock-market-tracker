# GIC Holdings Tracker

A standalone Streamlit terminal for U.S. AI equities, macro conditions, and portfolio P&L. The default watchlist contains NVDA, MSFT, GOOGL, META, AMD, AVGO, TSM, PLTR, ARM, MU, SMCI, CRM, ORCL, and SMH. The example share counts and entry costs are illustrative.

## Install and run

Use Python 3.12. Open a terminal in the repository directory and run the commands for your platform.

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run gic_holdings_tracker.py --server.address 127.0.0.1
```

**macOS or Linux**

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m streamlit run gic_holdings_tracker.py --server.address 127.0.0.1
```

Open [localhost:8501](http://localhost:8501) if your browser does not open automatically. Use normal browser zoom on a 1080p display. Press **Ctrl+C** in the terminal to stop the server.

## Optional API keys

The dashboard works without keys. It uses `yfinance` for recent data and switches to labeled simulation when data is unavailable. To configure optional providers, set the environment variables shown below or add the keys you want to use to `.streamlit/secrets.toml` in the repository root.

```toml
APCA_API_KEY_ID = "your-alpaca-key-id"
APCA_API_SECRET_KEY = "your-alpaca-secret"
OPENAI_API_KEY = "your-openai-key"
```

- Generate Alpaca credentials in its **Paper Trading** dashboard. The sidebar offers delayed **SIP** for broader coverage and real-time **IEX** for trades on one exchange. The macro benchmarks still come from `yfinance`. [Alpaca market data FAQ](https://docs.alpaca.markets/docs/market-data-faq)
- The GPT‑4o mini Co-Pilot uses an OpenAI API key with model access and can incur charges. Paste a key into the sidebar’s **OpenAI API key** password field to override the configured key for the browser session. Financial requests can send recent conversation, learned context, and requested tool outputs, including portfolio figures, to OpenAI. The local engine takes over if OpenAI is unavailable or turned off. [OpenAI API keys](https://platform.openai.com/api-keys)

Environment variables take precedence for each key. Keep the secrets file out of Git and restart the app after changing credentials.

## Use the terminal

- Open **Portfolio settings** from the top-left sidebar button. Select a ticker to edit its shares or average cost, or select **Add ticker…**. A zero-share position stays on the watchlist. Edits and chat are kept for the current browser session.
- Select a holdings row to change the intraday chart. Enable **vs SMH** to compare each holding’s return since the prior regular close with SMH’s return, in percentage points. The comparison skips holdings when their marks and SMH’s marks mix live and simulated prices.
- The ET, UK, and KST clocks and market panels refresh every second. **Live Sim** generates synthetic ticks even when the exchange is closed. With Live Sim off, weekends and holidays show the latest completed trading date and its available regular and after-hours prices.
- Ask about any ticker, the macro regime, news, or your portfolio, or use **Macro Impact**, **Top AI Movers**, or **Portfolio P&L**. The Co-Pilot remembers financial preferences, risk limits, targets, and ticker observations in the current session. **Export Brief (.md)** downloads the latest question, answer, snapshot time, and tools used.

## Data and calculations

- One cached `yfinance.download` call requests five days of one-minute holdings and macro bars with extended hours. Live feed requests are cached for 10 seconds. A separate cached daily-history batch supplies the 20-session volume baseline and macro correlations. Downloads run in the background.
- Standard Eastern Time sessions are pre-market 04:00–09:30, regular 09:30–16:00, and after-hours 16:00–20:00. The NYSE calendar handles holidays and early regular closes. Pre-market and regular changes use the prior regular close. After-hours compares with the final available regular trade-bar close. A dash indicates an unavailable value.
- The volume ratio uses current regular-session shares divided by the average for the prior 20 completed sessions. The anomaly score combines >1.8× volume, >±3% extended-hours moves, volume Z-scores, and an Isolation Forest when there are enough comparable observations.
- **Position P&L** is the current marked price minus average entry cost, multiplied by shares. **Day P&L** compares with the prior regular close. After-hours P&L compares with the same day’s regular close. The Co-Pilot ranks contributors and detractors by day P&L and reports how many positions used simulated marks. A single-ticker scenario holds other marks constant. A Nasdaq scenario uses historical sensitivity to QQQ where available and assumes a one-for-one move otherwise.
- The macro regime covers the 10-year Treasury yield, VIX, the dollar index, and QQQ. Catalyst sentiment is a headline heuristic. Unavailable news falls back to labeled sample headlines.
