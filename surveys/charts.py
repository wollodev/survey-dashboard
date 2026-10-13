"""Diagramme mit matplotlib, als PNG-Bytes für den PDF-Bericht."""

import io

from matplotlib.figure import Figure

ACCENT = "#2f6db5"
MUTED = "#6b6b66"


def _to_png(fig: Figure) -> bytes:
    """Zeichnet die Figure in den Speicher statt in eine Datei."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
    return buffer.getvalue()


def _style(ax) -> None:
    """Schlichter Stil: keine Rahmen oben/rechts, graue Beschriftung."""
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_facecolor("white")
    ax.spines["left"].set_color(MUTED)
    ax.spines["bottom"].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=9)


def brand_share_chart(brands: list[dict]) -> bytes:
    """Waagerechte Balken: Anteil der Antworten je Marke."""
    names = [b["brand"] for b in brands][::-1]  # größte Marke oben
    shares = [b["share"] for b in brands][::-1]

    fig = Figure(figsize=(7, 3), facecolor="white")
    ax = fig.subplots()
    bars = ax.barh(names, shares, color=ACCENT)
    ax.bar_label(bars, labels=[f"{s:.1f} %" for s in shares], padding=4, fontsize=9, color=MUTED)
    ax.set_xlabel("Anteil der Antworten in %", fontsize=9, color=MUTED)
    ax.set_xlim(0, max(shares) * 1.2)
    _style(ax)
    return _to_png(fig)


def weekly_chart(weekly: list[dict]) -> bytes:
    """Linie: Antworten pro Woche."""
    weeks = [f"{w['week'][8:10]}.{w['week'][5:7]}." for w in weekly]  # "2026-03-02" -> "02.03."
    counts = [w["responses"] for w in weekly]

    fig = Figure(figsize=(7, 2.6), facecolor="white")
    ax = fig.subplots()
    ax.plot(weeks, counts, color=ACCENT, linewidth=2, marker="o", markersize=3)
    ax.set_ylabel("Antworten", fontsize=9, color=MUTED)
    ax.set_ylim(bottom=0)
    ax.set_xticks(range(0, len(weeks), 4))  # nur jede vierte Woche beschriften
    ax.grid(axis="y", color="#e3e2dd", linewidth=0.8)
    _style(ax)
    return _to_png(fig)
