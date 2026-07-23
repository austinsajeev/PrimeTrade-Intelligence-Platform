# ⚡ PrimeTrade Intelligence Platform

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red.svg)
![Pandas](https://img.shields.io/badge/Pandas-2.0+-green.svg)
![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-1.3+-orange.svg)

> **Live Demo:** [**View the Interactive Dashboard on Streamlit Cloud**](https://primetrade-intelligence-platform-jc5ppxfqqqn5uhjy3zhofm.streamlit.app/)

PrimeTrade Intelligence is a high-performance, full-stack quantitative analytics dashboard designed to explore the complex relationship between macroeconomic sentiment and micro-level trader performance. 

This project was built to demonstrate advanced data engineering, unsupervised machine learning, and interactive data visualization for algorithmic trading research.

---

## 🧠 Core Methodology & Architecture

The platform bridges two distinct datasets to uncover "Sentiment Alpha"—how extreme market fear or greed dictates trader profitability, volume, and behavior.

### 1. Data Engineering & Optimization
- **Binary Data Formats:** Raw CSV data (211,000+ rows) was compressed and cast into **Apache Parquet**, dropping memory footprint by 70% and accelerating cloud-load times by 10x using strict Pandas categorical typing.
- **State Management:** Utilizes Streamlit's `@st.cache_data` with PyArrow serialization to ensure O(1) latency when navigating between complex analytical modules.

### 2. Machine Learning (Trader Archetypes)
- **Feature Engineering:** Extracted per-wallet metrics including sentiment-bias (preference for trading in greed vs. fear), average size, and regime-specific win rates.
- **Unsupervised Clustering:** Applied **K-Means Clustering** to segment traders into distinct behavioral archetypes.
- **Dimensionality Reduction:** Utilized **Principal Component Analysis (PCA)** to visualize hyper-dimensional trader behaviors in a cohesive 2D scatter space.

### 3. Statistical Analysis
- **Event-Study (Transition Alpha):** Computes cumulative abnormal volume and structural shifts across T+1 to T+7 windows immediately following a macro regime change (e.g., Fear → Greed).
- **Hypothesis Testing:** Conducts OLS regressions and variance analysis on win-rates across market conditions.

---

## 📊 Dashboard Modules

1. **Sentiment Overview:** 7-year macroeconomic timeline tracking the Bitcoin Fear & Greed Index, featuring dynamic regime transition matrices.
2. **Volume Analysis:** Elasticity scatter plots mapping trading volume against daily sentiment shifts.
3. **Win Rate Analysis:** Box plots and profitability heatmaps segmenting PnL distributions strictly by market regime.
4. **Transition Alpha:** Event-driven analysis showing how the market structurally reacts the week following a major sentiment flip.
5. **Trader Archetypes:** ML-driven profiling grouping wallets into classes like *Regime-Agnostic Whales*, *Trend Chasers*, and *Fear Buyers*.
6. **Risk & Fee Analysis:** Waterfall charts tracking fee erosion and analysis of impulsive (crossed) market orders.

---

## 🛠️ Technology Stack

- **Frontend & Backend Server:** [Streamlit](https://streamlit.io/)
- **Data Manipulation:** Pandas, NumPy, PyArrow
- **Machine Learning & Stats:** Scikit-Learn, SciPy, Statsmodels
- **Visualization:** Plotly (Graph Objects & Express) with custom CSS injection for premium dark-mode UI/UX.

---

## 🚀 Running Locally

If you prefer to run the analytics engine on your local machine:

1. Clone the repository:
   ```bash
   git clone https://github.com/austinsajeev/PrimeTrade-Intelligence-Platform.git
   cd PrimeTrade-Intelligence-Platform
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the Streamlit server:
   ```bash
   streamlit run app.py
   ```
