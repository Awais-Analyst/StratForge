"""
StratForge – Data Studio
Upload CSV/Excel or use built-in data. Auto-detect columns. 50+ interactive Plotly charts.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utils.styling import apply_custom_css, render_kpi_card, render_section_header, STRATFORGE_TEMPLATE, format_currency
from utils.data_utils import (
    generate_synthetic_data,
    auto_detect_columns,
    get_summary_stats,
    init_session_state,
    load_uploaded_file,
    compute_kpis,
    auto_map_columns,
    get_col,
    MAPPING_FIELDS,
)

st.set_page_config(page_title="StratForge – Data Studio", page_icon="📊", layout="wide")
apply_custom_css()
init_session_state()

# ── Page Header ──
st.markdown("""
<div style="display:flex; align-items:center; gap:0.8rem; margin-bottom:0.3rem;">
    <span style="font-size:2rem;">📊</span>
    <div>
        <div style="font-size:1.6rem; font-weight:800; color:#E8ECF1;">Data Studio</div>
        <div style="font-size:0.8rem; color:#6B7280;">Upload your data or explore the built-in business dataset</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ── Data Source Selection ──
col_upload, col_synthetic = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "📁 Upload CSV or Excel file",
        type=["csv", "xlsx", "xls"],
        help="Upload your business data to analyze",
    )
    if uploaded_file is not None:
        df, error = load_uploaded_file(uploaded_file)
        if error:
            st.error(f"❌ {error}")
        else:
            st.session_state.df = df
            st.session_state.data_loaded = True
            st.session_state.data_source = "uploaded"
            st.success(f"✅ Loaded **{uploaded_file.name}** — {len(df)} rows × {len(df.columns)} columns")

with col_synthetic:
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    if st.button("🔄 Load Built-in Dataset", use_container_width=True):
        st.session_state.df = generate_synthetic_data()
        st.session_state.data_loaded = True
        st.session_state.data_source = "synthetic"
        st.rerun()

# ── Guard: no data yet ──
if not st.session_state.data_loaded or st.session_state.df is None:
    st.info("👆 Upload a file or load the built-in dataset to get started.")
    st.stop()

df = st.session_state.df
col_types = auto_detect_columns(df)
date_cols = col_types["date"]
num_cols = col_types["numeric"]
cat_cols = col_types["categorical"]

# ── Column Mapping ──
# Auto-map on first load if no mappings exist
if not st.session_state.column_mapping:
    auto_mapping, auto_mkt = auto_map_columns(df)
    st.session_state.column_mapping = auto_mapping
    st.session_state.marketing_columns = auto_mkt

with st.expander("📌 Map Your Columns", expanded=not bool(st.session_state.column_mapping)):
    st.markdown("""
    <div style="font-size:0.82rem; color:#8B95A8; margin-bottom:0.8rem;">
        Map your data columns to the expected business fields. Only <strong style="color:#FF6B6B;">Date</strong> is required — all others are optional.
        Unmapped fields will simply be hidden from the relevant pages.
    </div>
    """, unsafe_allow_html=True)

    all_cols = ["— None —"] + list(df.columns)
    current_map = st.session_state.column_mapping

    mc1, mc2, mc3 = st.columns(3)
    mapping_updates = {}

    for i, (field, info) in enumerate(MAPPING_FIELDS.items()):
        target_col = [mc1, mc2, mc3][i % 3]
        with target_col:
            current_val = current_map.get(field, "— None —")
            if current_val not in all_cols:
                current_val = "— None —"
            idx = all_cols.index(current_val) if current_val in all_cols else 0
            label = info["label"] + (" *" if info["required"] else "")
            selected = st.selectbox(
                label, all_cols, index=idx,
                key=f"map_{field}",
            )
            if selected != "— None —":
                mapping_updates[field] = selected

    # Marketing channel columns (multi-select)
    st.markdown("##### 📣 Marketing Channel Columns (optional)")
    mkt_options = [c for c in num_cols]
    current_mkt = [c for c in st.session_state.marketing_columns if c in mkt_options]
    selected_mkt = st.multiselect(
        "Select all marketing channel columns",
        mkt_options,
        default=current_mkt,
        key="map_mkt_channels",
    )

    if st.button("✅ Apply Mapping", use_container_width=True, key="apply_mapping"):
        st.session_state.column_mapping = mapping_updates
        st.session_state.marketing_columns = selected_mkt
        st.rerun()

    # Show current mapping status
    mapped_count = len(st.session_state.column_mapping)
    total_fields = len(MAPPING_FIELDS)
    st.caption(f"Mapped: {mapped_count}/{total_fields} fields · {len(st.session_state.marketing_columns)} marketing channels")

