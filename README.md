# PrimeTrade Intelligence Platform ⚡

A high-performance analytics dashboard that explores the relationship between trader performance (Hyperliquid) and market sentiment (Bitcoin Fear & Greed Index). Built with Python, Streamlit, and Plotly.

## Features

- **Sentiment Overview**: 7-year Bitcoin Fear & Greed timeline and regime transition matrix.
- **Volume Analysis**: Trade activity mapping and sentiment-elasticity scatter plots.
- **Win Rate Analysis**: Profitability heatmaps and statistical significance (t-tests) across regimes.
- **Transition Alpha**: Event-study analysis on T+1 to T+7 windows after regime shifts.
- **Trader Archetypes**: Unsupervised Machine Learning (K-Means + PCA) clustering trader behavior into distinct profiles.
- **Risk & Fee Analysis**: Position sizing, impulsive (crossed) order tracking, and fee erosion waterfalls.

## Data Sources

1. **Bitcoin Fear & Greed Index**: 2,645 days of sentiment data (2018–2025).
2. **Hyperliquid Trader Data**: 211,224 rows of historical trade executions (Dec 2024–Apr 2025).

## Running Locally

1. Clone the repository.
2. Install the requirements:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the Streamlit dashboard:
   ```bash
   streamlit run app.py
   ```
