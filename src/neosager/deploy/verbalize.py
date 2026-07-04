"""Verbalization layer v2 — Sager-format output, calibrated content.

Format (mirrors the 1942 dial's output structure):
  "Forecast for the next 12-24 hours: {weather narrative}. {wind clause}.
   {confidence word}"

The weather narrative uses the SHAPE of the calibrated probabilities across
the 6/12/24h leads to say what the dial said with hand-built cells —
"increasing cloudiness followed by rain", "rain, then improvement within
12 hours" — but each phrasing is triggered by committed probability
patterns, so the words stay honest (thresholds tie to the verified
calibration bands: "likely" >= 0.70 observes 73-83% on held-out data).

Wind clause reconstructs the dial's absolute vocabulary from the current
direction plus the predicted relative shift: current SW + veering ->
"Southwest or West winds", plus the expected band in the dial's mph
vocabulary and an explicit gale-risk percentage when material.

Pure function, no I/O; property-tested in tests/test_verbalize.py.
"""

from __future__ import annotations

# ---- committed thresholds ----
T_VERY = 0.85
T_LIKELY = 0.70
T_POSSIBLE = 0.40
T_UNLIKELY = 0.15
T_IMPROVE_DROP = 0.35    # later-lead prob below this after an early high
RISING_TREND = 0.5       # hPa / 3h
T_GALE_RISK = 0.15
T_STRONG_POSSIBLE = 0.30
T_DIR_CONF = 0.45

SECTOR8 = ["North", "Northeast", "East", "Southeast", "South", "Southwest",
           "West", "Northwest"]
BAND_TEXT = ["calm", "light (1-12 mph)", "moderate to fresh (13-24 mph)",
             "strong (25-38 mph)", "gale (39 mph and above)"]

_DAYPART = ["overnight", "overnight", "by early morning", "by morning",
            "by midday", "by afternoon", "by evening", "by night"]


