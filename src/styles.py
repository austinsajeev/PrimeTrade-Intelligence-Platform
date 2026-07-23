"""
styles.py
---------
Shared CSS injection and UI component helpers for the dashboard.
"""

import streamlit as st


GLOBAL_CSS = """
<style>
/* ── Fonts ───────────────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [data-testid="stApp"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide default Streamlit elements ─────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }

/* ── Sidebar ─────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d0d1a 0%, #111827 100%) !important;
    border-right: 1px solid rgba(124,58,237,0.2) !important;
}

[data-testid="stSidebarNav"] a {
    transition: all 0.2s ease;
}

/* ── Hero title ──────────────────────────────────────────────────────── */
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    background: linear-gradient(135deg, #a78bfa 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    line-height: 1.2;
    margin-bottom: 0.4rem;
}

.hero-subtitle {
    text-align: center;
    color: #94a3b8;
    font-size: 1.05rem;
    margin-bottom: 0.25rem;
}

.hero-badge {
    display: inline-block;
    background: linear-gradient(135deg, rgba(124,58,237,0.3), rgba(6,182,212,0.3));
    border: 1px solid rgba(124,58,237,0.5);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.78rem;
    color: #c4b5fd;
    margin: 0.5rem 0.25rem;
}

/* ── KPI Metric Cards ────────────────────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 1rem;
    margin: 1.5rem 0;
}

.kpi-card {
    background: linear-gradient(135deg, rgba(30,10,60,0.8), rgba(15,30,60,0.8));
    border: 1px solid rgba(124,58,237,0.35);
    border-radius: 16px;
    padding: 1.4rem 1rem;
    text-align: center;
    transition: all 0.3s cubic-bezier(0.4,0,0.2,1);
    position: relative;
    overflow: hidden;
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #7c3aed, #06b6d4);
}

.kpi-card:hover {
    border-color: rgba(124,58,237,0.7);
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(124,58,237,0.25);
}

.kpi-icon  { font-size: 1.6rem; margin-bottom: 0.5rem; display: block; }
.kpi-value { font-size: 1.9rem; font-weight: 700; color: #a78bfa; display: block; }
.kpi-label { font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: 0.05em; }
.kpi-delta { font-size: 0.78rem; color: #34d399; margin-top: 0.3rem; }

/* ── Section headers ─────────────────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin: 2rem 0 1rem;
}

.section-header-bar {
    width: 4px;
    height: 28px;
    background: linear-gradient(180deg, #7c3aed, #06b6d4);
    border-radius: 2px;
}

.section-header-text {
    font-size: 1.25rem;
    font-weight: 700;
    color: #f1f5f9;
}

/* ── Insight cards ───────────────────────────────────────────────────── */
.insight-card {
    background: linear-gradient(135deg, rgba(124,58,237,0.08), rgba(6,182,212,0.08));
    border: 1px solid rgba(124,58,237,0.3);
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin: 0.75rem 0;
    position: relative;
    overflow: hidden;
}

.insight-card::before {
    content: '';
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: linear-gradient(180deg, #7c3aed, #06b6d4);
}

.insight-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #c4b5fd;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-bottom: 0.35rem;
}

.insight-text {
    font-size: 0.95rem;
    color: #cbd5e1;
    line-height: 1.6;
}

/* ── Regime pill badges ──────────────────────────────────────────────── */
.regime-pill {
    display: inline-block;
    border-radius: 20px;
    padding: 2px 10px;
    font-size: 0.78rem;
    font-weight: 600;
}

.pill-extreme-fear  { background: rgba(220,38,38,0.2);  color: #fca5a5; border: 1px solid rgba(220,38,38,0.4); }
.pill-fear          { background: rgba(249,115,22,0.2); color: #fdba74; border: 1px solid rgba(249,115,22,0.4); }
.pill-neutral       { background: rgba(234,179,8,0.2);  color: #fde047; border: 1px solid rgba(234,179,8,0.4); }
.pill-greed         { background: rgba(34,197,94,0.2);  color: #86efac; border: 1px solid rgba(34,197,94,0.4); }
.pill-extreme-greed { background: rgba(22,163,74,0.2);  color: #4ade80; border: 1px solid rgba(22,163,74,0.4); }

/* ── Dividers ────────────────────────────────────────────────────────── */
.gradient-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(124,58,237,0.5), transparent);
    margin: 2rem 0;
}

/* ── Tabs ────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: rgba(17,24,39,0.8);
    border-radius: 10px;
    padding: 4px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 500 !important;
}
</style>
"""


