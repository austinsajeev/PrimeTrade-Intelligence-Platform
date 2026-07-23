"""
Page 3 — Win Rate Analysis
Examines trader profitability (win rate, avg PnL) broken down by
sentiment regime and trade direction (Long / Short).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from scipy import stats

from src.data_loader import load_merged, REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

st.set_page_config(page_title="Win Rate Analysis", page_icon="🎯", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar()
page_header("🎯", "Win Rate Analysis",
            "Profitability breakdown: which regimes produce winners — and which destroy capital?")

merged, fg = load_merged()
closed = merged[merged["is_closed"]].copy()
closed = closed.dropna(subset=["classification"])

st.info(f"Analysis based on **{len(closed):,} closed trade rows** with realised PnL. "
        f"({len(merged)-len(closed):,} open/zero-PnL rows excluded from profitability metrics)")

# ── KPIs ─────────────────────────────────────────────────────────────────────
section_header("📌 Overall Profitability")
wr_all   = closed["is_profitable"].mean()
avg_pnl  = closed["net_pnl"].mean()
med_pnl  = closed["net_pnl"].median()
total_pnl = closed["net_pnl"].sum()
best_reg  = (
    closed.groupby("classification")["is_profitable"].mean()
    .reindex(REGIME_ORDER).idxmax()
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Overall Win Rate",    f"{wr_all:.1%}")
c2.metric("Avg Net PnL / Trade", f"${avg_pnl:,.2f}")
c3.metric("Median Net PnL",      f"${med_pnl:,.2f}")
c4.metric("Total Net PnL",       f"${total_pnl:,.0f}")
c5.metric("Best Regime",         best_reg)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Win rate by regime ────────────────────────────────────────────────────────
section_header("🏆 Win Rate by Sentiment Regime")

regime_perf = (
    closed.groupby("classification")
    .agg(
        win_rate    = ("is_profitable", "mean"),
        avg_pnl     = ("net_pnl",       "mean"),
        median_pnl  = ("net_pnl",       "median"),
        total_pnl   = ("net_pnl",       "sum"),
        trade_count = ("net_pnl",       "count"),
    )
    .reindex(REGIME_ORDER).fillna(0).reset_index()
)

col_a, col_b = st.columns(2)

with col_a:
    fig_wr = go.Figure(go.Bar(
        x=regime_perf["classification"],
        y=regime_perf["win_rate"] * 100,
        marker=dict(
            color=[REGIME_COLORS[r] for r in regime_perf["classification"]],
            line=dict(color="#0a0a14", width=1.5),
            opacity=0.9,
        ),
        text=[f"{v:.1f}%" for v in regime_perf["win_rate"]*100],
        textposition="outside",
        textfont_color="#e2e8f0",
        hovertemplate="<b>%{x}</b><br>Win Rate: %{y:.1f}%<extra></extra>",
    ))
    # Add 50% reference line
    fig_wr.add_hline(y=50, line_dash="dot", line_color="#94a3b8",
                     annotation_text="50% break-even", annotation_position="right")
    fig_wr.update_layout(
        **{k: v for k, v in CHART_TEMPLATE.items() if k != 'yaxis'},
        title="Win Rate (%) per Sentiment Regime",
        xaxis_title="Regime",
        yaxis=dict(range=[0, 100], title="Win Rate (%)"),
        height=380,
    )
    st.plotly_chart(fig_wr, use_container_width=True)

with col_b:
    fig_pnl = go.Figure()
    colors_pos = [REGIME_COLORS[r] if v >= 0 else "#ef4444"
                  for r, v in zip(regime_perf["classification"], regime_perf["avg_pnl"])]
    fig_pnl.add_trace(go.Bar(
        name="Avg Net PnL",
        x=regime_perf["classification"],
        y=regime_perf["avg_pnl"],
        marker=dict(color=[REGIME_COLORS[r] for r in regime_perf["classification"]],
                    line=dict(color="#0a0a14", width=1.5), opacity=0.85),
        text=[f"${v:.2f}" for v in regime_perf["avg_pnl"]],
        textposition="outside",
        textfont_color="#e2e8f0",
    ))
    fig_pnl.add_trace(go.Scatter(
        name="Median Net PnL",
        x=regime_perf["classification"],
        y=regime_perf["median_pnl"],
        mode="markers+lines",
        marker=dict(size=10, color="#f59e0b", symbol="diamond"),
        line=dict(color="#f59e0b", width=2, dash="dot"),
    ))
    fig_pnl.add_hline(y=0, line_color="#475569", line_width=1)
    fig_pnl.update_layout(
        **CHART_TEMPLATE,
        title="Avg vs Median Net PnL per Regime",
        xaxis_title="Regime",
        yaxis_title="Net PnL (USD)",
        height=380,
    )
    st.plotly_chart(fig_pnl, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Heatmap: Regime × Direction ───────────────────────────────────────────────
section_header("🔥 Win Rate Heatmap — Regime × Trade Direction")

closed_dir = closed[closed["Direction"].isin(["Buy","Sell"])].copy()
heatmap_data = (
    closed_dir.groupby(["classification","Direction"])["is_profitable"]
    .mean().unstack(fill_value=0)
    .reindex(index=REGIME_ORDER)
)
heatmap_data.columns = [c for c in heatmap_data.columns]

fig_heat = go.Figure(go.Heatmap(
    z=heatmap_data.values * 100,
    x=heatmap_data.columns.tolist(),
    y=heatmap_data.index.tolist(),
    colorscale=[[0,"#7f1d1d"],[0.5,"#eab308"],[1,"#14532d"]],
    zmin=0, zmax=100,
    text=[[f"{v:.1f}%" for v in row] for row in heatmap_data.values * 100],
    texttemplate="%{text}",
    textfont=dict(size=16, color="#ffffff"),
    hovertemplate="<b>%{y} · %{x}</b><br>Win Rate: %{text}<extra></extra>",
    showscale=True,
    colorbar=dict(title="Win Rate %", ticksuffix="%"),
))
fig_heat.update_layout(
    **CHART_TEMPLATE,
    title="Win Rate Heatmap: Sentiment Regime × Direction<br><sup>Green = high win rate, Red = high loss rate</sup>",
    xaxis_title="Trade Direction",
    yaxis_title="Sentiment Regime",
    height=380,
)
st.plotly_chart(fig_heat, use_container_width=True)

# ── PnL Distribution Box Plots ────────────────────────────────────────────────
section_header("📦 PnL Distribution by Regime")

# Cap at 5th–95th percentile for readability
low_cap  = closed["net_pnl"].quantile(0.02)
high_cap = closed["net_pnl"].quantile(0.98)
closed_cap = closed[(closed["net_pnl"] >= low_cap) & (closed["net_pnl"] <= high_cap)].copy()

fig_box = go.Figure()
for regime in REGIME_ORDER:
    sub = closed_cap[closed_cap["classification"] == regime]["net_pnl"]
    if len(sub) > 0:
        hex_c = REGIME_COLORS[regime]
        r_c, g_c, b_c = int(hex_c[1:3],16), int(hex_c[3:5],16), int(hex_c[5:7],16)
        fig_box.add_trace(go.Box(
            y=sub,
            name=regime,
            marker_color=REGIME_COLORS[regime],
            line_color=REGIME_COLORS[regime],
            fillcolor=f"rgba({r_c},{g_c},{b_c},0.2)",
            boxmean="sd",
            hovertemplate=f"<b>{regime}</b><br>PnL: %{{y:.2f}}<extra></extra>",
        ))
fig_box.add_hline(y=0, line_dash="dot", line_color="#94a3b8")
fig_box.update_layout(
    **CHART_TEMPLATE,
    title="Net PnL Distribution per Regime (2nd–98th percentile, boxmean shows μ)",
    yaxis_title="Net PnL (USD)",
    xaxis_title="Sentiment Regime",
    height=400,
    showlegend=False,
)
st.plotly_chart(fig_box, use_container_width=True)

# ── Statistical significance ──────────────────────────────────────────────────
section_header("📐 Statistical Significance of Regime PnL Differences")

st.markdown("**One-sample t-test**: Does each regime's avg PnL differ significantly from $0.00?")

sig_rows = []
for regime in REGIME_ORDER:
    sub = closed[closed["classification"] == regime]["net_pnl"].dropna()
    if len(sub) > 10:
        t_stat, p_val = stats.ttest_1samp(sub, 0)
        sig_rows.append({
            "Regime":      regime,
            "N Trades":    len(sub),
            "Mean PnL":    f"${sub.mean():.4f}",
            "T-Statistic": f"{t_stat:.3f}",
            "P-Value":     f"{p_val:.4f}",
            "Significant?": "✅ Yes" if p_val < 0.05 else "❌ No",
        })

sig_df = pd.DataFrame(sig_rows)
st.dataframe(sig_df, use_container_width=True, hide_index=True)

# ── Insights ──────────────────────────────────────────────────────────────────
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
col_i1, col_i2 = st.columns(2)
with col_i1:
    insight_box(
        "Contrarian Longs Thesis",
        "If Buy win rates during <b>Extreme Fear</b> exceed those during Extreme Greed, "
        "it validates the classical contrarian strategy: <i>be fearful when others are greedy, "
        "and greedy when others are fearful</i> — now quantified with real on-chain data."
    )
with col_i2:
    insight_box(
        "Skewness vs Win Rate",
        "The box plots may show a <b>positive skew in profitable regimes</b> — a few very large wins "
        "pull the mean above the median. A high win rate with high skew suggests an environment "
        "where smart money bets small frequently and wins large occasionally."
    )
