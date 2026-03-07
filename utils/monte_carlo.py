"""
StratForge - Monte Carlo Simulation Engine
Risk simulation with configurable parameters, VaR/CVaR, fan charts, scenario paths.
All heavy computations cached with @st.cache_data.
"""

import numpy as np
import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600)
def run_simulation(
    base_value,
    growth_rate=0.05,
    volatility=0.15,
    periods=12,
    n_simulations=10000,
    seed=42,
):
    """
    Run Geometric Brownian Motion Monte Carlo simulation.

    Parameters:
        base_value: Starting value (e.g., current annual revenue)
        growth_rate: Expected annual growth rate (e.g., 0.05 = 5%)
        volatility: Annual volatility / standard deviation (e.g., 0.15 = 15%)
        periods: Number of future periods (months)
        n_simulations: Number of simulation runs (capped at 50,000)
        seed: Random seed for reproducibility

    Returns dict with simulation paths, final values, and risk metrics.
    """
    # Safety cap
    n_simulations = min(n_simulations, 50_000)

    np.random.seed(seed)

    # Monthly parameters
    dt = 1 / 12
    monthly_drift = (growth_rate - 0.5 * volatility**2) * dt
    monthly_vol = volatility * np.sqrt(dt)

    # Generate random returns
    random_shocks = np.random.normal(0, 1, (n_simulations, periods))
    monthly_returns = monthly_drift + monthly_vol * random_shocks

    # Build price paths
    paths = np.zeros((n_simulations, periods + 1))
    paths[:, 0] = base_value
    for t in range(1, periods + 1):
        paths[:, t] = paths[:, t - 1] * np.exp(monthly_returns[:, t - 1])

    # Final values
    final_values = paths[:, -1]

    # Risk metrics
    metrics = calculate_risk_metrics(final_values, base_value)

    # Percentile paths for fan chart
    fan_chart = generate_fan_chart_data(paths)

    # Scenario paths
    scenarios = generate_scenarios(paths, final_values)

    return {
        "final_values": final_values.tolist(),
        "metrics": metrics,
        "fan_chart": fan_chart,
        "scenarios": scenarios,
        "n_simulations": n_simulations,
        "periods": periods,
    }


def calculate_risk_metrics(final_values, base_value, target_growth=0.20):
    """
    Calculate comprehensive risk metrics from simulation results.
    """
    final = np.array(final_values)
    returns = (final - base_value) / base_value

    target_value = base_value * (1 + target_growth)

    # Value at Risk (VaR) at various confidence levels
    var_95 = float(np.percentile(final, 5))
    var_99 = float(np.percentile(final, 1))

    # Conditional VaR (CVaR / Expected Shortfall)
    cvar_95 = float(np.mean(final[final <= var_95]))

    # Probability metrics
    prob_profit = float(np.mean(final > base_value) * 100)
    prob_target = float(np.mean(final > target_value) * 100)
    prob_loss_10 = float(np.mean(final < base_value * 0.9) * 100)

    return {
        "mean": float(np.mean(final)),
        "median": float(np.median(final)),
        "std": float(np.std(final)),
        "min": float(np.min(final)),
        "max": float(np.max(final)),
        "var_95": var_95,
        "var_99": var_99,
        "cvar_95": cvar_95,
        "prob_profit": prob_profit,
        "prob_target": prob_target,
        "prob_loss_10": prob_loss_10,
        "expected_return_pct": float(np.mean(returns) * 100),
        "return_std_pct": float(np.std(returns) * 100),
        "skewness": float(pd.Series(final).skew()),
        "kurtosis": float(pd.Series(final).kurtosis()),
        "p10": float(np.percentile(final, 10)),
        "p25": float(np.percentile(final, 25)),
        "p50": float(np.percentile(final, 50)),
        "p75": float(np.percentile(final, 75)),
        "p90": float(np.percentile(final, 90)),
        "target_value": target_value,
        "target_growth_pct": target_growth * 100,
    }


def generate_fan_chart_data(paths):
    """
    Generate percentile bands for fan chart / cone of uncertainty.
    Returns dict with percentile arrays: p10, p25, p50 (median), p75, p90.
    """
    periods = paths.shape[1]
    percentiles = {}
    for p in [5, 10, 25, 50, 75, 90, 95]:
        percentiles[f"p{p}"] = np.percentile(paths, p, axis=0).tolist()
    return percentiles


def generate_scenarios(paths, final_values):
    """
    Extract best, worst, and median scenario paths.
    """
    final = np.array(final_values)

    best_idx = np.argmax(final)
    worst_idx = np.argmin(final)
    median_idx = np.argsort(final)[len(final) // 2]

    return {
        "best": paths[best_idx].tolist(),
        "worst": paths[worst_idx].tolist(),
        "median": paths[median_idx].tolist(),
    }


# ── Scenario Presets ──

RISK_PRESETS = {
    "Aggressive Growth": {
        "growth_rate": 0.15,
        "volatility": 0.30,
        "description": "High growth target with significant market uncertainty",
    },
    "Conservative": {
        "growth_rate": 0.03,
        "volatility": 0.08,
        "description": "Steady, low-risk growth trajectory",
    },
    "Balanced": {
        "growth_rate": 0.08,
        "volatility": 0.18,
        "description": "Moderate growth with normal market volatility",
    },
    "Recession Stress": {
        "growth_rate": -0.05,
        "volatility": 0.35,
        "description": "Negative growth scenario with extreme volatility",
    },
    "Market Boom": {
        "growth_rate": 0.25,
        "volatility": 0.22,
        "description": "Strong bull market with above-average returns",
    },
}
