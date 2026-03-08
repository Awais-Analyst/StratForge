"""
StratForge – Risk Fortress (Monte Carlo Simulation)
10k–50k simulations, fan chart, VaR/CVaR, scenario paths, presets.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.styling import apply_custom_css, render_kpi_card, render_section_header, STRATFORGE_TEMPLATE, format_currency
from utils.data_utils import init_session_state, compute_kpis, get_col
from utils.monte_carlo import run_simulation, RISK_PRESETS

st.set_page_config(page_title="StratForge – Risk Simulation", page_icon="🎲", layout="wide")
apply_custom_css()
init_session_state()

# ── Header ──
st.markdown("""
<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.3rem;">
    <span style="font-size:2rem;">🎲</span>
    <div>
        <div style="font-size:1.6rem; font-weight:800; color:#E8ECF1;">Risk Fortress</div>
        <div style="font-size:0.8rem; color:#6B7280;">Monte Carlo simulation with 10k+ scenarios, VaR, fan charts & stress testing</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Guard ──
if not st.session_state.data_loaded or st.session_state.df is None:
    st.warning("⚠️ No data loaded. Go to **Data Studio** first.")
    st.stop()

df = st.session_state.df

# Determine base value from mapped revenue column
rev_col = get_col("revenue")
base_value = float(df[rev_col].iloc[-1]) if rev_col and rev_col in df.columns else 1_000_000

# ── Configuration ──
col_cfg, col_main = st.columns([1, 3])

with col_cfg:
    st.markdown("#### ⚙️ Simulation Settings")

    # Scenario Presets
    render_section_header("🎯", "Quick Presets")
    preset_choice = st.selectbox(
        "Load Preset",
        ["Custom"] + list(RISK_PRESETS.keys()),
        key="risk_preset",
    )

    if preset_choice != "Custom":
        p = RISK_PRESETS[preset_choice]
        default_growth = p["growth_rate"]
        default_vol = p["volatility"]
        st.caption(f"_{p['description']}_")
    else:
        default_growth = 0.08
        default_vol = 0.15

    st.markdown("---")

    base_val = st.number_input(
        "💰 Base Value (current period)",
        min_value=10_000.0,
        value=float(base_value),
        step=50_000.0,
        format="%.0f",
        key="mc_base",
    )

    growth_rate = st.slider(
        "📈 Expected Growth Rate",
        min_value=-0.20, max_value=0.50,
        value=float(default_growth),
        step=0.01,
        format="%.2f",
        key="mc_growth",
        help="Annual expected growth rate (e.g., 0.08 = 8%)",
    )

    volatility = st.slider(
        "📊 Volatility",
        min_value=0.01, max_value=0.60,
        value=float(default_vol),
        step=0.01,
        key="mc_vol",
        help="Annual standard deviation of returns",
    )

    periods = st.slider("📅 Horizon (months)", 3, 36, 12, key="mc_periods")

    n_sims = st.select_slider(
        "🎲 Simulations",
        options=[1000, 2500, 5000, 10000, 20000, 50000],
        value=10000,
        key="mc_nsims",
    )
    if n_sims > 20000:
        st.caption("⚠️ >20k sims may take a few seconds")

    target_growth = st.slider(
        "🎯 Target Growth %",
        min_value=0, max_value=100, value=20,
        key="mc_target",
        help="Probability of exceeding this growth target",
    )

    run_btn = st.button("🚀 Run Simulation", use_container_width=True, key="mc_run")

