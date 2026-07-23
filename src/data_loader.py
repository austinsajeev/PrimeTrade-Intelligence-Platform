"""
data_loader.py
--------------
Central data loading, cleaning, and feature engineering module.
All other pages import from here. Streamlit @st.cache_data decorators
ensure data is loaded only once across the entire session.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import streamlit as st

# ─── Paths ────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent
FEAR_GREED_PATH = ROOT_DIR / "fear_greed_index.csv"
HISTORICAL_PATH = ROOT_DIR / "historical_data.parquet"

# ─── Constants ────────────────────────────────────────────────────────────────
REGIME_ORDER = ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]
REGIME_ORDINAL = {r: i for i, r in enumerate(REGIME_ORDER)}

REGIME_COLORS = {
    "Extreme Fear": "#dc2626",
    "Fear":         "#f97316",
    "Neutral":      "#eab308",
    "Greed":        "#22c55e",
    "Extreme Greed":"#16a34a",
}

CHART_TEMPLATE = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(10,10,20,0)",
    plot_bgcolor="rgba(15,15,30,0.6)",
    font=dict(family="Inter, sans-serif", color="#e2e8f0", size=12),
    title_font=dict(size=16, color="#f1f5f9"),
    margin=dict(l=50, r=30, t=60, b=50),
)

# Reusable axis style dict — apply manually when needed
AXIS_STYLE = dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.1)")


# ─── Loaders ─────────────────────────────────────────────────────────────────

@st.cache_data(show_spinner="⚡ Loading Fear & Greed Index …")
def load_fear_greed() -> pd.DataFrame:
    """Load and enrich the Bitcoin Fear & Greed Index dataset."""
    df = pd.read_csv(FEAR_GREED_PATH)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)

    # Ordinal encoding
    df["regime_ordinal"] = df["classification"].map(REGIME_ORDINAL)

    # Rolling metrics
    df["fg_7d_avg"]  = df["value"].rolling(7,  min_periods=1).mean()
    df["fg_30d_avg"] = df["value"].rolling(30, min_periods=1).mean()
    df["fg_delta"]   = df["value"].diff().fillna(0)

    # Transition detection
    df["prev_class"]     = df["classification"].shift(1)
    df["regime_shift"]   = (df["classification"] != df["prev_class"]) & df["prev_class"].notna()
    df["transition"]     = df.apply(
        lambda r: f"{r['prev_class']} → {r['classification']}"
        if pd.notna(r["prev_class"]) else None,
        axis=1,
    )

    return df


@st.cache_data(show_spinner="⚡ Loading 211K+ trade records …")
def load_trades() -> pd.DataFrame:
    """Load, clean and feature-engineer the Hyperliquid trade history."""
    df = pd.read_parquet(HISTORICAL_PATH)

    # ── Timestamps ──────────────────────────────────────────────────────────
    df["trade_date"] = df["Timestamp IST"].dt.normalize()
    df["hour"]       = df["Timestamp IST"].dt.hour
    df["month_year"] = df["Timestamp IST"].dt.to_period("M").astype(str)

    # ── Numerics ─────────────────────────────────────────────────────────────
    for col in ["Execution Price", "Size Tokens", "Size USD",
                "Closed PnL", "Fee", "Start Position"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Boolean ──────────────────────────────────────────────────────────────
    df["Crossed"] = df["Crossed"].astype(str).str.upper().str.strip() == "TRUE"

    # ── Derived features ─────────────────────────────────────────────────────
    df["net_pnl"]        = df["Closed PnL"].fillna(0) - df["Fee"].fillna(0)
    df["is_closed"]      = df["Closed PnL"].abs() > 0          # row is a closed trade
    df["is_profitable"]  = df["net_pnl"] > 0
    df["pnl_per_usd"]    = np.where(
        df["Size USD"] > 0, df["net_pnl"] / df["Size USD"], np.nan
    )
    df["gross_pnl"]      = df["Closed PnL"].fillna(0)
    df["fee_drag"]       = df["Fee"].fillna(0)

    # Short wallet address for display
    df["Account_short"] = (df["Account"].str[:6] + "…" + df["Account"].str[-4:]).astype("category")

    # Normalize Direction column
    df["Direction"] = df["Direction"].str.strip().str.title().astype("category")

    # Memory Optimization: Convert other string columns to categoricals
    for cat_col in ["Account", "Symbol", "Event", "Side"]:
        if cat_col in df.columns:
            df[cat_col] = df[cat_col].astype("category")

    # Drop original timestamp to save memory since we extracted what we need
    if "Timestamp IST" in df.columns:
        df = df.drop(columns=["Timestamp IST"])

    return df


@st.cache_data(show_spinner="⚡ Joining datasets on trade date …")
def load_merged() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return (merged_trades, fear_greed) joined on trade date."""
    fg     = load_fear_greed()
    trades = load_trades()

    fg_slim = fg[[
        "date", "value", "classification",
        "fg_7d_avg", "fg_30d_avg", "fg_delta",
        "regime_ordinal", "regime_shift", "transition",
    ]].rename(columns={"value": "fg_value"})

    merged = trades.merge(fg_slim, left_on="trade_date", right_on="date", how="left")
    return merged, fg


