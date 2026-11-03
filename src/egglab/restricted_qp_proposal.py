"""Numerical restricted-pool simplex proposal, without certification or pricing.

Inputs are fixed complete-fleet operating costs and hourly load vectors. The
caller must separately replay columns, rational objective and residual, then
obtain a fresh global pricing bound before any hull certification claim.
"""
from __future__ import annotations

from fractions import Fraction
import math
from time import perf_counter

import numpy as np
from scipy.optimize import minimize


def _inputs(costs, loads, a, b):
    c = np.asarray(costs, dtype=float)
    x = np.asarray(loads, dtype=float)
    intercept = np.asarray(a, dtype=float)
    curvature = np.asarray(b, dtype=float)
    if (c.ndim != 1 or not len(c) or x.ndim != 2 or x.shape[0] != len(c)
            or intercept.ndim != 1 or curvature.ndim != 1
            or x.shape[1] != len(intercept) or len(intercept) != len(curvature)
            or not all(np.all(np.isfinite(v)) for v in (c, x, intercept, curvature))
            or np.any(x < 0) or np.any(curvature < 0)):
        raise ValueError("Expected finite fixed columns, nonnegative loads and curvature")
    return c, x, intercept, curvature


def _objective(weights, costs, loads, a, b):
    hourly = weights @ loads
    price = a + b * hourly
    value = float(weights @ costs + a @ hourly + .5 * b @ (hourly * hourly))
    gradient = costs + loads @ price
    return value, gradient, hourly


def _round_simplex(weights, denominator):
    if type(denominator) is not int or denominator <= 0:
        raise ValueError("denominator must be a positive integer")
    values = np.asarray(weights, dtype=float)
    if values.ndim != 1 or not len(values) or not np.all(np.isfinite(values)):
        raise ValueError("Expected finite simplex proposal")
    values = np.maximum(values, 0)
    if values.sum() <= 0:
        raise ValueError("Zero simplex proposal")
    values /= values.sum()
    scaled = values * denominator
    units = [int(math.floor(float(v))) for v in scaled]
    missing = denominator - sum(units)
    order = sorted(range(len(units)), key=lambda i: (-(scaled[i] - units[i]), i))
    for i in order[:missing]:
        units[i] += 1
    if any(u < 0 for u in units) or sum(units) != denominator:
        raise ValueError("Rational simplex rounding failed")
    return units, [Fraction(u, denominator) for u in units]


def propose(costs, loads, a, b, *, denominator=1_000_000_000, maxiter=500):
    """Return a finite numerical candidate and fixed-denominator rational weights.

    `success` is only SciPy's termination flag. Residual values here are
    diagnostics for later independent exact replay, never a certificate.
    """
    c, x, intercept, curvature = _inputs(costs, loads, a, b)
    if type(maxiter) is not int or maxiter <= 0:
        raise ValueError("maxiter must be a positive integer")
    start = perf_counter()
    n = len(c)
    initial = np.zeros(n)
    initial[int(np.argmin(c + x @ intercept))] = 1
    solved = minimize(lambda w: _objective(w, c, x, intercept, curvature)[0],
                      initial, jac=lambda w: _objective(w, c, x, intercept, curvature)[1],
                      method="SLSQP", bounds=[(0.0, 1.0)] * n,
                      constraints=[{"type": "eq", "fun": lambda w: float(sum(w) - 1),
                                    "jac": lambda w: np.ones(n)}],
                      options={"ftol": 1e-12, "maxiter": maxiter, "disp": False})
    numeric_seconds = perf_counter() - start
    if not np.all(np.isfinite(solved.x)) or solved.x.sum() <= 0:
        raise RuntimeError("SLSQP returned no finite simplex proposal")
    numeric_value, numeric_gradient, numeric_load = _objective(
        solved.x, c, x, intercept, curvature)
    if (not math.isfinite(numeric_value) or not np.all(np.isfinite(numeric_gradient))
            or not np.all(np.isfinite(numeric_load))):
        raise RuntimeError("SLSQP proposal has nonfinite objective or gradient")
    rounding_start = perf_counter()
    units, rational = _round_simplex(solved.x, denominator)
    rounded = np.asarray([float(w) for w in rational])
    objective, gradient, hourly = _objective(rounded, c, x, intercept, curvature)
    if (not math.isfinite(objective) or not np.all(np.isfinite(gradient))
            or not np.all(np.isfinite(hourly))):
        raise RuntimeError("Rounded proposal has nonfinite objective or gradient")
    directional_residual = max(0.0, float(rounded @ gradient - np.min(gradient)))
    rounding_seconds = perf_counter() - rounding_start
    return {"scope": "restricted-pool proposal only; no replay, global bound or certificate",
            "solver": "SciPy SLSQP", "success": bool(solved.success),
            "solver_status": int(solved.status), "solver_message": str(solved.message),
            "iterations": int(solved.nit), "numeric_seconds": numeric_seconds,
            "rounding_seconds": rounding_seconds, "denominator": denominator,
            "numeric_weights": [float(v) for v in solved.x],
            "numeric_objective_diagnostic": numeric_value,
            "numeric_simplex_sum": float(sum(solved.x)),
            "numeric_negative_mass": float(sum(np.maximum(-solved.x, 0))),
            "numeric_column_gradients": [float(v) for v in numeric_gradient],
            "numeric_hourly_load": [float(v) for v in numeric_load],
            "integer_units": units, "weights_exact": [str(w) for w in rational],
            "rounded_objective_diagnostic": objective,
            "rounded_hourly_load": [float(v) for v in hourly],
            "rounded_column_gradients": [float(v) for v in gradient],
            "rounded_directional_residual_diagnostic": directional_residual}
