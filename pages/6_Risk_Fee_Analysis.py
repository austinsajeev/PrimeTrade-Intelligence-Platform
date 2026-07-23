"""
Page 6 — Risk & Fee Analysis
Examines position sizing behavior, impulsive (crossed) order rates,
and fee erosion across sentiment regimes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from src.data_loader import load_merged, REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

st.set_page_config(page_title="Risk & Fee Analysis", page_icon="💰", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar()
page_header("💰", "Risk & Fee Analysis",
            "Position sizing, impulsive orders, and fee erosion across sentiment regimes")

merged, fg = load_merged()
closed = merged[merged["is_closed"]].dropna(subset=["classification"]).copy()

# ─── KPIs ─────────────────────────────────────────────────────────────────────
section_header("📌 Fee & Risk Overview")

total_fees  = merged["fee_drag"].sum()
total_gross = merged["gross_pnl"].sum()
total_net   = merged["net_pnl"].sum()
crossed_rate = merged["Crossed"].mean()
avg_size    = merged["Size USD"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Fees Paid",    f"${total_fees:,.2f}")
c2.metric("Total Gross PnL",   f"${total_gross:,.2f}")
c3.metric("Total Net PnL",     f"${total_net:,.2f}")
c4.metric("Crossed (Taker) %", f"{crossed_rate:.1%}")
c5.metric("Avg Trade Size",    f"${avg_size:,.0f}")

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Position sizing by regime ─────────────────────────────────────────────────
section_header("📏 Position Sizing Behavior by Sentiment Regime")

size_regime = (
    merged.groupby("classification")
    .agg(
        avg_size_usd   = ("Size USD","mean"),
        median_size    = ("Size USD","median"),
        p90_size       = ("Size USD", lambda x: x.quantile(0.90)),
        p10_size       = ("Size USD", lambda x: x.quantile(0.10)),
        total_vol      = ("Size USD","sum"),
    )
    .reindex(REGIME_ORDER).fillna(0).reset_index()
)

col_a, col_b = st.columns(2)

with col_a:
    fig_size = go.Figure()
    fig_size.add_trace(go.Bar(
        name="Avg Size",
        x=size_regime["classification"],
        y=size_regime["avg_size_usd"],
        marker=dict(color=[REGIME_COLORS[r] for r in size_regime["classification"]],
                    line=dict(color="#0a0a14", width=1.5), opacity=0.85),
        error_y=dict(
            type="data",
            array=(size_regime["p90_size"] - size_regime["avg_size_usd"]).clip(0),
            arrayminus=(size_regime["avg_size_usd"] - size_regime["p10_size"]).clip(0),
            visible=True,
            color="#94a3b8",
        ),
        hovertemplate="<b>%{x}</b><br>Avg: $%{y:,.0f}<extra></extra>",
    ))
    fig_size.add_trace(go.Scatter(
        name="Median Size",
        x=size_regime["classification"],
        y=size_regime["median_size"],
        mode="markers+lines",
        marker=dict(size=10, color="#f59e0b", symbol="diamond"),
        line=dict(color="#f59e0b", width=2, dash="dot"),
    ))
    fig_size.update_layout(
        **CHART_TEMPLATE,
        title="Avg & Median Position Size (USD) by Regime<br><sup>Error bars: 10th–90th percentile</sup>",
        xaxis_title="Regime",
        yaxis_title="Position Size (USD)",
        height=380,
    )
    st.plotly_chart(fig_size, use_container_width=True)

with col_b:
    # Large trade share (>90th percentile of overall size)
    p90_overall = merged["Size USD"].quantile(0.90)
    merged["is_large"] = merged["Size USD"] >= p90_overall

    large_share = (
        merged.groupby("classification")["is_large"]
        .mean()
        .reindex(REGIME_ORDER).fillna(0).reset_index()
    )
    large_share.columns = ["classification","large_pct"]

    fig_large = go.Figure(go.Bar(
        x=large_share["classification"],
        y=large_share["large_pct"] * 100,
        marker=dict(color=[REGIME_COLORS[r] for r in large_share["classification"]],
                    line=dict(color="#0a0a14", width=1.5), opacity=0.85),
        text=[f"{v:.1f}%" for v in large_share["large_pct"]*100],
        textposition="outside",
        textfont_color="#e2e8f0",
        hovertemplate="<b>%{x}</b><br>Large Trade %: %{y:.1f}%<extra></extra>",
    ))
    fig_large.update_layout(
        **CHART_TEMPLATE,
        title=f"% of Large Trades (≥ P90 = ${p90_overall:,.0f}) per Regime<br><sup>Reveals whale/overleveraging activity at sentiment extremes</sup>",
        xaxis_title="Regime",
        yaxis_title="Large Trade Share (%)",
        height=380,
    )
    st.plotly_chart(fig_large, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Crossed order analysis ────────────────────────────────────────────────────
section_header("⚠️ Impulsive Order Rate (Crossed = Taker Market Orders)")

crossed_regime = (
    merged.groupby("classification")
    .agg(
        crossed_rate = ("Crossed","mean"),
        crossed_count= ("Crossed","sum"),
        total_count  = ("Crossed","count"),
    )
    .reindex(REGIME_ORDER).fillna(0).reset_index()
)

col_c, col_d = st.columns(2)

with col_c:
    fig_crossed = go.Figure(go.Bar(
        x=crossed_regime["classification"],
        y=crossed_regime["crossed_rate"] * 100,
        marker=dict(
            color=crossed_regime["crossed_rate"],
            colorscale=[[0,"#14532d"],[0.5,"#eab308"],[1,"#7f1d1d"]],
            line=dict(color="#0a0a14", width=1.5),
        ),
        text=[f"{v:.1f}%" for v in crossed_regime["crossed_rate"]*100],
        textposition="outside",
        textfont_color="#e2e8f0",
        hovertemplate="<b>%{x}</b><br>Crossed Rate: %{y:.1f}%<extra></extra>",
    ))
    fig_crossed.update_layout(
        **CHART_TEMPLATE,
        title="Crossed (Taker) Order Rate per Regime<br><sup>Higher = more impulsive/emotional market orders</sup>",
        xaxis_title="Regime",
        yaxis_title="Crossed Order Rate (%)",
        height=380,
    )
    st.plotly_chart(fig_crossed, use_container_width=True)

with col_d:
    # Crossed rate vs FG value scatter
    daily_crossed = (
        merged.groupby("trade_date")
        .agg(crossed_rate=("Crossed","mean"), fg_value=("fg_value","first"))
        .dropna().reset_index()
    )

    fig_cross_scatter = px.scatter(
        daily_crossed,
        x="fg_value",
        y="crossed_rate",
        trendline="ols",
        trendline_color_override="#f59e0b",
        labels={"fg_value":"Fear & Greed Score","crossed_rate":"Daily Crossed Rate"},
        title="Daily Crossed Rate vs Fear & Greed Score",
        template="plotly_dark",
        color_discrete_sequence=["#7c3aed"],
        opacity=0.6,
    )
    fig_cross_scatter.update_layout(**CHART_TEMPLATE, height=380)
    st.plotly_chart(fig_cross_scatter, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Fee Waterfall ────────────────────────────────────────────────────────────
section_header("💧 Fee Erosion Waterfall — Gross PnL vs Net PnL per Regime")

fee_regime = (
    closed.groupby("classification")
    .agg(
        gross_pnl  = ("gross_pnl","sum"),
        total_fees = ("fee_drag","sum"),
        net_pnl    = ("net_pnl","sum"),
        trade_count= ("net_pnl","count"),
    )
    .reindex(REGIME_ORDER).fillna(0).reset_index()
)
fee_regime["fee_erosion_pct"] = (
    fee_regime["total_fees"] / fee_regime["gross_pnl"].abs().replace(0, np.nan) * 100
).fillna(0)

col_e, col_f = st.columns(2)

with col_e:
    fig_waterfall = go.Figure()
    fig_waterfall.add_trace(go.Bar(
        name="Gross PnL",
        x=fee_regime["classification"],
        y=fee_regime["gross_pnl"],
        marker_color=[REGIME_COLORS[r] for r in fee_regime["classification"]],
        marker_opacity=0.85,
        marker_line_color="#0a0a14",
        marker_line_width=1.5,
    ))
    fig_waterfall.add_trace(go.Bar(
        name="Net PnL (after fees)",
        x=fee_regime["classification"],
        y=fee_regime["net_pnl"],
        marker_color="#06b6d4",
        marker_opacity=0.7,
        marker_line_color="#0a0a14",
        marker_line_width=1.5,
    ))
    fig_waterfall.add_trace(go.Scatter(
        name="Fee Erosion %",
        x=fee_regime["classification"],
        y=fee_regime["fee_erosion_pct"],
        mode="markers+lines",
        marker=dict(size=10, color="#f59e0b", symbol="triangle-up"),
        line=dict(color="#f59e0b", width=2, dash="dot"),
        yaxis="y2",
    ))
    fig_waterfall.update_layout(
        **CHART_TEMPLATE,
        barmode="group",
        title="Gross PnL vs Net PnL with Fee Erosion % by Regime",
        xaxis_title="Regime",
        yaxis=dict(title="PnL (USD)"),
        yaxis2=dict(
            title="Fee Erosion (%)",
            overlaying="y",
            side="right",
            showgrid=False,
            color="#f59e0b",
        ),
        height=400,
    )
    st.plotly_chart(fig_waterfall, use_container_width=True)

with col_f:
    # Per-trade fee analysis
    fig_fee_per_trade = go.Figure()
    per_trade_fee = (
        closed.groupby("classification")
        .agg(avg_fee=("fee_drag","mean"), avg_net_pnl=("net_pnl","mean"))
        .reindex(REGIME_ORDER).fillna(0).reset_index()
    )
    fig_fee_per_trade.add_trace(go.Bar(
        name="Avg Fee / Trade",
        x=per_trade_fee["classification"],
        y=per_trade_fee["avg_fee"],
        marker_color="#ef4444",
        marker_opacity=0.8,
        marker_line_color="#0a0a14",
        marker_line_width=1.5,
    ))
    fig_fee_per_trade.add_trace(go.Bar(
        name="Avg Net PnL / Trade",
        x=per_trade_fee["classification"],
        y=per_trade_fee["avg_net_pnl"],
        marker_color="#22c55e",
        marker_opacity=0.8,
        marker_line_color="#0a0a14",
        marker_line_width=1.5,
    ))
    fig_fee_per_trade.add_hline(y=0, line_color="#475569")
    fig_fee_per_trade.update_layout(
        **CHART_TEMPLATE,
        barmode="group",
        title="Avg Fee vs Avg Net PnL Per Trade by Regime",
        xaxis_title="Regime",
        yaxis_title="Amount (USD)",
        height=400,
    )
    st.plotly_chart(fig_fee_per_trade, use_container_width=True)

# ─── Top Fee Payers ────────────────────────────────────────────────────────────
section_header("🏦 Top 10 Fee-Paying Accounts (Fee vs Net PnL)")

top_fee_accounts = (
    closed.groupby("Account_short")
    .agg(
        total_fees  = ("fee_drag","sum"),
        total_net   = ("net_pnl","sum"),
        trade_count = ("net_pnl","count"),
    )
    .sort_values("total_fees", ascending=False)
    .head(10)
    .reset_index()
)
top_fee_accounts["fee_efficiency"] = top_fee_accounts["total_net"] / top_fee_accounts["total_fees"].replace(0,np.nan)

fig_top_fees = go.Figure()
fig_top_fees.add_trace(go.Bar(
    name="Total Fees Paid",
    x=top_fee_accounts["Account_short"],
    y=top_fee_accounts["total_fees"],
    marker_color="#ef4444", marker_opacity=0.8,
))
fig_top_fees.add_trace(go.Scatter(
    name="Net PnL",
    x=top_fee_accounts["Account_short"],
    y=top_fee_accounts["total_net"],
    mode="markers",
    marker=dict(size=14, color="#22c55e", symbol="diamond",
                line=dict(color="#0a0a14", width=2)),
))
fig_top_fees.add_hline(y=0, line_color="#475569")
fig_top_fees.update_layout(
    **CHART_TEMPLATE,
    title="Top 10 Fee Payers: Total Fees vs Net PnL",
    xaxis_title="Account",
    yaxis_title="Amount (USD)",
    height=360,
)
st.plotly_chart(fig_top_fees, use_container_width=True)

# ─── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
col_i1, col_i2, col_i3 = st.columns(3)
with col_i1:
    insight_box(
        "The Overconfidence Tax",
        "Position sizes inflate during Greed regimes — classic <b>overconfidence bias</b>. "
        "Traders size up when they feel good, creating asymmetric downside if the trend reverses. "
        "The P90 size spikes confirm whale-level bets at market tops."
    )
with col_i2:
    insight_box(
        "Emotional Orders Cost More",
        "Crossed (taker) orders spike at <b>emotional extremes</b>. In panic or FOMO, "
        "traders hit market prices — paying the spread + taker fee. "
        "A discipline rule: <em>only limit orders during Extreme Fear or Greed</em> "
        "would meaningfully reduce fee drag."
    )
with col_i3:
    insight_box(
        "The Hidden Fee Bleed",
        "Even regimes with positive gross PnL can show negative net PnL once fees are subtracted. "
        "This is the 'house edge' in perpetuals trading: <b>frequent trading + taker fees "
        "= systematic alpha erosion</b> that only appears at the regime-aggregation level."
    )