@st.cache_data(show_spinner="⚡ Building trader profiles …")
def load_trader_profiles() -> pd.DataFrame:
    """
    Aggregate per-wallet statistics for behavioral clustering.
    Returns one row per Account with features across all sentiment regimes.
    """
    merged, _ = load_merged()
    closed = merged[merged["is_closed"]].copy()

    # Overall stats
    overall = closed.groupby("Account").agg(
        total_trades   = ("net_pnl", "count"),
        total_pnl      = ("net_pnl", "sum"),
        overall_win_rate = ("is_profitable", "mean"),
        avg_size_usd   = ("Size USD", "mean"),
        total_volume   = ("Size USD", "sum"),
    ).reset_index()

    # Per-regime stats (trade count share and win rate)
    regime_stats = []
    for regime in REGIME_ORDER:
        sub = closed[closed["classification"] == regime]
        by_acc = sub.groupby("Account").agg(
            trade_count_r = ("net_pnl", "count"),
            win_rate_r    = ("is_profitable", "mean"),
            avg_size_r    = ("Size USD", "mean"),
        ).rename(columns={
            "trade_count_r": f"trades_{regime.lower().replace(' ', '_')}",
            "win_rate_r":    f"winrate_{regime.lower().replace(' ', '_')}",
            "avg_size_r":    f"avgsize_{regime.lower().replace(' ', '_')}",
        })
        regime_stats.append(by_acc)

    # Total by account for % calculation
    total_by_acc = closed.groupby("Account")["net_pnl"].count().rename("total_closed")

    profiles = overall.set_index("Account")
    for rs in regime_stats:
        profiles = profiles.join(rs, how="left")
    profiles = profiles.join(total_by_acc, how="left")
    profiles = profiles.fillna(0).reset_index()

    # Derive % of trades in each regime
    for regime in REGIME_ORDER:
        col = f"trades_{regime.lower().replace(' ', '_')}"
        pct_col = f"pct_{regime.lower().replace(' ', '_')}"
        profiles[pct_col] = profiles[col] / profiles["total_closed"].replace(0, np.nan)
        profiles[pct_col] = profiles[pct_col].fillna(0)

    # Sentiment sensitivity: ratio of greed-regime trading to fear-regime trading
    profiles["greed_pct"] = (
        profiles.get("pct_greed", 0) + profiles.get("pct_extreme_greed", 0)
    )
    profiles["fear_pct"] = (
        profiles.get("pct_fear", 0) + profiles.get("pct_extreme_fear", 0)
    )
    profiles["sentiment_bias"] = profiles["greed_pct"] - profiles["fear_pct"]

    # Filter to traders with meaningful activity
    profiles = profiles[profiles["total_trades"] >= 5].copy()

    return profiles
