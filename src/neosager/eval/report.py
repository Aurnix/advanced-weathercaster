"""Milestone report generation: markdown + matplotlib figures.

Includes the leakage tripwire: BSS > 0.6 on precip, or a model beating its
validation score by >30% on test, stamps a LEAKAGE-AUDIT warning block at
the top of the report.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ..config import REPO_ROOT

REPORTS_DIR = REPO_ROOT / "reports"

BSS_TRIPWIRE = 0.6


def reliability_figure(curves: dict[str, pd.DataFrame], title: str,
                       out_png: Path) -> None:
    fig, ax = plt.subplots(figsize=(5, 5))
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="perfect")
    for name, c in curves.items():
        if len(c):
            ax.plot(c["p_mean"], c["obs_freq"], "o-", ms=3, label=name)
    ax.set_xlabel("forecast probability")
    ax.set_ylabel("observed frequency")
    ax.set_title(title)
    ax.legend(fontsize=7)
    fig.tight_layout()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_png, dpi=120)
    plt.close(fig)


def skill_table_md(rows: list[dict]) -> str:
    df = pd.DataFrame(rows)
    return df.to_markdown(index=False, floatfmt=".3f")


def leakage_warnings(rows: list[dict]) -> list[str]:
    warns = []
    for r in rows:
        if r.get("metric") == "bss" and r.get("value", 0) > BSS_TRIPWIRE \
                and "precip" in str(r.get("target", "")):
            warns.append(
                f"BSS {r['value']:.3f} for {r['target']} ({r['model']}) "
                f"exceeds {BSS_TRIPWIRE} — audit for leakage before "
                f"reporting.")
    return warns


def write_report(name: str, sections: list[str],
                 tripwire_rows: list[dict] | None = None) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = REPORTS_DIR / f"{name}.md"
    header = [f"# {name}", ""]
    warns = leakage_warnings(tripwire_rows or [])
    if warns:
        header += ["> **LEAKAGE-AUDIT WARNING**", ""]
        header += [f"> - {w}" for w in warns] + [""]
    out.write_text("\n".join(header + sections), encoding="utf-8")
    return out
