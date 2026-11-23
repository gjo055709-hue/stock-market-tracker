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

## Connect market data and the Co-Pilot

1. Create a free Finnhub account and copy your API key from the dashboard. [Finnhub dashboard](https://finnhub.io/dashboard)
2. Open the sidebar, enter the admin password under **API connections**, and select **Unlock Admin Panel**. Paste the key into **Finnhub API Key** and select **Save keys**. **FINNHUB LIVE** appears after the first valid quote.
3. To use the GPT-4o mini Co-Pilot, enter an **OpenAI / AI API Key** in the same panel. Financial requests can send recent chat, learned context and requested portfolio data to OpenAI. Without an OpenAI key, the local quant tools handle financial questions. [OpenAI API keys](https://platform.openai.com/api-keys)
4. Select **Lock Admin Panel** to hide the connection controls. Saved browser overrides continue to serve that session. **Use configured keys** clears those overrides.

For automatic setup, set the environment variables below or put the following entries in a local `.streamlit/secrets.toml`. Environment variables take precedence over the file, and browser overrides take precedence for the current session. Preloaded keys work with the panel locked. Keep credentials out of Git.

```toml
FINNHUB_API_KEY = "your-finnhub-key"
OPENAI_API_KEY = "your-optional-openai-key"
```

## Use the terminal

- Search by ticker or company name, or browse an exchange with the filter pills and pagination. Select a row to open its chart and edit its shares and average cost in **Portfolio settings**.
- The ET, UK and KST clocks tick every second. The table checks cached marks every five seconds. Chart quotes refresh up to every 12 seconds, visible stocks every 30 seconds and the 12 benchmark funds every 60 seconds. The header and ticker strip use the same benchmark observations.
- The chart plots timestamped quotes collected during the browser session. Previous close, day low and day high appear as separate reference points because the quote endpoint supplies no trade times for those levels. **vs SMH** compares daily returns from the same trading date.
- Ask the Co-Pilot about holdings, tickers, macro conditions, headlines, portfolio risk or a price scenario. Learned preferences, risk limits, targets and dated observations live in the browser session. **Export Brief (.md)** downloads the latest answer.

## Reading the numbers

- All market prices come from Finnhub. Missing keys, zero prices and unavailable quotes display as `--`. The app shares an eight-worker pool and coalesces duplicate requests. Tabs using the same key in one app process share a rolling budget of 58 requests per minute. On a provider throttle, requests pause for at least 60 seconds and respect a longer retry interval. [Finnhub quote API](https://finnhub.io/docs/api/quote)
- **REG CLOSE** uses the provider’s previous regular close until the app observes a trade at the scheduled close. The app keeps that observation through failed polls so it can calculate after-hours changes when quotes resume. Extended-hours alerts use trades from the displayed trading date. The quote feed omits volume, so volume ratios and volume-based anomaly scores display as `--`.
- **Position P&L** uses marked price minus average entry cost, multiplied by shares. Day P&L uses Finnhub’s dollar change for the displayed trading date. Portfolio totals cover the positions with available marks. A single-stock scenario applies the specified move to that holding. The Nasdaq scenario assumes each marked holding moves one-for-one with QQQ.
- The strip shows U.S.-listed fund share prices in dollars. For example, IEF is a Treasury bond fund, VIXY holds short-term VIX futures, and EWU and EWY give UK and Korean equity exposure. Hover over a benchmark to see its symbol and quote time.
