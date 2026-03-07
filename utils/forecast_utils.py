"""
StratForge - Forecasting Utilities
Uses statsforecast (AutoARIMA, AutoETS, SeasonalNaive) for fast, lightweight forecasting.
Includes pandas-based seasonal decomposition (no scipy/statsmodels needed).
All heavy computations cached with @st.cache_data.
"""

import pandas as pd
import numpy as np
import streamlit as st
import warnings

warnings.filterwarnings("ignore")


@st.cache_data(ttl=3600)
def run_sarima_forecast(series_values, series_index_str, periods=12):
    """
    Fit AutoARIMA via statsforecast and forecast `periods` steps ahead.
    Returns dict with forecast, confidence intervals, fitted values, and model info.
    """
    try:
        from statsforecast import StatsForecast
        from statsforecast.models import AutoARIMA

        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        # Prepare data in statsforecast format
        sf_df = pd.DataFrame({
            "unique_id": ["series"] * len(series),
            "ds": series.index,
            "y": series.values,
        })

        sf = StatsForecast(
            models=[AutoARIMA(season_length=12)],
            freq="MS",
        )
        sf.fit(sf_df)

        # Forecast with 95% confidence intervals
        forecast_df = sf.predict(h=periods, level=[95])

        # Extract fitted values (in-sample) - safe fallback
        try:
            fitted_df = sf.fitted_[0]
            fitted_vals = fitted_df["AutoARIMA"].values.tolist() if "AutoARIMA" in fitted_df.columns else series.values.tolist()
        except (AttributeError, IndexError, KeyError):
            fitted_vals = series.values.tolist()

        forecast_vals = forecast_df["AutoARIMA"].values
        conf_lower = forecast_df["AutoARIMA-lo-95"].values
        conf_upper = forecast_df["AutoARIMA-hi-95"].values
        # Handle ds column - might be index or column
        if "ds" in forecast_df.columns:
            future_dates = pd.to_datetime(forecast_df["ds"]).dt.strftime("%Y-%m-%d").tolist()
        else:
            future_dates = pd.to_datetime(forecast_df.index).strftime("%Y-%m-%d").tolist()

        return {
            "success": True,
            "forecast": forecast_vals.tolist(),
            "forecast_dates": future_dates,
            "conf_lower": conf_lower.tolist(),
            "conf_upper": conf_upper.tolist(),
            "fitted_values": fitted_vals,
            "aic": None,
            "bic": None,
            "model_type": "AutoARIMA",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AutoARIMA failed: {str(e)}. Try Holt-Winters (AutoETS) instead.",
            "model_type": "AutoARIMA",
        }


@st.cache_data(ttl=3600)
def run_exp_smoothing(series_values, series_index_str, periods=12):
    """
    Fit AutoETS (Holt-Winters family) via statsforecast and forecast.
    """
    try:
        from statsforecast import StatsForecast
        from statsforecast.models import AutoETS

        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        sf_df = pd.DataFrame({
            "unique_id": ["series"] * len(series),
            "ds": series.index,
            "y": series.values,
        })

        sf = StatsForecast(
            models=[AutoETS(season_length=12)],
            freq="MS",
        )
        sf.fit(sf_df)

        forecast_df = sf.predict(h=periods, level=[95])

        try:
            fitted_df = sf.fitted_[0]
            fitted_vals = fitted_df["AutoETS"].values.tolist() if "AutoETS" in fitted_df.columns else series.values.tolist()
        except (AttributeError, IndexError, KeyError):
            fitted_vals = series.values.tolist()

        forecast_vals = forecast_df["AutoETS"].values
        conf_lower = forecast_df["AutoETS-lo-95"].values
        conf_upper = forecast_df["AutoETS-hi-95"].values
        if "ds" in forecast_df.columns:
            future_dates = pd.to_datetime(forecast_df["ds"]).dt.strftime("%Y-%m-%d").tolist()
        else:
            future_dates = pd.to_datetime(forecast_df.index).strftime("%Y-%m-%d").tolist()

        return {
            "success": True,
            "forecast": forecast_vals.tolist(),
            "forecast_dates": future_dates,
            "conf_lower": conf_lower.tolist(),
            "conf_upper": conf_upper.tolist(),
            "fitted_values": fitted_vals,
            "aic": None,
            "bic": None,
            "model_type": "AutoETS (Holt-Winters)",
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"AutoETS failed: {str(e)}",
            "model_type": "AutoETS (Holt-Winters)",
        }


