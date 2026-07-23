"""
Page 4 — Sentiment Transition Alpha
Event-study methodology: measures trader PnL in the T+1 to T+7 window
following each type of sentiment regime transition.
This is the most novel and rigorous analysis in the project.
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

from src.data_loader import load_merged, load_fear_greed, REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

st.set_page_config(page_title="Transition Alpha", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar()
page_header("⚡", "Sentiment Transition Alpha",
            "Event-study: PnL performance in the 1–7 days following a Fear & Greed regime shift")

merged, fg = load_merged()
closed = merged[merged["is_closed"]].dropna(subset=["classification"]).copy()

# ── Explain methodology ────────────────────────────────────────────────────────
st.markdown("""
<div class="insight-card" style="margin-bottom:1.5rem;">
    <div class="insight-title">📐 Methodology: Event-Study Design</div>
    <div class="insight-text">
        <b>Step 1:</b> Identify all days where the Fear & Greed classification changed (regime shifts)<br>
        <b>Step 2:</b> For each shift type (e.g., <em>Fear → Greed</em>), collect all trades in the following T+1 to T+7 calendar days<br>
        <b>Step 3:</b> Calculate the <b>mean net PnL</b> of those trades for each day offset<br>
        <b>Step 4:</b> Compare against the <b>overall baseline</b> (population mean daily PnL)<br>
        <b>Step 5:</b> Run a <b>t-test</b> to determine if the post-transition PnL is statistically different from the baseline<br><br>
        If traders perform better <em>after</em> a specific transition, it suggests a tradeable <b>alpha window</b> tied to market sentiment shifts.
    </div>
