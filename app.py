"""Local Streamlit dashboard for US equity sessions."""

import math
import os
import random
import re
import zlib
from datetime import datetime, time, timedelta
from html import escape

import exchange_calendars as calendars
import pandas as pd
import plotly.graph_objects as go
import pytz
import requests
import streamlit as st
from plotly.subplots import make_subplots

ET = pytz.timezone("America/New_York")
NYSE = calendars.get_calendar("XNYS")
WATCHLIST = {
    "NVDA": ("NVIDIA", 180), "MSFT": ("Microsoft", 485),
    "GOOGL": ("Alphabet", 205), "META": ("Meta Platforms", 640),
    "AMD": ("Advanced Micro Devices", 158), "AVGO": ("Broadcom", 286),
    "TSM": ("Taiwan Semiconductor", 246), "PLTR": ("Palantir", 98),
    "ARM": ("Arm Holdings", 135), "MU": ("Micron Technology", 126),
    "SMCI": ("Super Micro Computer", 45), "CRM": ("Salesforce", 278),
    "ORCL": ("Oracle", 177), "SMH": ("VanEck Semiconductor ETF", 250),
}
SESSIONS = ("Pre-Market", "Regular Hours", "After-Hours")
COLORS = ("#e8ad5d", "#5de4f2", "#a793ff")
STATES = {
    "Pre-Market": "pre", "Regular Hours": "regular",
    "After-Hours": "after", "Closed": "closed",
}
DEMO_MOVES = {"NVDA": 4.35, "AMD": -3.7, "PLTR": 3.6, "SMCI": -4.4}
BAR_FIELDS = ["t", "c", "v"]
FEED_LABELS = {"sip": "SIP · 15 min delay", "iex": "IEX · real time"}
SIP_DELAY = timedelta(minutes=15)

