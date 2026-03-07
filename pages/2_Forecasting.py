"""
StratForge – Crystal Ball Forecasting
SARIMA / Holt-Winters / Naive model comparison + What-If War Room.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.styling import apply_custom_css, render_kpi_card, render_section_header, STRATFORGE_TEMPLATE, format_currency
from utils.data_utils import init_session_state, auto_detect_columns
from utils.forecast_utils import (
    run_sarima_forecast,
    run_exp_smoothing,
    run_naive_forecast,
    decompose_series,
    apply_what_if,
)

st.set_page_config(page_title="StratForge – Forecasting", page_icon="🔮", layout="wide")
apply_custom_css()
init_session_state()

# ── Header ──
st.markdown("""
<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.3rem;">
    <span style="font-size:2rem;">🔮</span>
    <div>
        <div style="font-size:1.6rem; font-weight:800; color:#E8ECF1;">Crystal Ball Forecasting</div>
        <div style="font-size:0.8rem; color:#6B7280;">Predict the future with SARIMA, Holt-Winters & What-If scenarios</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Guard ──
if not st.session_state.data_loaded or st.session_state.df is None:
    st.warning("⚠️ No data loaded. Go to **Data Studio** first to load your dataset.")
    st.stop()

df = st.session_state.df
col_types = auto_detect_columns(df)
date_cols = col_types["date"]
num_cols = col_types["numeric"]

if not date_cols or not num_cols:
    st.error("❌ Need at least one date and one numeric column for forecasting.")
    st.stop()

# ── Tabs ──
tab_forecast, tab_whatif, tab_decomp = st.tabs([
    "🔮 Forecast & Compare", "⚔️ What-If War Room", "🔬 Trend Decomposition"
])

