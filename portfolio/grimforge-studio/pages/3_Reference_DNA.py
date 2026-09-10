from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from engine import REFERENCE_DNA

st.set_page_config(page_title="GrimForge · Reference DNA", page_icon="🧬", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1450px;padding-top:1.1rem}.hero{padding:1.55rem 1.65rem;border-radius:24px;background:radial-gradient(circle at 80% 10%,rgba(216,103,56,.16),transparent 30%),linear-gradient(135deg,#0b1018,#1b2638);border:1px solid rgba(214,174,89,.22);margin-bottom:1rem}.k{font-size:.7rem;letter-spacing:.16em;text-transform:uppercase;color:#d6ae59;font-weight:800}.card{border:1px solid rgba(130,145,170,.18);border-radius:18px;padding:1rem 1.05rem;background:rgba(100,120,150,.035);min-height:280px}.good{border-left:4px solid #65b88e}.warn{border-left:4px solid #d6ae59}.micro{font-size:.8rem;line-height:1.5;opacity:.7}.pill{display:inline-block;padding:.2rem .48rem;border-radius:999px;background:rgba(115,201,198,.08);color:#73c9c6;font-size:.68rem;font-weight:800;margin:.1rem}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><div class="k">Reference DNA Lab · analyzed patterns</div><h1>Three ingredients. One original house style.</h1>Keep the production strengths; discard the fingerprints. The goal is not to impersonate a creator. It is to understand why specific storytelling and editing choices work, then rebuild them into a distinct GrimForge grammar.</div>', unsafe_allow_html=True)

cards = [
    {
        "title": "Scholar / Voice DNA",
        "take": ["High-concept question before lore recap", "Calm, educated narration", "Lore → outside intellectual lens → synthesis", "Micro-summaries before deeper sections", "Explicit canon-versus-interpretation signaling", "Archive/terminal UI, diagrams and restrained glitch", "Rare deadpan gag, then immediate return to seriousness"],
        "avoid": "Do not mimic the narrator's exact voice, phrasing, personal theology, screen layout or recurring jokes.",
    },
    {
        "title": "Deadpan Comedy DNA",
        "take": ["Cosmic horror framed with mundane administrative language", "Straight-man / zealot / confused-outsider character triangle", "Tiny conversational overlaps and interruptions", "Rhythm-of-three escalation", "Hard cut to silence after chaos", "One-frame punch-ins and economical puppet movement", "Kinetic captions as visual percussion"],
        "avoid": "Do not reproduce specific jokes, characters, dialogue beats or recognizable recurring bits from the reference.",
    },
    {
        "title": "Premium Chronicler DNA",
        "take": ["Chaptered chronological arcs", "4–6 plane parallax for hero illustrations", "Continuous almost-invisible camera micro-movement", "Tactical maps and system-to-battlefield orientation", "Volumetric lighting, particles and selective color accents", "Narration-centered broadcast mix with ducked music", "Reserve full 3D scale shots for pivotal moments"],
        "avoid": "Do not reuse official/reference art, exact compositions, voice identity, branded overlays or footage unless separately licensed.",
    },
]

cols = st.columns(3, gap="large")
for col, card in zip(cols, cards):
    with col:
        points = "".join(f"<li>{p}</li>" for p in card["take"])
        st.markdown(f'<div class="card good"><h3>{card["title"]}</h3><ul class="micro">{points}</ul><b>Boundary</b><br><span class="micro">{card["avoid"]}</span></div>', unsafe_allow_html=True)

st.divider()
st.markdown("### GrimForge house blend")
left, right = st.columns([1.35, 1], gap="large")
with left:
    st.markdown('<div class="card warn"><span class="pill">35% narrator + scholar</span><span class="pill">25% deadpan mechanics</span><span class="pill">40% premium cinema</span><h3>Default creative doctrine</h3><span class="micro">Open on a question worth arguing about. Ground the viewer quickly. Move from source fact to interpretation. Make abstract ideas visible with maps, diagrams and dimensional art. Use humor as a pressure release, not wallpaper. Give the strongest counter-reading a fair hearing. Then close by making the opening question feel different than it did at the beginning.</span></div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="card"><h3>Visual rhythm</h3><span class="micro"><b>Think:</b> premium slow-burn image → tactical explanation → source/archive frame → deeper diagram → one sharp comic rupture → silence → rebuild into a cinematic payoff.<br><br><b>Audio:</b> centered narrator, low ambient bed, spatial foley, music ducking, and deliberate silence around important reversals.<br><br><b>Typography:</b> one ceremonial display family + one clean technical/monospace system. Text should clarify hierarchy, not cover the screen.</span></div>', unsafe_allow_html=True)

st.caption("The Reference DNA page records general production observations from the three user-selected references. It is a design-analysis tool, not a library of copied creator assets.")
