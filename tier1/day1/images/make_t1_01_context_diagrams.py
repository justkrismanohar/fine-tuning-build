"""Draw T1-01 context / attention diagrams. Author machine only. Not a classroom cell."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = Path(__file__).resolve().parent
NAVY = "#1B365D"
TEAL = "#1A7A6D"
GOLD = "#C4A35A"
GREY = "#E8EAED"
INK = "#1A1A1A"


def _setup(w=14.0, h=7.2):
    fig, ax = plt.subplots(figsize=(w, h), dpi=140)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 7.2)
    ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")
    return fig, ax


def _box(ax, x, y, w, h, text, fc=NAVY, ec=NAVY, tc="white", fs=11, weight="bold"):
    ax.add_patch(
        FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.04,rounding_size=0.12",
            linewidth=1.4,
            facecolor=fc,
            edgecolor=ec,
        )
    )
    ax.text(
        x + w / 2,
        y + h / 2,
        text,
        ha="center",
        va="center",
        color=tc,
        fontsize=fs,
        fontweight=weight,
        wrap=True,
    )


def _arrow(ax, x1, y1, x2, y2, color=TEAL):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1),
            (x2, y2),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=2.0,
            color=color,
        )
    )


def tokens_to_next_token() -> None:
    fig, ax = _setup(16.2, 5.8)
    ax.set_xlim(0, 16.2)
    ax.set_ylim(0, 5.8)
    ax.set_title("Your text to the next token", fontsize=20, fontweight="bold", color=INK, pad=8)
    steps = [
        (0.25, "your text"),
        (2.85, "tokenizer\n(text → token IDs)"),
        (5.45, "embedding\n(IDs → vectors)"),
        (8.05, "transformer\nblock × 16\nattention, then\nfeed-forward"),
        (10.85, "language-model\nhead\n(next-token scores)"),
        (13.65, "chosen token\nappended, repeat"),
    ]
    y, w, h = 1.55, 2.35, 2.55
    for i, (x, label) in enumerate(steps):
        fc = TEAL if i in (2, 3) else NAVY
        _box(ax, x, y, w, h, label, fc=fc, fs=10)
        if i < len(steps) - 1:
            _arrow(ax, x + w, y + h / 2, steps[i + 1][0], y + h / 2)
    ax.text(
        8.1,
        0.5,
        "Same words as the T1-02 architecture card. One token at a time.",
        ha="center",
        fontsize=12,
        color=INK,
    )
    fig.savefig(HERE / "t1_01_tokens_to_next_token.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def same_id_same_start() -> None:
    fig, ax = _setup(14, 7.0)
    ax.set_title('Same token ID, same starting row: " bank"', fontsize=20, fontweight="bold", color=INK)
    _box(ax, 0.4, 4.6, 6.3, 1.6, 'money:  … deposit … check …  " bank"  to', fc=NAVY, fs=12)
    _box(ax, 0.4, 2.5, 6.3, 1.6, 'river:  … fishing … rod … river  " bank"  to', fc=TEAL, fs=12)
    _box(ax, 8.3, 2.3, 5.2, 4.0, "embedding table\n\nrow 6201  ←  \" bank\"\n(same starting numbers)\n\nThe table does not know\nwhich bank you mean.", fc=GREY, ec=NAVY, tc=INK, fs=12)
    _arrow(ax, 6.7, 5.4, 8.3, 4.7, GOLD)
    _arrow(ax, 6.7, 3.3, 8.3, 4.0, GOLD)
    ax.text(7.5, 0.55, "Illustration of a lookup, not a measured embedding.", ha="center", fontsize=12, color=INK)
    fig.savefig(HERE / "t1_01_same_id_same_start.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def attention_spotlights() -> None:
    fig, ax = _setup(14, 7.2)
    ax.set_title("Attention as spotlights over the words so far", fontsize=20, fontweight="bold", color=INK)

    def sentence(y, words, beams, title, fc):
        ax.text(0.5, y + 1.55, title, fontsize=13, fontweight="bold", color=fc)
        xs = []
        for i, w in enumerate(words):
            x = 0.4 + i * 1.55
            xs.append(x + 0.65)
            highlight = w in {"bank", "to"}
            _box(
                ax,
                x,
                y,
                1.4,
                0.85,
                w,
                fc=GOLD if highlight else NAVY,
                ec=NAVY,
                tc=INK if highlight else "white",
                fs=11,
            )
        src = xs[-1]
        for i in beams:
            ax.annotate(
                "",
                xy=(xs[i], y + 0.9),
                xytext=(src, y + 0.05),
                arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=2.0, connectionstyle="arc3,rad=0.25"),
            )

    sentence(
        4.7,
        ["I", "deposit", "check", "going", "bank", "to"],
        [1, 2],
        "Money sentence — light can land on deposit and check",
        NAVY,
    )
    sentence(
        1.7,
        ["I", "fishing", "rod", "river", "bank", "to"],
        [1, 2, 3],
        "River sentence — light can land on fishing, rod and river",
        TEAL,
    )
    ax.text(
        7,
        0.45,
        "Illustration. Not a measured attention map.",
        ha="center",
        fontsize=14,
        fontweight="bold",
        color=INK,
    )
    fig.savefig(HERE / "t1_01_attention_spotlights.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def input_vs_weights() -> None:
    fig, ax = _setup(14, 6.4)
    ax.set_ylim(0, 6.4)
    ax.set_title("Two levers", fontsize=20, fontweight="bold", color=INK)
    _box(
        ax,
        0.5,
        1.5,
        6.2,
        3.8,
        "Today: change the input\n\nsystem text  +  user text\n\nWeights stay frozen.\nUsed in this notebook.",
        fc=TEAL,
        fs=14,
    )
    _box(
        ax,
        7.3,
        1.5,
        6.2,
        3.8,
        "Later: change the weights\n\ntraining, or a small adapter\n\nDay 3. Not today.",
        fc=NAVY,
        fs=14,
    )
    ax.text(3.6, 0.55, "Instructions steer. They do not retrain.", ha="center", fontsize=12, color=INK)
    ax.text(10.4, 0.55, "Whether an adapter helps is measured.", ha="center", fontsize=12, color=INK)
    fig.savefig(HERE / "t1_01_input_vs_weights.png", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    tokens_to_next_token()
    same_id_same_start()
    attention_spotlights()
    input_vs_weights()
    for name in (
        "t1_01_tokens_to_next_token.png",
        "t1_01_same_id_same_start.png",
        "t1_01_attention_spotlights.png",
        "t1_01_input_vs_weights.png",
    ):
        print("wrote", HERE / name)


if __name__ == "__main__":
    main()
