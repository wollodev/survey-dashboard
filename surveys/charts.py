"""Charts with matplotlib, as PNG bytes for the PDF report."""

import io
from datetime import date

from matplotlib.figure import Figure

ACCENT = "#2f6db5"
MUTED = "#6b6b66"


def _to_png(fig: Figure) -> bytes:
    """Renders the figure into memory instead of a file."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
    return buffer.getvalue()


def _style(ax) -> None:
    """Plain style: no top/right spines, grey labels."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_facecolor("white")
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)


def brand_share_chart(brands: list[dict]) -> bytes:
    """Horizontal bars: share of responses per brand."""
    fig = Figure(figsize=(7, 3), facecolor="white")
    ax = fig.subplots()
    _style(ax)
    if not brands:
        return _to_png(fig)

    names = [b["brand"] for b in brands][::-1]  # largest brand on top
    shares = [b["share"] for b in brands][::-1]

    bars = ax.barh(names, shares, color=ACCENT)
    ax.bar_label(bars, labels=[f"{s:.1f} %" for s in shares], padding=4, fontsize=9, color=MUTED)
    ax.set_xlabel("Share of responses in %", fontsize=9, color=MUTED)
    ax.set_xlim(0, max(shares) * 1.2)
    return _to_png(fig)


def weekly_chart(weekly: list[dict]) -> bytes:
    """Line: responses per week."""
    weeks = [date.fromisoformat(w["week"]).strftime("%b %d") for w in weekly]  # "2026-03-02" -> "Mar 02"
    counts = [w["responses"] for w in weekly]

    fig = Figure(figsize=(7, 2.6), facecolor="white")
    ax = fig.subplots()
    ax.plot(weeks, counts, color=ACCENT, linewidth=2, marker="o", markersize=3)
    ax.set_ylabel("Responses", fontsize=9, color=MUTED)
    ax.set_ylim(bottom=0)
    ax.set_xticks(range(0, len(weeks), 4))  # label only every fourth week
    ax.grid(axis="y", color="#e3e2dd", linewidth=0.8)
    _style(ax)
    return _to_png(fig)
