from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import PRODUCTION_RECIPES

st.set_page_config(page_title="GrimForge · Shot Recipes", page_icon="🎬", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.2rem}.hero{padding:1.5rem;border-radius:24px;background:linear-gradient(135deg,#0b1019,#1c2638);border:1px solid rgba(214,174,89,.22);margin-bottom:1rem}.k{color:#d6ae59;font-size:.7rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}.card{border:1px solid rgba(130,145,170,.18);border-radius:18px;padding:1rem;min-height:250px;background:rgba(100,120,150,.035)}.tag{display:inline-block;border-radius:999px;padding:.2rem .48rem;margin:.1rem;background:rgba(214,174,89,.09);color:#d6ae59;font-size:.7rem;font-weight:750}.micro{font-size:.78rem;opacity:.65}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="k">Cinematic grammar library</div><h1>Shot Recipes</h1>Reusable original production patterns distilled from the reference analysis: depth, camera, graphics, editing and sound should each have a job.</div>', unsafe_allow_html=True)

cols = st.columns(3, gap="large")
for idx, (name, recipe) in enumerate(PRODUCTION_RECIPES.items()):
    with cols[idx % 3]:
        st.markdown(
            f'<div class="card"><span class="tag">RECIPE {idx+1:02d}</span><h3>{name}</h3><b>Camera</b><br><span class="micro">{recipe["camera"]}</span><br><br><b>Graphics</b><br><span class="micro">{recipe["graphics"]}</span><br><br><b>Edit rule</b><br><span class="micro">{recipe["edit"]}</span></div>',
            unsafe_allow_html=True,
        )
        st.write("")

st.divider()
st.markdown("### The premium-motion rule")
st.write("A still should rarely be literally still, but movement should remain nearly invisible until the story needs impact. Use 4–6 depth planes for hero art, constant micro-drift rather than restless zooming, foreground occlusion to sell depth, selective particles/volumetrics, and reserve full 3D establishing shots for act openings or major reversals.")
st.markdown("### The comedy-motion rule")
st.write("Comedy works in the opposite direction: economical posing, sudden one-frame punch-ins, prop scale jokes, kinetic word emphasis, and hard cuts to room tone can outperform expensive animation. The contrast between premium solemnity and one brutally simple comic cut is part of the house style.")
st.caption("These are general production principles. GrimForge does not reproduce copyrighted reference footage or proprietary artwork.")
