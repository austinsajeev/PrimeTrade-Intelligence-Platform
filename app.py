"""
app.py  ── Home / Executive Dashboard
======================================
Entry point for the Hyperliquid × Fear & Greed Intelligence Platform.
Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from src.data_loader import (
    load_fear_greed, load_trades, load_merged,
    REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE,
)
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

# ─── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="PrimeTrade Intelligence | Home",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()
render_sidebar()

# ─── Hero header ──────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:2rem 0 1rem;">
    <div style="font-size:3.5rem; margin-bottom:0.5rem;">⚡</div>
    <div class="hero-title">PrimeTrade Intelligence Platform</div>
    <p class="hero-subtitle">Decoding Alpha: How Bitcoin Market Sentiment Shapes Trader Behavior on Hyperliquid</p>
    <div>
        <span class="hero-badge">📊 Fear &amp; Greed Index</span>
        <span class="hero-badge">🔗 On-Chain Trade Data</span>
        <span class="hero-badge">🤖 ML Clustering</span>
        <span class="hero-badge">📈 Event Study Analysis</span>
    </div>
</div>
<div class="gradient-divider"></div>
""", unsafe_allow_html=True)

# ─── Load data ────────────────────────────────────────────────────────────────
with st.spinner("Initialising datasets…"):
    merged, fg = load_merged()
    trades      = load_trades()

# ─── KPI Metrics ──────────────────────────────────────────────────────────────
section_header("📌 Executive Summary")

total_trades    = len(merged)
unique_traders  = merged["Account"].nunique()
total_vol_m     = merged["Size USD"].sum() / 1e6
closed          = merged[merged["is_closed"]]
overall_wr      = closed["is_profitable"].mean() * 100 if len(closed) > 0 else 0
net_pnl_total   = closed["net_pnl"].sum()
unique_coins    = merged["Coin"].nunique()
date_range_days = (merged["trade_date"].max() - merged["trade_date"].min()).days
avg_fg          = fg["value"].mean()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("📦 Total Trades", f"{total_trades:,}")
with col2:
    st.metric("👥 Unique Traders", f"{unique_traders:,}")
with col3:
    st.metric("💵 Total Volume", f"${total_vol_m:.1f}M")
with col4:
    st.metric("🎯 Overall Win Rate", f"{overall_wr:.1f}%")

col5, col6, col7, col8 = st.columns(4)
with col5:
    st.metric("💰 Net PnL (All)", f"${net_pnl_total:,.0f}")
with col6:
    st.metric("🪙 Unique Assets", f"{unique_coins}")
with col7:
    st.metric("📅 Data Span", f"{date_range_days} days")
with col8:
    st.metric("😨 Avg Fear/Greed", f"{avg_fg:.1f}")

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Two-column layout: Timeline + Regime Distribution ────────────────────────
section_header("📊 Sentiment Landscape (Bitcoin Fear & Greed Index 2018–2025)")

col_left, col_right = st.columns([2, 1])