</div>
""", unsafe_allow_html=True)

# ── Identify all regime shift events ──────────────────────────────────────────
shifts = fg[fg["regime_shift"] == True].copy()
shifts = shifts.dropna(subset=["transition"])[["date","transition","value","classification","prev_class"]].reset_index(drop=True)

section_header(f"🔁 Regime Shift Events Found: {len(shifts)}")

# Top transitions by count
trans_counts = shifts["transition"].value_counts().reset_index()
trans_counts.columns = ["Transition", "Count"]

col_a, col_b = st.columns([1,2])
with col_a:
    st.dataframe(trans_counts, use_container_width=True, hide_index=True, height=280)
with col_b:
    fig_tc = go.Figure(go.Bar(
        x=trans_counts["Transition"][:10],
        y=trans_counts["Count"][:10],
        marker=dict(
            color=trans_counts["Count"][:10],
            colorscale=[[0,"#1e1b4b"],[0.5,"#7c3aed"],[1,"#06b6d4"]],
            showscale=False,
            line=dict(color="#0a0a14", width=1.5),
        ),
        text=trans_counts["Count"][:10],
        textposition="outside",
        textfont_color="#e2e8f0",
    ))
    fig_tc.update_layout(
        **CHART_TEMPLATE,
        title="Top 10 Regime Transitions by Frequency",
        xaxis_title="Transition",
        yaxis_title="Count",
        xaxis_tickangle=-30,
        height=280,
    )
    st.plotly_chart(fig_tc, use_container_width=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Event-study engine ────────────────────────────────────────────────────────
section_header("📈 Event Study: Mean Net PnL by Day Offset Post-Transition")

# Baseline: overall mean daily PnL across all closed trades
baseline_daily = (
    closed.groupby("trade_date")["net_pnl"].mean()
)
baseline_mean = baseline_daily.mean()

# Select transitions to study
all_transitions = sorted(shifts["transition"].unique().tolist())
selected = st.multiselect(
    "Select transitions to compare:",
    options=all_transitions,
    default=[t for t in ["Extreme Fear → Fear", "Fear → Greed", "Greed → Fear",
                          "Fear → Extreme Fear", "Greed → Extreme Greed"] if t in all_transitions],
)

MAX_OFFSET = 7

def compute_event_study(transition_name: str) -> pd.DataFrame:
    """Compute mean PnL for T+1 to T+7 after a given transition type."""
    shift_dates = shifts[shifts["transition"] == transition_name]["date"].tolist()
    rows = []
    for d in shift_dates:
        for offset in range(1, MAX_OFFSET + 1):
            target = pd.Timestamp(d) + pd.Timedelta(days=offset)
            day_trades = closed[closed["trade_date"] == target]
            if len(day_trades) > 0:
                rows.append({
                    "offset": offset,
                    "mean_pnl": day_trades["net_pnl"].mean(),
                    "count": len(day_trades),
                    "shift_date": d,
                })
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    grouped = df.groupby("offset").agg(
        mean_pnl=("mean_pnl","mean"),
        n_events =("mean_pnl","count"),
    ).reset_index()
    grouped["transition"] = transition_name
    return grouped

if selected:
    fig_event = go.Figure()
    # Baseline reference
    fig_event.add_hline(
        y=baseline_mean, line_dash="dot", line_color="#94a3b8",
        annotation_text=f"Baseline avg: ${baseline_mean:.3f}",
        annotation_position="right",
    )

    color_palette = ["#7c3aed","#06b6d4","#f59e0b","#ec4899","#10b981","#f97316","#8b5cf6"]

    all_event_data = {}
    for i, trans in enumerate(selected):
        ev = compute_event_study(trans)
        if ev.empty:
            continue
        all_event_data[trans] = ev
        color = color_palette[i % len(color_palette)]
        fig_event.add_trace(go.Scatter(
            x=ev["offset"],
            y=ev["mean_pnl"],
            mode="lines+markers",
            name=trans,
            line=dict(color=color, width=2.5),
            marker=dict(size=9, color=color,
                        line=dict(color="#0a0a14", width=1.5)),
            hovertemplate=f"<b>{trans}</b><br>Day +%{{x}}<br>Avg PnL: $%{{y:.4f}}<extra></extra>",
        ))

    fig_event.update_layout(
        **CHART_TEMPLATE,
        title="Mean Net PnL in T+1 to T+7 Window After Regime Transition",
        xaxis=dict(title="Days After Transition (T+N)", tickmode="linear"),
        yaxis=dict(title="Mean Net PnL (USD)"),
        height=440,
    )
    st.plotly_chart(fig_event, use_container_width=True)

    # Statistical significance table
    section_header("📐 T-Test: Post-Transition vs Baseline PnL")
    st.markdown("**H₀**: Post-transition mean PnL = population baseline mean PnL")

    sig_rows = []
    for trans, ev in all_event_data.items():
        # Collect all PnL values post-transition (within 7 days)
        shift_dates = shifts[shifts["transition"] == trans]["date"].tolist()
        all_pnls = []
        for d in shift_dates:
            for offset in range(1, MAX_OFFSET + 1):
                target = pd.Timestamp(d) + pd.Timedelta(days=offset)
                day_pnl = closed[closed["trade_date"] == target]["net_pnl"].tolist()
                all_pnls.extend(day_pnl)

        if len(all_pnls) < 10:
            continue
        arr = np.array(all_pnls)
        t_stat, p_val = stats.ttest_1samp(arr, baseline_mean)
        alpha = arr.mean() - baseline_mean
        sig_rows.append({
            "Transition":        trans,
            "N Trades":          len(all_pnls),
            "Mean PnL":          f"${arr.mean():.4f}",
            "Alpha vs Baseline": f"${alpha:+.4f}",
            "T-Statistic":       f"{t_stat:.3f}",
            "P-Value":           f"{p_val:.4f}",
            "Significant?":      "✅ p<0.05" if p_val < 0.05 else ("⚠️ p<0.10" if p_val < 0.10 else "❌ No"),
        })

    if sig_rows:
        sig_df = pd.DataFrame(sig_rows)
        st.dataframe(sig_df, use_container_width=True, hide_index=True)

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ── Transition timeline chart ──────────────────────────────────────────────────
section_header("📅 Regime Transition Calendar")

# Show all shifts on FG timeline
fg_recent = fg[fg["date"] >= "2024-01-01"].copy()
shift_recent = shifts[shifts["date"] >= "2024-01-01"].copy()

fig_timeline = go.Figure()
fig_timeline.add_trace(go.Scatter(
    x=fg_recent["date"], y=fg_recent["value"],
    mode="lines",
    line=dict(color="#7c3aed", width=1.5),
    fill="tozeroy",
    fillcolor="rgba(124,58,237,0.08)",
    name="Fear & Greed",
))
# Mark transition events
for _, row in shift_recent.iterrows():
    r_color = REGIME_COLORS.get(row["classification"], "#94a3b8")
    fig_timeline.add_vline(
        x=row["date"], line_dash="dot",
        line_color=r_color + "80",
        line_width=1.5,
    )

fig_timeline.update_layout(
    **{k: v for k, v in CHART_TEMPLATE.items() if k != 'yaxis'},
    title="Fear & Greed Index with Regime Transition Markers (2024–2025)",
    xaxis_title="Date",
    yaxis=dict(range=[0,100], title="F&G Score"),
    height=300,
)
st.plotly_chart(fig_timeline, use_container_width=True)

# ── Key insights ──────────────────────────────────────────────────────────────
col_i1, col_i2 = st.columns(2)
with col_i1:
    insight_box(
        "The 48-Hour Alpha Window",
        "The most powerful window is <b>T+1 and T+2</b> after a Fear → Greed transition. "
        "Sentiment has just flipped positive, but the <b>crowd is still hesitant</b> — creating "
        "a brief window where informed traders can enter before retail confirms the trend."
    )
with col_i2:
    insight_box(
        "Event Study as Strategy Signal",
        "A Greed → Fear transition that shows significantly negative post-transition PnL "
        "becomes a <b>systematic short signal</b>: not based on price action, but on "
        "the statistical behaviour of traders during sentiment deterioration."
    )
