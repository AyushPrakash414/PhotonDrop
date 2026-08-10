"""
PhotonDrop — Degree Distribution

Implements the Robust Soliton Distribution (RSD) for LT fountain coding.

The RSD provides a theoretically optimal degree distribution that ensures
the belief-propagation decoder can recover K source blocks from roughly
K * (1 + ε) encoded symbols with high probability.
"""

from __future__ import annotations

import math
import random
from typing import List


def _ideal_soliton(K: int) -> List[float]:
    """Compute the Ideal Soliton Distribution ρ(d) for d = 1 … K.

    ρ(1) = 1/K
    ρ(d) = 1 / (d * (d - 1))  for d = 2 … K
    """
    rho = [0.0]  # placeholder for index 0 (degrees are 1-based)
    rho.append(1.0 / K)
    for d in range(2, K + 1):
        rho.append(1.0 / (d * (d - 1)))
    return rho


def _tau(K: int, c: float, delta: float) -> List[float]:
    """Compute the extra component τ(d) of the Robust Soliton Distribution.

    Parameters
    ----------
    K : int
        Number of source blocks.
    c : float
        A free parameter (typically 0.01 – 0.5).  Controls the "spike"
        position and height.
    delta : float
        Failure probability bound (typically 0.05 – 0.5).
    """
    S = c * math.log(K / delta) * math.sqrt(K)
    S = max(S, 1.0)  # safety floor
    pivot = max(1, int(math.floor(K / S)))

    tau = [0.0]  # placeholder for index 0
    for d in range(1, K + 1):
        if 1 <= d < pivot:
            tau.append(S / (d * K))
        elif d == pivot:
            tau.append(S * math.log(S / delta) / K)
        else:
            tau.append(0.0)
    return tau


def robust_soliton_distribution(
    K: int,
    c: float = 0.1,
    delta: float = 0.5,
) -> List[float]:
    """Compute the normalised Robust Soliton Distribution μ(d) for d = 1 … K.

    Parameters
    ----------
    K : int
        Number of source blocks.
    c : float
        Free parameter controlling the spike (default 0.1).
    delta : float
        Failure probability bound (default 0.5).

    Returns
    -------
    List[float]
        Probability mass function indexed 0 … K.  Index 0 is unused
        (degrees start at 1).
    """
    if K < 1:
        raise ValueError("K must be >= 1")

    rho = _ideal_soliton(K)
    tau = _tau(K, c, delta)

    # Unnormalised μ = ρ + τ
    mu = [0.0] + [rho[d] + tau[d] for d in range(1, K + 1)]

    # Normalise
    total = sum(mu[1:])
    if total > 0:
        mu = [0.0] + [mu[d] / total for d in range(1, K + 1)]

    return mu


class DegreeSampler:
    """Efficiently samples degrees from the Robust Soliton Distribution.

    Uses a cumulative distribution function (CDF) for O(log K) sampling
    via binary search.
    """

    def __init__(self, K: int, c: float = 0.1, delta: float = 0.5):
        self.K = K
        self.pmf = robust_soliton_distribution(K, c, delta)
        # Build CDF
        self._cdf: List[float] = [0.0]
        cumulative = 0.0
        for d in range(1, K + 1):
            cumulative += self.pmf[d]
            self._cdf.append(cumulative)
        # Ensure the last entry is exactly 1.0 to avoid floating-point edge cases
        self._cdf[-1] = 1.0

    def sample(self, rng: random.Random) -> int:
        """Sample a degree from the distribution using the given RNG."""
        u = rng.random()
        # Binary search for the smallest d such that CDF[d] >= u
        lo, hi = 1, self.K
        while lo < hi:
            mid = (lo + hi) // 2
            if self._cdf[mid] < u:
                lo = mid + 1
            else:
                hi = mid
        return lo