def _daypart(local_hour: int, lead_h: int) -> str:
    return _DAYPART[((local_hour + lead_h) % 24) // 3]


def _confidence(p: float) -> str:
    d = abs(p - 0.5)
    if d >= 0.35:
        return "High confidence."
    if d >= 0.2:
        return "Fairly confident."
    return "Uncertain."


def weather_narrative(p6: float | None, p12: float | None,
                      p24: float | None, local_hour: int,
                      trend_hpa_3h: float | None,
                      pfall_12h: float | None) -> tuple[str, float]:
    """Returns (clause, headline probability used for confidence)."""
    ps = [p for p in (p6, p12, p24) if p is not None]
    if not ps:
        return "No forecast: insufficient data", 0.5
    best = max(ps)
    pct = f" ({round(best * 100)}%)"

    hi6 = p6 is not None and p6 >= T_LIKELY
    hi12 = p12 is not None and p12 >= T_LIKELY
    hi24 = p24 is not None and p24 >= T_LIKELY
    later_drops = (p24 is not None and p24 <= T_IMPROVE_DROP)
    strength = "very likely" if best >= T_VERY else "likely"

    if hi6:
        if later_drops:
            w = f"Rain or showers within a few hours{pct}, followed by " \
                f"improvement within 12 hours"
        elif hi24 or hi12:
            w = f"Rain or showers within a few hours{pct}, continuing " \
                f"through the period"
        else:
            w = f"Rain or showers within a few hours{pct}, gradually easing"
    elif hi12:
        when = _daypart(local_hour, 12)
        if later_drops:
            w = f"Rain or showers {strength} {when}{pct}, then improvement"
        else:
            w = f"Increasing cloudiness followed by rain or showers " \
                f"{when}{pct}"
    elif hi24:
        w = f"Fair at first, rain or showers {strength} " \
            f"{_daypart(local_hour, 24)}{pct}"
    elif best >= T_POSSIBLE:
        lead = 6 if (p6 or 0) >= T_POSSIBLE else \
            12 if (p12 or 0) >= T_POSSIBLE else 24
        when = "soon" if lead == 6 else _daypart(local_hour, lead)
        w = f"Unsettled; rain or showers possible {when}{pct}"
    elif best <= T_UNLIKELY:
        if trend_hpa_3h is not None and trend_hpa_3h >= RISING_TREND:
            w = "Fair and improving"
        else:
            w = "Fair"
    else:
        w = "Mainly fair; an isolated shower cannot be ruled out"

    if pfall_12h is not None and pfall_12h >= 0.6 and best > T_UNLIKELY:
        w += "; barometer still falling"
    return w, best


def wind_clause(current_sector16: int | None,
                band_probs_12h: list[float] | None,
                dir_probs_12h: list[float] | None,
                windup_12h: float | None) -> str | None:
    """Sager-style '{Direction} winds, {band}' from current direction +
    predicted relative shift + band distribution. Falls back to the plain
    windup wording when the wind heads are unavailable."""
    if band_probs_12h is None or dir_probs_12h is None:
        if windup_12h is None:
            return None
        if windup_12h >= 0.70:
            return "Wind increasing markedly"
        if windup_12h >= 0.50:
            return "Wind freshening"
        return None

    # direction phrase
    top_d = max(range(len(dir_probs_12h)), key=lambda i: dir_probs_12h[i])
    p_d = dir_probs_12h[top_d]
    if current_sector16 is None:
        dir_txt = "Winds"
    else:
        cur8 = int(current_sector16) // 2
        if top_d == 5 and p_d >= T_DIR_CONF:
            dir_txt = "Light and variable winds"
        elif top_d in (1, 2) and p_d >= T_DIR_CONF:      # veer
            step = 1 if top_d == 1 else 2
            dir_txt = f"{SECTOR8[cur8]} or {SECTOR8[(cur8 + step) % 8]} winds"
        elif top_d in (3, 4) and p_d >= T_DIR_CONF:      # back
            step = 1 if top_d == 3 else 2
            dir_txt = f"{SECTOR8[cur8]} or {SECTOR8[(cur8 - step) % 8]} winds"
        else:
            dir_txt = f"{SECTOR8[cur8]} winds"

    # band phrase (most likely band; explicit gale risk when material)
    top_b = max(range(5), key=lambda i: band_probs_12h[i])
    p_gale = band_probs_12h[4]
    p_strong_plus = band_probs_12h[3] + band_probs_12h[4]
    band_txt = BAND_TEXT[top_b]
    if p_gale >= T_GALE_RISK and top_b < 4:
        band_txt += f"; gale risk ({round(p_gale * 100)}%)"
    elif p_strong_plus >= T_STRONG_POSSIBLE and top_b < 3:
        band_txt += f", possibly {BAND_TEXT[3]}"
    return f"{dir_txt}, {band_txt}"


def verbalize(probs: dict[str, float | None], local_hour: int = 12,
              trend_hpa_3h: float | None = None,
              band_probs_12h: list[float] | None = None,
              dir_probs_12h: list[float] | None = None,
              current_sector16: int | None = None) -> str:
    """probs keys: precip_6h/12h/24h, windup_12h, pfall_12h (others
    tolerated). Wind-head arguments optional — degrades to windup wording."""
    def g(k):
        v = probs.get(k)
        return None if v is None else float(v)

    weather, headline = weather_narrative(
        g("precip_6h"), g("precip_12h"), g("precip_24h"),
        local_hour, trend_hpa_3h, g("pfall_12h"))
    if weather.startswith("No forecast"):
        return "No forecast: insufficient data."

    wind = wind_clause(current_sector16, band_probs_12h, dir_probs_12h,
                       g("windup_12h"))
    parts = [f"Forecast for the next 12-24 hours: {weather}."]
    if wind:
        parts.append(f"{wind}.")
    parts.append(_confidence(headline))
    return " ".join(parts)


# ordinal wording strength for the monotonicity property test
WORDING_RANK = ["Fair and improving", "Fair",
                "Mainly fair", "Unsettled", "Fair at first",
                "Increasing cloudiness", "Rain or showers"]


def wording_rank(text: str) -> int:
    body = text.split("Forecast for the next 12-24 hours: ", 1)[-1]
    for i, w in reversed(list(enumerate(WORDING_RANK))):
        if body.startswith(w):
            return i
    return -1
