
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import time

st.cache_data.clear()

st.set_page_config(
    page_title="S&P 500 Market Breadth Analyzer",
    page_icon="📊",
    layout="wide"
)

st.title("📊 S&P 500 Market Breadth Analyzer")
from datetime import datetime
import pytz
eastern = pytz.timezone('US/Eastern')
last_updated = datetime.now(eastern).strftime("%B %d, %Y at %I:%M %p ET")
st.caption(f"Real-time breadth analysis across all S&P 500 constituents.")

@st.cache_data(ttl=300)
def get_sp500_tickers():
    spy_url = 'https://www.ssga.com/library-content/products/fund-data/etfs/us/holdings-daily-us-en-spy.xlsx'
    spy_holdings = pd.read_excel(spy_url, skiprows=4)
    spy_holdings = spy_holdings.dropna(subset=['Ticker'])
    spy_holdings = spy_holdings[spy_holdings['Ticker'].str.strip() != '-']
    spy_holdings['Ticker'] = spy_holdings['Ticker'].str.replace('.', '-', regex=False)
    tickers = spy_holdings['Ticker'].tolist()
    name_map = dict(zip(spy_holdings['Ticker'], spy_holdings['Name']))
    return tickers, name_map

@st.cache_data(ttl=604800)
def get_sector_map(tickers):
    sector_df = pd.read_csv('sectors.csv')
    sector_map = dict(zip(sector_df['Ticker'], sector_df['Sector']))
    st.write(f"Debug — sector_df rows after filtering: {len(sector_df)}")
    st.write(sector_df['Sector'].value_counts())
    return sector_map

    results = []
    batch_size = 50
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            batch_results = list(executor.map(fetch_sector, batch))
        results.extend(batch_results)
        time.sleep(2)

    sector_map = dict(results)
    unknown_count = sum(1 for v in sector_map.values() if v == 'Unknown')
    if unknown_count > len(tickers) * 0.2:
        st.warning(f"⚠️ Sector data incomplete — {unknown_count} tickers returned Unknown. Try refreshing.")

    return sector_map

@st.cache_data(ttl=300)
def get_price_data(tickers):
    data = yf.download(tickers, period='2d', interval='1d', progress=False)
    return data['Close']

@st.cache_data(ttl=300)
def get_sp500_price():
    try:
        sp500 = yf.Ticker("^GSPC")
        data = sp500.history(period='2d')
        current_price = data['Close'].iloc[-1]
        prev_close = data['Close'].iloc[-2]
        pct_change = ((current_price - prev_close) / prev_close) * 100
        return round(current_price, 2), round(pct_change, 2)
    except:
        return None, None

def categorize_breadth(pct):
    if pct >= 20:
        return 'Up >20%'
    elif pct >= 10:
        return 'Up 10-20%'
    elif pct >= 5:
        return 'Up 5-10%'
    elif pct >= 2:
        return 'Up 2-5%'
    elif pct >= 0:
        return 'Up 0-2%'
    elif pct >= -2:
        return 'Down 0-2%'
    elif pct >= -5:
        return 'Down 2-5%'
    elif pct >= -10:
        return 'Down 5-10%'
    elif pct >= -20:
        return 'Down 10-20%'
    else:
        return 'Down >20%'

def calculate_breadth(close_prices):
    pct_change = close_prices.pct_change(fill_method=None) * 100
    todays_change = pct_change.iloc[-1].dropna()
    buckets = todays_change.apply(categorize_breadth)

    category_order = [
        'Up >20%', 'Up 10-20%', 'Up 5-10%', 'Up 2-5%', 'Up 0-2%',
        'Down 0-2%', 'Down 2-5%', 'Down 5-10%', 'Down 10-20%', 'Down >20%'
    ]

    summary = buckets.value_counts().reindex(category_order).fillna(0).astype(int)
    total = todays_change.count()

    breadth_table = pd.DataFrame({
        'Count': summary,
        '% of Index': (summary / total * 100).round(1)
    })

    breadth_table.loc['TOTAL'] = [breadth_table['Count'].sum(), breadth_table['% of Index'].sum().round(1)]

    return todays_change, breadth_table

# ── Main App ──────────────────────────────────────────────────────────────────

