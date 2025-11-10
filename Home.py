"""
Landing page for the Sharenote planning suite.
-----------------------------------------------

Describes the planner and the arithmetic playground that live in the project's
multi-page layout.
"""

import streamlit as st

st.set_page_config(page_title="Sharenote Studio", page_icon="🧮", layout="centered")

st.markdown(
    "<div align='center'><img src='https://sharenote.xyz/optimized/pcb-w640.avif' width='380' style='max-width:100%;height:auto'></div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div align='center' style='margin-top:20px'><strong style='font-size:34px'>Print your Sharenote</strong></div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="margin:48px auto; max-width:900px; display:flex; gap:24px; flex-wrap:wrap; justify-content:center;">
        <div style="flex:1 1 280px; padding:20px; background:#0c0f15; border-radius:18px; color:#f4f6fb; box-shadow:0 10px 30px rgba(15,23,42,.25); min-width:280px;">
            <p style="font-size:18px; font-weight:600; margin:0;">Arithmetic Lab</p>
            <p style="margin:8px 0 0; color:#c5c9d2; font-size:14px;">
                Mix, subtract, and scale Sharenotes.
            </p>
        </div>
        <div style="flex:1 1 280px; padding:20px; background:#0c0f15; border-radius:18px; color:#f4f6fb; box-shadow:0 10px 30px rgba(15,23,42,.25); min-width:280px;">
            <p style="font-size:18px; font-weight:600; margin:0;">Print Planner</p>
            <p style="margin:8px 0 0; color:#c5c9d2; font-size:14px;">
                Convert hashpower into mintable Sharenote targets.
            </p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)