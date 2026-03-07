"""
StratForge – Optimization Engine
PuLP LP budget allocation, pricing optimization, sensitivity analysis.
Supports continuous + integer variables.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.styling import apply_custom_css, render_kpi_card, render_section_header, STRATFORGE_TEMPLATE, format_currency
from utils.data_utils import init_session_state
from utils.optimization import (
    optimize_budget_allocation,
    run_sensitivity_analysis,
    optimize_pricing,
    OPTIMIZATION_PRESETS,
)

st.set_page_config(page_title="StratForge – Optimization", page_icon="⚡", layout="wide")
apply_custom_css()
init_session_state()

# ── Header ──
st.markdown("""
<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.3rem;">
    <span style="font-size:2rem;">⚡</span>
    <div>
        <div style="font-size:1.6rem; font-weight:800; color:#E8ECF1;">Optimization Engine</div>
        <div style="font-size:0.8rem; color:#6B7280;">Optimal budget allocation & pricing via linear programming — same math as Amazon & Google</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

# ── Tabs ──
tab_budget, tab_pricing, tab_sensitivity = st.tabs([
    "💰 Budget Allocation", "💲 Price Optimization", "📐 Sensitivity Analysis"
])

# ═══════════════════════════════════════════════════
#  TAB 1: BUDGET ALLOCATION
# ═══════════════════════════════════════════════════
with tab_budget:
    col_cfg, col_result = st.columns([1, 2.5])

    channels = ["Digital", "Print", "TV", "Social Media", "Events"]
    default_roi = [3.2, 1.1, 2.0, 2.8, 1.5]

    with col_cfg:
        st.markdown("#### ⚙️ Configuration")

        # Presets
        render_section_header("🎯", "Quick Presets")
        preset = st.selectbox(
            "Load Preset",
            ["Custom"] + list(OPTIMIZATION_PRESETS.keys()),
            key="opt_preset",
        )

        if preset != "Custom":
            p = OPTIMIZATION_PRESETS[preset]
            default_budget = p["total_budget"]
            st.caption(f"_{p['description']}_")
        else:
            default_budget = 1_000_000

        st.markdown("---")

        total_budget = st.number_input(
            "💰 Total Budget (₹)",
            min_value=50_000.0,
            value=float(default_budget),
            step=50_000.0,
            format="%.0f",
            key="opt_budget",
        )

        use_integer = st.toggle(
            "🔢 Integer Allocation (discrete chunks)",
            value=False,
            key="opt_integer",
            help="Allocate in fixed chunks (e.g., ₹50,000 steps) instead of continuous amounts",
        )

        if use_integer:
            integer_step = st.number_input(
                "Step Size (₹)", value=50_000.0, step=10_000.0, format="%.0f", key="opt_step"
            )
        else:
            integer_step = 10_000

        st.markdown("---")
        st.markdown("##### Expected ROI per ₹1 Spend")

        roi_values = []
        for i, ch in enumerate(channels):
            val = st.slider(
                f"{ch}", 0.1, 8.0, default_roi[i], 0.1,
                key=f"roi_{ch}",
            )
            roi_values.append(val)

        st.markdown("---")
        st.markdown("##### Constraints")

        min_allocs = {}
        max_allocs = {}
        for ch in channels:
            if preset != "Custom":
                p = OPTIMIZATION_PRESETS[preset]
                min_pct = p["min_pct"].get(ch, 0)
                max_pct = p["max_pct"].get(ch, 1)
            else:
                min_pct = 0.0
                max_pct = 1.0

            min_allocs[ch] = total_budget * min_pct
            max_allocs[ch] = total_budget * max_pct

        show_constraints = st.toggle("Customize constraints", value=False, key="opt_show_const")
        if show_constraints:
            for ch in channels:
                c1, c2 = st.columns(2)
                with c1:
                    min_allocs[ch] = st.number_input(
                        f"Min {ch}", value=min_allocs[ch], step=10_000.0,
                        format="%.0f", key=f"min_{ch}",
                    )
                with c2:
                    max_allocs[ch] = st.number_input(
                        f"Max {ch}", value=max_allocs[ch], step=10_000.0,
                        format="%.0f", key=f"max_{ch}",
                    )

        run_btn = st.button("⚡ Optimize", use_container_width=True, key="opt_run")

    with col_result:
        if run_btn:
            with st.spinner("Solving optimization problem..."):
                result = optimize_budget_allocation(
                    total_budget=total_budget,
                    channels=channels,
                    roi_coefficients=roi_values,
                    min_allocations=min_allocs,
                    max_allocations=max_allocs,
                    use_integer=use_integer,
                    integer_step=integer_step,
                )

            if not result["success"]:
                st.error(f"❌ **{result['status']}**: {result['error']}")
            else:
                st.session_state.optimization_results = result

                # ── KPI Cards ──
                k1, k2, k3 = st.columns(3)
                with k1:
                    render_kpi_card(
                        "Total Budget",
                        format_currency(total_budget),
                    )
                with k2:
                    render_kpi_card(
                        "Optimal ROI",
                        format_currency(result["total_roi"]),
                        f"{result['total_roi']/total_budget:.1f}x return",
                        True,
                    )
                with k3:
                    render_kpi_card(
                        "Budget Utilization",
                        f"{result['budget_utilization']:.1f}%",
                        format_currency(result["total_allocated"]) + " used",
                        result["budget_utilization"] > 90,
                    )

                st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

                # ── Allocation Charts ──
                c1, c2 = st.columns(2)

                allocs = result["allocations"]
                ch_roi = result["channel_roi"]

                with c1:
                    # Bar chart — allocation
                    fig_alloc = go.Figure(go.Bar(
                        x=list(allocs.keys()),
                        y=list(allocs.values()),
                        marker=dict(
                            color=list(allocs.values()),
                            colorscale=[[0, "#111827"], [0.5, "#00B4D8"], [1, "#00D4AA"]],
                        ),
                        text=[format_currency(v) for v in allocs.values()],
                        textposition="outside",
                        textfont=dict(color="#C5CDD8", size=11),
                    ))
                    fig_alloc.update_layout(
                        template=STRATFORGE_TEMPLATE, height=380,
                        title="Optimal Budget Allocation",
                        yaxis_title="Amount (₹)", showlegend=False,
                    )
                    st.plotly_chart(fig_alloc, use_container_width=True)

                with c2:
                    # Donut — share
                    fig_donut = go.Figure(go.Pie(
                        labels=list(allocs.keys()),
                        values=list(allocs.values()),
                        hole=0.55,
                        marker=dict(colors=["#00D4AA", "#00B4D8", "#7C3AED", "#FFB74D", "#FF6B6B"]),
                        textinfo="label+percent",
                        textfont=dict(size=11, color="#E8ECF1"),
                    ))
                    fig_donut.update_layout(
                        template=STRATFORGE_TEMPLATE, height=380,
                        title="Allocation Share",
                        showlegend=False,
                    )
                    st.plotly_chart(fig_donut, use_container_width=True)

                # ── ROI by Channel ──
                render_section_header("💎", "Expected ROI by Channel")
                fig_roi = go.Figure()
                fig_roi.add_trace(go.Bar(
                    x=list(ch_roi.keys()),
                    y=list(ch_roi.values()),
                    marker_color="#00D4AA",
                    text=[format_currency(v) for v in ch_roi.values()],
                    textposition="outside",
                    textfont=dict(color="#C5CDD8", size=11),
                    name="ROI",
                ))
                fig_roi.add_trace(go.Bar(
                    x=list(allocs.keys()),
                    y=list(allocs.values()),
                    marker_color="rgba(0, 180, 216, 0.4)",
                    name="Spend",
                ))
                fig_roi.update_layout(
                    template=STRATFORGE_TEMPLATE, height=380,
                    barmode="group",
                    title="Spend vs Expected Return",
                    yaxis_title="Amount (₹)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
                )
                st.plotly_chart(fig_roi, use_container_width=True)

                # ── Allocation Table ──
                table_data = []
                for ch in channels:
                    table_data.append({
                        "Channel": ch,
                        "Allocated": format_currency(allocs[ch]),
                        "Share %": f"{allocs[ch]/total_budget*100:.1f}%",
                        "ROI Coefficient": f"{roi_values[channels.index(ch)]:.1f}x",
                        "Expected Return": format_currency(ch_roi[ch]),
                    })
                st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)

                # ── Download ──
                alloc_df = pd.DataFrame(list(allocs.items()), columns=["Channel", "Allocation"])
                alloc_df["Expected_ROI"] = [ch_roi[ch] for ch in alloc_df["Channel"]]
                st.download_button(
                    "📥 Download Allocation (CSV)",
                    data=alloc_df.to_csv(index=False).encode("utf-8"),
                    file_name="stratforge_optimal_allocation.csv",
                    mime="text/csv",
                )
        else:
            st.markdown("""
            <div class="glass-card" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">⚡</div>
                <div style="font-size:1.1rem; color:#8B95A8;">
                    Configure budget, ROI rates, and constraints, then click <strong style="color:#00D4AA;">Optimize</strong>
                </div>
                <div style="font-size:0.78rem; color:#4B5563; margin-top:0.5rem;">
                    Uses PuLP linear programming — the same math behind Amazon & Google's resource allocation
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  TAB 2: PRICING OPTIMIZATION
# ═══════════════════════════════════════════════════
with tab_pricing:
    col_p1, col_p2 = st.columns([1, 2.5])

    with col_p1:
        st.markdown("#### ⚙️ Pricing Settings")
        current_price = st.number_input("Current Price (₹)", value=650.0, step=50.0, key="price_current")
        current_volume = st.number_input("Current Volume (units/month)", value=1500, step=100, key="price_vol")
        elasticity = st.slider("Price Elasticity", -3.0, -0.1, -0.8, 0.1, key="price_elast",
                              help="How demand changes with price. -0.8 = 1% price increase → 0.8% volume drop")
        cost_per_unit = st.number_input("Cost per Unit (₹)", value=260.0, step=10.0, key="price_cost")
        price_run = st.button("🔍 Find Optimal Price", use_container_width=True, key="price_run")

    with col_p2:
        if price_run:
            with st.spinner("Analyzing price-demand curve..."):
                result = optimize_pricing(
                    current_price=current_price,
                    current_volume=current_volume,
                    elasticity=elasticity,
                    cost_per_unit=cost_per_unit,
                )

            if not result["success"]:
                st.error(f"❌ {result['error']}")
            else:
                # KPIs
                k1, k2, k3, k4 = st.columns(4)
                with k1:
                    render_kpi_card("Optimal Price", f"₹{result['optimal_profit_price']:.0f}")
                with k2:
                    render_kpi_card(
                        "Max Profit",
                        format_currency(result["optimal_profit"]),
                        f"vs ₹{result['current_profit']:,.0f} current",
                        result["optimal_profit"] > result["current_profit"],
                    )
                with k3:
                    render_kpi_card("Optimal Volume", f"{result['optimal_profit_volume']:,.0f}")
                with k4:
                    render_kpi_card("Optimal Margin", f"{result['optimal_profit_margin']:.1f}%")

                # Price-Revenue-Profit curves
                sweep = pd.DataFrame(result["sweep_data"])

                fig_sweep = make_subplots(specs=[[{"secondary_y": True}]])
                fig_sweep.add_trace(go.Scatter(
                    x=sweep["price"], y=sweep["revenue"],
                    name="Revenue", line=dict(color="#00D4AA", width=2.5),
                ), secondary_y=False)
                fig_sweep.add_trace(go.Scatter(
                    x=sweep["price"], y=sweep["profit"],
                    name="Profit", line=dict(color="#00B4D8", width=2.5),
                ), secondary_y=False)
                fig_sweep.add_trace(go.Scatter(
                    x=sweep["price"], y=sweep["volume"],
                    name="Volume", line=dict(color="#FFB74D", width=2, dash="dash"),
                ), secondary_y=True)

                # Mark optimal
                fig_sweep.add_vline(
                    x=result["optimal_profit_price"],
                    line=dict(color="#7C3AED", dash="dot", width=2),
                    annotation_text="Optimal Price",
                    annotation_font_color="#7C3AED",
                )
                fig_sweep.add_vline(
                    x=current_price,
                    line=dict(color="#8B95A8", dash="dot", width=1.5),
                    annotation_text="Current",
                    annotation_font_color="#8B95A8",
                )

                fig_sweep.update_layout(
                    template=STRATFORGE_TEMPLATE, height=450,
                    title="Price Optimization Sweep",
                    xaxis_title="Unit Price (₹)",
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
                )
                fig_sweep.update_yaxes(title_text="Revenue / Profit (₹)", secondary_y=False)
                fig_sweep.update_yaxes(title_text="Volume (units)", secondary_y=True)

                st.plotly_chart(fig_sweep, use_container_width=True)
        else:
            st.markdown("""
            <div class="glass-card" style="text-align:center; padding:3rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">💲</div>
                <div style="font-size:1.1rem; color:#8B95A8;">
                    Set your current price, volume, and elasticity to find the <strong style="color:#00D4AA;">profit-maximizing price point</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ═══════════════════════════════════════════════════
#  TAB 3: SENSITIVITY ANALYSIS
# ═══════════════════════════════════════════════════
with tab_sensitivity:
    st.markdown("""
    <div class="glass-card">
        <div style="font-size:1rem; font-weight:700; color:#E8ECF1;">📐 Budget Sensitivity Analysis</div>
        <div style="font-size:0.78rem; color:#6B7280;">
            How does the optimal ROI change as total budget varies from 50% to 150%?
        </div>
    </div>
    """, unsafe_allow_html=True)

    sens_budget = st.number_input(
        "Base Budget for Sensitivity (₹)",
        value=1_000_000.0, step=100_000.0, format="%.0f",
        key="sens_budget",
    )
    sens_roi = [3.2, 1.1, 2.0, 2.8, 1.5]

    if st.button("📐 Run Sensitivity", use_container_width=True, key="sens_run"):
        with st.spinner("Running sensitivity analysis..."):
            variations = [0.50, 0.60, 0.70, 0.80, 0.90, 1.00, 1.10, 1.20, 1.30, 1.40, 1.50]
            sens_results = run_sensitivity_analysis(
                total_budget=sens_budget,
                channels=channels,
                roi_coefficients=sens_roi,
                budget_variations=variations,
            )

        budgets = [r["budget"] for r in sens_results]
        rois = [r["total_roi"] for r in sens_results]
        successes = [r["success"] for r in sens_results]

        fig_sens = go.Figure()
        fig_sens.add_trace(go.Scatter(
            x=budgets, y=rois,
            mode="lines+markers",
            line=dict(color="#00D4AA", width=3),
            marker=dict(size=8, color=["#00D4AA" if s else "#FF6B6B" for s in successes]),
            name="Optimal ROI",
        ))
        # Mark base budget
        base_idx = variations.index(1.0) if 1.0 in variations else len(variations) // 2
        fig_sens.add_trace(go.Scatter(
            x=[budgets[base_idx]], y=[rois[base_idx]],
            mode="markers", marker=dict(size=16, color="#FFB74D", symbol="star"),
            name="Base Budget",
        ))
        fig_sens.update_layout(
            template=STRATFORGE_TEMPLATE, height=420,
            title="Sensitivity: Budget vs Optimal ROI",
            xaxis_title="Total Budget (₹)",
            yaxis_title="Optimal ROI (₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
        )
        st.plotly_chart(fig_sens, use_container_width=True)

        # Allocation shift table
        render_section_header("📊", "Allocation Shift Across Budget Levels")
        shift_data = []
        for r in sens_results:
            if r["success"]:
                row = {"Budget": format_currency(r["budget"])}
                row["Total ROI"] = format_currency(r["total_roi"])
                for ch in channels:
                    row[ch] = format_currency(r["allocations"].get(ch, 0))
                shift_data.append(row)
        if shift_data:
            st.dataframe(pd.DataFrame(shift_data), use_container_width=True, hide_index=True)
    else:
        st.markdown("""
        <div class="glass-card" style="text-align:center; padding:3rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📐</div>
            <div style="font-size:1.1rem; color:#8B95A8;">
                Click <strong style="color:#00D4AA;">Run Sensitivity</strong> to see how budget changes impact optimal allocation
            </div>
        </div>
        """, unsafe_allow_html=True)
