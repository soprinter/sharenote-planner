"""
Arithmetic playground page powered by sharenotelib.
----------------------------------------------------

This page showcases the arithmetic operations that underlie the planner: combine,
subtract, scale, divide, and convert between labels, zbits, and nBits.  It is
designed for crunching numbers with a readable UI and useful annotations.
"""

from __future__ import annotations

import ast
import html
import operator
from typing import Dict, Optional, Tuple, List

import streamlit as st


st.set_page_config(page_title="Arithmetic Lab", page_icon="🧪", layout="centered")

from sharenotelib import (
    CENT_ZBIT_STEP,
    MAX_CENTZ,
    MIN_CENTZ,
    ReliabilityLevel,
    combine_notes_serial,
    divide_notes,
    ensure_note,
    format_zbits_label,
    get_reliability_levels,
    human_hashrate,
    note_difference,
    note_from_zbits,
    nbits_to_sharenote,
    required_hashrate,
    scale_note,
    sharenote_to_nbits,
    SharenoteError,
)

MIN_ZEROS = 1
MAX_ZEROS = 256
MIN_ZBITS = MIN_ZEROS + MIN_CENTZ * CENT_ZBIT_STEP
MAX_ZBITS = MAX_ZEROS + MAX_CENTZ * CENT_ZBIT_STEP

DEFAULT_TARGET_SECS = 5

_LAB_SECONDS = DEFAULT_TARGET_SECS
_LAB_RELIABILITY: ReliabilityLevel | None = None


def _load_reliability_levels() -> list[ReliabilityLevel]:
    levels = list(get_reliability_levels())
    if not levels:
        raise RuntimeError("sharenotelib did not expose any reliability levels")
    return levels


RELIABILITY_LEVELS = _load_reliability_levels()
RELIABILITY_LABELS = [level.label for level in RELIABILITY_LEVELS]
LABEL_TO_LEVEL = {level.label: level for level in RELIABILITY_LEVELS}
DEFAULT_LEVEL_INDEX = 0


def _lab_seconds() -> int:
    return max(1, int(_LAB_SECONDS or DEFAULT_TARGET_SECS))


def _lab_reliability() -> ReliabilityLevel:
    return _LAB_RELIABILITY or RELIABILITY_LEVELS[0]



def _summarize_note(note) -> Dict[str, object]:
    seconds = _lab_seconds()
    level = _lab_reliability()
    selected_hashrate = required_hashrate(note, seconds, reliability=level.id).value
    return {
        "label": note.label,
        "zbits": note.zbits,
        "seconds": seconds,
        "selected_label": level.label,
        "hashrate_value": selected_hashrate,
        "hashrate_display": human_hashrate(selected_hashrate).display,
    }


def _resolve(note_str: str) -> Tuple[Optional[object], Optional[Dict[str, object]], str]:
    trimmed = note_str.strip()
    if not trimmed:
        return None, None, "enter a Sharenote label (format: xxZyy)"
    try:
        note = ensure_note(trimmed)
        if not _note_within_lab_limits(note):
            return None, None, f"Z must stay between {MIN_ZEROS} and {MAX_ZEROS} (CZ 0–{MAX_CENTZ}) for this lab."
    except Exception as exc:
        return None, None, str(exc)
    return note, _summarize_note(note), "ok"


def _note_panel(col, title: str, default: str) -> Tuple[Optional[object], Optional[Dict[str, object]]]:
    col.subheader(title)
    note_input = col.text_input(
        "Label",
        value=default,
        key=f"label_{title}",
        help=f"Sharenote label (xxZyy) with Z between {MIN_ZEROS} and {MAX_ZEROS} and CZ between {MIN_CENTZ} and {MAX_CENTZ}.",
    )
    description = col.empty()
    note, stats, status = _resolve(note_input)
    if note and stats:
        col.metric("ZBits", f"{stats['zbits']:.2f}")
        col.metric("Hashrate", f"{stats['hashrate_display']}")
    else:
        description.error(status)
    return note, stats


def _note_within_lab_limits(note) -> bool:
    return MIN_ZEROS <= note.z <= MAX_ZEROS


def _render_note_metric(
    col,
    label: str,
    note,
    value_builder,
) -> None:
    if not note:
        col.info(f"{label} result awaits a valid Sharenote.")
        return

    if not _note_within_lab_limits(note):
        if note.z < MIN_ZEROS:
            boundary_msg = f"is below the lab minimum of {MIN_ZEROS}Z (got {note.label})."
        elif note.z > MAX_ZEROS:
            boundary_msg = f"exceeds the lab maximum of {MAX_ZEROS}Z (got {note.label})."
        else:
            boundary_msg = "is not supported in this lab."
        col.info(f"{label} result {boundary_msg}")
        return
    stats = _summarize_note(note)
    col.metric(label=label, value=value_builder(note), delta=_format_difficulty_display(stats))


def _format_difficulty_display(stats: Dict[str, object]) -> str:
    return (
        f"{format_zbits_label(stats['zbits'], 2)} → {stats['hashrate_display']}"
    )


def _maybe_note_from_zbits(zbits_value: float) -> Optional[object]:
    try:
        if zbits_value < 0:
            return None
        return note_from_zbits(zbits_value)
    except Exception:
        return None