st.divider()

with st.expander("📖 How to read this dashboard"):
    st.markdown("""
    **Market Breadth** measures how many stocks are actually participating in a market move — not just the index price.
    
    - **S&P 500 up but most stocks down?** → Narrow rally driven by mega-caps. Potentially fragile.
    - **S&P 500 up and most stocks up?** → Broad rally. Healthy and more sustainable.
    - **Avg Stock Change vs S&P 500 price** → If these diverge significantly, a few large stocks are driving the index.
    
    **Breadth Distribution** shows how today's moves are spread across all 500 stocks by return bucket.
    
    **Sector Breadth** shows which sectors are leading and which are lagging — useful for spotting rotation.
    
    **Top Movers** shows the biggest individual winners and losers within the index today.
    
    *Data refreshes every 5 minutes.*
    """)

progress_bar = st.progress(0)
status = st.empty()

status.info("⏳ Step 1 of 3 — Fetching S&P 500 constituents...")
tickers, name_map = get_sp500_tickers()
progress_bar.progress(33)

status.info("⏳ Step 2 of 3 — Downloading live price data for 500+ stocks from Yahoo Finance...")
close_prices = get_price_data(tickers)
progress_bar.progress(66)

status.info("⏳ Step 3 of 3 — Fetching sector classifications for all constituents...")
sector_map = get_sector_map(tickers)
progress_bar.progress(100)

status.empty()
progress_bar.empty()

st.info("🔄 Data auto-refreshes every 5 minutes. Last updated: " + last_updated)

todays_change, breadth_table = calculate_breadth(close_prices)
total_stocks = todays_change.count()

# ── Summary Metrics ───────────────────────────────────────────────────────────

stocks_up = (todays_change > 0).sum()
stocks_down = (todays_change < 0).sum()
avg_change = todays_change.mean()

sp500_price, sp500_change = get_sp500_price()

st.markdown(f"**As of {last_updated}**")

col0, col1, col2, col3, col4 = st.columns(5)
if sp500_price is not None:
    col0.metric("S&P 500", f"{sp500_price:,.2f}", f"{sp500_change}%", delta_color="normal")
else:
    col0.metric("S&P 500", "Unavailable", "Refresh in 1 min")
col1.metric("Stocks Analyzed", f"{total_stocks}")
col2.metric("Stocks Up", f"{stocks_up}", f"{round(stocks_up/total_stocks*100,1)}% of index")
col3.metric("Stocks Down", f"{stocks_down}", f"{round(stocks_down/total_stocks*100,1)}% of index", delta_color="inverse")
col4.metric("Avg Stock Change", f"{avg_change:.2f}%")

st.divider()

# ── Breadth Chart ─────────────────────────────────────────────────────────────

st.subheader("📊 Market Breadth Distribution")

category_order = [
    'Up >20%', 'Up 10-20%', 'Up 5-10%', 'Up 2-5%', 'Up 0-2%',
    'Down 0-2%', 'Down 2-5%', 'Down 5-10%', 'Down 10-20%', 'Down >20%'
]

chart_data = breadth_table.drop('TOTAL').reset_index()
chart_data.columns = ['Category', 'Count', '% of Index']
chart_data['Count'] = chart_data['Count'].astype(int)

colors = ['#00C805' if 'Up' in cat else '#ef5350' for cat in chart_data['Category']]

fig = go.Figure(go.Bar(
    x=chart_data['Count'],
    y=chart_data['Category'],
    orientation='h',
    marker_color=colors,
    text=[f"{c} stocks ({p}%)" for c, p in zip(chart_data['Count'], chart_data['% of Index'])],
    textposition='outside'
))

fig.update_layout(
    title='S&P 500 Stocks by Return Bucket — Today',
    xaxis_title='Number of Stocks',
    height=500,
    xaxis=dict(fixedrange=True),
    yaxis=dict(fixedrange=True, categoryorder='array', categoryarray=category_order[::-1])
)

st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

# ── Breadth Table ─────────────────────────────────────────────────────────────

st.subheader("📋 Breadth Summary Table")

