"""
Page 1 — Sentiment Overview
Provides a comprehensive exploration of the Bitcoin Fear & Greed Index
across its full 7-year history (2018–2025).
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

from src.data_loader import load_fear_greed, REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

st.set_page_config(page_title="Sentiment Overview", page_icon="📊", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar()
page_header("📊", "Sentiment Overview", "Bitcoin Fear & Greed Index · 2018–2025 · 2,645 Daily Records")

# ─── Load ─────────────────────────────────────────────────────────────────────
fg = load_fear_greed()

# ─── Tabs ─────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Full Timeline", "🔁 Regime Analysis", "📋 Transition Matrix"])

# ── Tab 1: Full Timeline ────────────────────────────────────────────────────
with tab1:
    section_header("Fear & Greed Index — Full History with Regime Bands")

    fig = go.Figure()
    # Regime band fills
    for regime, lo, hi in [
        ("Extreme Fear", 0,  25),
        ("Fear",         25, 46),
        ("Neutral",      46, 55),
        ("Greed",        55, 75),
        ("Extreme Greed",75, 100),
    ]:
        color = REGIME_COLORS[regime].replace(")", ",0.12)").replace("rgb","rgba") if "rgb" in REGIME_COLORS[regime] else REGIME_COLORS[regime]
        hex_c = REGIME_COLORS[regime]
        r, g, b = int(hex_c[1:3],16), int(hex_c[3:5],16), int(hex_c[5:7],16)
        fig.add_hrect(
            y0=lo, y1=hi,
            fillcolor=f"rgba({r},{g},{b},0.09)",
            line_width=0,
            annotation_text=regime,
            annotation_position="right",
            annotation_font_color=f"rgba({r},{g},{b},0.7)",
            annotation_font_size=10,
        )

    # Main index line
    fig.add_trace(go.Scatter(
        x=fg["date"], y=fg["value"],
        mode="lines",
        line=dict(color="#7c3aed", width=1.5),
        fill="tozeroy",
        fillcolor="rgba(124,58,237,0.06)",
        name="Daily Index",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>Score: %{y}<extra></extra>",
    ))
    # 7-day moving average
    fig.add_trace(go.Scatter(
        x=fg["date"], y=fg["fg_7d_avg"],
        mode="lines",
        line=dict(color="#f59e0b", width=1.8, dash="dot"),
        name="7d MA",
        hovertemplate="7d Avg: %{y:.1f}<extra></extra>",
    ))
    # 30-day moving average
    fig.add_trace(go.Scatter(
        x=fg["date"], y=fg["fg_30d_avg"],
        mode="lines",
        line=dict(color="#06b6d4", width=2),
        name="30d MA",
        hovertemplate="30d Avg: %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        **{k: v for k, v in CHART_TEMPLATE.items() if k != 'yaxis'},
        title="Bitcoin Fear & Greed Index (2018–2025) — Daily Values with Moving Averages",
        xaxis_title="Date",
        yaxis=dict(range=[0, 100], title="Index Score"),
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)

    # Summary stats per year
    section_header("📅 Annual Sentiment Summary")
    fg_year = fg.copy()
    fg_year["year"] = fg_year["date"].dt.year
    annual = fg_year.groupby("year")["value"].agg(["mean","min","max","std"]).round(1)
    annual.columns = ["Avg Score", "Min", "Max", "Std Dev"]
    def color_avg(val):
        if val < 25: return "color:#fca5a5"
        elif val < 46: return "color:#fdba74"
        elif val < 55: return "color:#fde047"
        elif val < 75: return "color:#86efac"
        else: return "color:#4ade80"
    st.dataframe(
        annual.style.applymap(color_avg, subset=["Avg Score"]),
        use_container_width=True,
    )

# ── Tab 2: Regime Analysis ──────────────────────────────────────────────────
with tab2:
    col_a, col_b = st.columns([1,1])

    with col_a:
        section_header("Regime Time Distribution")
        rc = fg["classification"].value_counts().reindex(REGIME_ORDER).fillna(0)
        fig_pie = go.Figure(go.Pie(
            labels=rc.index,
            values=rc.values,
            hole=0.55,
            marker=dict(
                colors=[REGIME_COLORS[r] for r in rc.index],
                line=dict(color="#0a0a14", width=2.5),
            ),
            textinfo="label+percent",
            insidetextorientation="radial",
        ))
        fig_pie.update_layout(
            **CHART_TEMPLATE,
            title="Days Spent in Each Sentiment Regime",
            height=380,
            showlegend=False,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        section_header("Average Score by Regime (Validation)")
        regime_avg = fg.groupby("classification")["value"].agg(["mean","std","count"]).reindex(REGIME_ORDER).fillna(0).reset_index()
        fig_bar = go.Figure(go.Bar(
            x=regime_avg["classification"],
            y=regime_avg["mean"],
            error_y=dict(type="data", array=regime_avg["std"], visible=True, color="#94a3b8"),
            marker_color=[REGIME_COLORS[r] for r in regime_avg["classification"]],
            marker_line_color="#0a0a14",
            marker_line_width=1.5,
            text=regime_avg["mean"].round(1),
            textposition="outside",
            textfont_color="#e2e8f0",
        ))
        fig_bar.update_layout(
            **CHART_TEMPLATE,
            title="Mean Index Score per Regime ± 1 Std Dev",
            xaxis_title="Regime",
            yaxis_title="Average Score",
            height=380,
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Regime streaks (longest continuous periods)
    section_header("🏆 Longest Consecutive Regime Streaks")
    streaks = []
    current_regime = None
    streak_start = None
    streak_count = 0
    for _, row in fg.iterrows():
        if row["classification"] == current_regime:
            streak_count += 1
        else:
            if current_regime:
                streaks.append({"Regime": current_regime, "Start": streak_start, "Days": streak_count})
            current_regime = row["classification"]
            streak_start = row["date"]
            streak_count = 1
    streaks_df = pd.DataFrame(streaks).sort_values("Days", ascending=False).head(10).reset_index(drop=True)
    streaks_df["Start"] = streaks_df["Start"].dt.strftime("%b %d, %Y")
    st.dataframe(
        streaks_df.style.background_gradient(subset=["Days"], cmap="RdYlGn"),
        use_container_width=True, hide_index=True
    )

# ── Tab 3: Transition Matrix ────────────────────────────────────────────────
with tab3:
    section_header("Sentiment Regime Transition Frequency Matrix")

    # Build transition count matrix
    transitions = fg.dropna(subset=["prev_class"]).copy()
    trans_matrix = transitions.groupby(["prev_class","classification"]).size().unstack(fill_value=0)
    trans_matrix = trans_matrix.reindex(index=REGIME_ORDER, columns=REGIME_ORDER, fill_value=0)

    # Normalize to probabilities
    trans_prob = trans_matrix.div(trans_matrix.sum(axis=1), axis=0).round(3)

    fig_heatmap = go.Figure(go.Heatmap(
        z=trans_prob.values,
        x=trans_prob.columns,
        y=trans_prob.index,
        colorscale=[[0,"rgba(15,15,30,1)"],[0.5,"rgba(124,58,237,0.6)"],[1,"rgba(6,182,212,1)"]],
        text=[[f"{v:.1%}" for v in row] for row in trans_prob.values],
        texttemplate="%{text}",
        textfont=dict(size=13, color="#f1f5f9"),
        hovertemplate="<b>%{y} → %{x}</b><br>Probability: %{text}<extra></extra>",
        showscale=True,
        colorbar=dict(title="Probability", tickformat=".0%"),
    ))
    fig_heatmap.update_layout(
        **CHART_TEMPLATE,
        title="Day-to-Day Regime Transition Probability Matrix<br><sup>Row = current regime, Column = next day regime</sup>",
        xaxis_title="Next Day Regime",
        yaxis_title="Current Regime",
        height=440,
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

    insight_box(
        "Self-Persistence Bias",
        "The diagonal values reveal strong <b>regime persistence</b>: market sentiment tends to "
        "stay in the same zone for consecutive days. Extreme regimes (Extreme Fear / Extreme Greed) "
        "show the highest persistence, confirming that <b>emotional extremes do not reverse overnight</b>. "
        "This is the statistical foundation for the Transition Alpha event study."
    )