def main() -> None:
    global _LAB_SECONDS, _LAB_RELIABILITY

    st.title("Sharenote Arithmetic")
    st.caption("Think of this lab as a note calculator: drop two labels in, then try combinations, scaling, or format swaps to see how the math responds.")

    with st.sidebar:
        st.header("Lab conditions")
        level_name = st.radio(
            "Reliability",
            options=RELIABILITY_LABELS,
            index=DEFAULT_LEVEL_INDEX,
        )
        selected_level = LABEL_TO_LEVEL.get(level_name, RELIABILITY_LEVELS[0])
        t_secs = st.number_input(
            "Target window (seconds)",
            min_value=1,
            value=DEFAULT_TARGET_SECS,
            step=1,
        )
    _LAB_RELIABILITY = selected_level
    _LAB_SECONDS = t_secs


    # Note inputs + summaries
    note_cols = st.columns(2)
    note_a, stats_a = _note_panel(note_cols[0], "Sharenote A", "32Z00")
    note_b, stats_b = _note_panel(note_cols[1], "Sharenote B", "31Z50")
    
    st.divider()
    st.markdown("### Arithmetic operations")
    combine_cols = st.columns(3)
    if note_a and note_b and stats_a and stats_b:
        combined = combine_notes_serial((note_a, note_b))
        diff_ab = note_difference(note_a, note_b)
        ratio_value = "A / B not possible"
        ratio_delta = "awaiting safe operands"
        try:
            ratio_zbits = divide_notes(note_a, note_b)
            ratio_note = _maybe_note_from_zbits(ratio_zbits)
            if ratio_note:
                ratio_value = f"A / B = {ratio_note.label}"
                ratio_delta = _format_difficulty_display(_summarize_note(ratio_note))
            else:
                ratio_delta = "failed to convert to note"
        except Exception as exc:
            ratio_value = "A / B not possible"
            ratio_delta = f"division error: {exc}"

        _render_note_metric(
            combine_cols[0], "Addition", combined, lambda note: f"A + B = {note.label}"
        )
        _render_note_metric(
            combine_cols[1], "Subtraction", diff_ab, lambda note: f"A − B = {note.label}"
        )
        combine_cols[2].metric(
            label="Division",
            value=ratio_value,
            delta=ratio_delta,
        )


    else:
        for col in combine_cols:
            col.info("Awaiting two valid notes to compare.")

    # Scale & ratio
    st.divider()
    st.markdown("### Scaling")
    scale_cols = st.columns(2)
    factor_a = st.slider("A scale factor", 0.25, 50.0, 1.0, step=0.05)
    factor_b = st.slider("B scale factor", 0.25, 50.0, 1.0, step=0.05)

    if note_a and stats_a:
        scaled_a = scale_note(note_a, factor_a)
        _render_note_metric(
            scale_cols[0],
            "Scaled A",
            scaled_a,
            lambda note: f"A * {factor_a:g} = {note.label}",
        )
    else:
        scale_cols[0].info("Enter a valid Note A to scale it.")

    if note_b and stats_b:
        scaled_b = scale_note(note_b, factor_b)
        _render_note_metric(
            scale_cols[1],
            "Scaled B",
            scaled_b,
            lambda note: f"B * {factor_b:g} = {note.label}",
        )
    else:
        scale_cols[1].info("Enter a valid Note B to scale it.")

    # Division by scalar (per-number division experience)
    st.divider()
    st.markdown("### Division by a scalar")
    div_cols = st.columns(2)
    divisor_a = st.slider("A division factor", 0.25, 50.0, 2.0, step=0.25)
    divisor_b = st.slider("B division factor", 0.25, 50.0, 2.0, step=0.25)

    if note_a and stats_a:
        try:
            divided_a = scale_note(note_a, 1.0 / divisor_a)
        except SharenoteError as exc:
            div_cols[0].error(f"Division failed: {exc}")
        else:
            _render_note_metric(
                div_cols[0],
                "A ÷ factor",
                divided_a,
                lambda note: f"A ÷ {divisor_a:g} = {note.label}",
            )
    else:
        div_cols[0].info("Enter a valid Note A to divide it.")

    if note_b and stats_b:
        try:
            divided_b = scale_note(note_b, 1.0 / divisor_b)
        except SharenoteError as exc:
            div_cols[1].error(f"Division failed: {exc}")
        else:
            _render_note_metric(
                div_cols[1],
                "B ÷ factor",
                divided_b,
                lambda note: f"B ÷ {divisor_b:g} = {note.label}",
            )
    else:
        div_cols[1].info("Enter a valid Note B to divide it.")

 

    # Format conversions
    st.divider()
    st.markdown("### Format conversions")
    format_cols = st.columns(2)
    with format_cols[0]:
        nbits_input = st.text_input("nBits (8 hex)", value="1a2b3c4d")
        if nbits_input:
            try:
                converted = nbits_to_sharenote(nbits_input)
            except Exception as exc:
                st.error(f"nBits parse failed: {exc}")
            else:
                if _note_within_lab_limits(converted):
                    converted_stats = _summarize_note(converted)
                    st.success(f"{converted.label} → {converted_stats['hashrate_display']}")
                else:
                    st.error(
                        f"nBits result {converted.label} exceeds the lab cap of {MAX_ZEROS}Z{MAX_CENTZ:02d}."
                    )

    with format_cols[1]:
        sharenote_input = st.text_input(
            "Sharenote label",
            value="32Z00",
            help=f"Enter a label between {MIN_ZEROS}Z00 and {MAX_ZEROS}Z{MAX_CENTZ:02d}.",
        )
        if sharenote_input:
            note_from_label, stats_from_label, status = _resolve(sharenote_input)
            if note_from_label and stats_from_label:
                st.success(
                    f"{note_from_label.label} → {sharenote_to_nbits(note_from_label)} ({stats_from_label['hashrate_display']})"
                )
            else:
                st.error(status)




if __name__ == "__main__":
    main()
