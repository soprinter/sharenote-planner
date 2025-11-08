"""
Streamlit app for planning Sharenote printing including fractional “cents”
-----------------------------------------------------------------------

This application lets miners explore what size of Sharenote they can mint
within a target window, and conversely what hashrate is required to mint
a desired Sharenote.  A Sharenote is identified by an integer number of
leading zeros (Z) and an optional two‑digit “cents” suffix that
represents an additional fractional difficulty.  In this model one cent
represents 0.01 of a zero, so a note labelled ``33Z54`` requires
\(33 + 0.54\) zeros of work on average.  Required hashrate grows
exponentially with zeros: \(H = k · 2^{zeros} / t\), where ``k`` is a
reliability multiplier derived from the chosen confidence level and
``t`` is the target window in seconds.

The app provides two tabs:
  • **Hashrate → Print Sharenote:** enter your hashrate and choose a
    reliability level to see the biggest note (Z and cents) you can
    reliably mint every ``t`` seconds.  A summary table shows how
    changing reliability affects the maximum note.
  • **Target Sharenote → Required hashrate:** specify the desired
    note as an integer Z plus a cents value (0–99) and see how much
    hashrate is needed at different reliability levels.

The reliability levels map to different ``k`` multipliers:

  - *On average*: k=1.0 (mean case)
  - *Usually* (90 %): k=−ln(1−0.90)
  - *Often* (95 %): k=−ln(1−0.95)
  - *Very likely* (99 %): k=−ln(1−0.99)
  - *Almost certain* (99.9 %): k=−ln(1−0.999)

"""

import streamlit as st

from sharenotelib import (
    Sharenote,
    SharenoteError,
    get_reliability_levels,
    human_hashrate,
    note_from_components,
    note_from_hashrate,
    required_hashrate,
    required_hashrate_mean,
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

RELIABILITY_LEVELS = list(get_reliability_levels())
RELIABILITY_LABELS = [level.label for level in RELIABILITY_LEVELS]
LABEL_TO_LEVEL = {level.label: level for level in RELIABILITY_LEVELS}
DEFAULT_LEVEL_INDEX = 0 # max(0, min(2, len(RELIABILITY_LABELS) - 1))

if not RELIABILITY_LEVELS:
    raise RuntimeError("sharenotelib did not expose any reliability levels")


def _note_label_or_dash(note: Sharenote | None) -> str:
    if note is None or note.z < MIN_ZEROS:
        return "—"
    return note.label


# Streamlit page setup
st.set_page_config(page_title="Sharenote Print Planner", page_icon="⛏️", layout="centered")
st.title("Sharenote Print Planner")

# Sidebar: choose reliability level and target window
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

st.caption(
    f"Miner-focused helper: pick a reliability target, then match hashrate to the Sharenote you want to print every {t_secs:g} seconds."
)

# Tabs for forward and inverse calculations
tab1, tab2 = st.tabs(["Hashrate → Print Sharenote", "Target Sharenote → Required hashrate"])

with tab1:
    st.subheader(f"Given my hashrate, what’s the biggest Sharenote I can print every {t_secs:g} s?")
    cols = st.columns(2)
    with cols[0]:
        h_value = st.number_input("Enter your hashrate", min_value=0.0, value=1000.0, step=1.0)
    with cols[1]:
        unit = st.selectbox("Unit", list(UNIT_FACTORS.keys()), index=2)  # default MH/s

    user_hps = h_value * UNIT_FACTORS[unit]
    best_note: Sharenote | None = None
    best_note_error: str | None = None
    table_rows: list[tuple[str, str]] = []

    if user_hps > 0:
        try:
            best_note = note_from_hashrate(user_hps, t_secs, reliability=selected_level.id)
        except SharenoteError as exc:
            best_note_error = str(exc)
    else:
        best_note_error = "Enter a hashrate greater than 0 to see what you can print."

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

    for level in RELIABILITY_LEVELS:
        if user_hps > 0:
            try:
                note = note_from_hashrate(user_hps, t_secs, reliability=level.id)
            except SharenoteError:
                label = "—"
            else:
                label = _note_label_or_dash(note)
        else:
            label = "—"
        table_rows.append((level.label, label))

    st.markdown("#### What if I change reliability?")
    st.table(
        {
            "Reliability": [row[0] for row in table_rows],
            "Max Sharenote": [row[1] for row in table_rows],
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
    req_mean = required_hashrate_mean(target_note, t_secs)
    req_chosen = required_hashrate(target_note, t_secs, reliability=selected_level.id)

    mcol1, mcol2 = st.columns(2)
    with mcol1:
        st.metric(label="Mean (on average)", value=human_hashrate(req_mean.value).display)
    with mcol2:
        st.metric(label=f"{selected_level.label}", value=human_hashrate(req_chosen.value).display)

    st.markdown("#### All reliability levels")
    table = {"Reliability": [], "Required H/s": []}
    for level in RELIABILITY_LEVELS:
        measurement = required_hashrate(target_note, t_secs, reliability=level.id)
        table["Reliability"].append(level.label)
        table["Required H/s"].append(measurement.human().display)
    st.table(table)

st.divider()
st.caption(
    f"Stay in your target window and print the Sharenote you need, every {t_secs:g} seconds."
)
