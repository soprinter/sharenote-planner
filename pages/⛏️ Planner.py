"""
Sharenote planning page for hashrate ↔ note conversions.
--------------------------------------------------------

Hosts the planner UI that used to live in the main `app.py`.  This page keeps
the same tabs (Hashrate → Print and Target Sharenote → Required Hashrate)
while relying on `sharenotelib` helpers for calculations.
"""

from __future__ import annotations

from typing import List, Tuple

import streamlit as st
import local_sharenotelib  # noqa: F401 - ensures local sharenotelib is importable

st.set_page_config(page_title="Print Planner", page_icon="⛏️", layout="centered")

from sharenotelib import (
    ReliabilityLevel,
    Sharenote,
    SharenoteError,
    hashrate_range_for_note,
    get_reliability_levels,
    human_hashrate,
    note_from_components,
    note_from_hashrate,
)

DEFAULT_TARGET_SECS = 5  # default SLA window
MIN_ZEROS = 1
MAX_ZEROS = 256

UNIT_FACTORS = {
    "H/s": 1.0,
    "kH/s": 1e3,
    "MH/s": 1e6,
    "GH/s": 1e9,
    "TH/s": 1e12,
    "PH/s": 1e15,
    "EH/s": 1e18,
    "ZH/s": 1e21,
    "YH/s": 1e24,
}


def _format_range_label(range_) -> str:
    low, high = range_.human()
    return f"{low.display} – {high.display}"


def _load_reliability_levels() -> List[ReliabilityLevel]:
    levels = list(get_reliability_levels())
    if not levels:
        raise RuntimeError("sharenotelib did not expose any reliability levels")
    return levels


RELIABILITY_LEVELS = _load_reliability_levels()
RELIABILITY_LABELS = [level.label for level in RELIABILITY_LEVELS]
LABEL_TO_LEVEL = {level.label: level for level in RELIABILITY_LEVELS}
DEFAULT_LEVEL_INDEX = max(0, min(0, len(RELIABILITY_LABELS) - 1))


def _note_label_or_dash(note: Sharenote | None) -> str:
    if note is None or note.z < MIN_ZEROS:
        return "—"
    return note.label


def _compute_best_note(hps: float, seconds: int, level: ReliabilityLevel) -> Tuple[Sharenote | None, str | None]:
    if hps <= 0:
        return None, "Enter a hashrate greater than 0 to see what you can print."
    try:
        return note_from_hashrate(hps, seconds, reliability=level.id), None
    except SharenoteError as exc:
        return None, str(exc)


def _build_reliability_table(hps: float, seconds: int) -> List[Tuple[str, str]]:
    rows: List[Tuple[str, str]] = []
    for level in RELIABILITY_LEVELS:
        if hps <= 0:
            label = "—"
        else:
            try:
                note = note_from_hashrate(hps, seconds, reliability=level.id)
            except SharenoteError:
                label = "—"
            else:
                label = _note_label_or_dash(note)
        rows.append((level.label, label))
    return rows


def main() -> None:
    with st.sidebar:
        st.header("Confidence level")
        level_name = st.radio(
            "Service reliability",
            options=RELIABILITY_LABELS,
            index=DEFAULT_LEVEL_INDEX,
            help="""
- **On average**: expected once per selected window (no guarantee).
- **Usually (90%)**: ~90% chance to get ≥1 in the window.
- **Often (95%)**: ~95% chance in the window.
- **Very likely (99%)**: ~99% chance in the window.
- **Almost certain (99.9%)**: ~99.9% chance in the window.
""".strip(),
        )
        selected_level = LABEL_TO_LEVEL.get(level_name, RELIABILITY_LEVELS[0])
        t_secs = st.number_input("Target window (seconds)", min_value=1, value=DEFAULT_TARGET_SECS, step=1)

    st.title("Print Planner")
    st.caption("Bridge your hardware speed to the right Sharenote label in plain language.")


    tab1, tab2 = st.tabs(["Hashrate → Print Sharenote", "Target Sharenote → Required hashrate"])

    with tab1:
        st.subheader(f"Given my hashrate, what’s the biggest Sharenote I can print every {t_secs:g} s?")
        cols = st.columns(2)
        with cols[0]:
            h_value = st.number_input("Enter your hashrate", min_value=0.0, value=1000.0, step=1.0)
        with cols[1]:
            unit = st.selectbox("Unit", list(UNIT_FACTORS.keys()), index=2)  # default MH/s

        user_hps = h_value * UNIT_FACTORS[unit]
        best_note, best_note_error = _compute_best_note(user_hps, t_secs, selected_level)

        st.markdown("### Result")
        if best_note_error:
            st.error(best_note_error)
        elif best_note is None or best_note.z < MIN_ZEROS:
            st.error(
                f"Your hashrate is too low to reliably print even 0Z00 at this confidence within {t_secs:g} s. Try a lower confidence level or increase hashrate."
            )
        else:
            st.success(
                f"At **{human_hashrate(user_hps).display}** and **{selected_level.label}** reliability, you can print **{best_note.label}** every ~{t_secs:g} s."
            )

        rel_rows = _build_reliability_table(user_hps, t_secs)
        st.markdown("#### What if I change reliability?")
        st.table(
            {
                "Reliability": [row[0] for row in rel_rows],
                "Max Sharenote": [row[1] for row in rel_rows],
            }
        )

    with tab2:
        st.subheader(f"Given a Sharenote, how much hashrate do I need to print every {t_secs:g} s?")
        note_cols = st.columns(2)
        with note_cols[0]:
            zeros = st.number_input(
                "Sharenote (Z unit):", min_value=MIN_ZEROS, max_value=MAX_ZEROS, value=32, step=1, help="Integer number of leading zeros (Z)."
            )
        with note_cols[1]:
            cents = st.number_input(
                "Cents (0–99):", min_value=0, max_value=99, value=0, step=1, help="Fractional part of the note: 0 means .00, 50 means .50, etc."
            )

        target_note = note_from_components(int(zeros), int(cents))
        label = target_note.label

        st.markdown(f"### Required hashrate for **{label}**")
        mean_range = hashrate_range_for_note(target_note, t_secs, multiplier=1.0)
        selected_range = hashrate_range_for_note(target_note, t_secs, reliability=selected_level.id)

        mcol1, mcol2 = st.columns(2)
        with mcol1:
            st.metric(label="Mean (on average)", value=_format_range_label(mean_range))
        with mcol2:
            st.metric(label=f"{selected_level.label}", value=_format_range_label(selected_range))

        st.markdown("#### All reliability levels")
        table = {"Reliability": [], "Required H/s Range": []}
        for level in RELIABILITY_LEVELS:
            rng = hashrate_range_for_note(target_note, t_secs, reliability=level.id)
            table["Reliability"].append(level.label)
            table["Required H/s Range"].append(_format_range_label(rng))
        st.table(table)


if __name__ == "__main__":
    main()