@st.cache_data(ttl=3600)
def run_naive_forecast(series_values, series_index_str, periods=12):
    """
    Seasonal naive forecast using statsforecast SeasonalNaive.
    Falls back to pure pandas if statsforecast fails.
    """
    try:
        from statsforecast import StatsForecast
        from statsforecast.models import SeasonalNaive

        series = pd.Series(list(series_values), index=pd.to_datetime(list(series_index_str)))
        series = series.asfreq("MS")
        if series.isna().any():
            series = series.interpolate(method="linear")

        sf_df = pd.DataFrame({
            "unique_id": ["series"] * len(series),
            "ds": series.index,
            "y": series.values,
        })

        sf = StatsForecast(
            models=[SeasonalNaive(season_length=12)],
            freq="MS",
        )
        sf.fit(sf_df)

        forecast_df = sf.predict(h=periods, level=[95])

        forecast_vals = forecast_df["SeasonalNaive"].values
        conf_lower = forecast_df["SeasonalNaive-lo-95"].values
        conf_upper = forecast_df["SeasonalNaive-hi-95"].values
        if "ds" in forecast_df.columns:
            future_dates = pd.to_datetime(forecast_df["ds"]).dt.strftime("%Y-%m-%d").tolist()
        else:
            future_dates = pd.to_datetime(forecast_df.index).strftime("%Y-%m-%d").tolist()

        return {
            "success": True,
            "forecast": forecast_vals.tolist(),
            "forecast_dates": future_dates,
            "conf_lower": conf_lower.tolist(),
            "conf_upper": conf_upper.tolist(),
            "fitted_values": series.values.tolist(),
            "aic": None,
            "bic": None,
            "model_type": "Seasonal Naive",
            "error": None,
        }
    except Exception as e:
        # Pure pandas fallback
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
                "aic": None,
                "bic": None,
                "model_type": "Seasonal Naive (Fallback)",
                "error": None,
            }
        except Exception as e2:
            return {
                "success": False,
                "error": f"Naive forecast failed: {str(e2)}",
                "model_type": "Seasonal Naive",
            }


@st.cache_data(ttl=3600)
def decompose_series(series_values, series_index_str, model="additive", period=12):
    """
    Perform seasonal decomposition using pure pandas (no scipy/statsmodels).
    Uses centered moving average for trend extraction.
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

        # ── Step 1: Trend via centered moving average ──
        if period % 2 == 0:
            # For even period: 2x moving average
            ma1 = pd.Series(values).rolling(window=period, center=True).mean()
            trend = ma1.rolling(window=2, center=True).mean().values
        else:
            trend = pd.Series(values).rolling(window=period, center=True).mean().values

        # ── Step 2: Detrend ──
        if model == "multiplicative":
            detrended = np.where(trend != 0, values / np.where(np.isnan(trend), 1, trend), 0)
        else:
            detrended = values - np.where(np.isnan(trend), 0, trend)

        # ── Step 3: Seasonal component ──
        seasonal = np.zeros(n)
        for i in range(period):
            indices = list(range(i, n, period))
            valid_vals = [detrended[j] for j in indices if not np.isnan(detrended[j]) and not np.isnan(trend[j])]
            if valid_vals:
                seasonal_val = np.mean(valid_vals)
            else:
                seasonal_val = 0
            for j in indices:
                seasonal[j] = seasonal_val

        # Normalize seasonal component
        if model == "multiplicative":
            seasonal_mean = np.mean(seasonal[:period])
            if seasonal_mean != 0:
                seasonal = seasonal / seasonal_mean
        else:
            seasonal = seasonal - np.mean(seasonal[:period])

        # ── Step 4: Residual ──
        if model == "multiplicative":
            residual = np.where(
                (trend != 0) & (~np.isnan(trend)) & (seasonal != 0),
                values / (trend * seasonal),
                np.nan,
            )
        else:
            residual = values - np.where(np.isnan(trend), np.nan, trend) - seasonal

        dates_str = series.index.strftime("%Y-%m-%d").tolist()
        return {
            "success": True,
            "dates": dates_str,
            "observed": values.tolist(),
            "trend": [None if np.isnan(v) else float(v) for v in trend],
            "seasonal": seasonal.tolist(),
            "residual": [None if np.isnan(v) else float(v) for v in residual],
            "error": None,
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Decomposition failed: {str(e)}",
        }


def apply_what_if(base_forecast, price_change_pct=0, budget_change_pct=0, cost_change_pct=0):
    """
    Apply What-If scenario adjustments to a base forecast.
    Returns adjusted forecast values with impact breakdown.
    """
    base = np.array(base_forecast)

    # Revenue impact from price change (simplified elasticity model)
    price_elasticity = -0.8  # typical demand elasticity
    volume_effect = price_change_pct * price_elasticity / 100
    price_revenue_impact = base * (price_change_pct / 100 + volume_effect)

    # Revenue impact from marketing budget change
    marketing_roi_multiplier = 0.35  # 35% of budget change translates to revenue
    marketing_impact = base * (budget_change_pct / 100 * marketing_roi_multiplier)

    # Cost impact
    cost_impact = -base * (cost_change_pct / 100 * 0.6)  # 60% pass-through to profit

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
