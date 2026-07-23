"""
Page 5 — Trader Archetypes (Behavioral Clustering)
Uses K-Means + PCA to segment traders into behavioral profiles
based on how they respond to different sentiment regimes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score

from src.data_loader import (
    load_merged, load_trader_profiles,
    REGIME_COLORS, REGIME_ORDER, CHART_TEMPLATE,
)
from src.styles import inject_css, page_header, section_header, insight_box, render_sidebar

st.set_page_config(page_title="Trader Archetypes", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")
inject_css()
render_sidebar()
page_header("🧠", "Trader Behavioral Archetypes",
            "K-Means clustering reveals 4 distinct trader profiles defined by sentiment-driven behavior")

# ─── Load trader profiles ──────────────────────────────────────────────────────
with st.spinner("Building per-trader feature matrix …"):
    profiles = load_trader_profiles()

st.success(f"✅ Trader profiles built: **{len(profiles):,} traders** with ≥5 closed trades")

st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)

# ─── Feature selection for clustering ─────────────────────────────────────────
section_header("🔧 Feature Engineering for Clustering")

feature_cols = [
    "overall_win_rate",
    "avg_size_usd",
    "sentiment_bias",      # greed_pct − fear_pct
    "greed_pct",
    "fear_pct",
    "total_trades",
]
# Win rates per regime (only those available)
for regime in REGIME_ORDER:
    col = f"winrate_{regime.lower().replace(' ', '_')}"
    if col in profiles.columns:
        feature_cols.append(col)

feature_cols = [c for c in feature_cols if c in profiles.columns]
X_raw = profiles[feature_cols].fillna(0)

with st.expander("📋 View Feature Matrix (first 10 rows)"):
    st.dataframe(X_raw.head(10), use_container_width=True)

# ─── Optimal K selection ───────────────────────────────────────────────────────
section_header("📐 Optimal Cluster Count — Elbow + Silhouette")

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_raw)

k_range = range(2, 9)
inertias, silhouettes = [], []
for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)
    inertias.append(km.inertia_)
    if k > 1 and len(set(labels)) > 1:
        silhouettes.append(silhouette_score(X_scaled, labels))
    else:
        silhouettes.append(0)

col_elbow, col_sil = st.columns(2)

with col_elbow:
    fig_elbow = go.Figure()
    fig_elbow.add_trace(go.Scatter(
        x=list(k_range), y=inertias,
        mode="lines+markers",
        line=dict(color="#7c3aed", width=2.5),
        marker=dict(size=10, color="#7c3aed",
                    line=dict(color="#0a0a14", width=2)),
        name="Inertia",
    ))
    fig_elbow.update_layout(
        **CHART_TEMPLATE,
        title="Elbow Method — Inertia vs K",
        xaxis_title="Number of Clusters (K)",
        yaxis_title="Within-Cluster Inertia",
        height=300,
    )
    st.plotly_chart(fig_elbow, use_container_width=True)

with col_sil:
    fig_sil = go.Figure()
    fig_sil.add_trace(go.Scatter(
        x=list(k_range), y=silhouettes,
        mode="lines+markers",
        line=dict(color="#06b6d4", width=2.5),
        marker=dict(size=10, color="#06b6d4",
                    line=dict(color="#0a0a14", width=2)),
        name="Silhouette",
    ))
    fig_sil.update_layout(
        **CHART_TEMPLATE,
        title="Silhouette Score vs K",
        xaxis_title="Number of Clusters (K)",
        yaxis_title="Silhouette Score",
        height=300,
    )
    st.plotly_chart(fig_sil, use_container_width=True)

# ─── Clustering ───────────────────────────────────────────────────────────────
section_header("🎯 K-Means Clustering (K=4)")

N_CLUSTERS = st.slider("Adjust number of clusters:", min_value=2, max_value=6, value=4)

km_final = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=15)
cluster_labels = km_final.fit_predict(X_scaled)
profiles["cluster"] = cluster_labels

# ─── PCA for 2D visualisation ─────────────────────────────────────────────────
pca = PCA(n_components=2, random_state=42)
X_pca = pca.fit_transform(X_scaled)
profiles["pca_1"] = X_pca[:, 0]
profiles["pca_2"] = X_pca[:, 1]

var_explained = pca.explained_variance_ratio_ * 100

ARCHETYPE_NAMES = {
    0: "🔴 Momentum Chaser",
    1: "🟡 Scared Sideliner",
    2: "🟢 Contrarian Predator",
    3: "🔵 Systematic Algo",
    4: "🟣 Whale Trader",
    5: "⚪ Mixed Profile",
}
ARCHETYPE_COLORS = ["#ef4444","#eab308","#22c55e","#3b82f6","#a78bfa","#94a3b8"]

profiles["archetype"] = profiles["cluster"].map(
    lambda c: ARCHETYPE_NAMES.get(c, f"Cluster {c}")
)

# ─── PCA Scatter ──────────────────────────────────────────────────────────────
section_header("🗺️ Trader Archetype Map — PCA Projection")

fig_pca = go.Figure()
# Derive display label from Account column
profiles["Account_short"] = profiles["Account"].str[:6] + "…" + profiles["Account"].str[-4:]

for c_id in sorted(profiles["cluster"].unique()):
    sub = profiles[profiles["cluster"] == c_id]
    arch_name = ARCHETYPE_NAMES.get(c_id, f"Cluster {c_id}")
    color = ARCHETYPE_COLORS[c_id % len(ARCHETYPE_COLORS)]
    fig_pca.add_trace(go.Scatter(
        x=sub["pca_1"], y=sub["pca_2"],
        mode="markers",
        name=arch_name,
        marker=dict(
            size=np.clip(np.log1p(sub["total_trades"]) * 3, 5, 20),
            color=color,
            opacity=0.75,
            line=dict(color="#0a0a14", width=0.5),
        ),
        customdata=sub[["Account_short","overall_win_rate","total_trades","total_pnl","sentiment_bias"]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Win Rate: %{customdata[1]:.1%}<br>"
            "Trades: %{customdata[2]:.0f}<br>"
            "Net PnL: $%{customdata[3]:.2f}<br>"
            "Sentiment Bias: %{customdata[4]:+.2f}<br>"
            f"<b>{arch_name}</b><extra></extra>"
        ),
    ))

fig_pca.update_layout(
    **CHART_TEMPLATE,
    title=(
        f"Trader Behavioral Archetypes — PCA Projection<br>"
        f"<sup>PC1 explains {var_explained[0]:.1f}% variance · "
        f"PC2 explains {var_explained[1]:.1f}% variance · "
        f"Marker size ∝ log(trade count)</sup>"
    ),
    xaxis_title=f"PC1 ({var_explained[0]:.1f}% variance)",
    yaxis_title=f"PC2 ({var_explained[1]:.1f}% variance)",
    height=520,
)
st.plotly_chart(fig_pca, use_container_width=True)

# ─── Archetype profiles ────────────────────────────────────────────────────────
section_header("📊 Archetype Profile Comparison")

cluster_profile = (
    profiles.groupby("cluster")
    .agg(
        n_traders       = ("Account","count"),
        avg_win_rate    = ("overall_win_rate","mean"),
        avg_total_pnl   = ("total_pnl","mean"),
        avg_trades      = ("total_trades","mean"),
        avg_size_usd    = ("avg_size_usd","mean"),
        avg_sentiment_bias = ("sentiment_bias","mean"),
        avg_greed_pct   = ("greed_pct","mean"),
        avg_fear_pct    = ("fear_pct","mean"),
    )
    .reset_index()
)
cluster_profile["archetype"] = cluster_profile["cluster"].map(
    lambda c: ARCHETYPE_NAMES.get(c, f"Cluster {c}")
)
cluster_profile = cluster_profile.drop(columns=["cluster"])
cluster_profile = cluster_profile.rename(columns={
    "n_traders": "# Traders",
    "avg_win_rate": "Win Rate",
    "avg_total_pnl": "Avg Net PnL",
    "avg_trades": "Avg Trades",
    "avg_size_usd": "Avg Size (USD)",
    "avg_sentiment_bias": "Sentiment Bias",
    "avg_greed_pct": "Greed %",
    "avg_fear_pct": "Fear %",
    "archetype": "Archetype",
})

cp = cluster_profile.set_index("Archetype")
cp["Win Rate"] = cp["Win Rate"].map(lambda v: f"{v:.1%}")
cp["Avg Net PnL"] = cp["Avg Net PnL"].map(lambda v: f"${v:,.2f}")
cp["Avg Size (USD)"] = cp["Avg Size (USD)"].map(lambda v: f"${v:,.0f}")
cp["Sentiment Bias"] = cp["Sentiment Bias"].map(lambda v: f"{v:+.3f}")
cp["Greed %"] = cp["Greed %"].map(lambda v: f"{v:.1%}")
cp["Fear %"] = cp["Fear %"].map(lambda v: f"{v:.1%}")
st.dataframe(cp, use_container_width=True)

# ─── Radar chart ──────────────────────────────────────────────────────────────
section_header("🕸️ Archetype Radar — Multi-Dimensional Profile")

radar_features = ["overall_win_rate","greed_pct","fear_pct","avg_size_usd","total_trades","total_pnl"]
radar_labels   = ["Win Rate","Greed %","Fear %","Avg Size","# Trades","Total PnL"]

# Normalise each feature to 0-1 for radar
radar_df = profiles.groupby("cluster")[radar_features].mean().reset_index()
for feat in radar_features:
    rng = radar_df[feat].max() - radar_df[feat].min()
    radar_df[feat] = (radar_df[feat] - radar_df[feat].min()) / (rng if rng > 0 else 1)

fig_radar = go.Figure()
for _, row in radar_df.iterrows():
    c_id = int(row["cluster"])
    color = ARCHETYPE_COLORS[c_id % len(ARCHETYPE_COLORS)]
    fig_radar.add_trace(go.Scatterpolar(
        r=row[radar_features].tolist() + [row[radar_features[0]]],
        theta=radar_labels + [radar_labels[0]],
        fill="toself",
        name=ARCHETYPE_NAMES.get(c_id, f"C{c_id}"),
        line_color=color,
        fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.15)",
    ))
fig_radar.update_layout(
    **CHART_TEMPLATE,
    polar=dict(
        radialaxis=dict(visible=True, range=[0,1], color="#475569"),
        bgcolor="rgba(15,15,30,0.5)",
    ),
    title="Archetype Radar (Normalised 0–1 per Feature)",
    height=480,
)
st.plotly_chart(fig_radar, use_container_width=True)

# ─── Archetype descriptions ────────────────────────────────────────────────────
st.markdown('<div class="gradient-divider"></div>', unsafe_allow_html=True)
section_header("📖 Archetype Intelligence Profiles")

arch_descriptions = [
    ("🔴", "Momentum Chaser",
     "Trades heavily during Greed regimes. Position sizes inflate as the market heats up (overconfidence effect). "
     "Win rate is good mid-trend but deteriorates sharply at Extreme Greed peaks — enters too late. "
     "<b>Risk profile: High reward short-term, high blowup risk at tops.</b>"),
    ("🟡", "Scared Sideliner",
     "Paralysed during Fear/Extreme Fear — misses the best contrarian entries. Low overall trade count. "
     "When they do trade, signal quality is high (conviction filter). But they systematically underperform "
     "by skipping the highest-alpha regimes. <b>Risk profile: Opportunity cost is their primary loss.</b>"),
    ("🟢", "Contrarian Predator",
     "Elevated activity during Extreme Fear — the exact opposite of the crowd. Lower average size but higher win rate. "
     "Consistent PnL across regime cycles. Likely informed or experienced. "
     "<b>Risk profile: Smart money archetype. Signals worth following.</b>"),
    ("🔵", "Systematic Algo",
     "Uniform trade frequency and size across all sentiment regimes. Win rate is consistent regardless of market mood. "
     "Sentiment is effectively noise for this trader. Likely quantitative or market-making strategy. "
     "<b>Risk profile: Lowest sentiment sensitivity. Most regime-agnostic.</b>"),
]

cols = st.columns(2)
for i, (icon, name, desc) in enumerate(arch_descriptions):
    with cols[i % 2]:
        color = ARCHETYPE_COLORS[i]
        st.markdown(f"""
        <div class="insight-card" style="border-left-color:{color}; margin-bottom:1rem;">
            <div class="insight-title" style="color:{color};">{icon} {name}</div>
            <div class="insight-text">{desc}</div>
        </div>
        """, unsafe_allow_html=True)