def inject_css():
    """Inject the global dark CSS into the Streamlit app."""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, subtitle: str = ""):
    """Render a consistent gradient page header."""
    st.markdown(
        f"""
        <div style="text-align:center; padding: 1.5rem 0 1rem;">
            <div style="font-size:3rem; margin-bottom:0.5rem;">{icon}</div>
            <div class="hero-title" style="font-size:2rem;">{title}</div>
            {"<p class='hero-subtitle'>" + subtitle + "</p>" if subtitle else ""}
        </div>
        <div class="gradient-divider"></div>
        """,
        unsafe_allow_html=True,
    )


def section_header(text: str):
    """Render a section header with accent bar."""
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-header-bar"></div>
            <div class="section-header-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_box(title: str, text: str):
    """Render an insight callout card."""
    st.markdown(
        f"""
        <div class="insight-card">
            <div class="insight-title">💡 {title}</div>
            <div class="insight-text">{text}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render the shared sidebar present on every page."""
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; padding:1rem 0 0.5rem;">
            <div style="font-size:2rem;">⚡</div>
            <div style="font-weight:800; font-size:1.05rem; color:#a78bfa; line-height:1.3;">
                PrimeTrade<br>Intelligence
            </div>
            <div style="font-size:0.72rem; color:#64748b; margin-top:0.25rem;">
                Sentiment × Performance
            </div>
        </div>
        <hr style="border-color:rgba(124,58,237,0.25); margin:0.75rem 0;">
        """, unsafe_allow_html=True)

        pages = [
            ("🏠", "Home",               "/"),
            ("📊", "Sentiment Overview", "/Sentiment_Overview"),
            ("📈", "Volume Analysis",    "/Volume_Analysis"),
            ("🎯", "Win Rate Analysis",  "/Win_Rate_Analysis"),
            ("⚡", "Transition Alpha",   "/Transition_Alpha"),
            ("🧠", "Trader Archetypes",  "/Trader_Archetypes"),
            ("💰", "Risk & Fee Analysis","/Risk_Fee_Analysis"),
        ]
        st.markdown("<div style='font-size:0.72rem; color:#64748b; text-transform:uppercase; letter-spacing:0.08em; padding:0 0.25rem 0.4rem;'>Navigation</div>", unsafe_allow_html=True)
        for icon, label, path in pages:
            st.markdown(
                f"""<a href="{path}" target="_self" style="
                    display:flex; align-items:center; gap:0.6rem;
                    padding:0.5rem 0.75rem; border-radius:8px; margin-bottom:2px;
                    text-decoration:none; color:#cbd5e1; font-size:0.88rem;
                    transition:all 0.2s;
                    background:rgba(124,58,237,0.08);
                    border:1px solid rgba(124,58,237,0.15);
                ">
                <span style='font-size:1rem;'>{icon}</span>{label}</a>""",
                unsafe_allow_html=True,
            )

        st.markdown("""
        <hr style="border-color:rgba(124,58,237,0.15); margin:1rem 0 0.75rem;">
        <div style="font-size:0.75rem; color:#64748b; padding:0 0.25rem; line-height:1.7;">
            <b style="color:#a78bfa; font-size:0.72rem;">📁 DATASETS</b><br>
            Fear &amp; Greed Index<br>
            &nbsp;└ 2018–2025 · 2,645 days<br>
            Hyperliquid Trades<br>
            &nbsp;└ Dec 2024–Apr 2025<br>
            &nbsp;└ 211,224 rows
        </div>
        """, unsafe_allow_html=True)