CSS = """
<style>
:root {
  color-scheme: dark;
  --bg: #0B0E14; --card: #151922; --line: #262C3A;
  --text: #eef2fa; --muted: #a0abc1; --dim: #79869e; --cyan: #5de4f2;
  --gain: #00E676; --loss: #FF5252;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
.stApp, [data-testid="stHeader"] { background: var(--bg); color: var(--text); }
[data-testid="stHeader"] { height: 3rem; background: transparent; }
[data-testid="stHeader"], [data-testid="stHeader"] * { pointer-events: none !important; }
[data-testid="stHeader"] [data-testid="stExpandSidebarButton"] { pointer-events: auto !important; }
[data-testid="stAppDeployButton"], [data-testid="stToolbarActions"],
[data-testid="stDecoration"], #MainMenu, footer { display: none; }
[data-testid="stExpandSidebarButton"] { background: #10252e; border: 1px solid #215460; border-radius: 7px; padding: 3px; }
[data-testid="stExpandSidebarButton"] [data-testid="stIconMaterial"],
[data-testid="stSidebar"] button [data-testid="stIconMaterial"] { color: var(--cyan); }
[data-testid="stSidebar"] { background: #10141d; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] label p, [data-testid="stSidebar"] p { color: var(--text); }
.stMainBlockContainer { max-width: 1760px; padding: 1.05rem 2.4rem .6rem; }
.stMainBlockContainer [data-testid="stVerticalBlock"] { gap: .68rem; }
.stMainBlockContainer [data-testid="stHorizontalBlock"] { gap: .8rem; align-items: start; }
.st-key-terminal_header { padding-left: 1.2rem; border-bottom: 1px solid var(--line); padding-bottom: .6rem; }
.st-key-terminal_header [data-testid="stHorizontalBlock"] { align-items: center; }
.brand, .clockbar, .feed, .section-row, .quote-line, .legend { display: flex; align-items: center; }
.brand { gap: 10px; white-space: nowrap; font-size: 15px; font-weight: 750; letter-spacing: .015em; }
.brand-icon {
  color: var(--cyan); border: 1px solid #215460; border-radius: 8px; width: 31px; height: 31px;
  display: grid; place-items: center; background: #10252e; font-size: 19px;
}
.clockbar { gap: 12px; justify-content: flex-end; white-space: nowrap; }
.session, .feed-tag {
  border-radius: 5px; padding: 4px 8px; font-size: 10px; font-weight: 750;
  letter-spacing: .08em; text-transform: uppercase; white-space: nowrap;
}
.session::before {
  display: inline-block; width: 6px; height: 6px; content: ""; border-radius: 50%;
  background: currentColor; margin-right: 7px; vertical-align: 1px;
}
.session.pre, .session.after { color: #ffc574; background: #302516; border: 1px solid #755225; }
.session.regular { color: var(--cyan); background: #103038; border: 1px solid #22636f; }
.session:not(.closed)::before { box-shadow: 0 0 9px currentColor; }
.session.closed { color: #b5bed0; background: #202632; border: 1px solid #374052; }
.clocks { color: var(--muted); font: 10px var(--mono); }
.clocks b { font-weight: 650; color: var(--text); }
.st-key-terminal_header [data-testid="stWidgetLabel"] p { color: var(--muted); font-size: 12px; white-space: nowrap; }
.st-key-terminal_header [data-baseweb="checkbox"]:has(input:checked) > div { background-color: #4ab5c3; }
.st-key-terminal_header button[kind="secondary"], .st-key-terminal_header button[data-testid="stBaseButton-secondary"] {
  min-height: 31px; padding: .22rem .65rem; color: var(--text); background: var(--card); border-color: var(--line);
}
.st-key-terminal_header button p { font-size: 12px; }
.hero { display: flex; align-items: end; justify-content: space-between; gap: 16px; padding: 4px 0 1px; }
.hero h1 { margin: 0; padding: 0; font-size: clamp(25px, 2.4vw, 38px); letter-spacing: -.048em; line-height: 1.13; color: var(--text); }
.hero p { margin: 5px 0 0; color: var(--muted); font-size: 12px; }
.feed { gap: 8px; }
.feed-tag { background: #122a32; color: var(--cyan); border: 1px solid #244c57; }
.feed-tag.demo { background: #302516; color: #ffc574; border-color: #674a26; }
.feed-tag.error { background: #342027; color: #ff9ca5; border-color: #683842; }
.kpis { display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); gap: .8rem; }
.kpi { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 11px 14px; min-width: 0; }
.kpi-label, .kpi-detail, .panel-sub, .panel-caption, .symbol-name, .footnote { color: var(--muted); }
.kpi-label { font-size: 11px; font-weight: 700; }
.kpi-value { font: 650 25px/1.25 var(--mono); margin: 3px 0; letter-spacing: -.055em; white-space: nowrap; }
.kpi-detail, .panel-caption, .footnote { font-size: 11px; }
.panel, .st-key-intraday {
  background: var(--card); border: 1px solid var(--line); border-radius: 10px;
  min-width: 0;
}
.panel { overflow: hidden; }
.section-row { justify-content: space-between; padding: 12px 14px 10px; gap: 8px; }
.section-row h2, .chart-title h2 { color: var(--text); font-size: 16px; line-height: 1.2; padding: 0; margin: 0; letter-spacing: -.025em; }
.panel-sub { font: 10px var(--mono); white-space: nowrap; }
.table-wrap { overflow-x: auto; }
.watch { width: 100%; border-collapse: collapse; font-size: 12px; font-variant-numeric: tabular-nums; }
.watch th { text-align: right; padding: 7px 11px; color: var(--muted); background: #10141d; font-size: 10px; white-space: nowrap; }
.watch td { height: 33px; padding: 3px 11px; text-align: right; border-top: 1px solid #242a37; white-space: nowrap; font-family: var(--mono); }
.watch th:first-child, .watch td:first-child { text-align: left; padding-left: 14px; }
.watch th:last-child, .watch td:last-child { padding-right: 14px; }
.watch tbody tr:hover { background: #1b2230; }
.watch .symbol { color: #f3f5fb; font-size: 12px; font-weight: 750; }
.symbol-name { font: 11px system-ui, sans-serif; padding-left: 8px; }
.watch .active-col { color: var(--cyan); }
.watch .selected { background: #172a35; }
.watch .selected td:first-child { box-shadow: inset 2px 0 var(--cyan); }
.watch .alert-cell { font-weight: 750; background: #00e67613; text-shadow: 0 0 10px #00e67655; }
.watch .alert-cell.loss { background: #ff525219; text-shadow: 0 0 10px #ff525266; }
.watch .volume, .flat { color: var(--muted); }
.gain { color: var(--gain); }
.loss { color: var(--loss); }
.price { color: var(--text); font-weight: 650; }
.panel-caption { padding: 8px 14px; border-top: 1px solid var(--line); }
.st-key-intraday { padding: 10px 13px 9px; }
.st-key-intraday [data-testid="stVerticalBlock"] { gap: .38rem; }
.st-key-intraday [data-testid="stHorizontalBlock"] { align-items: center; }
.st-key-intraday [data-baseweb="select"] > div {
  background: #10141d; border-color: #343d50; color: var(--text); min-height: 32px;
}
.quote-line { gap: 10px; align-items: baseline; font-family: var(--mono); }
.quote-price { font-size: 27px; font-weight: 650; letter-spacing: -.06em; color: var(--text); }
.quote-line .panel-sub { margin-left: auto; }
.quote-meta { font-size: 12px; }
.legend { gap: 13px; flex-wrap: wrap; color: var(--muted); font-size: 10px; padding: 0 0 1px; }
.legend span::before { content: ""; display: inline-block; width: 8px; height: 8px; margin-right: 5px; border-radius: 2px; background: var(--swatch); }
.legend .legend-ref::before { height: 0; border-top: 1px dashed var(--dim); background: none; vertical-align: 3px; }
.footnote { display: flex; justify-content: space-between; gap: 10px; padding: 1px 2px 0; }
[data-baseweb="popover"] [role="listbox"] { background: #151922; color: var(--text); }
[data-testid="stSidebar"] textarea,
[data-testid="stSidebar"] [data-baseweb="select"] > div { background: #151922; color: var(--text); }
@media (max-width: 1300px) { .symbol-name { display: none; } }
@media (max-width: 950px) {
  .stMainBlockContainer { padding-inline: .9rem; }
  .st-key-terminal_header { padding-left: 2rem; }
  .clockbar { flex-wrap: wrap; gap: 4px; }
  .watch th, .watch td { padding-inline: 5px; }
}
@media (max-width: 640px) {
  .kpis { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .hero, .footnote { flex-wrap: wrap; }
  .clockbar { justify-content: flex-start; }
}
</style>
"""


