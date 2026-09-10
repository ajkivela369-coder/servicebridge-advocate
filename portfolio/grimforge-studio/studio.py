from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from engine import (
    ASSET_RIGHTS,
    REFERENCE_DNA,
    VOICE_PROFILES,
    blend_reference_dna,
    build_channel_concept,
    build_director_timeline,
    build_script_blueprint,
    rights_gate,
)

st.set_page_config(page_title="GrimForge Studio", page_icon="⚔️", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
<style>
:root{--gf-gold:#d6ae59;--gf-ember:#d86738;--gf-cyan:#73c9c6;--gf-ink:#0b0f17;--gf-panel:#151c28}
.block-container{max-width:1600px;padding-top:1rem;padding-bottom:4rem}
[data-testid="stSidebar"]{border-right:1px solid rgba(214,174,89,.16)}
.gf-hero{position:relative;overflow:hidden;border-radius:28px;padding:2rem 2.1rem;margin-bottom:1rem;
background:radial-gradient(circle at 80% 15%,rgba(216,103,56,.19),transparent 28%),radial-gradient(circle at 14% 18%,rgba(115,201,198,.12),transparent 32%),linear-gradient(135deg,#090d14,#141d2c 62%,#1f1a18);border:1px solid rgba(214,174,89,.2);box-shadow:0 24px 70px rgba(0,0,0,.28)}
.gf-kicker{font-size:.70rem;text-transform:uppercase;letter-spacing:.18em;font-weight:800;color:#d6ae59}
.gf-title{font-size:3.1rem;line-height:1;font-weight:900;letter-spacing:-.045em;margin:.25rem 0 .55rem;color:#f8f3e9}
.gf-sub{max-width:1040px;font-size:1.02rem;line-height:1.55;color:#c8ced8}
.gf-seal{position:absolute;right:2.2rem;top:1.8rem;border:1px solid rgba(214,174,89,.4);width:82px;height:82px;border-radius:50%;display:grid;place-items:center;color:#d6ae59;font-size:2rem;box-shadow:inset 0 0 25px rgba(214,174,89,.08)}
.gf-card{border:1px solid rgba(150,165,190,.16);border-radius:18px;padding:1rem 1.05rem;background:linear-gradient(145deg,rgba(80,95,120,.055),rgba(10,15,24,.025));min-height:120px}
.gf-card h4{margin:.1rem 0 .4rem}.gf-micro{font-size:.78rem;opacity:.66;line-height:1.45}
.gf-chip{display:inline-block;padding:.22rem .55rem;border-radius:999px;background:rgba(214,174,89,.1);border:1px solid rgba(214,174,89,.2);font-size:.72rem;font-weight:750;margin:.12rem;color:#d6ae59}
.gf-metric{border:1px solid rgba(150,165,190,.14);border-radius:15px;padding:.75rem .9rem;background:rgba(90,105,130,.035)}
.gf-ml{font-size:.66rem;text-transform:uppercase;letter-spacing:.12em;opacity:.55;font-weight:800}.gf-mv{font-size:1.45rem;font-weight:850;margin-top:.1rem}
.gf-scene{border-left:3px solid #d6ae59;border-radius:0 14px 14px 0;padding:.75rem 1rem;margin:.45rem 0;background:rgba(214,174,89,.035)}
.gf-time{font-family:monospace;color:#d6ae59;font-weight:800}.gf-canon{font-size:.65rem;letter-spacing:.1em;border:1px solid rgba(115,201,198,.28);border-radius:999px;padding:.16rem .42rem;color:#73c9c6}
.gf-voice{border-radius:20px;padding:1.15rem;background:linear-gradient(135deg,rgba(214,174,89,.08),rgba(115,201,198,.05));border:1px solid rgba(214,174,89,.19)}
.gf-right-ok{border-left:4px solid #4fa977}.gf-right-block{border-left:4px solid #d86738}
.gf-footer{font-size:.78rem;opacity:.58;margin-top:1.5rem}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """<div class="gf-hero"><div class="gf-kicker">App XIII · AI cinematic lore director</div>
<div class="gf-title">GrimForge Studio</div>
<div class="gf-sub">Turn a lore idea into an original thesis, narrator brief, cinematic shot plan, motion-art timeline, humor map, source/canon labels, rights checklist, title concepts and a production-ready creative package. Built for grimdark science-fiction commentary and old-world dark-fantasy storytelling.</div>
<div class="gf-seal">XIII</div></div>""",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("### Forge controls")
    world = st.radio("World mode", ["Grimdark Galaxy", "Old World Dark Fantasy"], index=0)
    length = st.slider("Target length", 4, 60, 18, 1, format="%d min")
    humor = st.slider("Dry humor", 0, 100, 38)
    depth = st.slider("Lore / analysis depth", 0, 100, 86)
    motion = st.slider("Motion / cinematic intensity", 0, 100, 88)
    st.divider()
    narrator = st.selectbox("Narrator", list(VOICE_PROFILES), index=0)
    st.caption("Voice direction describes a new synthetic narrator character; it is not a clone of a reference creator.")

input_left, input_right = st.columns([1.55, 1], gap="large")
with input_left:
    topic = st.text_input("Episode subject", value="Why the greatest empire can never truly win its war")
    angle = st.text_area(
        "Thesis / angle",
        value="The empire's institutions survive by solving immediate crises in ways that reproduce the conditions of the next crisis.",
        height=105,
    )
with input_right:
    st.markdown("#### Creative doctrine")
    st.markdown(
        '<div class="gf-card"><span class="gf-chip">Thesis before trivia</span><span class="gf-chip">Canon ≠ interpretation</span><span class="gf-chip">Humor as pressure valve</span><span class="gf-chip">Motion with purpose</span><span class="gf-chip">Original assets</span><br><br><span class="gf-micro">The studio is designed to resist wiki-recital scripts and mass-produced template videos. Every episode should have a distinct argument, counterweight and visual motif.</span></div>',
        unsafe_allow_html=True,
    )

ref_tab, channel_tab, script_tab, timeline_tab, voice_tab, rights_tab, export_tab = st.tabs(
    ["Reference DNA", "Channel Forge", "Lore Scholar", "Director Timeline", "Voice Lab", "Rights Guard", "Export"]
)

with ref_tab:
    st.markdown("### Reference DNA Lab")
    st.caption("Blend high-level production traits. The presets describe analyzed qualities, not copied scripts, artwork, jokes, or voices.")
    cols = st.columns(3, gap="large")
    weights = {}
    defaults = [35, 25, 40]
    for col, (name, dna), default in zip(cols, REFERENCE_DNA.items(), defaults):
        with col:
            st.markdown(f"#### {name}")
            st.write(dna["notes"])
            st.caption(f"Narrator {dna['narrator']} · Humor {dna['humor']} · Cinematic {dna['cinematic']} · Depth {dna['depth']} · Motion {dna['motion']}")
            weights[name] = st.slider(f"Blend weight · {name}", 0, 100, default, key=f"w_{name}")
    blended = blend_reference_dna(weights)
    st.divider()
    mcols = st.columns(6)
    for col, trait in zip(mcols, ["narrator", "humor", "cinematic", "depth", "motion", "pace"]):
        with col:
            st.markdown(f'<div class="gf-metric"><div class="gf-ml">{trait}</div><div class="gf-mv">{blended[trait]}</div></div>', unsafe_allow_html=True)
    st.info("Default blend: narrator/intellectual authority from reference 1, comic mechanics from reference 2, and premium documentary construction from reference 3.")

with channel_tab:
    concept = build_channel_concept(world, narrator, humor, depth)
    st.markdown("### Channel Forge")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown("#### Audience promise")
        st.markdown(f'<div class="gf-card">{concept["channel_promise"]}</div>', unsafe_allow_html=True)
        st.markdown("#### Depth rule")
        st.markdown(f'<div class="gf-card">{concept["depth_rule"]}</div>', unsafe_allow_html=True)
    with c2:
        st.markdown("#### Visual language")
        st.markdown(f'<div class="gf-card">{concept["visual_language"]}</div>', unsafe_allow_html=True)
        st.markdown("#### Humor rule")
        st.markdown(f'<div class="gf-card">{concept["humor_rule"]}</div>', unsafe_allow_html=True)
    st.markdown("#### Recurring show formats")
    format_cols = st.columns(4)
    formats = [
        ("The Heresy File", "One contradiction or disputed interpretation, reconstructed from sources."),
        ("War Room", "A battle or campaign explained through command decisions, maps and failure points."),
        ("The Strange Footnote", "A bizarre lore detail used as the doorway into a deeper historical or philosophical idea."),
        ("Archive After Dark", "Old World folklore, cults, monsters and states treated like recovered historical documents."),
    ]
    for col, (name, copy) in zip(format_cols, formats):
        with col:
            st.markdown(f'<div class="gf-card"><h4>{name}</h4><span class="gf-micro">{copy}</span></div>', unsafe_allow_html=True)

with script_tab:
    st.markdown("### Lore Scholar")
    st.caption("A structured argument builder rather than an imitation of a specific creator.")
    blueprint = build_script_blueprint(topic, angle, world, depth, humor)
    for i, row in enumerate(blueprint, 1):
        st.markdown(f"**{i}. {row['section']}**")
        st.write(row["instruction"])
        if row["section"] in {"Evidence Ladder", "Counterweight"}:
            st.caption("Source discipline: mark statements as CANON/SOURCE, INFERENCE, INTERPRETATION or EDITORIAL before final narration.")
        st.divider()
    st.markdown("#### Original hook sketch")
    st.code(
        f"The obvious story of {topic} is easy to tell. The more interesting question is why that explanation stops working the moment we examine {angle.lower()} This episode starts there.",
        language=None,
    )

with timeline_tab:
    st.markdown("### Cinematic Director Timeline")
    scenes = build_director_timeline(topic, angle, world, length, humor, motion, depth)
    for scene in scenes:
        st.markdown(
            f'<div class="gf-scene"><span class="gf-time">{scene.start}</span> &nbsp; <b>{scene.purpose}</b> &nbsp; <span class="gf-canon">{scene.canon_label}</span><br><br><b>Narration:</b> {scene.narration_goal}<br><b>Visual:</b> {scene.visual}<br><b>Motion:</b> {scene.motion}<br><b>Sound:</b> {scene.sound}<br><b>Humor:</b> {scene.humor}</div>',
            unsafe_allow_html=True,
        )
    st.caption("Timeline durations are a production scaffold. A later generation pass should sync final shot lengths to the finished narration waveform.")

with voice_tab:
    profile = VOICE_PROFILES[narrator]
    st.markdown("### Voice Lab")
    st.markdown(
        f'<div class="gf-voice"><div class="gf-kicker">{narrator}</div><h3>{profile["age_character"]} · {profile["register"]} register</h3><b>Tempo:</b> {profile["tempo"]}<br><b>Texture:</b> {profile["texture"]}<br><br>{profile["direction"]}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("#### Performance map")
    voice_rows = [
        ("Hook", "Quiet confidence. Do not oversell. The first strange idea should feel inevitable once spoken."),
        ("Dense analysis", "Slow slightly; emphasize nouns and contrasts rather than every adjective."),
        ("Battle transition", "Increase forward momentum, not volume. Let percussion supply aggression."),
        ("Dry joke", "Underplay it. A trace of amusement is enough."),
        ("Counterargument", "Cooler, more neutral delivery. Sound willing to be wrong."),
        ("Final line", "Reduce pace and leave a short pocket of silence after the final phrase."),
    ]
    for beat, direction in voice_rows:
        st.write(f"**{beat}:** {direction}")
    st.warning("Reference videos may inspire broad vocal qualities, but GrimForge should use an original licensed/synthetic voice or a consenting speaker—not an unauthorized voice clone.")

with rights_tab:
    st.markdown("### Rights Guard")
    st.caption("Track provenance before an asset reaches the render queue. Labels are workflow aids, not legal conclusions.")
    if "gf_assets" not in st.session_state:
        st.session_state.gf_assets = [
            {"name": "Original cathedral-battle matte painting", "rights": "Original AI artwork"},
            {"name": "Animated campaign map", "rights": "Original AI artwork"},
            {"name": "Reference screenshot for internal analysis only", "rights": "Third-party / reference only"},
        ]
    for i, asset in enumerate(st.session_state.gf_assets):
        a, b = st.columns([2, 1])
        with a:
            asset["name"] = st.text_input("Asset", value=asset["name"], key=f"asset_name_{i}", label_visibility="collapsed")
        with b:
            asset["rights"] = st.selectbox("Rights", ASSET_RIGHTS, index=ASSET_RIGHTS.index(asset["rights"]), key=f"asset_rights_{i}", label_visibility="collapsed")
    if st.button("Add asset"):
        st.session_state.gf_assets.append({"name": "New asset", "rights": "Original AI artwork"})
        st.rerun()
    gate = rights_gate(st.session_state.gf_assets)
    if gate["ready"]:
        st.success("Rights gate: no asset is currently marked third-party/reference-only.")
    else:
        st.error(f"Rights gate: {len(gate['blocked'])} asset(s) should not enter the publication render until replaced or cleared.")
        for item in gate["blocked"]:
            st.write(f"• {item['name']}")
    st.caption(gate["note"])

with export_tab:
    scenes = build_director_timeline(topic, angle, world, length, humor, motion, depth)
    concept = build_channel_concept(world, narrator, humor, depth)
    blueprint = build_script_blueprint(topic, angle, world, depth, humor)
    package = {
        "app": "GrimForge Studio",
        "version": "0.1.0",
        "world_mode": world,
        "episode": {"topic": topic, "angle": angle, "target_minutes": length},
        "creative_controls": {"humor": humor, "depth": depth, "motion": motion},
        "narrator": {"name": narrator, **VOICE_PROFILES[narrator]},
        "channel_concept": concept,
        "reference_dna": {"weights": weights, "blend": blend_reference_dna(weights)},
        "script_blueprint": blueprint,
        "director_timeline": [scene.to_dict() for scene in scenes],
        "rights_gate": rights_gate(st.session_state.get("gf_assets", [])),
    }
    st.markdown("### Production Package")
    st.write("Export the creative brief for a later script, voice, image/video-generation or editing pipeline.")
    j1, j2 = st.columns(2)
    with j1:
        st.download_button("Download production JSON", json.dumps(package, indent=2), file_name="grimforge_production_package.json", mime="application/json", use_container_width=True)
    with j2:
        markdown = [f"# {topic}", "", f"**World:** {world}", f"**Thesis:** {angle}", f"**Narrator:** {narrator}", "", "## Director Timeline"]
        for scene in scenes:
            markdown.extend([f"### {scene.start} — {scene.purpose}", scene.narration_goal, f"- Visual: {scene.visual}", f"- Motion: {scene.motion}", f"- Sound: {scene.sound}", f"- Humor: {scene.humor}", f"- Label: {scene.canon_label}", ""])
        st.download_button("Download director brief", "\n".join(markdown), file_name="grimforge_director_brief.md", mime="text/markdown", use_container_width=True)
    st.markdown("#### Next render pipeline")
    st.markdown('<div class="gf-card"><span class="gf-chip">Research</span> → <span class="gf-chip">Canon check</span> → <span class="gf-chip">Script</span> → <span class="gf-chip">Narration</span> → <span class="gf-chip">Motion art / 3D</span> → <span class="gf-chip">Sound + music</span> → <span class="gf-chip">Rights gate</span> → <span class="gf-chip">Thumbnail + title</span> → <span class="gf-chip">Human final cut</span></div>', unsafe_allow_html=True)

st.markdown(
    '<div class="gf-footer">GrimForge Studio is an original creative-production tool. Reference DNA captures general production attributes only. Do not upload copyrighted assets you lack permission to use, and do not use unauthorized voice cloning. Fictional demo concepts are included for portfolio testing.</div>',
    unsafe_allow_html=True,
)
