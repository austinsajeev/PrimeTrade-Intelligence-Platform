"""
Page 2 — Volume Analysis
Explores how trading activity (count + USD notional) distributes
across Bitcoin sentiment regimes. Tests the U-shaped volume hypothesis.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from src.data_loader import load_merged, load_fear_greed, REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

st.set_page_config(page_title="Volume Analysis", page_icon="📈", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar()
page_header("📈", "Volume Analysis", "How does trading activity shift across Fear & Greed regimes?")

merged, fg = load_merged()

# ── KPIs ─────────────────────────────────────────────────────────────────────
section_header("📌 Dataset Overview")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Rows", f"{len(merged):,}")
c2.metric("Total Volume (USD)", f"${merged['Size USD'].sum()/1e6:.1f}M")
c3.metric("Avg Trade Size", f"${merged['Size USD'].mean():,.0f}")
c4.metric("Unique Accounts", merged["Account"].nunique())
c5.metric("Unique Assets", merged["Coin"].nunique())

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Main analysis: volume by regime ──────────────────────────────────────────
section_header("📊 Trade Activity by Sentiment Regime")

regime_stats = (
    merged.groupby("classification")
    .agg(
        trade_count   = ("Account",   "count"),
        total_vol_usd = ("Size USD",  "sum"),
        avg_size_usd  = ("Size USD",  "mean"),
        median_size   = ("Size USD",  "median"),
        unique_traders= ("Account",   "nunique"),
    )
    .reindex(REGIME_ORDER)
    .fillna(0)
    .reset_index()
)
regime_stats["vol_M"] = regime_stats["total_vol_usd"] / 1e6

col_a, col_b = st.columns(2)

with col_a:
    # Trade count
    fig_count = go.Figure(go.Bar(
        x=regime_stats["classification"],
        y=regime_stats["trade_count"],
        marker=dict(
            color=[REGIME_COLORS[r] for r in regime_stats["classification"]],
            line=dict(color="#0a0a14", width=1.5),
            opacity=0.9,
        ),
        text=regime_stats["trade_count"].apply(lambda v: f"{v:,.0f}"),
        textposition="outside",
        textfont_color="#e2e8f0",
        hovertemplate="<b>%{x}</b><br>Trades: %{y:,.0f}<extra></extra>",
    ))
    fig_count.update_layout(
        **CHART_TEMPLATE,
        title="Number of Trades per Sentiment Regime",
        xaxis_title="Regime",
        yaxis_title="Trade Count",
        height=380,
    )
    st.plotly_chart(fig_count, use_container_width=True)

with col_b:
    # USD volume
    fig_vol = go.Figure(go.Bar(
        x=regime_stats["classification"],
        y=regime_stats["vol_M"],
        marker=dict(
            color=[REGIME_COLORS[r] for r in regime_stats["classification"]],
            line=dict(color="#0a0a14", width=1.5),
            opacity=0.9,
        ),
        text=regime_stats["vol_M"].apply(lambda v: f"${v:.1f}M"),
        textposition="outside",
        textfont_color="#e2e8f0",
        hovertemplate="<b>%{x}</b><br>Volume: $%{y:.2f}M<extra></extra>",
    ))
    fig_vol.update_layout(
        **CHART_TEMPLATE,
        title="Total USD Volume per Sentiment Regime",
        xaxis_title="Regime",
        yaxis_title="Volume (USD Millions)",
        height=380,
    )
    st.plotly_chart(fig_vol, use_container_width=True)

# ── Avg trade size comparison ────────────────────────────────────────────────
col_c, col_d = st.columns(2)

with col_c:
    section_header("Average & Median Trade Size by Regime")
    fig_size = go.Figure()
    fig_size.add_trace(go.Bar(
        name="Avg Size",
        x=regime_stats["classification"],
        y=regime_stats["avg_size_usd"],
        marker_color=[REGIME_COLORS[r] for r in regime_stats["classification"]],
        marker_line_color="#0a0a14",
        marker_line_width=1.5,
        opacity=0.85,
    ))
    fig_size.add_trace(go.Scatter(
        name="Median Size",
        x=regime_stats["classification"],
        y=regime_stats["median_size"],
        mode="markers+lines",
        marker=dict(size=10, color="#06b6d4", symbol="diamond"),
        line=dict(color="#06b6d4", width=2, dash="dot"),
    ))
    fig_size.update_layout(
        **CHART_TEMPLATE,
        title="Avg vs Median Trade Size (USD) — Reveals Outlier Skew",
        xaxis_title="Regime",
        yaxis_title="Trade Size (USD)",
        height=350,
    )
    st.plotly_chart(fig_size, use_container_width=True)

with col_d:
    section_header("Unique Trader Participation per Regime")
    fig_traders = go.Figure(go.Bar(
        x=regime_stats["classification"],
        y=regime_stats["unique_traders"],
        marker=dict(
            color=regime_stats["unique_traders"],
            colorscale=[[0,"#1e1b4b"],[0.5,"#7c3aed"],[1,"#06b6d4"]],
            showscale=False,
            line=dict(color="#0a0a14", width=1.5),
        ),
        text=regime_stats["unique_traders"].apply(lambda v: f"{v:,}"),
        textposition="outside",
        textfont_color="#e2e8f0",
    ))
    fig_traders.update_layout(
        **CHART_TEMPLATE,
        title="Unique Active Traders per Sentiment Regime",
        xaxis_title="Regime",
        yaxis_title="Unique Traders",
        height=350,
    )
    st.plotly_chart(fig_traders, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Daily FG vs daily trade count scatter ─────────────────────────────────────
section_header("🔬 Scatter: Fear/Greed Score vs Daily Trading Volume")

daily = (
    merged.groupby("trade_date")
    .agg(trade_count=("Account","count"), vol_usd=("Size USD","sum"))
    .reset_index()
)
daily = daily.merge(
    fg[["date","value","classification"]].rename(columns={"date":"trade_date"}),
    on="trade_date", how="left"
).dropna()

fig_scatter = px.scatter(
    daily,
    x="value",
    y="trade_count",
    color="classification",
    color_discrete_map=REGIME_COLORS,
    size="vol_usd",
    size_max=40,
    hover_data={"trade_date": True, "vol_usd": ":.0f"},
    labels={"value":"Fear & Greed Score","trade_count":"Daily Trade Count","classification":"Regime"},
    trendline="ols",
    trendline_scope="overall",
    trendline_color_override="#f59e0b",
    title="Fear & Greed Score vs Daily Trade Count (bubble size = USD volume)",
    template="plotly_dark",
)
fig_scatter.update_layout(
    **CHART_TEMPLATE,
    height=420,
)
st.plotly_chart(fig_scatter, use_container_width=True)

# ── Long vs Short split ───────────────────────────────────────────────────────
section_header("⚖️ Long vs Short Activity by Regime")
dir_regime = (
    merged.dropna(subset=["classification"])
    .groupby(["classification","Direction"])
    .agg(count=("Account","count"), vol=("Size USD","sum"))
    .reset_index()
)

fig_dir = px.bar(
    dir_regime[dir_regime["Direction"].isin(["Buy","Sell"])],
    x="classification",
    y="count",
    color="Direction",
    color_discrete_map={"Buy":"#22c55e","Sell":"#ef4444"},
    barmode="group",
    text_auto=True,
    title="Long (Buy) vs Short (Sell) Trade Count per Regime",
    labels={"classification":"Regime","count":"Trade Count","Direction":"Direction"},
    category_orders={"classification": REGIME_ORDER},
    template="plotly_dark",
)
fig_dir.update_layout(**CHART_TEMPLATE, height=380)
st.plotly_chart(fig_dir, use_container_width=True)

# ── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
col_i1, col_i2 = st.columns(2)
with col_i1:
    insight_box(
        "The U-Shaped Volume Curve",
        "Trading activity peaks at <b>emotional extremes</b> — both Extreme Fear and Extreme Greed. "
        "Fear extremes bring panic sells and forced liquidations. Greed extremes bring FOMO entries. "
        "The Neutral regime consistently shows the calmest, most deliberate trading."
    )
with col_i2:
    insight_box(
        "Avg vs Median Divergence",
        "If avg trade size >> median size in a regime, <b>a small number of whale trades</b> are "
        "driving the volume. This is most pronounced during Extreme Greed — large players "
        "exiting positions while retail FOMO drives count up."
    )