def session_bounds(day):
    """Return Eastern boundaries for a valid exchange date."""
    return (
        ET.localize(datetime.combine(day, time(4))),
        NYSE.session_open(str(day)).tz_convert(ET),
        NYSE.session_close(str(day)).tz_convert(ET),
        ET.localize(datetime.combine(day, time(20))),
    )


def market_clock(now):
    today = now.date()
    day = NYSE.date_to_session(str(today), direction="previous").date()
    if day == today and now.time() < time(4):
        day = NYSE.previous_session(str(day)).date()
    bounds = session_bounds(day)
    for label, start, end in zip(SESSIONS, bounds, bounds[1:]):
        if start <= now < end:
            return day, label, bounds
    return day, "Closed", bounds


def credentials():
    key_name, secret_name = "APCA_API_KEY_ID", "APCA_API_SECRET_KEY"
    key, secret = os.getenv(key_name), os.getenv(secret_name)
    if key and secret:
        return key, secret
    try:
        key, secret = st.secrets.get(key_name), st.secrets.get(secret_name)
    except (st.errors.StreamlitSecretNotFoundError, ValueError):
        return None
    return (key, secret) if key and secret else None


def bars_frame(records):
    frame = pd.DataFrame.from_records(records, columns=BAR_FIELDS)
    frame["t"] = pd.to_datetime(frame["t"], utc=True, format="mixed").dt.tz_convert(ET)
    frame["c"] = pd.to_numeric(frame["c"])
    frame["v"] = pd.to_numeric(frame["v"])
    frame = frame.dropna(subset=BAR_FIELDS)
    return frame.drop_duplicates("t", keep="last").sort_values("t").set_index("t")


