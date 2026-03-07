"""
StratForge - Data Utilities
Synthetic data generation, auto column detection, session state management.
"""

import pandas as pd
import numpy as np
import streamlit as st
from datetime import datetime


@st.cache_data
def generate_synthetic_data():
    """
    Generate 5 years of realistic monthly business data.
    Returns a DataFrame with revenue, expenses, profit, marketing channels,
    customers, churn, sales volume, pricing, regions, and product categories.
    """
    np.random.seed(42)
    dates = pd.date_range("2020-01-01", "2025-12-31", freq="MS")
    n = len(dates)

    # ── Revenue with trend + seasonality + noise ──
    trend = np.linspace(500_000, 1_350_000, n)
    seasonality = 120_000 * np.sin(2 * np.pi * np.arange(n) / 12)
    holiday_bump = np.zeros(n)
    for i in range(n):
        if dates[i].month in [11, 12]:
            holiday_bump[i] = np.random.uniform(50_000, 130_000)
    noise = np.random.normal(0, 35_000, n)
    revenue = np.maximum(trend + seasonality + holiday_bump + noise, 100_000)

    # ── Marketing Channels ──
    digital_marketing = np.abs(np.random.uniform(25_000, 85_000, n) * (1 + np.linspace(0, 0.6, n)))
    print_marketing = np.abs(np.random.uniform(10_000, 40_000, n) * (1 - np.linspace(0, 0.35, n)))
    tv_marketing = np.abs(np.random.uniform(30_000, 95_000, n) + 10_000 * np.sin(np.arange(n) / 6))
    social_media_marketing = np.abs(np.random.uniform(15_000, 70_000, n) * (1 + np.linspace(0, 0.9, n)))
    event_marketing = np.abs(np.random.uniform(5_000, 35_000, n))
    total_marketing = (
        digital_marketing + print_marketing + tv_marketing +
        social_media_marketing + event_marketing
    )

    # ── Expenses & Profit ──
    cost_ratio = np.random.uniform(0.52, 0.72, n)
    operating_expenses = revenue * cost_ratio
    total_expenses = operating_expenses + total_marketing
    profit = revenue - total_expenses

    # ── Pricing & Volume ──
    unit_price = np.abs(np.random.normal(650, 120, n))
    unit_price = np.clip(unit_price, 350, 1100)
    sales_volume = (revenue / unit_price).astype(int)

    # ── Customers & Retention ──
    new_customers = np.random.randint(80, 350, n)
    churn_rate = np.clip(np.random.normal(0.045, 0.015, n), 0.01, 0.10)
    customer_base = np.zeros(n)
    customer_base[0] = 2500
    for i in range(1, n):
        customer_base[i] = customer_base[i - 1] * (1 - churn_rate[i]) + new_customers[i]
    customer_base = customer_base.astype(int)

    # ── Satisfaction Score ──
    satisfaction = np.clip(np.random.normal(7.8, 0.8, n), 4.0, 10.0)

    # ── Regions & Product Categories (cycled) ──
    regions = ["North", "South", "East", "West"]
    products = ["Premium", "Standard", "Economy"]
    region_col = [regions[i % len(regions)] for i in range(n)]
    product_col = [products[i % len(products)] for i in range(n)]

    df = pd.DataFrame({
        "Date": dates,
        "Revenue": revenue.round(2),
        "Operating_Expenses": operating_expenses.round(2),
        "Total_Marketing_Spend": total_marketing.round(2),
        "Digital_Marketing": digital_marketing.round(2),
        "Print_Marketing": print_marketing.round(2),
        "TV_Marketing": tv_marketing.round(2),
        "Social_Media_Marketing": social_media_marketing.round(2),
        "Event_Marketing": event_marketing.round(2),
        "Total_Expenses": total_expenses.round(2),
        "Profit": profit.round(2),
        "Unit_Price": unit_price.round(2),
        "Sales_Volume": sales_volume,
        "Customer_Base": customer_base,
        "New_Customers": new_customers,
        "Churn_Rate": churn_rate.round(4),
        "Satisfaction_Score": satisfaction.round(2),
        "Region": region_col,
        "Product_Category": product_col,
    })
    return df


def auto_detect_columns(df):
    """
    Classify DataFrame columns into date, numeric, and categorical types.
    Returns a dict: {'date': [...], 'numeric': [...], 'categorical': [...]}.
    """
    result = {"date": [], "numeric": [], "categorical": []}

    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            result["date"].append(col)
        elif pd.api.types.is_numeric_dtype(df[col]):
            result["numeric"].append(col)
        else:
            # Try to parse as dates
            try:
                pd.to_datetime(df[col])
                result["date"].append(col)
            except (ValueError, TypeError):
                result["categorical"].append(col)
    return result


def get_summary_stats(df, numeric_cols):
    """Compute summary statistics for numeric columns."""
    stats = {}
    for col in numeric_cols:
        s = df[col].dropna()
        stats[col] = {
            "mean": s.mean(),
            "median": s.median(),
            "std": s.std(),
            "min": s.min(),
            "max": s.max(),
            "q25": s.quantile(0.25),
            "q75": s.quantile(0.75),
            "skew": s.skew(),
            "trend": "↑" if len(s) > 1 and s.iloc[-1] > s.iloc[0] else "↓",
        }
    return stats


def init_session_state():
    """Initialize session state with default values."""
    defaults = {
        "df": None,
        "data_loaded": False,
        "forecast_results": None,
        "simulation_results": None,
        "optimization_results": None,
        "data_source": "synthetic",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_uploaded_file(uploaded_file):
    """Load an uploaded CSV or Excel file into a DataFrame."""
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith((".xlsx", ".xls")):
            df = pd.read_excel(uploaded_file)
        else:
            return None, "Unsupported file format. Please upload CSV or Excel."

        # Auto-convert date columns
        for col in df.columns:
            if df[col].dtype == "object":
                try:
                    df[col] = pd.to_datetime(df[col])
                except (ValueError, TypeError):
                    pass
        return df, None
    except Exception as e:
        return None, f"Error loading file: {str(e)}"


def compute_kpis(df):
    """Compute key KPIs from the dataset."""
    kpis = {}
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

    if "Revenue" in num_cols:
        kpis["total_revenue"] = df["Revenue"].sum()
        kpis["avg_revenue"] = df["Revenue"].mean()
        if len(df) >= 2:
            kpis["revenue_growth"] = (
                (df["Revenue"].iloc[-1] - df["Revenue"].iloc[0]) / df["Revenue"].iloc[0] * 100
            )
    if "Profit" in num_cols:
        kpis["total_profit"] = df["Profit"].sum()
        kpis["avg_profit_margin"] = (df["Profit"].sum() / df["Revenue"].sum() * 100) if "Revenue" in num_cols and df["Revenue"].sum() != 0 else 0
    if "Churn_Rate" in num_cols:
        kpis["avg_churn"] = df["Churn_Rate"].mean() * 100
    if "Customer_Base" in num_cols:
        kpis["current_customers"] = int(df["Customer_Base"].iloc[-1])
    if "Satisfaction_Score" in num_cols:
        kpis["avg_satisfaction"] = df["Satisfaction_Score"].mean()

    return kpis
