"""
StratForge - Forecasting Utilities
100% pure pandas/numpy — NO scipy, NO statsmodels, NO statsforecast.
Works on Streamlit Cloud without any compilation issues.

Implements:
  - Holt-Winters Triple Exponential Smoothing (manual)
  - Linear Trend + Seasonal Decomposition forecast
  - Seasonal Naive baseline
  - Pandas-based seasonal decomposition
  - What-If scenario engine
"""

import pandas as pd
import numpy as np
import streamlit as st
import warnings

warnings.filterwarnings("ignore")


# ═══════════════════════════════════════════════════
#  HOLT-WINTERS (Triple Exponential Smoothing)
# ═══════════════════════════════════════════════════

def _holt_winters_additive(series, season_length=12, alpha=0.3, beta=0.05, gamma=0.15, n_forecast=12):
    """
    Holt-Winters additive triple exponential smoothing.
    Pure numpy implementation — no scipy/statsmodels needed.
    """
    n = len(series)
    if n < season_length * 2:
        raise ValueError(f"Need at least {season_length * 2} points, got {n}")

    y = np.array(series, dtype=float)

    # Initialize level, trend, and seasonal components
    # Level: average of first season
    level = np.mean(y[:season_length])
    # Trend: average slope between first two seasons
    trend = np.mean(y[season_length:2*season_length] - y[:season_length]) / season_length
    # Seasonal: first season deviations from level
    seasonal = np.zeros(n + n_forecast)
    for i in range(season_length):
        seasonal[i] = y[i] - level

    # Arrays for fitted values
    fitted = np.zeros(n)
    fitted[0] = level + trend + seasonal[0]

    # Smooth
    for t in range(1, n):
        s_idx = t % season_length  # seasonal index for initialization
        prev_seasonal = seasonal[t - season_length] if t >= season_length else seasonal[s_idx]

        new_level = alpha * (y[t] - prev_seasonal) + (1 - alpha) * (level + trend)
        new_trend = beta * (new_level - level) + (1 - beta) * trend
        seasonal[t] = gamma * (y[t] - new_level) + (1 - gamma) * prev_seasonal

        level = new_level
        trend = new_trend
        fitted[t] = level + trend + seasonal[t]

    # Forecast
    forecast = np.zeros(n_forecast)
    for h in range(n_forecast):
        s_idx = n + h - season_length
        if s_idx >= 0:
            forecast[h] = level + (h + 1) * trend + seasonal[s_idx]
        else:
            forecast[h] = level + (h + 1) * trend

    # Confidence intervals (using residual standard deviation)
    residuals = y - fitted
    residual_std = np.std(residuals)
    steps = np.arange(1, n_forecast + 1)
    margin = 1.96 * residual_std * np.sqrt(steps / season_length)

    return forecast, fitted, forecast - margin, forecast + margin, residual_std


@st.cache_data(ttl=3600)
def run_exp_smoothing(series_values, series_index_str, periods=12):
    """
    Holt-Winters Triple Exponential Smoothing forecast.
    Uses grid search to find best alpha, beta, gamma.
    """
    try:
        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        y = series.values
        n = len(y)

        if n < 24:
            # Not enough data for full Holt-Winters, use simple exponential smoothing
            alpha = 0.3
            fitted = np.zeros(n)
            fitted[0] = y[0]
            for t in range(1, n):
                fitted[t] = alpha * y[t] + (1 - alpha) * fitted[t - 1]

            last_val = fitted[-1]
            forecast = np.full(periods, last_val)
            residual_std = np.std(y - fitted)
            steps = np.arange(1, periods + 1)
            margin = 1.96 * residual_std * np.sqrt(steps / 12)

            last_date = series.index[-1]
            future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq="MS")

            return {
                "success": True,
                "forecast": forecast.tolist(),
                "forecast_dates": future_dates.strftime("%Y-%m-%d").tolist(),
                "conf_lower": (forecast - margin).tolist(),
                "conf_upper": (forecast + margin).tolist(),
                "fitted_values": fitted.tolist(),
                "aic": None, "bic": None,
                "model_type": "Simple Exponential Smoothing",
                "error": None,
            }

        # Grid search for best parameters (minimizing MSE)
        best_mse = float("inf")
        best_params = (0.3, 0.05, 0.15)

        for alpha in [0.1, 0.2, 0.3, 0.5, 0.7]:
            for beta in [0.01, 0.05, 0.1, 0.2]:
                for gamma in [0.05, 0.1, 0.2, 0.3]:
                    try:
                        fc, ft, _, _, _ = _holt_winters_additive(
                            y, season_length=12, alpha=alpha, beta=beta, gamma=gamma, n_forecast=1
                        )
                        mse = np.mean((y - ft) ** 2)
                        if mse < best_mse:
                            best_mse = mse
                            best_params = (alpha, beta, gamma)
                    except Exception:
                        continue

        # Run with best parameters
        forecast, fitted, conf_lower, conf_upper, _ = _holt_winters_additive(
            y, season_length=12,
            alpha=best_params[0], beta=best_params[1], gamma=best_params[2],
            n_forecast=periods,
        )

        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq="MS")

        return {
            "success": True,
            "forecast": forecast.tolist(),
            "forecast_dates": future_dates.strftime("%Y-%m-%d").tolist(),
            "conf_lower": conf_lower.tolist(),
            "conf_upper": conf_upper.tolist(),
            "fitted_values": fitted.tolist(),
            "aic": None, "bic": None,
            "model_type": f"Holt-Winters (α={best_params[0]}, β={best_params[1]}, γ={best_params[2]})",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Holt-Winters failed: {str(e)}",
            "model_type": "Holt-Winters",
        }