@st.cache_data(ttl=9, show_spinner=False, max_entries=64)
def fetch_bars(symbols, start, end, feed, auth, timeframe="1Min"):
    """Fetch paginated trade bars for the watchlist."""
    endpoint = "https://data.alpaca.markets/v2/stocks/bars"
    headers = {"APCA-API-KEY-ID": auth[0], "APCA-API-SECRET-KEY": auth[1]}
    records = {symbol: [] for symbol in symbols}
    with requests.Session() as http:
        for offset in range(0, len(symbols), 20):
            params = {
                "symbols": ",".join(symbols[offset:offset + 20]),
                "timeframe": timeframe, "feed": feed, "adjustment": "split",
                "start": start.astimezone(pytz.UTC).isoformat(), "limit": 10_000,
            }
            if end is not None:
                params["end"] = end.astimezone(pytz.UTC).isoformat()
            page_tokens = set()
            while True:
                response = http.get(
                    endpoint, params=params, headers=headers, timeout=5, allow_redirects=False,
                )
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict) or "bars" not in payload:
                    raise ValueError("Unexpected Alpaca bars response")
                batch = payload["bars"] or {}
                if not isinstance(batch, dict):
                    raise ValueError("Unexpected Alpaca bars format")
                for symbol, bars in batch.items():
                    if symbol in records:
                        records[symbol].extend(bars)
                token = payload.get("next_page_token")
                if not token:
                    break
                if not isinstance(token, str) or token in page_tokens or len(page_tokens) >= 20:
                    raise ValueError("Invalid or excessive Alpaca pagination")
                page_tokens.add(token)
                params["page_token"] = token
    return {symbol: bars_frame(bars) for symbol, bars in records.items()}


def demo_bars(symbol, bounds, cutoff, prior_close_time):
    """Generate repeatable synthetic prices and volumes for one exchange date."""
    start, regular_open, regular_close, end = bounds
    seed = zlib.crc32(symbol.encode())
    rng = random.Random(seed + start.date().toordinal())
    base = WATCHLIST.get(symbol, ("", 45 + seed % 190))[1] * rng.uniform(.92, 1.08)
    pre_move = DEMO_MOVES.get(symbol, rng.uniform(-2.3, 2.7)) / 100
    regular_move = rng.uniform(-.045, .05)
    after_move = rng.uniform(-.019, .019)
    if symbol in ("META", "ORCL"):
        after_move = .039 if symbol == "META" else -.036
    anchors = [base, base * (1 + pre_move), base * (1 + regular_move)]
    anchors.append(anchors[-1] * (1 + after_move))
    records = [{"t": prior_close_time - timedelta(minutes=1), "c": base, "v": 0}]
    for i, (left, right) in enumerate(zip(bounds, bounds[1:])):
        times = pd.date_range(left, right, freq="5min", inclusive="left")
        for j, timestamp in enumerate(times):
            fraction = j / max(len(times) - 1, 1)
            swing = .009 * math.sin(fraction * 11 + i) * math.sin(fraction * math.pi)
            price = anchors[i] + (anchors[i + 1] - anchors[i]) * fraction
            price *= 1 + swing + rng.uniform(-.003, .003) * math.sin(fraction * math.pi)
            baseline_volume = 12_000 if i == 1 else 1_500
            regular_edges = 1 + 1.9 * abs(fraction - .5) if i == 1 else 1
            volume = int(rng.lognormvariate(0, .53) * baseline_volume * regular_edges)
            if timestamp < min(cutoff, end):
                records.append({"t": timestamp, "c": round(price, 2), "v": volume})
    return bars_frame(records)


