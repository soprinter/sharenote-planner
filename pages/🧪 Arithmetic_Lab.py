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
from typing import Dict, Optional, Tuple

import streamlit as st


st.set_page_config(page_title="Arithmetic Lab", page_icon="🧪", layout="centered")

from sharenotelib import (
    combine_notes_serial,
    divide_notes,
    ensure_note,
    expected_hashes_for_note,
    format_zbits_label,
    human_hashrate,
    note_difference,
    note_from_zbits,
    nbits_to_sharenote,
    probability_per_hash,
    scale_note,
    sharenote_to_nbits,
)

MAX_ZEROS = 256



def _summarize_note(note) -> Dict[str, object]:
    hashes = expected_hashes_for_note(note).value
    probability = probability_per_hash(note)
    return {
        "label": note.label,
        "zbits": note.zbits,
        "difficulty": hashes,
        "difficulty_display": human_hashrate(hashes).display,
        "probability": probability,
        "probability_display": f"{probability:.4g} success/hash",
    }


def _resolve(note_str: str) -> Tuple[Optional[object], Optional[Dict[str, object]], str]:
    trimmed = note_str.strip()
    if not trimmed:
        return None, None, "enter a Sharenote label (format: xxZyy)"
    try:
        note = ensure_note(trimmed)
    except Exception as exc:
        return None, None, str(exc)
    return note, _summarize_note(note), "ok"


def _note_panel(col, title: str, default: str) -> Tuple[Optional[object], Optional[Dict[str, object]]]:
    col.subheader(title)
    note_input = col.text_input("Label", value=default, key=f"label_{title}")
    description = col.empty()
    note, stats, status = _resolve(note_input)
    if note and stats:
        col.metric("ZBits", f"{stats['zbits']:.3f}")
        col.metric("Hashrate", f"{stats['difficulty_display']}")
    else:
        description.error(status)
    return note, stats


def _format_difficulty_display(stats: Dict[str, object]) -> str:
    return f"{format_zbits_label(stats['zbits'], 3)} → {stats['difficulty_display']}"


def _maybe_note_from_zbits(zbits_value: float) -> Optional[object]:
    try:
        return note_from_zbits(zbits_value)
    except Exception:
        return None


def main() -> None:
    st.title("Sharenote Arithmetic")


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
        ratio_zbits = divide_notes(note_a, note_b)
        ratio_note = _maybe_note_from_zbits(ratio_zbits)
        ratio_label = ratio_note.label if ratio_note else f"{ratio_zbits:.3f} zbits"
        ratio_delta = (
            _format_difficulty_display(_summarize_note(ratio_note)) if ratio_note else "failed to convert to note"
        )

        combine_cols[0].metric(
            label="Addition",
            value=f"A + B = {combined.label}",
            delta=_format_difficulty_display(_summarize_note(combined)),
        )
        combine_cols[1].metric(
            label="Subtraction",
            value=f"A − B = {diff_ab.label}",
            delta=_format_difficulty_display(_summarize_note(diff_ab)),
        )
        combine_cols[2].metric(
            label="Division",
            value=f"A / B = {ratio_label}",
            delta=ratio_delta,
        )


    else:
        for col in combine_cols:
            col.info("Awaiting two valid notes to compare.")

    # Scale & ratio
    st.divider()
    st.markdown("### Scaling")
    scale_cols = st.columns(2)
    factor_a = st.slider("A scale factor", 0.25, 5.0, 1.0, step=0.05)
    factor_b = st.slider("B scale factor", 0.25, 5.0, 1.0, step=0.05)

    if note_a and stats_a:
        scaled_a = scale_note(note_a, factor_a)
        scale_cols[0].metric(
            label="Scaled A",
            value=f"A * {factor_a} = {scaled_a.label}",
            delta=_format_difficulty_display(_summarize_note(scaled_a)),
        )
    else:
        scale_cols[0].info("Enter a valid Note A to scale it.")

    if note_b and stats_b:
        scaled_b = scale_note(note_b, factor_b)
        scale_cols[1].metric(
            label="Scaled B",
            value=f"B * {factor_b} = {scaled_b.label}",
            delta=_format_difficulty_display(_summarize_note(scaled_b)),
        )
    else:
        scale_cols[1].info("Enter a valid Note B to scale it.")

 

    # Format conversions
    st.divider()
    st.markdown("### Format conversions")
    format_cols = st.columns(2)
    with format_cols[0]:
        nbits_input = st.text_input("nBits (8 hex)", value="1a2b3c4d")
        if nbits_input:
            try:
                converted = nbits_to_sharenote(nbits_input)
                converted_stats = _summarize_note(converted)
                st.success(f"{_format_difficulty_display(converted_stats)}")
            except Exception as exc:
                st.error(f"nBits parse failed: {exc}")

    with format_cols[1]:
        zbits_input = st.number_input(
            "ZBits", min_value=0.0, max_value=MAX_ZEROS + 1.0, value=32.0, step=0.25
        )
        try:
            note_from_z = note_from_zbits(zbits_input)
            st.success(f"{note_from_z.label} → {sharenote_to_nbits(note_from_z)}")
        except Exception as exc:
            st.error(f"ZBits conversion failed: {exc}")




if __name__ == "__main__":
    main()