# ═══════════════════════════════════════════════════
#  TAB 1: FORECAST & MODEL COMPARISON
# ═══════════════════════════════════════════════════
with tab_forecast:
    col_cfg, col_chart = st.columns([1, 3])

    with col_cfg:
        st.markdown("#### ⚙️ Settings")
        date_col = st.selectbox("Date Column", date_cols, key="fc_date")
        target_col = st.selectbox("Target Variable", num_cols, key="fc_target")
        horizon = st.slider("Forecast Horizon (months)", 3, 36, 12, key="fc_horizon")

        models_to_run = st.multiselect(
            "Models",
            ["SARIMA", "Holt-Winters", "Seasonal Naive"],
            default=["SARIMA", "Holt-Winters"],
            key="fc_models",
        )

        run_btn = st.button("🚀 Run Forecast", use_container_width=True, key="fc_run")

    with col_chart:
        if run_btn and models_to_run:
            # Prepare series
            series_df = df[[date_col, target_col]].dropna()
            if not pd.api.types.is_datetime64_any_dtype(series_df[date_col]):
                series_df[date_col] = pd.to_datetime(series_df[date_col])
            series_df = series_df.sort_values(date_col)
            series_values = series_df[target_col].values.tolist()
            series_index = series_df[date_col].dt.strftime("%Y-%m-%d").tolist()

            results = {}
            progress = st.progress(0)

            for i, model_name in enumerate(models_to_run):
                with st.spinner(f"Fitting {model_name}..."):
                    if model_name == "SARIMA":
                        results["SARIMA"] = run_sarima_forecast(
                            tuple(series_values), tuple(series_index), horizon
                        )
                    elif model_name == "Holt-Winters":
                        results["Holt-Winters"] = run_exp_smoothing(
                            tuple(series_values), tuple(series_index), horizon
                        )
                    elif model_name == "Seasonal Naive":
                        results["Seasonal Naive"] = run_naive_forecast(
                            tuple(series_values), tuple(series_index), horizon
                        )
                progress.progress((i + 1) / len(models_to_run))

            # Store in session state for What-If tab
            st.session_state.forecast_results = results

            # ── Plot ──
            fig = go.Figure()

            # Historical
            fig.add_trace(go.Scatter(
                x=pd.to_datetime(series_index), y=series_values,
                name="Historical", line=dict(color="#8B95A8", width=2),
                mode="lines",
            ))

            # Model forecasts
            model_colors = {"SARIMA": "#00D4AA", "Holt-Winters": "#00B4D8", "Seasonal Naive": "#FFB74D"}
            for model_name, res in results.items():
                if not res.get("success"):
                    st.warning(f"⚠️ {res.get('error', f'{model_name} failed')}")
                    continue

                fc_dates = pd.to_datetime(res["forecast_dates"])
                color = model_colors.get(model_name, "#7C3AED")

                # Forecast line
                fig.add_trace(go.Scatter(
                    x=fc_dates, y=res["forecast"],
                    name=f"{model_name} Forecast",
                    line=dict(color=color, width=2.5, dash="dot"),
                ))

                # Confidence interval
                fig.add_trace(go.Scatter(
                    x=list(fc_dates) + list(fc_dates)[::-1],
                    y=res["conf_upper"] + res["conf_lower"][::-1],
                    fill="toself",
                    fillcolor=f"rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.08)",
                    line=dict(color="rgba(0,0,0,0)"),
                    name=f"{model_name} 95% CI",
                    showlegend=False,
                ))

            fig.update_layout(
                template=STRATFORGE_TEMPLATE, height=500,
                title=f"{target_col.replace('_', ' ')} Forecast — {horizon} Months",
                xaxis_title="Date", yaxis_title=target_col.replace("_", " "),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Model Comparison Table ──
            render_section_header("📊", "Model Comparison")
            comp_data = []
            for model_name, res in results.items():
                if res.get("success"):
                    comp_data.append({
                        "Model": model_name,
                        "AIC": f"{res.get('aic', 'N/A'):.1f}" if res.get('aic') else "N/A",
                        "BIC": f"{res.get('bic', 'N/A'):.1f}" if res.get('bic') else "N/A",
                        "Forecast Mean": f"₹{np.mean(res['forecast']):,.0f}",
                        "Forecast Range": f"₹{min(res['forecast']):,.0f} – ₹{max(res['forecast']):,.0f}",
                    })
            if comp_data:
                st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)

        elif not run_btn:
            st.markdown("""
            <div class="glass-card" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">🔮</div>
                <div style="font-size:1.1rem; color:#8B95A8;">
                    Configure your settings and click <strong style="color:#00D4AA;">Run Forecast</strong> to begin
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  TAB 2: WHAT-IF WAR ROOM
# ═══════════════════════════════════════════════════
with tab_whatif:
    st.markdown("""
    <div class="glass-card">
        <div style="font-size:1rem; font-weight:700; color:#E8ECF1; margin-bottom:0.3rem;">
            ⚔️ What-If Scenario Simulator
        </div>
        <div style="font-size:0.78rem; color:#6B7280;">
            Adjust business parameters to see their live impact on your forecast
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Scenario Presets
    render_section_header("🎯", "Quick Presets")
    preset_cols = st.columns(4)
    presets = {
        "🚀 Aggressive Growth": (15, 40, 5),
        "✂️ Cost-Cutting": (-5, -20, -15),
        "⚖️ Balanced": (5, 10, 3),
        "📉 Recession": (-10, -30, 20),
    }

    selected_preset = None
    for i, (name, values) in enumerate(presets.items()):
        with preset_cols[i]:
            if st.button(name, use_container_width=True, key=f"preset_{i}"):
                selected_preset = values

    # Sliders
    col_s1, col_s2, col_s3 = st.columns(3)
    default_price = selected_preset[0] if selected_preset else 0
    default_budget = selected_preset[1] if selected_preset else 0
    default_cost = selected_preset[2] if selected_preset else 0

    with col_s1:
        price_change = st.slider("💲 Price Change (%)", -30, 50, default_price, key="wi_price")
    with col_s2:
        budget_change = st.slider("📢 Marketing Budget (%)", -50, 100, default_budget, key="wi_budget")
    with col_s3:
        cost_change = st.slider("📦 Cost Inflation (%)", -20, 40, default_cost, key="wi_cost")

    # Get base forecast
    if st.session_state.forecast_results:
        # Use best available forecast
        for model in ["SARIMA", "Holt-Winters", "Seasonal Naive"]:
            if model in st.session_state.forecast_results and st.session_state.forecast_results[model].get("success"):
                base_result = st.session_state.forecast_results[model]
                break
        else:
            base_result = None

        if base_result:
            what_if = apply_what_if(
                base_result["forecast"],
                price_change_pct=price_change,
                budget_change_pct=budget_change,
                cost_change_pct=cost_change,
            )

            # Impact KPIs
            ki1, ki2, ki3, ki4 = st.columns(4)
            base_total = sum(what_if["base_forecast"])
            adj_total = sum(what_if["adjusted_forecast"])
            net_impact = adj_total - base_total

            with ki1:
                render_kpi_card("Base Forecast Total", format_currency(base_total))
            with ki2:
                render_kpi_card(
                    "Adjusted Forecast",
                    format_currency(adj_total),
                    f"{what_if['net_change_pct']:+.1f}%",
                    what_if["net_change_pct"] > 0,
                )
            with ki3:
                render_kpi_card(
                    "Net Impact",
                    format_currency(net_impact),
                    "Gain" if net_impact > 0 else "Loss",
                    net_impact > 0,
                )
            with ki4:
                render_kpi_card("Confidence", "Scenario Model", "What-If Engine")

            # Waterfall Chart
            render_section_header("📊", "Impact Waterfall")
            categories = ["Base", "Price Effect", "Marketing Effect", "Cost Effect", "Adjusted"]
            values = [
                base_total,
                sum(what_if["price_impact"]),
                sum(what_if["marketing_impact"]),
                sum(what_if["cost_impact"]),
                adj_total,
            ]
            measures = ["absolute", "relative", "relative", "relative", "total"]

            fig_waterfall = go.Figure(go.Waterfall(
                x=categories, y=values, measure=measures,
                increasing=dict(marker_color="#00D4AA"),
                decreasing=dict(marker_color="#FF6B6B"),
                totals=dict(marker_color="#00B4D8"),
                connector=dict(line=dict(color="#374151", width=1)),
                textposition="outside",
                texttemplate="%{y:,.0f}",
                textfont=dict(size=10, color="#C5CDD8"),
            ))
            fig_waterfall.update_layout(
                template=STRATFORGE_TEMPLATE, height=420,
                title="Revenue Impact Breakdown",
                showlegend=False,
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

            # Monthly Comparison
            fc_dates = pd.to_datetime(base_result["forecast_dates"])
            fig_comp = go.Figure()
            fig_comp.add_trace(go.Scatter(
                x=fc_dates, y=what_if["base_forecast"],
                name="Base Forecast", line=dict(color="#8B95A8", width=2, dash="dash"),
            ))
            fig_comp.add_trace(go.Scatter(
                x=fc_dates, y=what_if["adjusted_forecast"],
                name="Adjusted Forecast", line=dict(color="#00D4AA", width=3),
            ))
            fig_comp.update_layout(
                template=STRATFORGE_TEMPLATE, height=380,
                title="Monthly: Base vs Adjusted",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
            )
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("No successful forecast found. Run a forecast in the **Forecast & Compare** tab first.")
    else:
        st.info("📌 Run a forecast in the **Forecast & Compare** tab first, then come back here to simulate What-If scenarios.")

# ═══════════════════════════════════════════════════
#  TAB 3: TREND DECOMPOSITION
# ═══════════════════════════════════════════════════
with tab_decomp:
    col_d1, col_d2 = st.columns([1, 3])

    with col_d1:
        st.markdown("#### ⚙️ Settings")
        d_date = st.selectbox("Date Column", date_cols, key="dc_date")
        d_target = st.selectbox("Target Variable", num_cols, key="dc_target")
        d_model = st.selectbox("Decomposition Model", ["additive", "multiplicative"], key="dc_model")
        d_period = st.slider("Seasonal Period", 2, 24, 12, key="dc_period")
        d_run = st.button("🔬 Decompose", use_container_width=True, key="dc_run")

    with col_d2:
        if d_run:
            series_df = df[[d_date, d_target]].dropna()
            if not pd.api.types.is_datetime64_any_dtype(series_df[d_date]):
                series_df[d_date] = pd.to_datetime(series_df[d_date])
            series_df = series_df.sort_values(d_date)

            if len(series_df) < d_period * 2:
                st.error(f"❌ Need at least {d_period * 2} data points. You have {len(series_df)}.")
            else:
                result = decompose_series(
                    tuple(series_df[d_target].values.tolist()),
                    tuple(series_df[d_date].dt.strftime("%Y-%m-%d").tolist()),
                    model=d_model,
                    period=d_period,
                )

                if not result.get("success"):
                    st.error(f"❌ {result.get('error')}")
                else:
                    dates = pd.to_datetime(result["dates"])
                    components = [
                        ("Observed", result["observed"], "#00D4AA"),
                        ("Trend", result["trend"], "#00B4D8"),
                        ("Seasonal", result["seasonal"], "#7C3AED"),
                        ("Residual", result["residual"], "#FFB74D"),
                    ]

                    fig_decomp = make_subplots(rows=4, cols=1, shared_xaxes=True,
                                               subplot_titles=[c[0] for c in components],
                                               vertical_spacing=0.06)
                    for i, (name, values, color) in enumerate(components, 1):
                        fig_decomp.add_trace(go.Scatter(
                            x=dates, y=values, name=name,
                            line=dict(color=color, width=2),
                            showlegend=False,
                        ), row=i, col=1)
                    fig_decomp.update_layout(
                        template=STRATFORGE_TEMPLATE, height=700,
                        title=f"{d_model.title()} Decomposition — {d_target.replace('_', ' ')}",
                    )
                    st.plotly_chart(fig_decomp, use_container_width=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">🔬</div>
                <div style="font-size:1.1rem; color:#8B95A8;">
                    Select a variable and click <strong style="color:#00D4AA;">Decompose</strong> to view trend, seasonal, and residual components
                </div>
            </div>
            """, unsafe_allow_html=True)