# ── Column Detection Summary ──
st.markdown(f"""
<div class="glass-card" style="display:flex; gap:2rem; flex-wrap:wrap;">
    <div><span style="color:#00D4AA; font-weight:700; font-size:1.3rem;">{len(df)}</span>
         <span style="color:#8B95A8; font-size:0.8rem;"> rows</span></div>
    <div><span style="color:#00B4D8; font-weight:700; font-size:1.3rem;">{len(df.columns)}</span>
         <span style="color:#8B95A8; font-size:0.8rem;"> columns</span></div>
    <div><span style="color:#7C3AED; font-weight:700; font-size:1.3rem;">{len(date_cols)}</span>
         <span style="color:#8B95A8; font-size:0.8rem;"> date</span></div>
    <div><span style="color:#FFB74D; font-weight:700; font-size:1.3rem;">{len(num_cols)}</span>
         <span style="color:#8B95A8; font-size:0.8rem;"> numeric</span></div>
    <div><span style="color:#FF6B6B; font-weight:700; font-size:1.3rem;">{len(cat_cols)}</span>
         <span style="color:#8B95A8; font-size:0.8rem;"> categorical</span></div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ──
if any(c in num_cols for c in ["Revenue", "Profit", "Customer_Base"]):
    kpis = compute_kpis(df)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi_card("Total Revenue", format_currency(kpis.get("total_revenue", 0)))
    with k2:
        render_kpi_card("Total Profit", format_currency(kpis.get("total_profit", 0)))
    with k3:
        render_kpi_card("Avg Margin", f"{kpis.get('avg_profit_margin', 0):.1f}%")
    with k4:
        render_kpi_card("Avg Satisfaction", f"{kpis.get('avg_satisfaction', 0):.1f}/10")

# ── Data Preview ──
with st.expander("🔍 Data Preview (First 5 Rows)", expanded=False):
    st.dataframe(df.head(5), use_container_width=True)
    st.caption(f"Showing 5 of {len(df)} rows · {len(df.columns)} columns")

# ── Descriptive Statistics ──
with st.expander("📋 Descriptive Statistics", expanded=False):
    desc = df.describe().T
    desc.columns = ["Count", "Mean", "Std", "Min", "25%", "50% (Median)", "75%", "Max"]
    st.dataframe(desc.style.format("{:,.2f}"), use_container_width=True, height=400)

    # Data types & info summary
    st.markdown("##### 📌 Column Info")
    info_data = []
    for col in df.columns:
        non_null = df[col].notna().sum()
        info_data.append({
            "Column": col,
            "Dtype": str(df[col].dtype),
            "Non-Null": f"{non_null}/{len(df)}",
            "Missing %": f"{(1 - non_null/len(df))*100:.1f}%",
            "Unique": df[col].nunique(),
        })
    st.dataframe(pd.DataFrame(info_data), use_container_width=True, hide_index=True)

# ── Interactive Charts ──
render_section_header("📈", "Interactive Visualizations")

tab_trend, tab_dist, tab_corr, tab_comp, tab_advanced = st.tabs([
    "📈 Trends", "📊 Distributions", "🔥 Correlations", "🏷️ Comparisons", "🎨 Advanced"
])

# ─── Tab 1: Trends ───
with tab_trend:
    if date_cols and num_cols:
        date_col = date_cols[0]
        selected_metrics = st.multiselect(
            "Select metrics to plot",
            num_cols,
            default=num_cols[:3] if len(num_cols) >= 3 else num_cols,
            key="trend_metrics",
        )

        if selected_metrics:
            # Line Chart
            fig_line = go.Figure()
            colors = ["#00D4AA", "#00B4D8", "#7C3AED", "#FFB74D", "#FF6B6B",
                      "#4FC3F7", "#AB47BC", "#66BB6A"]
            for i, col_name in enumerate(selected_metrics):
                fig_line.add_trace(go.Scatter(
                    x=df[date_col], y=df[col_name],
                    name=col_name.replace("_", " "),
                    line=dict(color=colors[i % len(colors)], width=2),
                    mode="lines",
                ))
            fig_line.update_layout(
                template=STRATFORGE_TEMPLATE, height=400,
                title="Time Series Trends",
                legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5, xanchor="center"),
            )
            st.plotly_chart(fig_line, use_container_width=True)

            # Area Chart
            fig_area = go.Figure()
            for i, col_name in enumerate(selected_metrics[:4]):
                fig_area.add_trace(go.Scatter(
                    x=df[date_col], y=df[col_name],
                    name=col_name.replace("_", " "),
                    fill="tonexty" if i > 0 else "tozeroy",
                    line=dict(color=colors[i % len(colors)], width=1.5),
                    fillcolor=f"rgba({int(colors[i % len(colors)][1:3], 16)}, {int(colors[i % len(colors)][3:5], 16)}, {int(colors[i % len(colors)][5:7], 16)}, 0.10)",
                ))
            fig_area.update_layout(
                template=STRATFORGE_TEMPLATE, height=350,
                title="Stacked Area View",
            )
            st.plotly_chart(fig_area, use_container_width=True)

            # Moving Averages
            if len(df) > 6:
                ma_col = st.selectbox("Moving Average for:", selected_metrics, key="ma_select")
                fig_ma = go.Figure()
                fig_ma.add_trace(go.Scatter(
                    x=df[date_col], y=df[ma_col],
                    name="Actual", line=dict(color="#00D4AA", width=1.5), opacity=0.5,
                ))
                for window, color in [(3, "#FFB74D"), (6, "#00B4D8"), (12, "#7C3AED")]:
                    if len(df) >= window:
                        fig_ma.add_trace(go.Scatter(
                            x=df[date_col], y=df[ma_col].rolling(window).mean(),
                            name=f"{window}-MA", line=dict(color=color, width=2.5),
                        ))
                fig_ma.update_layout(template=STRATFORGE_TEMPLATE, height=350, title=f"Moving Averages — {ma_col}")
                st.plotly_chart(fig_ma, use_container_width=True)

    else:
        st.info("No date + numeric column combination found for trend charts.")

# ─── Tab 2: Distributions ───
with tab_dist:
    if num_cols:
        dist_cols = st.multiselect(
            "Select columns for distribution", num_cols,
            default=num_cols[:4] if len(num_cols) >= 4 else num_cols,
            key="dist_cols",
        )

        if dist_cols:
            # Histograms
            col_a, col_b = st.columns(2)
            for i, col_name in enumerate(dist_cols):
                target_col = col_a if i % 2 == 0 else col_b
                with target_col:
                    fig_hist = go.Figure()
                    fig_hist.add_trace(go.Histogram(
                        x=df[col_name], nbinsx=30,
                        marker_color="#00D4AA", opacity=0.75,
                        name=col_name.replace("_", " "),
                    ))
                    fig_hist.update_layout(
                        template=STRATFORGE_TEMPLATE, height=280,
                        title=f"Distribution — {col_name.replace('_', ' ')}",
                        showlegend=False,
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)

            # Box Plots
            fig_box = go.Figure()
            for i, col_name in enumerate(dist_cols):
                colors = ["#00D4AA", "#00B4D8", "#7C3AED", "#FFB74D", "#FF6B6B"]
                fig_box.add_trace(go.Box(
                    y=df[col_name], name=col_name.replace("_", " "),
                    marker_color=colors[i % len(colors)],
                    boxmean="sd",
                ))
            fig_box.update_layout(template=STRATFORGE_TEMPLATE, height=380, title="Box Plot Comparison")
            st.plotly_chart(fig_box, use_container_width=True)

            # Violin Plots
            if len(dist_cols) <= 6:
                fig_violin = go.Figure()
                for i, col_name in enumerate(dist_cols):
                    fig_violin.add_trace(go.Violin(
                        y=df[col_name], name=col_name.replace("_", " "),
                        marker_color=colors[i % len(colors)],
                        box_visible=True, meanline_visible=True,
                    ))
                fig_violin.update_layout(template=STRATFORGE_TEMPLATE, height=380, title="Violin Plots")
                st.plotly_chart(fig_violin, use_container_width=True)
    else:
        st.info("No numeric columns found for distribution analysis.")

# ─── Tab 3: Correlations ───
with tab_corr:
    if len(num_cols) >= 2:
        corr_cols = st.multiselect(
            "Select columns for correlation", num_cols,
            default=num_cols[:8] if len(num_cols) >= 8 else num_cols,
            key="corr_cols",
        )

        if len(corr_cols) >= 2:
            corr_matrix = df[corr_cols].corr()

            # Heatmap
            fig_heat = go.Figure(data=go.Heatmap(
                z=corr_matrix.values,
                x=[c.replace("_", " ") for c in corr_matrix.columns],
                y=[c.replace("_", " ") for c in corr_matrix.columns],
                colorscale=[[0, "#FF6B6B"], [0.5, "#111827"], [1, "#00D4AA"]],
                zmin=-1, zmax=1,
                text=corr_matrix.values.round(2),
                texttemplate="%{text}",
                textfont=dict(size=10, color="#C5CDD8"),
            ))
            fig_heat.update_layout(
                template=STRATFORGE_TEMPLATE, height=500,
                title="Correlation Heatmap",
            )
            st.plotly_chart(fig_heat, use_container_width=True)

            # Scatter Matrix (first 4 columns only for performance)
            scatter_cols = corr_cols[:4]
            if len(scatter_cols) >= 2:
                fig_scatter = px.scatter_matrix(
                    df[scatter_cols],
                    dimensions=scatter_cols,
                    color_discrete_sequence=["#00D4AA"],
                    opacity=0.5,
                )
                fig_scatter.update_layout(
                    template=STRATFORGE_TEMPLATE, height=600,
                    title="Scatter Matrix",
                )
                fig_scatter.update_traces(diagonal_visible=False, marker=dict(size=3))
                st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.info("Need at least 2 numeric columns for correlation analysis.")

# ─── Tab 4: Comparisons ───
with tab_comp:
    if cat_cols and num_cols:
        comp_cat = st.selectbox("Category column:", cat_cols, key="comp_cat")
        comp_metric = st.selectbox("Metric:", num_cols, key="comp_metric")

        c1, c2 = st.columns(2)

        with c1:
            # Bar Chart
            group_data = df.groupby(comp_cat)[comp_metric].mean().reset_index()
            fig_bar = go.Figure(go.Bar(
                x=group_data[comp_cat], y=group_data[comp_metric],
                marker=dict(
                    color=group_data[comp_metric],
                    colorscale=[[0, "#00B4D8"], [1, "#00D4AA"]],
                ),
                text=group_data[comp_metric].round(0),
                textposition="outside",
                textfont=dict(color="#C5CDD8"),
            ))
            fig_bar.update_layout(
                template=STRATFORGE_TEMPLATE, height=380,
                title=f"Avg {comp_metric.replace('_', ' ')} by {comp_cat.replace('_', ' ')}",
                showlegend=False,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            # Pie / Donut Chart
            fig_pie = go.Figure(go.Pie(
                labels=group_data[comp_cat], values=group_data[comp_metric],
                hole=0.55,
                marker=dict(colors=["#00D4AA", "#00B4D8", "#7C3AED", "#FFB74D", "#FF6B6B"]),
                textinfo="label+percent",
                textfont=dict(size=12, color="#E8ECF1"),
            ))
            fig_pie.update_layout(
                template=STRATFORGE_TEMPLATE, height=380,
                title=f"{comp_metric.replace('_', ' ')} Share",
                showlegend=False,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        # Treemap
        if len(cat_cols) >= 2:
            tree_cat2 = [c for c in cat_cols if c != comp_cat]
            if tree_cat2:
                fig_tree = px.treemap(
                    df, path=[comp_cat, tree_cat2[0]], values=comp_metric,
                    color=comp_metric,
                    color_continuous_scale=["#111827", "#00B4D8", "#00D4AA"],
                )
                fig_tree.update_layout(template=STRATFORGE_TEMPLATE, height=400, title="Treemap")
                st.plotly_chart(fig_tree, use_container_width=True)

        # Sunburst
        if len(cat_cols) >= 2:
            tree_cat2 = [c for c in cat_cols if c != comp_cat]
            if tree_cat2:
                fig_sun = px.sunburst(
                    df, path=[comp_cat, tree_cat2[0]], values=comp_metric,
                    color=comp_metric,
                    color_continuous_scale=["#111827", "#7C3AED", "#00D4AA"],
                )
                fig_sun.update_layout(template=STRATFORGE_TEMPLATE, height=450, title="Sunburst Chart")
                st.plotly_chart(fig_sun, use_container_width=True)
    else:
        st.info("Need categorical + numeric columns for comparison charts.")

# ─── Tab 5: Advanced ───
with tab_advanced:
    if date_cols and num_cols:
        adv_col = st.selectbox("Select metric:", num_cols, key="adv_col")
        date_col = date_cols[0]

        # Waterfall (Month-over-Month Change)
        if len(df) > 1:
            mom = df[adv_col].diff().fillna(0).values
            labels = df[date_col].dt.strftime("%b %Y").values if pd.api.types.is_datetime64_any_dtype(df[date_col]) else [str(i) for i in range(len(df))]

            # Show last 12 months
            n_show = min(12, len(df))
            fig_waterfall = go.Figure(go.Waterfall(
                x=labels[-n_show:],
                y=mom[-n_show:],
                measure=["relative"] * n_show,
                increasing=dict(marker_color="#00D4AA"),
                decreasing=dict(marker_color="#FF6B6B"),
                connector=dict(line=dict(color="#374151")),
                textposition="outside",
                textfont=dict(size=9, color="#8B95A8"),
            ))
            fig_waterfall.update_layout(
                template=STRATFORGE_TEMPLATE, height=380,
                title=f"Month-over-Month Changes — {adv_col.replace('_', ' ')}",
                showlegend=False,
            )
            st.plotly_chart(fig_waterfall, use_container_width=True)

        # Cumulative Sum
        fig_cum = go.Figure()
        fig_cum.add_trace(go.Scatter(
            x=df[date_col], y=df[adv_col].cumsum(),
            fill="tozeroy",
            line=dict(color="#00D4AA", width=2),
            fillcolor="rgba(0, 212, 170, 0.12)",
            name="Cumulative",
        ))
        fig_cum.update_layout(template=STRATFORGE_TEMPLATE, height=350, title=f"Cumulative — {adv_col.replace('_', ' ')}")
        st.plotly_chart(fig_cum, use_container_width=True)

        # Year-over-Year Comparison
        if pd.api.types.is_datetime64_any_dtype(df[date_col]) and len(df) > 12:
            df_temp = df.copy()
            df_temp["Year"] = df_temp[date_col].dt.year
            df_temp["Month"] = df_temp[date_col].dt.month
            years = sorted(df_temp["Year"].unique())

            fig_yoy = go.Figure()
            colors_yoy = ["#374151", "#6B7280", "#00B4D8", "#00D4AA", "#FFB74D", "#7C3AED"]
            for i, year in enumerate(years[-4:]):  # Last 4 years
                year_data = df_temp[df_temp["Year"] == year]
                fig_yoy.add_trace(go.Scatter(
                    x=year_data["Month"], y=year_data[adv_col],
                    name=str(year),
                    line=dict(
                        color=colors_yoy[i % len(colors_yoy)],
                        width=3 if i == len(years[-4:]) - 1 else 1.5,
                    ),
                ))
            fig_yoy.update_layout(
                template=STRATFORGE_TEMPLATE, height=380,
                title=f"Year-over-Year — {adv_col.replace('_', ' ')}",
                xaxis=dict(tickmode="array", tickvals=list(range(1, 13)),
                           ticktext=["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                                     "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]),
            )
            st.plotly_chart(fig_yoy, use_container_width=True)
    else:
        st.info("Need date + numeric columns for advanced charts.")

# ── Data Quality Report ──
with st.expander("🩺 Data Quality Report", expanded=False):
    quality_data = []
    for col in df.columns:
        missing = df[col].isna().sum()
        missing_pct = missing / len(df) * 100
        quality_data.append({
            "Column": col,
            "Type": str(df[col].dtype),
            "Non-Null": len(df) - missing,
            "Missing": missing,
            "Missing %": f"{missing_pct:.1f}%",
            "Unique": df[col].nunique(),
        })
    quality_df = pd.DataFrame(quality_data)
    st.dataframe(quality_df, use_container_width=True, height=400)

    # Download data as CSV
    st.download_button(
        label="📥 Download Data as CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="stratforge_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
