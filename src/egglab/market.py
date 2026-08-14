"""Price formation models and welfare accounting.

Phase 1 uses the transparent monotone affine model from the experiment ladder
(handoff Section 8.2): per slot t, the shared price is

    p_t(q_t) = a_t + b_t * q_t,   b_t >= 0,

where q_t = U_t + L_t is base load plus fleet charging load (kWh per slot).

Economic quantities (all separable across slots; L = fleet load vector):
- posted-price cost   : sum_t p_t^post * L_t                (price taker)
- bill(L)             : sum_t (a_t + b_t (U_t + L_t)) L_t   (strategist, B9)
- system cost delta(L): sum_t int_{U_t}^{U_t+L_t} p(q) dq
                      = sum_t (a_t + b_t U_t) L_t + b_t L_t^2 / 2   (dictator)
- marginal outlay     : a_t + b_t U_t + 2 b_t L_t  (B9: strategist == taker at
                        these prices, evaluated at the strategist's own L)

The bill and system-delta are convex separable quadratics; the MILP oracle
represents them exactly-up-to-tangent-granularity via epigraph tangents
(convex PWL lower envelope). Records store both the model objective and the
exact recomputed objective so the PWL error is always visible.
"""
from __future__ import annotations

import numpy as np


class AffineMarket:
    def __init__(self, a, b, base_load, name: str = "affine"):
        self.a = np.asarray(a, dtype=float)
        self.b = np.asarray(b, dtype=float)
        self.U = np.asarray(base_load, dtype=float)
        assert self.a.shape == self.b.shape == self.U.shape
        assert (self.b >= 0).all(), "supply slope must be nonnegative"
        self.name = name

    @property
    def n_slots(self) -> int:
        return len(self.a)

    def price(self, L) -> np.ndarray:
        """Clearing price when the fleet adds load L (kWh/slot)."""
        return self.a + self.b * (self.U + np.asarray(L, dtype=float))

    def bill(self, L) -> float:
        L = np.asarray(L, dtype=float)
        return float(np.dot(self.price(L), L))

    def system_cost_delta(self, L) -> float:
        L = np.asarray(L, dtype=float)
        return float(np.dot(self.a + self.b * self.U, L) + 0.5 * np.dot(self.b, L * L))

    def marginal_outlay(self, L) -> np.ndarray:
        L = np.asarray(L, dtype=float)
        return self.a + self.b * self.U + 2.0 * self.b * L

    # ---- convex PWL tangent segments for the MILP oracle -------------------
    def _tangents(self, coef_lin: np.ndarray, coef_quad: np.ndarray, l_max: float, n_seg: int):
        """Per-slot tangent lines (slope, intercept) of f_t(L)=coef_lin_t*L +
        coef_quad_t*L^2 at n_seg breakpoints on [0, l_max]. Epigraph of the
        max of tangents is the standard convex outer approximation; error is
        O((l_max/n_seg)^2 * coef_quad)."""
        xs = np.linspace(0.0, l_max, n_seg)
        segs = []
        for t in range(self.n_slots):
            rows = []
            for x in xs:
                slope = coef_lin[t] + 2.0 * coef_quad[t] * x
                intercept = -coef_quad[t] * x * x
                rows.append((float(slope), float(intercept)))
            segs.append(rows)
        return segs

    def bill_segments(self, l_max: float, n_seg: int = 16):
        return self._tangents(self.a + self.b * self.U, self.b, l_max, n_seg)

    def system_delta_segments(self, l_max: float, n_seg: int = 16):
        return self._tangents(self.a + self.b * self.U, 0.5 * self.b, l_max, n_seg)


PRICE_SHAPES = ("flat", "duck", "two_valley")


def make_affine_market(
    inst,
    shape: str = "duck",
    a_level: float = 1.0,
    a_amp: float = 0.8,
    b_scale: float = 0.0,
    base_load_level: float = 50.0,
    name: str | None = None,
) -> AffineMarket:
    """Standard Phase-1 market family. b_scale controls market depth (price
    impact); b_scale = 0 reproduces the exogenous-price (EVSP-DR) limit.
    Units: a in SEK/kWh, b in SEK/kWh per kWh-of-slot-load."""
    T = inst.n_slots
    h = np.arange(T) % 24
    if shape == "flat":
        a = np.full(T, a_level)
    elif shape == "duck":
        a = a_level + a_amp * (
            np.exp(-((h - 8) ** 2) / 8.0) + np.exp(-((h - 18) ** 2) / 8.0)
        ) - 0.4 * a_amp * np.exp(-((h - 13) ** 2) / 10.0)
    elif shape == "two_valley":
        a = a_level + a_amp * 0.5 * np.cos((h - 3) * np.pi / 6.0) ** 2
    else:
        raise ValueError(f"unknown shape {shape!r}")
    b = np.full(T, b_scale)
    U = np.full(T, base_load_level)
    return AffineMarket(a, b, U, name=name or f"{shape}-b{b_scale:g}")