def summarize(frame, bounds, previous_bounds, now):
    _, prior_open, prior_end, _ = previous_bounds
    prior = frame.loc[(frame.index >= prior_open) & (frame.index < prior_end), "c"]
    prior_close = float(prior.iloc[-1]) if not prior.empty else None
    segments = [
        frame.loc[(frame.index >= start) & (frame.index < end) & (frame.index <= now)]
        for start, end in zip(bounds, bounds[1:])
    ]
    closes = [float(segment["c"].iloc[-1]) if not segment.empty else None for segment in segments]
    changes = [
        (price / reference - 1) * 100 if price is not None and reference else None
        for price, reference in zip(closes, (prior_close, prior_close, closes[1]))
    ]
    current = pd.concat(segments)
    latest = None if current.empty else current.iloc[-1]
    return {
        "segments": segments, "prior_close": prior_close, "changes": changes,
        "price": None if latest is None else float(latest["c"]),
        "time": None if latest is None else current.index[-1],
        "volume": None if latest is None else int(current["v"].sum()),
        "last_session": next((i for i in (2, 1, 0) if closes[i] is not None), None),
    }


def tone(number):
    if number is None or round(number, 2) == 0:
        return "flat"
    return "gain" if number > 0 else "loss"


def percent(number):
    return "—" if number is None else f"{number:+.2f}%"


def price_text(number):
    return "—" if number is None else f"${number:,.2f}"


def compact(number):
    if number is None:
        return "—"
    if number >= 1_000_000:
        return f"{number / 1_000_000:.2f}M"
    if number >= 1_000:
        return f"{number / 1_000:.1f}K"
    return f"{number:,}"


def display_et(timestamp):
    return timestamp.strftime("%H:%M ET") if timestamp is not None else "—"


def momentum(change):
    return change is not None and round(abs(change), 10) > 3


def chart_for(symbol, stats, bounds, day):
    chart = make_subplots(
        rows=2, cols=1, shared_xaxes=True, row_heights=[.77, .23],
        vertical_spacing=.07,
    )
    for label, color, segment, left, right in zip(
        SESSIONS, COLORS, stats["segments"], bounds, bounds[1:]
    ):
        x = segment.index.tz_localize(None).to_pydatetime().tolist()
        chart.add_vrect(
            x0=pd.Timestamp(left).tz_localize(None), x1=pd.Timestamp(right).tz_localize(None),
            fillcolor=color, opacity=.045, line_width=0, layer="below", row=1, col=1,
        )
        if segment.empty:
            continue
        chart.add_trace(
            go.Scatter(
                x=x, y=segment["c"].tolist(), name=label,
                mode="lines" if len(segment) > 1 else "markers",
                line={"color": color, "width": 2}, marker={"size": 5},
                hovertemplate="%{x|%H:%M} ET · $%{y:,.2f}<extra>%{fullData.name}</extra>",
            ), row=1, col=1,
        )
        chart.add_trace(
            go.Bar(
                x=x, y=segment["v"].tolist(), marker_color=color, opacity=.52, name=label,
                hovertemplate="%{x|%H:%M} ET · %{y:,} shares<extra>%{fullData.name}</extra>",
            ), row=2, col=1,
        )
    if stats["prior_close"] is not None and stats["price"] is not None:
        chart.add_hline(
            y=stats["prior_close"], line_color="#8995ae", line_width=1,
            line_dash="dot", row=1, col=1,
        )
    if stats["price"] is None:
        chart.add_annotation(
            x=.5, y=.66, xref="paper", yref="paper", text="No trades available for this date",
            showarrow=False, font={"color": "#a0abc1", "size": 13},
        )
    chart.update_layout(
        height=416, margin={"l": 5, "r": 7, "t": 13, "b": 4},
        template="plotly_dark", paper_bgcolor="#151922", plot_bgcolor="#10141d",
        font={"family": "monospace", "color": "#a0abc1", "size": 10},
        showlegend=False, hovermode="closest", dragmode="zoom",
        uirevision=f"{symbol}:{day}",
    )
    chart.update_xaxes(
        type="date", range=[pd.Timestamp(bounds[0]).tz_localize(None), pd.Timestamp(bounds[-1]).tz_localize(None)],
        dtick=10_800_000, tick0=pd.Timestamp(bounds[0]).tz_localize(None),
        tickformat="%H:%M", gridcolor="#262c3a", showspikes=True,
        spikecolor="#7b8da9", spikethickness=1, spikemode="across",
    )
    chart.update_yaxes(side="right", gridcolor="#262c3a", zeroline=False, nticks=5, automargin=True)
    chart.update_yaxes(tickprefix="$", row=1, col=1)
    chart.update_yaxes(tickformat="~s", nticks=3, rangemode="tozero", row=2, col=1)
    return chart