with col_left:
    # Full FG timeline with regime bands
    fig_timeline = go.Figure()

    # Color band fills for each regime
    thresholds = [
        (0,  25, "rgba(220,38,38,0.12)",  "Extreme Fear"),
        (25, 46, "rgba(249,115,22,0.10)", "Fear"),
        (46, 55, "rgba(234,179,8,0.10)",  "Neutral"),
        (55, 75, "rgba(34,197,94,0.10)",  "Greed"),
        (75, 100,"rgba(22,163,74,0.12)",  "Extreme Greed"),
    ]
    for lo, hi, color, name in thresholds:
        fig_timeline.add_hrect(y0=lo, y1=hi, fillcolor=color, line_width=0, annotation_text="")

    fig_timeline.add_trace(go.Scatter(
        x=fg["date"], y=fg["value"],
        mode="lines",
        line=dict(color="#7c3aed", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(124,58,237,0.08)",
        name="Fear & Greed",
    ))
    fig_timeline.add_trace(go.Scatter(
        x=fg["date"], y=fg["fg_30d_avg"],
        mode="lines",
        line=dict(color="#06b6d4", width=2, dash="dot"),
        name="30-day Avg",
    ))

    fig_timeline.update_layout(
        **CHART_TEMPLATE,
        title="Bitcoin Fear & Greed Index — Full History",
        xaxis_title="Date",
        yaxis=dict(range=[0, 100], title="Index Value (0–100)"),
        height=340,
        showlegend=True,
    )
    st.plotly_chart(fig_timeline, use_container_width=True)

with col_right:
    # Regime distribution donut
    regime_counts = fg["classification"].value_counts().reindex(REGIME_ORDER).fillna(0)
    fig_donut = go.Figure(go.Pie(
        labels=regime_counts.index,
        values=regime_counts.values,
        hole=0.6,
        marker=dict(
            colors=[REGIME_COLORS[r] for r in regime_counts.index],
            line=dict(color="#0a0a14", width=2),
        ),
        textinfo="percent",
        textfont_size=11,
    ))
    fig_donut.update_layout(
        **CHART_TEMPLATE,
        title="Regime Distribution",
        height=340,
        showlegend=True,
        legend=dict(orientation="v", x=1.05),
    )
    st.plotly_chart(fig_donut, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Trade Activity Overview ───────────────────────────────────────────────────
section_header("📈 Trade Activity in Context")

col_a, col_b = st.columns([1, 1])

with col_a:
    # Daily trade count over time
    daily_trades = merged.groupby("trade_date").size().reset_index(name="count")
    daily_vol    = merged.groupby("trade_date")["Size USD"].sum().reset_index(name="volume")
    daily = daily_trades.merge(daily_vol, on="trade_date")

    # Add sentiment to daily
    daily = daily.merge(
        fg[["date", "value", "classification"]].rename(columns={"date":"trade_date"}),
        on="trade_date", how="left"
    )

    fig_activity = go.Figure()
    fig_activity.add_trace(go.Bar(
        x=daily["trade_date"],
        y=daily["count"],
        name="Trade Count",
        marker=dict(
            color=daily["value"],
            colorscale=[[0, "#dc2626"], [0.25, "#f97316"],
                        [0.5, "#eab308"], [0.75, "#22c55e"], [1, "#16a34a"]],
            cmin=0, cmax=100,
            showscale=True,
            colorbar=dict(title="Fear/Greed", len=0.5, thickness=10),
        ),
        opacity=0.85,
    ))
    fig_activity.update_layout(
        **CHART_TEMPLATE,
        title="Daily Trade Volume (bars colored by Fear/Greed score)",
        xaxis_title="Date",
        yaxis_title="Number of Trades",
        height=320,
    )
    st.plotly_chart(fig_activity, use_container_width=True)

with col_b:
    # Regime breakdown of trade data
    regime_trade = merged.groupby("classification").agg(
        trade_count=("Account","count"),
        volume_usd=("Size USD","sum"),
    ).reindex(REGIME_ORDER).fillna(0).reset_index()

    fig_regime_bar = go.Figure()
    fig_regime_bar.add_trace(go.Bar(
        x=regime_trade["classification"],
        y=regime_trade["trade_count"],
        name="Trades",
        marker_color=[REGIME_COLORS[r] for r in regime_trade["classification"]],
        marker_line_color="#0a0a14",
        marker_line_width=1.5,
    ))
    fig_regime_bar.update_layout(
        **CHART_TEMPLATE,
        title="Trade Count by Sentiment Regime",
        xaxis_title="Sentiment Regime",
        yaxis_title="Number of Trades",
        height=320,
    )
    st.plotly_chart(fig_regime_bar, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Key Insights ─────────────────────────────────────────────────────────────
section_header("💡 Core Hypotheses Under Investigation")

col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    insight_box(
        "Sentiment Transition Alpha",
        "Trades executed within 48 hours of a Fear → Greed regime shift statistically outperform "
        "the population mean — the <b>crowd is still scared while price already recovers</b>."
    )
with col_i2:
    insight_box(
        "Contrarian Profitability",
        "Contrarian longs placed during <b>Extreme Fear</b> regimes show asymmetric upside. "
        "Market oversold conditions create the highest quality entry points historically."
    )
with col_i3:
    insight_box(
        "Fee Erosion at Extremes",
        "During <b>Extreme Greed</b>, high-frequency taker orders erode net PnL. Even directionally "
        "correct traders may show negative net alpha after fee drag."
    )

# ─── Navigation guide ─────────────────────────────────────────────────────────
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
section_header("🗺️ Analysis Modules")

nav_cols = st.columns(3)
pages = [
    ("📊", "Sentiment Overview",   "Full Fear & Greed timeline, regime transitions, historical extremes"),
    ("📈", "Volume Analysis",      "Trade volume & USD notional by sentiment regime"),
    ("🎯", "Win Rate Analysis",    "Profitability heatmap · PnL distributions by regime & direction"),
    ("⚡", "Transition Alpha",     "Event-study: PnL windows after sentiment regime shifts"),
    ("🧠", "Trader Archetypes",    "K-Means clustering of behavioral profiles (PCA visualised)"),
    ("💰", "Risk & Fee Analysis",  "Position sizing · crossed order rates · fee waterfall by regime"),
]
for i, (icon, title, desc) in enumerate(pages):
    with nav_cols[i % 3]:
        st.markdown(f"""
        <div class="kpi-card" style="text-align:left; margin-bottom:1rem;">
            <div style="font-size:1.8rem; margin-bottom:0.5rem;">{icon}</div>
            <div style="font-weight:700; color:#e2e8f0; font-size:0.95rem; margin-bottom:0.35rem;">{title}</div>
            <div style="font-size:0.8rem; color:#64748b; line-height:1.5;">{desc}</div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("""
<div style="text-align:center; color:#475569; font-size:0.8rem; margin-top:1rem;">
    Navigate using the sidebar → | Built with Streamlit + Plotly + Scikit-Learn
</div>
""", unsafe_allow_html=True)
