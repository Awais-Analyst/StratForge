"""
StratForge - Optimization Engine
PuLP-based linear programming for budget allocation and pricing optimization.
Supports continuous and integer variables. Friendly error handling for infeasible/unbounded.
"""

import numpy as np
import pandas as pd
import streamlit as st
from pulp import (
    LpMaximize,
    LpMinimize,
    LpProblem,
    LpVariable,
    LpInteger,
    LpContinuous,
    lpSum,
    value,
    LpStatus,
)


@st.cache_data(ttl=3600)
def optimize_budget_allocation(
    total_budget,
    channels,
    roi_coefficients,
    min_allocations=None,
    max_allocations=None,
    use_integer=False,
    integer_step=10000,
):
    """
    Optimize marketing budget allocation across channels to maximize total ROI.

    Parameters:
        total_budget: Total available budget
        channels: List of channel names
        roi_coefficients: Expected ROI per unit spend for each channel
        min_allocations: Minimum spend per channel (dict or None)
        max_allocations: Maximum spend per channel (dict or None)
        use_integer: If True, use integer variables (discrete chunks)
        integer_step: Step size for integer allocation (e.g., 10,000 = allocate in chunks of 10k)

    Returns dict with optimal allocations, total ROI, status, and sensitivity info.
    """
    try:
        n = len(channels)
        if min_allocations is None:
            min_allocations = {ch: 0 for ch in channels}
        if max_allocations is None:
            max_allocations = {ch: total_budget for ch in channels}

        # Validate constraints
        min_total = sum(min_allocations.get(ch, 0) for ch in channels)
        if min_total > total_budget:
            return {
                "success": False,
                "status": "Infeasible",
                "error": (
                    f"Minimum allocations sum to ₹{min_total:,.0f} which exceeds "
                    f"total budget of ₹{total_budget:,.0f}. "
                    f"Try reducing minimum constraints by at least ₹{min_total - total_budget:,.0f}."
                ),
            }

        # Build LP problem
        prob = LpProblem("Budget_Allocation", LpMaximize)

        # Decision variables
        if use_integer:
            # Integer variables: allocate in chunks of `integer_step`
            vars_dict = {}
            for ch in channels:
                max_units = int(max_allocations.get(ch, total_budget) / integer_step)
                min_units = int(np.ceil(min_allocations.get(ch, 0) / integer_step))
                vars_dict[ch] = LpVariable(
                    f"alloc_{ch}", lowBound=min_units, upBound=max_units, cat=LpInteger
                )
            # Objective: maximize ROI
            prob += lpSum(
                roi_coefficients[i] * vars_dict[channels[i]] * integer_step
                for i in range(n)
            )
            # Budget constraint
            prob += lpSum(vars_dict[ch] * integer_step for ch in channels) <= total_budget
        else:
            # Continuous variables
            vars_dict = {}
            for ch in channels:
                vars_dict[ch] = LpVariable(
                    f"alloc_{ch}",
                    lowBound=min_allocations.get(ch, 0),
                    upBound=max_allocations.get(ch, total_budget),
                    cat=LpContinuous,
                )
            # Objective: maximize ROI
            prob += lpSum(roi_coefficients[i] * vars_dict[channels[i]] for i in range(n))
            # Budget constraint
            prob += lpSum(vars_dict[ch] for ch in channels) <= total_budget

        # Solve (suppress verbose output)
        from pulp import PULP_CBC_CMD
        prob.solve(PULP_CBC_CMD(msg=0))
        status = LpStatus[prob.status]

        if status != "Optimal":
            suggestions = {
                "Infeasible": "Try relaxing the minimum allocation constraints or increasing the total budget.",
                "Unbounded": "Try adding maximum allocation constraints per channel.",
                "Not Solved": "The solver encountered an error. Try simplifying constraints.",
            }
            return {
                "success": False,
                "status": status,
                "error": f"Optimization {status}. {suggestions.get(status, 'Please check your inputs.')}",
            }

        # Extract results
        allocations = {}
        for ch in channels:
            if use_integer:
                allocations[ch] = float(value(vars_dict[ch])) * integer_step
            else:
                allocations[ch] = float(value(vars_dict[ch]))

        total_allocated = sum(allocations.values())
        total_roi = float(value(prob.objective))

        # Calculate per-channel ROI
        channel_roi = {}
        for i, ch in enumerate(channels):
            channel_roi[ch] = allocations[ch] * roi_coefficients[i]

        return {
            "success": True,
            "status": "Optimal",
            "allocations": allocations,
            "channel_roi": channel_roi,
            "total_allocated": total_allocated,
            "total_roi": total_roi,
            "budget_utilization": total_allocated / total_budget * 100 if total_budget > 0 else 0,
            "error": None,
        }

    except Exception as e:
        return {
            "success": False,
            "status": "Error",
            "error": f"Optimization error: {str(e)}",
        }


