# GIC Holdings Tracker

A local Streamlit terminal for U.S. stocks, benchmark funds and portfolio P&L. It opens on 20 flagship symbols. Search by ticker or company across Nasdaq, NYSE and S&P 500 listings. The sidebar starts with 14 editable example positions.

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

## Opening animation

Place an exported clip at `assets/gic-opening.mp4` or `assets/gic-opening.webm` to play it during startup. Streamlit serves the file locally and plays it muted. The built-in opening plays when the clip is missing or cannot load, and the splash dismisses automatically.

## Connect market data and the Co-Pilot

1. Create a free Finnhub account and copy your API key from the dashboard. [Finnhub dashboard](https://finnhub.io/dashboard)
2. Open the sidebar, enter the admin password under **API connections**, and select **Unlock Admin Panel**. Paste the key into **Finnhub API Key** and select **Save keys**. Live prices appear in the watchlist and chart header as quotes arrive.
3. To use the GPT-4o mini Co-Pilot, enter an **OpenAI / AI API Key** in the same panel. Financial requests can send recent chat, learned context and requested portfolio data to OpenAI. Without an OpenAI key, the local quant tools handle financial questions. [OpenAI API keys](https://platform.openai.com/api-keys)
4. Select **Lock Admin Panel** to hide the connection controls. Saved browser overrides continue to serve that session. **Use configured keys** clears those overrides.

For automatic setup, set the environment variables below or put the following entries in a local `.streamlit/secrets.toml`. Environment variables take precedence over the file, and browser overrides take precedence for the current session. Preloaded keys work with the panel locked. Keep credentials out of Git.

```toml
FINNHUB_API_KEY = "your-finnhub-key"
OPENAI_API_KEY = "your-optional-openai-key"
```

## Use the terminal

- Search by ticker or company name, or browse with the exchange filters and pagination. Scroll within the watchlist to see the rest of the page. Select a company row to open its chart and edit its shares and average cost in **Portfolio settings**.
- The ET, UK and KST clocks tick every second. The watchlist checks cached marks every five seconds. Finnhub chart quotes refresh up to every 12 seconds and visible stock quotes every 30 seconds.
- Each sparkline shows five days of hourly closes from Yahoo chart data. The intraday chart uses today’s five-minute bars or five days of 15-minute bars when today’s session has too few observations. It adds a timestamped Finnhub quote when available. **vs SMH** compares daily returns from the same trading date.
- Ask the Co-Pilot about holdings, tickers, macro conditions, headlines, portfolio risk or a price scenario. Learned preferences, risk limits, targets and dated observations live in the browser session. **Export Brief (.md)** downloads the latest answer.

## Reading the numbers

- Live stock prices and daily changes come from Finnhub. Missing keys, zero prices and unavailable quotes display as `--`. Tabs using the same key in one app process share a rolling budget of 58 requests per minute. On a provider throttle, requests pause for at least 60 seconds and respect a longer retry interval. [Finnhub quote API](https://finnhub.io/docs/api/quote)
- The Co-Pilot uses timestamped Finnhub observations for regular and extended-hours analysis. The chart history, sparklines, and benchmark readings use a separate eight-worker pool. Intraday history is cached for 30 seconds. Sparklines and market benchmarks are cached for 60 seconds.
- **Position P&L** uses marked price minus average entry cost, multiplied by shares. Day P&L uses Finnhub’s dollar change for the displayed trading date. Portfolio totals cover the positions with available marks. A single-stock scenario applies the specified move to that holding. The Nasdaq scenario assumes each marked holding moves one-for-one with QQQ.
- The header and scrolling strip share the latest true benchmark readings. Index levels are in points and fund prices are in dollars. The 10-year Treasury yield is a percentage with its daily move in basis points. Hover over a benchmark to see its symbol and observation time.