def kpi(label, value, detail, color=""):
    return (
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value {color}">{value}</div><div class="kpi-detail">{detail}</div></div>'
    )


def render_kpis(quotes, session):
    traded = [quote for quote in quotes.values() if quote["price"] is not None]
    index = SESSIONS.index(session) if session in SESSIONS else 1
    changes = [quote["changes"][index] for quote in traded if quote["changes"][index] is not None]
    up = sum(change > 0 for change in changes)
    down = sum(change < 0 for change in changes)
    alerts = sum(any(momentum(quote["changes"][i]) for i in (0, 2)) for quote in traded)
    benchmark = quotes.get("SMH")
    smh_change = None if benchmark is None else benchmark["changes"][index]
    cards = [
        kpi("WATCHLIST", f"{len(quotes):02d}", f"{len(traded)} with trades"),
        kpi(
            "MARKET BREADTH", f'<span class="gain">{up} ↑</span> <span class="flat">/</span> <span class="loss">{down} ↓</span>',
            SESSIONS[index],
        ),
        kpi("SMH BENCHMARK", percent(smh_change), SESSIONS[index], tone(smh_change)),
        kpi("EXTENDED MOVERS", f"{alerts:02d}", "Beyond ±3% in pre or after", "gain" if alerts else ""),
    ]
    st.html('<div class="kpis">' + "".join(cards) + "</div>")


def render_watchlist(quotes, selected, session):
    headings = ["Symbol", "Last", "Pre-market", "Regular", "After-hours", "Volume"]
    active_column = SESSIONS.index(session) + 2 if session in SESSIONS else -1
    header = "".join(
        f'<th scope="col" class="{"active-col" if i == active_column else ""}">{label}</th>'
        for i, label in enumerate(headings)
    )
    rows = []
    for symbol, quote in quotes.items():
        cells = []
        for i, change in enumerate(quote["changes"]):
            alert = " alert-cell" if i != 1 and momentum(change) else ""
            cells.append(f'<td class="{tone(change)}{alert}">{percent(change)}</td>')
        name = escape(WATCHLIST.get(symbol, ("",))[0])
        symbol_html = f'<span class="symbol">{escape(symbol)}</span>'
        if name:
            symbol_html += f'<span class="symbol-name">{name}</span>'
        highlight = ' class="selected"' if symbol == selected else ""
        rows.append(
            f'<tr{highlight}><td>{symbol_html}</td>'
            f'<td class="price" title="{display_et(quote["time"])}">{price_text(quote["price"])}</td>'
            f'{"".join(cells)}<td class="volume">{compact(quote["volume"])}</td></tr>'
        )
    st.html(
        '<section class="panel" aria-label="Watchlist"><div class="section-row"><h2>Watchlist</h2>'
        f'<span class="panel-sub">{len(quotes)} SYMBOLS</span></div>'
        '<div class="table-wrap"><table class="watch" aria-label="Watchlist prices and session changes">'
        f'<thead><tr>{header}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
        '<div class="panel-caption">Pre / regular vs. prior close · After vs. regular close</div></section>'
    )