# ═══════════════════════════════════════════════════
#  TREND + SEASONAL FORECAST (ARIMA-like)
# ═══════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def run_sarima_forecast(series_values, series_index_str, periods=12):
    """
    Linear Trend + Seasonal decomposition forecast.
    Extracts trend via linear regression, seasonal pattern via averaging,
    then projects both forward. Simulates ARIMA-style forecasting without scipy.
    """
    try:
        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        y = series.values
        n = len(y)
        x = np.arange(n)

        # ── Linear Trend (numpy polyfit — no scipy needed) ──
        coeffs = np.polyfit(x, y, deg=1)  # slope, intercept
        trend_line = np.polyval(coeffs, x)

        # ── Seasonal Component ──
        season_length = 12
        detrended = y - trend_line
        seasonal = np.zeros(season_length)
        for m in range(season_length):
            month_vals = detrended[m::season_length]
            seasonal[m] = np.mean(month_vals) if len(month_vals) > 0 else 0
        seasonal -= np.mean(seasonal)  # normalize

        # ── Residual ──
        seasonal_full = np.array([seasonal[i % season_length] for i in range(n)])
        residual = y - trend_line - seasonal_full
        residual_std = np.std(residual)

        # ── Fitted values ──
        fitted = trend_line + seasonal_full

        # ── Forecast ──
        future_x = np.arange(n, n + periods)
        future_trend = np.polyval(coeffs, future_x)
        future_seasonal = np.array([seasonal[i % season_length] for i in range(n, n + periods)])
        forecast = future_trend + future_seasonal

        # ── Confidence intervals ──
        steps = np.arange(1, periods + 1)
        margin = 1.96 * residual_std * np.sqrt(1 + steps / n)

        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq="MS")

        return {
            "success": True,
            "forecast": forecast.tolist(),
            "forecast_dates": future_dates.strftime("%Y-%m-%d").tolist(),
            "conf_lower": (forecast - margin).tolist(),
            "conf_upper": (forecast + margin).tolist(),
            "fitted_values": fitted.tolist(),
            "aic": None, "bic": None,
            "model_type": f"Trend+Seasonal (slope={coeffs[0]:,.1f}/mo)",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Trend+Seasonal forecast failed: {str(e)}",
            "model_type": "Trend+Seasonal",
        }


