"""
Landing page for the Sharenote planning suite.
-----------------------------------------------

Describes the planner and the arithmetic playground that live in the project's
multi-page layout.
"""

import streamlit as st

st.set_page_config(page_title="Sharenote Welcome Hub", page_icon="🧮", layout="centered")

st.markdown("<div align='center'><img src='https://sharenote.xyz/optimized/pcb-w640.avif' width='360' style='max-width:100%;height:auto'></div>", unsafe_allow_html=True)
st.markdown(
    """
<style>
.hero-container {
    text-align:center;
    margin: 12px auto 32px;
    font-family: "IBM Plex Sans", "Inter", system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.hero-line {
    display:block;
    font-size:42px;
    font-weight:700;
    color:#0b3d2c;
    letter-spacing:2px;
}
.hero-line-small {
    font-size:18px;
    color:#4b5b68;
    margin-top:8px;
}
.hero-line-dynamic {
    display:flex;
    justify-content:center;
    align-items:flex-end;
    gap:12px;
}
.hero-word {
    display:inline-block;
    position:relative;
    width: 150px;
    height: 1.6em;
}
.hero-bank,
.hero-share {
    position:absolute;
    top:0;
    left:0;
    right:0;
    text-align:center;
}
.hero-bank {
    color:#c62828;
    animation:hero-bank-exit 1.3s ease forwards;
}
.hero-bank::after {
    content:"";
    position:absolute;
    left:-6px;
    right:-6px;
    top:55%;
    height:4px;
    background:#c62828;
    transform-origin:left;
    animation:hero-strike 0.9s ease forwards;
}
@keyframes hero-strike {
    0% {transform:scaleX(0);}
    100% {transform:scaleX(1);}
}
@keyframes hero-bank-exit {
    0% {opacity:1; transform:translateY(0);}
    60% {opacity:1; transform:translateY(0);}
    100% {opacity:0; transform:translateY(-10px);}
}
.hero-share {
    opacity:0;
    color:#0f7948;
    animation:hero-share-enter 0.9s ease forwards;
    animation-delay:1.1s;
}
@keyframes hero-share-enter {
    0% {opacity:0; transform:translateY(12px);}
    100% {opacity:1; transform:translateY(0);}
}
</style>
<div class="hero-container">
    <span class="hero-line">PRINT YOUR</span>
    <span class="hero-line hero-line-dynamic"><span class="hero-word"><span class="hero-bank">BANK</span><span class="hero-share">SHARE</span></span><span>NOTE</span></span>
    <span class="hero-line-small">Turn every accepted proof-of-work share into a transparent note you control.</span>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("### What is a Sharenote?")
st.markdown(
    "A Sharenote is simply a note that proves your miner solved a share—think of it as a receipt you can hold, pass along, or burn once the job is done. "
    "Each accepted share prints one, so you always know what your hardware produced without trusting a mystery payout screen. "
    "That’s the core idea; if you want the deep dive, check out [sharenote.xyz](https://sharenote.xyz) or the [manifesto](https://docs.flokicoin.org/wof/sharenote)."
)

st.markdown("### How this workspace helps")
st.markdown(
    """
- **⛏️ Print Planner:** Translate your rigs (or a desired note label) into the hashrate/reliability math the protocol expects. Great for proving “can I mint `33Z53` every 5 seconds at 95% confidence?”
- **🧪 Arithmetic Lab:** Experiment with combining, scaling, and converting notes without touching real shares. It mirrors the same ZBit + cent-Z math referenced in the manifesto so automation ideas stay realistic.
"""
)

st.markdown("### Understand the label: `ZBits` and `cent-Z`")
st.info(
    """
**`ZBits`** count how many leading zero bits were in the hash that printed the note. More zeros → rarer note.
**`cent-Z (CZ)`** are hundredths of a bit, written as two digits. `34Z10` means “34 full zeros plus 0.10 extra bit,” so each cent increases difficulty by ~0.7%.
"""
)

st.markdown(
    "Curious about the philosophy behind the project? Read the [Sharenote manifesto ↗](https://docs.flokicoin.org/wof/sharenote)."
)

st.divider()
st.subheader("Choose where to start")
tool_cols = st.columns(2)
with tool_cols[0]:
    st.markdown("#### ⛏️ Print Planner")
    st.write(
        "Enter your hashrate, pick a reliability window, and learn the biggest Sharenote you can mint (or the power you need for a specific note)."
    )
    if hasattr(st, "page_link"):
        st.page_link("pages/⛏️ Planner.py", label="Open the planner", icon="⛏️")
    else:
        st.write("👉 Select “Print Planner” in the menu on the left.")

with tool_cols[1]:
    st.markdown("#### 🧪 Arithmetic Lab")
    st.write(
        "Experiment with combining, scaling, and translating Sharenotes. See how labels change, and compare hashrates before you build automations."
    )
    if hasattr(st, "page_link"):
        st.page_link("pages/🧪 Arithmetic_Lab.py", label="Open the lab", icon="🧪")
    else:
        st.write("👉 Select “Arithmetic Lab” in the menu on the left.")

st.divider()
st.markdown("### Need a refresher?")
st.markdown(
    """
- **Reliability levels** describe how confident you want to be that at least one note prints in your chosen time window.
- **Hashrate ranges** show the minimum and maximum speeds that map to a single note label.
- **Human-readable hashrates** (kH/s, MH/s, …) are auto-formatted everywhere, so you can work in the unit that feels natural.
"""
)