def get_market_data(symbols, bounds, prior_bounds, now, auth, demo, feed):
    refresh_now = st.session_state.pop("refresh_now", False)
    if demo:
        return {symbol: demo_bars(symbol, bounds, now, prior_bounds[2]) for symbol in symbols}, None

    start = prior_bounds[1]
    if feed == "sip":
        cutoff = now - SIP_DELAY - timedelta(seconds=5)
        cutoff -= timedelta(seconds=cutoff.second % 10, microseconds=cutoff.microsecond)
        end = min(bounds[-1], cutoff)
    else:
        end = bounds[-1] if now >= bounds[-1] else None
    request_id = (symbols, start, bounds[0], feed, auth)
    try:
        if refresh_now:
            fetch_bars.clear(symbols, start, end, feed, auth)
        bars = fetch_bars(symbols, start, end, feed, auth)
    except requests.HTTPError as error:
        status = error.response.status_code
        message = {
            401: "Alpaca rejected the credentials.",
            403: f"Alpaca denied {feed.upper()} feed access. Check the account's market data permissions.",
            429: "Alpaca rate limit reached.",
        }.get(status, f"Alpaca returned HTTP {status}.")
    except (requests.RequestException, ValueError):
        message = "The Alpaca feed could not be reached or returned invalid data."
    else:
        st.session_state["last_live_bars"] = (request_id, bars)
        return bars, None
    saved = st.session_state.get("last_live_bars")
    if saved and saved[0] == request_id:
        return saved[1], message + " Showing the last successful update."
    return {symbol: bars_frame([]) for symbol in symbols}, message


def render_chart(symbol, stats, bounds, day):
    index = stats["last_session"]
    change = None if index is None else stats["changes"][index]
    session_label = "No trades" if index is None else SESSIONS[index]
    st.html(
        f'<div class="quote-line"><span class="quote-price">{price_text(stats["price"])}</span>'
        f'<span class="quote-meta {tone(change)}">{percent(change)}</span>'
        f'<span class="panel-sub">{session_label} · {display_et(stats["time"])}</span></div>'
    )
    st.plotly_chart(
        chart_for(symbol, stats, bounds, day), width="stretch", theme=None,
        key="intraday_plot", config={"displaylogo": False, "modeBarButtonsToRemove": ["select2d", "lasso2d"]},
    )
    legend = "".join(
        f'<span style="--swatch:{color}">{label}</span>' for label, color in zip(SESSIONS, COLORS)
    )
    st.html(f'<div class="legend">{legend}<span class="legend-ref">Prior close</span></div>')