with col_main:
    if run_btn:
        with st.spinner(f"Running {n_sims:,} Monte Carlo simulations..."):
            sim = run_simulation(
                base_value=base_val,
                growth_rate=growth_rate,
                volatility=volatility,
                periods=periods,
                n_simulations=n_sims,
                seed=42,
            )

        # Recalculate target-specific metrics
        final_values = np.array(sim["final_values"])
        target_val = base_val * (1 + target_growth / 100)
        prob_target = float(np.mean(final_values > target_val) * 100)
        metrics = sim["metrics"]
        metrics["prob_target"] = prob_target
        metrics["target_growth_pct"] = target_growth
        metrics["target_value"] = target_val

        st.session_state.simulation_results = sim

        # ── KPI Cards ──
        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            render_kpi_card(
                "Expected Value",
                format_currency(metrics["mean"]),
                f"{metrics['expected_return_pct']:+.1f}% return",
                metrics["expected_return_pct"] > 0,
            )
        with k2:
            render_kpi_card("Median Value", format_currency(metrics["median"]))
        with k3:
            render_kpi_card(
                f"P(>{target_growth}% Growth)",
                f"{prob_target:.1f}%",
                "Target hit" if prob_target > 50 else "Below 50%",
                prob_target > 50,
            )
        with k4:
            render_kpi_card(
                "VaR (95%)",
                format_currency(metrics["var_95"]),
                "5% worst case",
                False,
            )
        with k5:
            render_kpi_card(
                "P(Profit)",
                f"{metrics['prob_profit']:.1f}%",
                "Above base" if metrics["prob_profit"] > 50 else "Risk zone",
                metrics["prob_profit"] > 50,
            )

        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

        # ── Distribution Plot ──
        render_section_header("📊", "Outcome Distribution")

        fig_dist = go.Figure()

        # Histogram
        fig_dist.add_trace(go.Histogram(
            x=final_values,
            nbinsx=80,
            marker_color="rgba(0, 212, 170, 0.55)",
            marker_line=dict(color="#00D4AA", width=0.5),
            name="Frequency",
        ))

        # VaR lines
        fig_dist.add_vline(x=metrics["var_95"], line=dict(color="#FF6B6B", dash="dash", width=2),
                          annotation_text="VaR 95%", annotation_font_color="#FF6B6B")
        fig_dist.add_vline(x=metrics["mean"], line=dict(color="#00B4D8", dash="solid", width=2),
                          annotation_text="Mean", annotation_font_color="#00B4D8")
        fig_dist.add_vline(x=target_val, line=dict(color="#FFB74D", dash="dot", width=2),
                          annotation_text=f"Target ({target_growth}%)", annotation_font_color="#FFB74D")
        fig_dist.add_vline(x=base_val, line=dict(color="#8B95A8", dash="dot", width=1.5),
                          annotation_text="Base", annotation_font_color="#8B95A8")

        fig_dist.update_layout(
            template=STRATFORGE_TEMPLATE, height=420,
            title=f"Distribution of Final Values ({n_sims:,} simulations)",
            xaxis_title="Final Value (₹)", yaxis_title="Frequency",
            showlegend=False,
        )
        st.plotly_chart(fig_dist, use_container_width=True)

        # ── Fan Chart / Cone of Uncertainty ──
        render_section_header("🌊", "Cone of Uncertainty (Fan Chart)")

        fan = sim["fan_chart"]
        months = list(range(periods + 1))
        month_labels = [f"M{i}" for i in months]

        fig_fan = go.Figure()

        # 5–95 band
        fig_fan.add_trace(go.Scatter(
            x=months + months[::-1],
            y=fan["p95"] + fan["p5"][::-1],
            fill="toself", fillcolor="rgba(0, 212, 170, 0.06)",
            line=dict(color="rgba(0,0,0,0)"), name="5th–95th",
            showlegend=True,
        ))
        # 10–90 band
        fig_fan.add_trace(go.Scatter(
            x=months + months[::-1],
            y=fan["p90"] + fan["p10"][::-1],
            fill="toself", fillcolor="rgba(0, 212, 170, 0.10)",
            line=dict(color="rgba(0,0,0,0)"), name="10th–90th",
            showlegend=True,
        ))
        # 25–75 band
        fig_fan.add_trace(go.Scatter(
            x=months + months[::-1],
            y=fan["p75"] + fan["p25"][::-1],
            fill="toself", fillcolor="rgba(0, 212, 170, 0.16)",
            line=dict(color="rgba(0,0,0,0)"), name="25th–75th",
            showlegend=True,
        ))
        # Median line
        fig_fan.add_trace(go.Scatter(
            x=months, y=fan["p50"],
            line=dict(color="#00D4AA", width=3), name="Median",
        ))

        fig_fan.update_layout(
            template=STRATFORGE_TEMPLATE, height=420,
            title="Simulation Path Cone",
            xaxis_title="Month", yaxis_title="Value (₹)",
            xaxis=dict(tickmode="array", tickvals=months, ticktext=month_labels),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_fan, use_container_width=True)

        # ── Scenario Paths ──
        render_section_header("🛤️", "Scenario Paths")

        scenarios = sim["scenarios"]
        fig_paths = go.Figure()
        fig_paths.add_trace(go.Scatter(
            x=months, y=scenarios["best"], name="Best Case",
            line=dict(color="#00D4AA", width=2.5),
        ))
        fig_paths.add_trace(go.Scatter(
            x=months, y=scenarios["median"], name="Median Case",
            line=dict(color="#00B4D8", width=2.5),
        ))
        fig_paths.add_trace(go.Scatter(
            x=months, y=scenarios["worst"], name="Worst Case",
            line=dict(color="#FF6B6B", width=2.5),
        ))
        fig_paths.add_hline(y=base_val, line=dict(color="#8B95A8", dash="dot", width=1),
                           annotation_text="Base Value")

        fig_paths.update_layout(
            template=STRATFORGE_TEMPLATE, height=380,
            title="Best / Median / Worst Scenario Paths",
            xaxis_title="Month", yaxis_title="Value (₹)",
            xaxis=dict(tickmode="array", tickvals=months, ticktext=month_labels),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_paths, use_container_width=True)

        # ── Detailed Metrics ──
        with st.expander("📋 Detailed Risk Metrics", expanded=False):
            m1, m2 = st.columns(2)
            with m1:
                st.markdown("##### Return Metrics")
                st.markdown(f"""
                | Metric | Value |
                |--------|-------|
                | Expected Return | {metrics['expected_return_pct']:+.2f}% |
                | Return Std Dev | {metrics['return_std_pct']:.2f}% |
                | Skewness | {metrics['skewness']:.3f} |
                | Kurtosis | {metrics['kurtosis']:.3f} |
                """)
            with m2:
                st.markdown("##### Percentiles")
                st.markdown(f"""
                | Percentile | Value |
                |------------|-------|
                | P10 | {format_currency(metrics['p10'])} |
                | P25 | {format_currency(metrics['p25'])} |
                | P50 (Median) | {format_currency(metrics['p50'])} |
                | P75 | {format_currency(metrics['p75'])} |
                | P90 | {format_currency(metrics['p90'])} |
                """)

        # ── Download ──
        csv_data = pd.DataFrame({
            "Simulation": range(1, len(sim["final_values"]) + 1),
            "Final_Value": sim["final_values"],
        })
        st.download_button(
            "📥 Download Simulation Results (CSV)",
            data=csv_data.to_csv(index=False).encode("utf-8"),
            file_name="stratforge_monte_carlo_results.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">🎲</div>
            <div style="font-size:1.1rem; color:#8B95A8;">
                Configure parameters and click <strong style="color:#00D4AA;">Run Simulation</strong> to begin Monte Carlo analysis
            </div>
            <div style="font-size:0.78rem; color:#4B5563; margin-top:0.5rem;">
                Use presets for quick scenario comparison or fine-tune each parameter manually
            </div>
        </div>
        """, unsafe_allow_html=True)
