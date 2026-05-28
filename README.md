# 📊 S&P 500 Market Breadth Analyzer

A real-time market breadth dashboard that goes beyond the index price to show 
how many S&P 500 stocks are actually participating in a market move.

🔗 **[Live App](https://market-breadth-analyzer.streamlit.app/)**

---

## Why This Tool Exists

The S&P 500 index is market-cap weighted — meaning Apple, Microsoft, and Nvidia 
alone represent ~25% of the index. On any given day, these five stocks can push 
the index up 1% while 400 other stocks are flat or down. This tool unmasks that 
hidden picture in real time.

---

## Features

- 📈 **Live S&P 500 price** with intraday % change
- 📊 **Breadth distribution** across 10 return buckets (Up >20% to Down >20%)
- 🏆 **Top 10 gainers and losers** with full company names
- 🏭 **Sector breadth** — % of stocks up vs down across all 11 GICS sectors
- 🔄 **Auto-refreshing** every 5 minutes during market hours
- 📋 **Breadth summary table** with stock counts and % of index

---

## Data Sources

- **S&P 500 constituents** — State Street Global Advisors SPY holdings file (updated daily)
- **Live price data** — Yahoo Finance via yfinance
- **Sector classifications** — Yahoo Finance (cached for 24 hours)

---

## Tech Stack

- Python
- Streamlit
- yfinance
- pandas
- Plotly
- concurrent.futures (parallel API calls for sector data)

---

## How to Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Key Technical Decisions

- **State Street over Wikipedia** for constituent data — more authoritative and updated daily
- **Parallel sector fetching** using ThreadPoolExecutor — reduces fetch time from ~200s to ~20s
- **Smart caching** — price data cached 5 minutes, sector data cached 24 hours
- **Graceful error handling** — app degrades cleanly if Yahoo Finance rate limits

---

*Built by Raj Abhisar Agarwal, CFA*  
*For informational purposes only. Not financial advice.*
