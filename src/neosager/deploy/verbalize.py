"""Verbalization layer: calibrated probabilities -> at most two short
sentences plus a confidence word. Pure function, no I/O, integer-friendly
thresholds. The prose must never contradict the probabilities: wording
strength is monotone in P(precip) (property-tested).

Threshold semantics are tied to calibration: "likely" is issued at p >= 0.70
so it should verify 70-85% of the time (checked against the calib fold in
the M4 report; adjust THRESH there if the bands drift).

Precedence: the earliest lead whose signal clears a threshold wins the
precip sentence — "rain soon" beats "rain tomorrow".
"""

from __future__ import annotations

# ---- committed thresholds (documented in the M4 report) ----
T_LIKELY = 0.70
T_VERY_LIKELY = 0.85
T_POSSIBLE = 0.40
T_UNLIKELY = 0.15
T_WIND_FRESH = 0.50
T_WIND_STRONG = 0.70
T_DETERIORATE = 0.60
RISING_TREND = 0.5        # hPa / 3h

_DAYPART = ["overnight", "overnight", "by early morning", "by morning",
            "by midday", "by afternoon", "by evening", "by night"]


def _daypart(local_hour: int, lead_h: int) -> str:
    h = (local_hour + lead_h) % 24
    return _DAYPART[h // 3]


def _confidence(p_max_signal: float) -> str:
    """Confidence word from how decisive the strongest signal is."""
    d = abs(p_max_signal - 0.5)
    if d >= 0.35:
        return "High confidence."
    if d >= 0.2:
        return "Fairly confident."
    return "Uncertain."


def verbalize(probs: dict[str, float | None], local_hour: int = 12,
              trend_hpa_3h: float | None = None) -> str:
    """probs keys: precip_6h/12h/24h, windup_6h/12h/24h, pfall_6h/12h/24h.
    Missing/None entries are tolerated (degrades to the leads present)."""
    def g(k: str) -> float | None:
        v = probs.get(k)
        return None if v is None else float(v)

    p6, p12, p24 = g("precip_6h"), g("precip_12h"), g("precip_24h")
    w12 = g("windup_12h")
    f12 = g("pfall_12h")

    # ---- sentence 1: precipitation, earliest decisive lead wins ----
    s1 = None
    for p, lead, soon in [(p6, 6, "within a few hours"),
                          (p12, 12, None), (p24, 24, None)]:
        if p is None:
            continue
        when = soon or _daypart(local_hour, lead)
        if p >= T_VERY_LIKELY:
            s1 = f"Rain very likely {when} ({round(p * 100)}%)."
            break
        if p >= T_LIKELY:
            s1 = f"Rain likely {when} ({round(p * 100)}%)."
            break
    if s1 is None:
        best = max((p for p in (p6, p12, p24) if p is not None),
                   default=None)
        if best is None:
            return "No forecast: insufficient data."
        if best >= T_POSSIBLE:
            lead = 6 if (p6 or 0) >= T_POSSIBLE else 12 if (p12 or 0) >= T_POSSIBLE else 24
            when = "soon" if lead == 6 else _daypart(local_hour, lead)
            s1 = f"Rain possible {when} ({round(best * 100)}%)."
        elif best <= T_UNLIKELY:
            if trend_hpa_3h is not None and trend_hpa_3h >= RISING_TREND:
                s1 = "Fair and improving."
            else:
                s1 = "Fair; rain unlikely."
        else:
            s1 = "Mainly dry; a shower cannot be ruled out."

    # ---- sentence 2: wind / deterioration (one clause each at most) ----
    clauses = []
    if w12 is not None:
        if w12 >= T_WIND_STRONG:
            clauses.append("wind increasing markedly")
        elif w12 >= T_WIND_FRESH:
            clauses.append("wind freshening")
    if f12 is not None and f12 >= T_DETERIORATE:
        clauses.append("pressure falling — conditions deteriorating")
    s2 = (clauses[0][0].upper() + clauses[0][1:] +
          ("; " + clauses[1] if len(clauses) > 1 else "") + "."
          ) if clauses else None

    signals = [p for p in (p6, p12, p24, w12, f12) if p is not None]
    conf = _confidence(max(signals, key=lambda p: abs(p - 0.5))
                       if signals else 0.5)

    return " ".join(x for x in (s1, s2, conf) if x)


# ordinal wording strength, exported for the monotonicity property test
WORDING_RANK = ["Fair and improving.", "Fair; rain unlikely.",
                "Mainly dry; a shower cannot be ruled out.",
                "Rain possible", "Rain likely", "Rain very likely"]


def wording_rank(text: str) -> int:
    for i, w in reversed(list(enumerate(WORDING_RANK))):
        if text.startswith(w.split(" (")[0][:12]):
            return i
    return -1
