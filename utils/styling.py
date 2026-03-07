"""
StratForge - Premium Styling Module
Glass-morphism CSS, animations, custom Plotly templates, and WCAG-compliant dark theme.
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.io as pio


def apply_custom_css():
    """Inject premium glass-morphism CSS into the Streamlit app."""
    st.markdown("""
    <style>
        /* ── Import Google Font ── */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        /* ── Global Base ── */
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif !important;
        }

        /* ── Main Container ── */
        .main .block-container {
            padding: 2rem 2.5rem 3rem 2.5rem;
            max-width: 1400px;
        }

        /* ── Sidebar ── */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #080C18 0%, #0D1325 50%, #111B33 100%) !important;
            border-right: 1px solid rgba(0, 212, 170, 0.12);
        }
        [data-testid="stSidebar"] .block-container {
            padding-top: 1.5rem;
        }

        /* ── Glass Card ── */
        .glass-card {
            background: rgba(17, 24, 39, 0.65);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(0, 212, 170, 0.10);
            border-radius: 16px;
            padding: 1.5rem 1.8rem;
            margin-bottom: 1rem;
            box-shadow:
                0 4px 24px rgba(0, 0, 0, 0.25),
                inset 0 1px 0 rgba(255, 255, 255, 0.04);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }
        .glass-card:hover {
            transform: translateY(-2px);
            box-shadow:
                0 8px 32px rgba(0, 212, 170, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.06);
        }

        /* ── KPI Metric Card ── */
        .kpi-card {
            background: rgba(17, 24, 39, 0.70);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(0, 212, 170, 0.10);
            border-radius: 16px;
            padding: 1.3rem 1.5rem;
            text-align: center;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.20);
            transition: transform 0.25s ease, box-shadow 0.25s ease;
            position: relative;
            overflow: hidden;
        }
        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0;
            height: 3px;
            background: linear-gradient(90deg, #00D4AA, #00B4D8, #7C3AED);
            border-radius: 16px 16px 0 0;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            box-shadow:
                0 8px 30px rgba(0, 212, 170, 0.15),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        .kpi-card .kpi-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #8B95A8;
            text-transform: uppercase;
            letter-spacing: 1.2px;
            margin-bottom: 0.4rem;
        }
        .kpi-card .kpi-value {
            font-size: 1.9rem;
            font-weight: 800;
            background: linear-gradient(135deg, #00D4AA, #00B4D8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.2;
        }
        .kpi-card .kpi-delta {
            font-size: 0.82rem;
            font-weight: 600;
            margin-top: 0.3rem;
        }
        .kpi-delta.positive { color: #00D4AA; }
        .kpi-delta.negative { color: #FF6B6B; }

        /* ── Section Header ── */
        .section-header {
            font-size: 1.4rem;
            font-weight: 700;
            color: #E8ECF1;
            margin: 1.5rem 0 0.8rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid rgba(0, 212, 170, 0.15);
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* ── Tabs ── */
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
            background: rgba(17, 24, 39, 0.40);
            border-radius: 12px;
            padding: 0.3rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            font-size: 0.85rem;
            color: #8B95A8;
            background: transparent;
            border: none;
        }
        .stTabs [aria-selected="true"] {
            background: rgba(0, 212, 170, 0.12) !important;
            color: #00D4AA !important;
            border: 1px solid rgba(0, 212, 170, 0.20) !important;
        }

        /* ── Buttons ── */
        .stButton > button {
            background: linear-gradient(135deg, #00D4AA 0%, #00B4D8 100%);
            color: #0A0E1A;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            font-size: 0.85rem;
            padding: 0.55rem 1.5rem;
            letter-spacing: 0.3px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px rgba(0, 212, 170, 0.25);
        }
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 24px rgba(0, 212, 170, 0.35);
        }

        /* ── Preset Buttons ── */
        .preset-btn {
            display: inline-block;
            background: rgba(0, 212, 170, 0.08);
            border: 1px solid rgba(0, 212, 170, 0.18);
            border-radius: 10px;
            padding: 0.5rem 1.2rem;
            font-weight: 600;
            font-size: 0.82rem;
            color: #00D4AA;
            cursor: pointer;
            transition: all 0.25s ease;
            text-align: center;
        }
        .preset-btn:hover {
            background: rgba(0, 212, 170, 0.15);
            box-shadow: 0 4px 14px rgba(0, 212, 170, 0.15);
        }

        /* ── Sliders ── */
        .stSlider > div > div > div {
            background: linear-gradient(90deg, #00D4AA, #00B4D8) !important;
        }
        .stSlider > div > div > div > div {
            background: #00D4AA !important;
            box-shadow: 0 0 8px rgba(0, 212, 170, 0.5);
        }

        /* ── Metrics ── */
        [data-testid="stMetric"] {
            background: rgba(17, 24, 39, 0.55);
            border: 1px solid rgba(0, 212, 170, 0.08);
            border-radius: 12px;
            padding: 1rem 1.2rem;
        }
        [data-testid="stMetricValue"] {
            font-size: 1.6rem;
            font-weight: 800;
        }

        /* ── DataFrames ── */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
        }

        /* ── Spinner / Loading ── */
        .loading-pulse {
            animation: pulse 1.8s ease-in-out infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 0.5; }
            50% { opacity: 1; }
        }

        /* ── Animated Gradient Border ── */
        .gradient-border {
            position: relative;
            border-radius: 16px;
            padding: 1.5rem;
            background: rgba(17, 24, 39, 0.65);
            overflow: hidden;
        }
        .gradient-border::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 16px;
            padding: 1.5px;
            background: linear-gradient(135deg, #00D4AA, #00B4D8, #7C3AED, #00D4AA);
            background-size: 300% 300%;
            -webkit-mask:
                linear-gradient(#fff 0 0) content-box,
                linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            animation: gradientShift 4s ease infinite;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        /* ── Feature Tile ── */
        .feature-tile {
            background: rgba(17, 24, 39, 0.55);
            border: 1px solid rgba(0, 212, 170, 0.08);
            border-radius: 14px;
            padding: 1.3rem;
            text-align: center;
            transition: all 0.3s ease;
        }
        .feature-tile:hover {
            border-color: rgba(0, 212, 170, 0.25);
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(0, 212, 170, 0.10);
        }
        .feature-tile .tile-icon {
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }
        .feature-tile .tile-title {
            font-size: 0.95rem;
            font-weight: 700;
            color: #E8ECF1;
        }
        .feature-tile .tile-desc {
            font-size: 0.78rem;
            color: #8B95A8;
            margin-top: 0.3rem;
        }

        /* ── Status Badge ── */
        .status-badge {
            display: inline-block;
            padding: 0.25rem 0.8rem;
            border-radius: 20px;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }
        .status-badge.success {
            background: rgba(0, 212, 170, 0.12);
            color: #00D4AA;
            border: 1px solid rgba(0, 212, 170, 0.25);
        }
        .status-badge.warning {
            background: rgba(255, 183, 77, 0.12);
            color: #FFB74D;
            border: 1px solid rgba(255, 183, 77, 0.25);
        }
        .status-badge.danger {
            background: rgba(255, 107, 107, 0.12);
            color: #FF6B6B;
            border: 1px solid rgba(255, 107, 107, 0.25);
        }

        /* ── Expander ── */
        .streamlit-expanderHeader {
            font-weight: 600;
            font-size: 0.9rem;
            color: #C5CDD8;
            background: rgba(17, 24, 39, 0.35);
            border-radius: 10px;
        }

        /* ── Scrollbar ── */
        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #0A0E1A; }
        ::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 170, 0.25);
            border-radius: 3px;
        }
        ::-webkit-scrollbar-thumb:hover { background: rgba(0, 212, 170, 0.40); }

        /* ── Hide Streamlit defaults ── */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }
    </style>
    """, unsafe_allow_html=True)


def get_plotly_template():
    """Return a premium dark Plotly template matching StratForge theme."""
    template = go.layout.Template()

    template.layout = go.Layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(17, 24, 39, 0.45)",
        font=dict(family="Inter, sans-serif", color="#C5CDD8", size=12),
        title=dict(font=dict(size=18, color="#E8ECF1", family="Inter, sans-serif")),
        xaxis=dict(
            gridcolor="rgba(139, 149, 168, 0.08)",
            zerolinecolor="rgba(139, 149, 168, 0.12)",
            linecolor="rgba(139, 149, 168, 0.15)",
            tickfont=dict(size=11),
        ),
        yaxis=dict(
            gridcolor="rgba(139, 149, 168, 0.08)",
            zerolinecolor="rgba(139, 149, 168, 0.12)",
            linecolor="rgba(139, 149, 168, 0.15)",
            tickfont=dict(size=11),
        ),
        legend=dict(
            bgcolor="rgba(17, 24, 39, 0.60)",
            bordercolor="rgba(0, 212, 170, 0.10)",
            borderwidth=1,
            font=dict(size=11),
        ),
        colorway=[
            "#00D4AA", "#00B4D8", "#7C3AED", "#FFB74D",
            "#FF6B6B", "#4FC3F7", "#AB47BC", "#66BB6A",
            "#FFA726", "#EF5350", "#29B6F6", "#EC407A",
        ],
        margin=dict(l=40, r=20, t=50, b=40),
        hoverlabel=dict(
            bgcolor="rgba(17, 24, 39, 0.90)",
            bordercolor="rgba(0, 212, 170, 0.20)",
            font=dict(size=12, color="#E8ECF1"),
        ),
    )

    return template


STRATFORGE_TEMPLATE = get_plotly_template()


def render_kpi_card(label, value, delta=None, delta_positive=True):
    """Render a premium KPI metric card with glass-morphism."""
    delta_html = ""
    if delta is not None:
        cls = "positive" if delta_positive else "negative"
        arrow = "▲" if delta_positive else "▼"
        delta_html = f'<div class="kpi-delta {cls}">{arrow} {delta}</div>'

    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)


def render_section_header(icon, title):
    """Render a styled section header."""
    st.markdown(f"""
    <div class="section-header">
        <span>{icon}</span> {title}
    </div>
    """, unsafe_allow_html=True)


def render_feature_tile(icon, title, description):
    """Render a navigation feature tile."""
    return f"""
    <div class="feature-tile">
        <div class="tile-icon">{icon}</div>
        <div class="tile-title">{title}</div>
        <div class="tile-desc">{description}</div>
    </div>
    """


def render_status_badge(text, status="success"):
    """Render a colored status badge. status: success | warning | danger"""
    return f'<span class="status-badge {status}">{text}</span>'


def format_currency(value, prefix="₹", decimals=0):
    """Format a number as a currency string with commas."""
    if abs(value) >= 1e7:
        return f"{prefix}{value / 1e7:.2f} Cr"
    elif abs(value) >= 1e5:
        return f"{prefix}{value / 1e5:.2f} L"
    elif abs(value) >= 1e3:
        return f"{prefix}{value / 1e3:.1f}K"
    else:
        return f"{prefix}{value:,.{decimals}f}"


def format_percentage(value, decimals=1):
    """Format a number as a percentage string."""
    return f"{value:+.{decimals}f}%"