@st.cache_data(ttl=3600)
def run_sensitivity_analysis(
    total_budget,
    channels,
    roi_coefficients,
    min_allocations=None,
    max_allocations=None,
    budget_variations=None,
):
    """
    Run sensitivity analysis: how does the optimal ROI change as budget varies?

    Parameters:
        budget_variations: List of budget multipliers (e.g., [0.5, 0.75, 1.0, 1.25, 1.5])

    Returns list of results for each budget level.
    """
    if budget_variations is None:
        budget_variations = [0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5]

    results = []
    for mult in budget_variations:
        adj_budget = total_budget * mult
        result = optimize_budget_allocation(
            adj_budget, channels, roi_coefficients,
            min_allocations=min_allocations,
            max_allocations=max_allocations,
            use_integer=False,
        )
        results.append({
            "budget_multiplier": mult,
            "budget": adj_budget,
            "total_roi": result.get("total_roi", 0) if result["success"] else 0,
            "allocations": result.get("allocations", {}) if result["success"] else {},
            "success": result["success"],
        })
    return results


@st.cache_data(ttl=3600)
def optimize_pricing(
    current_price,
    current_volume,
    elasticity=-0.8,
    cost_per_unit=None,
    price_range=(0.7, 1.5),
    steps=50,
):
    """
    Find optimal price point given demand elasticity.
    Uses grid search over price range.

    Parameters:
        current_price: Current unit price
        current_volume: Current sales volume
        elasticity: Price elasticity of demand (typically negative)
        cost_per_unit: Variable cost per unit (for profit optimization)
        price_range: Tuple of (min_multiplier, max_multiplier) relative to current price
        steps: Number of price points to evaluate

    Returns optimal price, volume, revenue, and profit with the full sweep data.
    """
    try:
        if cost_per_unit is None:
            cost_per_unit = current_price * 0.4  # Assume 40% cost

        prices = np.linspace(
            current_price * price_range[0],
            current_price * price_range[1],
            steps,
        )

        results = []
        for price in prices:
            price_change_pct = (price - current_price) / current_price
            volume_change_pct = price_change_pct * elasticity
            volume = current_volume * (1 + volume_change_pct)
            volume = max(volume, 0)

            revenue = price * volume
            profit = (price - cost_per_unit) * volume

            results.append({
                "price": float(price),
                "volume": float(volume),
                "revenue": float(revenue),
                "profit": float(profit),
                "margin": float((price - cost_per_unit) / price * 100) if price > 0 else 0,
            })

        # Find optimal points
        if len(results) > 0:
            results_df = pd.DataFrame(results)
            max_revenue_idx = results_df["revenue"].idxmax()
            max_profit_idx = results_df["profit"].idxmax()

            return {
                "success": True,
                "sweep_data": results,
                "optimal_revenue_price": results[max_revenue_idx]["price"],
                "optimal_revenue": results[max_revenue_idx]["revenue"],
                "optimal_profit_price": results[max_profit_idx]["price"],
                "optimal_profit": results[max_profit_idx]["profit"],
                "optimal_profit_volume": results[max_profit_idx]["volume"],
                "optimal_profit_margin": results[max_profit_idx]["margin"],
                "current_revenue": current_price * current_volume,
                "current_profit": (current_price - cost_per_unit) * current_volume,
                "error": None,
            }
        else:
            return {"success": False, "error": "No valid price points found."}

    except Exception as e:
        return {"success": False, "error": f"Pricing optimization error: {str(e)}"}


# ── Optimization Presets ──

OPTIMIZATION_PRESETS = {
    "Aggressive Growth": {
        "total_budget": 1_500_000,
        "min_pct": {"Digital": 0.20, "Print": 0.0, "TV": 0.05, "Social Media": 0.15, "Events": 0.05},
        "max_pct": {"Digital": 0.50, "Print": 0.15, "TV": 0.30, "Social Media": 0.40, "Events": 0.20},
        "description": "Heavy digital & social investment, minimal print",
    },
    "Cost-Cutting": {
        "total_budget": 500_000,
        "min_pct": {"Digital": 0.10, "Print": 0.0, "TV": 0.0, "Social Media": 0.10, "Events": 0.0},
        "max_pct": {"Digital": 0.40, "Print": 0.10, "TV": 0.15, "Social Media": 0.35, "Events": 0.10},
        "description": "Lean budget focused on highest-ROI channels",
    },
    "Balanced": {
        "total_budget": 1_000_000,
        "min_pct": {"Digital": 0.10, "Print": 0.05, "TV": 0.10, "Social Media": 0.10, "Events": 0.05},
        "max_pct": {"Digital": 0.35, "Print": 0.20, "TV": 0.30, "Social Media": 0.30, "Events": 0.15},
        "description": "Even distribution across all channels",
    },
}