def main():
    st.set_page_config(
        page_title="AI Market Monitor", page_icon="◈", layout="wide",
        initial_sidebar_state="collapsed",
    )
    st.html(CSS)
    auth = credentials()
    with st.sidebar:
        st.header("Watchlist settings")
        ticker_input = st.text_area(
            "Ticker symbols", value=", ".join(WATCHLIST), height=110,
            help="Separate up to 30 US ticker symbols with commas, spaces, or new lines.",
        )
        entered = tuple(dict.fromkeys(re.split(r"[\s,]+", ticker_input.strip().upper())))
        entered = tuple(symbol for symbol in entered if symbol)
        if not entered or len(entered) > 30 or any(
            not re.fullmatch(r"[A-Z0-9][A-Z0-9.\-]{0,9}", symbol) for symbol in entered
        ):
            st.warning("Enter 1–30 valid ticker symbols. The default watchlist is shown.")
            entered = tuple(WATCHLIST)
        force_demo = st.checkbox("Use demo data", disabled=auth is None, value=auth is None)
        st.caption("Demo mode is automatic when Alpaca credentials are missing.")
        feed = st.selectbox(
            "Alpaca data feed", list(FEED_LABELS), format_func=FEED_LABELS.get,
            disabled=auth is None or force_demo,
            help="SIP covers multiple exchanges. IEX is real time with single-exchange coverage.",
        )
    demo = auth is None or force_demo

    with st.container(key="terminal_header"):
        brand, clocks, controls = st.columns([1.05, 2, 1.08], vertical_alignment="center")
        with brand:
            st.html('<div class="brand"><span class="brand-icon" aria-hidden="true">◈</span> AI Market Monitor</div>')
        with controls:
            toggle_col, refresh_col = st.columns([1.4, 1], vertical_alignment="center")
            with toggle_col:
                auto = st.toggle("Auto · 10s", value=True, help="Refresh market data every 10 seconds")
            with refresh_col:
                if st.button("Refresh", width="stretch"):
                    st.session_state["refresh_now"] = True

        @st.fragment(run_every=10)
        def render_clocks():
            now = datetime.now(ET)
            _, session, _ = market_clock(now)
            try:
                tz = pytz.timezone(st.context.timezone or "UTC")
            except pytz.UnknownTimeZoneError:
                tz = pytz.UTC
            local = now.astimezone(tz)
            description = "Local" if st.context.timezone else "UTC"
            st.html(
                f'<div class="clockbar"><span class="session {STATES[session]}">{session}</span>'
                f'<span class="clocks"><b>{now:%H:%M:%S}</b> ET &nbsp;'
                f'<b>{local:%H:%M:%S}</b> {description} ({escape(local.strftime("%Z"))})</span></div>'
            )

        with clocks:
            render_clocks()

    @st.fragment(run_every=10 if auto else None)
    def render_dashboard():
        now = datetime.now(ET)
        day, session, bounds = market_clock(now)
        previous = session_bounds(NYSE.previous_session(str(day)).date())
        bars, error = get_market_data(entered, bounds, previous, now, auth, demo, feed)
        quotes = {symbol: summarize(bars[symbol], bounds, previous, now) for symbol in entered}
        last_bar = max((q["time"] for q in quotes.values() if q["time"] is not None), default=None)
        feed_time = now - SIP_DELAY if feed == "sip" else now
        stale = (
            not demo and not error and session != "Closed" and
            feed_time >= bounds[0] + timedelta(minutes=15) and
            (last_bar is None or feed_time - last_bar >= timedelta(minutes=15))
        )
        feed_text, feed_class = (
            ("Simulated data", "demo") if demo else
            (f"{feed.upper()} · Feed error", "error") if error else
            (FEED_LABELS[feed], "demo" if stale or feed == "sip" else "")
        )
        st.html(
            '<div class="hero"><div><h1>AI equities dashboard</h1>'
            '<p>U.S. equity prices across pre-market, regular and after-hours trading</p></div>'
            f'<div class="feed"><span class="panel-sub">{day:%b %d, %Y} · ET</span>'
            f'<span class="feed-tag {feed_class}">{feed_text}</span></div></div>'
        )
        if error:
            st.warning(error)
        render_kpis(quotes, session)
        left, right = st.columns([3, 2])
        with right, st.container(key="intraday"):
            title, picker = st.columns([1.35, 1], vertical_alignment="center")
            with title:
                st.html('<div class="chart-title"><h2>Intraday price &amp; volume</h2></div>')
            with picker:
                selected = st.selectbox("Chart ticker", entered, label_visibility="collapsed")
            render_chart(selected, quotes[selected], bounds, day)
        with left:
            render_watchlist(quotes, selected, session)
        source_note = (
            "Simulated prices and shares" if demo else
            "Alpaca · Latest trades may be sparse or unavailable" if stale else
            "Alpaca · Consolidated SIP trades" if feed == "sip" else
            "Alpaca · IEX trades only · Extended-hours coverage varies"
        )
        st.html(
            f'<div class="footnote"><span>{source_note}</span>'
            f'<span>Latest bar {display_et(last_bar)} · All chart times ET</span></div>'
        )

    render_dashboard()


if __name__ == "__main__":
    main()