display_table = breadth_table.copy()
display_table['Count'] = display_table['Count'].astype(int).astype(str)
display_table['% of Index'] = display_table['% of Index'].apply(lambda x: f"{x}%")
display_table.index.name = 'Category'
display_table = display_table.reset_index()

st.table(display_table.set_index('Category').style.set_properties(**{'text-align': 'left'}))

# ── Top Movers ────────────────────────────────────────────────────────────────

st.divider()
st.subheader("🏆 Top Movers Today")

col_g, col_l = st.columns(2)

top_gainers = todays_change.sort_values(ascending=False).head(10).reset_index()
top_gainers.columns = ['Ticker', '% Change']
top_gainers['Company'] = top_gainers['Ticker'].map(name_map).fillna('') + ' (' + top_gainers['Ticker'] + ')'
top_gainers['% Change'] = top_gainers['% Change'].apply(lambda x: f"+{x:.2f}%")
top_gainers = top_gainers[['Company', '% Change']].set_index('Company')

top_losers = todays_change.sort_values(ascending=True).head(10).reset_index()
top_losers.columns = ['Ticker', '% Change']
top_losers['Company'] = top_losers['Ticker'].map(name_map).fillna('') + ' (' + top_losers['Ticker'] + ')'
top_losers['% Change'] = top_losers['% Change'].apply(lambda x: f"{x:.2f}%")
top_losers = top_losers[['Company', '% Change']].set_index('Company')

with col_g:
    st.markdown("**🟢 Top 10 Gainers**")
    st.table(top_gainers)

with col_l:
    st.markdown("**🔴 Top 10 Losers**")
    st.table(top_losers)

# ── Sector Breadth ────────────────────────────────────────────────────────────

st.divider()
st.subheader("🏭 Sector Breadth")

sector_df = pd.DataFrame({
    'Ticker': todays_change.index,
    '% Change': todays_change.values
})
sector_df['Sector'] = sector_df['Ticker'].map(sector_map)
sector_df = sector_df[sector_df['Sector'] != 'Unknown']
sector_df = sector_df.dropna(subset=['Sector'])
sector_df = sector_df[~sector_df['Sector'].isin(['Unknown', 'None', ''])]

sector_summary = sector_df.groupby('Sector').agg(
    Total=('% Change', 'count'),
    Up=('% Change', lambda x: (x > 0).sum()),
    Down=('% Change', lambda x: (x < 0).sum()),
    Avg_Change=('% Change', 'mean')
).reset_index()

sector_summary['% Up'] = (sector_summary['Up'] / sector_summary['Total'] * 100).round(1)
sector_summary['% Down'] = (100 - sector_summary['% Up']).round(1)
sector_summary['Avg Change'] = sector_summary['Avg_Change'].apply(lambda x: f"{x:.2f}%")
sector_summary = sector_summary.sort_values('% Up', ascending=True)

fig_sector = go.Figure()

fig_sector.add_trace(go.Bar(
    y=sector_summary['Sector'],
    x=sector_summary['% Up'],
    name='% Up',
    orientation='h',
    marker_color='#00C805',
    text=[f"{p}% ({u} stocks)" for p, u in zip(sector_summary['% Up'], sector_summary['Up'])],
    textposition='inside',
    insidetextfont=dict(color='black', size=12)
))

fig_sector.add_trace(go.Bar(
    y=sector_summary['Sector'],
    x=sector_summary['% Down'],
    name='% Down',
    orientation='h',
    marker_color='#ef5350',
    text=[f"{p}% ({d} stocks)" for p, d in zip(sector_summary['% Down'], sector_summary['Down'])],
    textposition='inside',
    insidetextfont=dict(color='black', size=12)
))

fig_sector.update_layout(
    barmode='stack',
    title='Sector Breadth — % of Stocks Up vs Down',
    xaxis_title='% of Stocks',
    xaxis=dict(fixedrange=True, range=[0, 100]),
    yaxis=dict(fixedrange=True),
    height=500,
    legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
)

st.plotly_chart(fig_sector, use_container_width=True, config={'displayModeBar': False})

st.divider()
st.caption("⚠️ This tool is for informational purposes only and does not constitute financial advice. Data sourced from Yahoo Finance and State Street Global Advisors. Past market conditions do not guarantee future results.")