# ═══════════════════════════════════════════════════
#  SEASONAL NAIVE
# ═══════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def run_naive_forecast(series_values, series_index_str, periods=12):
    """
    Seasonal Naive: forecast = same value from one year ago.
    Pure pandas, zero dependencies.
    """
    try:
        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        last_date = series.index[-1]
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq="MS")

        seasonal_period = min(12, len(series))
        last_season = series.values[-seasonal_period:]
        forecast = np.array([last_season[i % seasonal_period] for i in range(periods)])

        error_std = series.std() * 0.15
        steps = np.arange(1, periods + 1)
        margin = 1.96 * error_std * np.sqrt(steps / 12)

        return {
            "success": True,
            "forecast": forecast.tolist(),
            "forecast_dates": future_dates.strftime("%Y-%m-%d").tolist(),
            "conf_lower": (forecast - margin).tolist(),
            "conf_upper": (forecast + margin).tolist(),
            "fitted_values": series.values.tolist(),
            "aic": None, "bic": None,
            "model_type": "Seasonal Naive",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Naive forecast failed: {str(e)}",
            "model_type": "Seasonal Naive",
        }


# ═══════════════════════════════════════════════════
#  SEASONAL DECOMPOSITION (pure pandas)
# ═══════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def decompose_series(series_values, series_index_str, model="additive", period=12):
    """
    Seasonal decomposition using centered moving average.
    Pure pandas — no scipy/statsmodels.
    """
    try:
        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        n = len(series)
        if n < period * 2:
            return {
                "success": False,
                "error": f"Need at least {period * 2} data points for decomposition. You have {n}.",
            }

        values = series.values

        # Step 1: Trend via centered moving average
        if period % 2 == 0:
            ma1 = pd.Series(values).rolling(window=period, center=True).mean()
            trend = ma1.rolling(window=2, center=True).mean().values
        else:
            trend = pd.Series(values).rolling(window=period, center=True).mean().values

        # Step 2: Detrend
        if model == "multiplicative":
            detrended = np.where(trend != 0, values / np.where(np.isnan(trend), 1, trend), 0)
        else:
            detrended = values - np.where(np.isnan(trend), 0, trend)

        # Step 3: Seasonal component
        seasonal = np.zeros(n)
        for i in range(period):
            indices = list(range(i, n, period))
            valid_vals = [detrended[j] for j in indices if not np.isnan(detrended[j]) and not np.isnan(trend[j])]
            seasonal_val = np.mean(valid_vals) if valid_vals else 0
            for j in indices:
                seasonal[j] = seasonal_val

        # Normalize
        if model == "multiplicative":
            seasonal_mean = np.mean(seasonal[:period])
            if seasonal_mean != 0:
                seasonal = seasonal / seasonal_mean
        else:
            seasonal = seasonal - np.mean(seasonal[:period])

        # Step 4: Residual
        if model == "multiplicative":
            residual = np.where(
                (trend != 0) & (~np.isnan(trend)) & (seasonal != 0),
                values / (trend * seasonal), np.nan,
            )
        else:
            residual = values - np.where(np.isnan(trend), np.nan, trend) - seasonal

        return {
            "success": True,
            "dates": series.index.strftime("%Y-%m-%d").tolist(),
            "observed": values.tolist(),
            "trend": [None if np.isnan(v) else float(v) for v in trend],
            "seasonal": seasonal.tolist(),
            "residual": [None if np.isnan(v) else float(v) for v in residual],
            "error": None,
        }
    except Exception as e:
        return {"success": False, "error": f"Decomposition failed: {str(e)}"}


# ═══════════════════════════════════════════════════
#  WHAT-IF SCENARIO ENGINE
# ═══════════════════════════════════════════════════

def apply_what_if(base_forecast, price_change_pct=0, budget_change_pct=0, cost_change_pct=0):
    """Apply What-If adjustments to a base forecast."""
    base = np.array(base_forecast)

    price_elasticity = -0.8
    volume_effect = price_change_pct * price_elasticity / 100
    price_revenue_impact = base * (price_change_pct / 100 + volume_effect)

    marketing_roi_multiplier = 0.35
    marketing_impact = base * (budget_change_pct / 100 * marketing_roi_multiplier)

    cost_impact = -base * (cost_change_pct / 100 * 0.6)

    total_impact = price_revenue_impact + marketing_impact + cost_impact
    adjusted = base + total_impact

    return {
        "adjusted_forecast": adjusted.tolist(),
        "base_forecast": base.tolist(),
        "price_impact": price_revenue_impact.tolist(),
        "marketing_impact": marketing_impact.tolist(),
        "cost_impact": cost_impact.tolist(),
        "total_impact": total_impact.tolist(),
        "net_change_pct": float((adjusted.sum() - base.sum()) / base.sum() * 100) if base.sum() != 0 else 0,
    }
