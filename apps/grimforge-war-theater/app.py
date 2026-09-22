import html
import json
import random
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from war_engine import (
    FACTIONS,
    PRESETS,
    REFERENCE_EMBED,
    REFERENCE_LENSES,
    REFERENCE_URL,
    make_episode,
    random_presets,
    veyr_advice,
)

st.set_page_config(
    page_title="GrimForge War Theater",
    page_icon="⚔️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root { --gold:#c79a43; --ember:#9b3a22; --teal:#2f8f83; }
.block-container {max-width: 1500px; padding-top: 1.1rem; padding-bottom: 4rem;}
[data-testid="stAppViewContainer"] {background:
    radial-gradient(circle at 90% 0%, rgba(130,50,28,.20), transparent 26%),
    radial-gradient(circle at 4% 4%, rgba(39,105,95,.15), transparent 23%),
    #080909;}
[data-testid="stSidebar"] {background:#0d100f; border-right:1px solid #262a27;}
.gf-card {border:1px solid #33352f; background:rgba(18,19,17,.92); border-radius:18px; padding:16px; margin-bottom:12px;}
.gf-eyebrow {font-size:.72rem; letter-spacing:.14em; text-transform:uppercase; font-weight:800; color:#a69a84;}
.gf-title {font-family:Georgia,serif; font-size:2.05rem; font-weight:800; line-height:1.05; margin:0;}
.gf-muted {color:#938e84; font-size:.84rem;}
.gf-badge {display:inline-block; border:1px solid #5b4728; background:#211b10; color:#dfbd76; padding:5px 9px; border-radius:999px; font-size:.72rem; margin:2px;}
.gf-status {display:flex; gap:8px; flex-wrap:wrap; margin:8px 0 14px;}
.gf-status span {border:1px solid #4b3c22; background:#19150d; color:#d7b46b; padding:6px 10px; border-radius:999px; font-size:.75rem;}
.gf-status .ok {border-color:#285a4d; background:#0d211b; color:#9fdec7;}
.gf-summary {border:1px solid #4d422c; background:#17140d; padding:12px 14px; border-radius:14px; margin:10px 0 14px;}
.gf-summary strong {color:#e4c17b;}
.gf-scene {border-left:3px solid #8c6a2e; padding:10px 12px; margin:8px 0; background:#10110f; border-radius:0 12px 12px 0;}
.gf-scene h4 {margin:0 0 4px 0;}
.gf-ai-orb {
    position: fixed; right: 24px; bottom: 22px; z-index: 9999;
    width:58px; height:58px; border-radius:50%;
    display:flex; align-items:center; justify-content:center;
    background:radial-gradient(circle at 35% 30%, #60c7b6, #1b4a43 43%, #6b341f 75%, #1a0d09);
    border:1px solid #c29342; box-shadow:0 0 0 5px rgba(199,154,67,.08),0 12px 35px #000b;
    color:#f5ddb0; font-weight:900; font-size:11px; letter-spacing:.05em;
    pointer-events:none;
}
.gf-ai-orb:after {content:""; position:absolute; inset:-7px; border-radius:50%; border:1px solid rgba(199,154,67,.2); animation:pulse 2.6s ease-in-out infinite;}
@keyframes pulse {50%{transform:scale(1.12);opacity:.25}}
div[data-testid="stPopover"] button {border-color:#6b542d !important;}
</style>
<div class="gf-ai-orb">VEYR</div>
""",
    unsafe_allow_html=True,
)

if "mode" not in st.session_state:
    st.session_state.mode = "Simple"
if "presets" not in st.session_state:
    st.session_state.presets = {group: options[0] for group, options in PRESETS.items()}
if "faction" not in st.session_state:
    st.session_state.faction = "Ashen Crown"
if "lens_name" not in st.session_state:
    st.session_state.lens_name = "Tactical War Chronicle"
if "episode" not in st.session_state:
    st.session_state.episode = None
if "title" not in st.session_state:
    st.session_state.title = "The Siege of Hollow Meridian"
if "enemy" not in st.session_state:
    st.session_state.enemy = "The Saltbound Legions"
if "commander" not in st.session_state:
    st.session_state.commander = "Marshal Veyra Kest"
if "objective" not in st.session_state:
    st.session_state.objective = "Hold the bridge-city until the moon-gate closes."
if "custom_minutes" not in st.session_state:
    st.session_state.custom_minutes = 12
if "scene_count" not in st.session_state:
    st.session_state.scene_count = 8

with st.sidebar:
    st.markdown('<div class="gf-eyebrow">GRIMFORGE</div><div class="gf-title">War Theater</div>', unsafe_allow_html=True)
    st.caption("GitHub-first · Streamlit build")
    st.session_state.mode = st.radio("Workspace", ["Simple", "Pro"], horizontal=True, index=0 if st.session_state.mode == "Simple" else 1)
    st.divider()
    st.markdown("**Provider status**")
    st.caption("Episode generator: local/deterministic")
    st.caption("Reference analyzer: not connected")
    st.caption("Video renderer: not connected")
    st.caption("Premium TTS: not connected")
    st.caption("Final MP4 worker: not connected")
    st.divider()
    with st.popover("◉ Director Veyr", use_container_width=True):
        st.caption("Local copilot · persistent project-aware advice")
        veyr_actions = [
            "Improve battle pacing",
            "Strengthen the opening hook",
            "Make this feel larger scale",
            "Clarify battlefield geography",
            "Fix continuity",
            "Improve commander arc",
            "Strengthen sound design",
            "Add a tactical reversal",
            "Diagnose weak scene",
            "Prepare final QC",
            "What is missing for final episode",
        ]
        action = st.selectbox("Director pass", veyr_actions)
        if st.button("Ask Veyr", use_container_width=True):
            st.session_state.veyr_answer = veyr_advice(action, st.session_state.episode, st.session_state.mode == "Pro")
        if st.session_state.get("veyr_answer"):
            st.markdown(st.session_state.veyr_answer)

top_left, top_right = st.columns([0.68, 0.32])
with top_left:
    st.markdown('<div class="gf-eyebrow">Original war-fantasy production workspace</div>', unsafe_allow_html=True)
    st.title("GrimForge War Theater")
    st.caption("Reference theater → preset forge → original episode → playable animatic → provider-aware final render")
with top_right:
    st.markdown(
        '<div class="gf-status"><span class="ok">GitHub source</span><span>Streamlit-ready</span><span>Final render provider not connected</span></div>',
        unsafe_allow_html=True,
    )

st.warning(
    "Reference material is used only for broad production mechanics such as pacing, scale, camera grammar, narration density, lighting, sound, and story rhythm. "
    "Do not copy the source video's characters, lore, dialogue, scripts, music, branding, or visual assets."
)

st.subheader("Reference Theater")
ref_col, lens_col = st.columns([1.2, 0.8], gap="large")
with ref_col:
    st.video(REFERENCE_URL)
    st.caption("Current test reference: YouTube video XQ1jlW7hQrA. Use the external player if embedding is restricted.")
    st.link_button("Open reference on YouTube", REFERENCE_URL)
with lens_col:
    lens_name = st.selectbox("Reference Lens preset", list(REFERENCE_LENSES.keys()), index=list(REFERENCE_LENSES.keys()).index(st.session_state.lens_name))
    st.session_state.lens_name = lens_name
    lens = REFERENCE_LENSES[lens_name]
    for key, label in [
        ("scale", "Scale"), ("shot_rhythm", "Shot rhythm"), ("camera", "Camera"),
        ("narration", "Narration"), ("lighting", "Lighting"), ("sound", "Sound"), ("story", "Story rhythm"),
    ]:
        st.text_area(label, lens[key], height=70, key=f"lens_{key}")
    st.caption("These are editable production notes, not an automated analysis of the linked video.")

if st.session_state.mode == "Simple":
    st.subheader("Choose your war-film presets")
    c1, c2 = st.columns([1, 0.28])
    with c2:
        if st.button("🎲 Surprise Me", use_container_width=True):
            st.session_state.presets = random_presets(st.session_state.title + st.session_state.enemy)
            st.rerun()

    for group, options in PRESETS.items():
        current = st.session_state.presets.get(group, options[0])
        st.session_state.presets[group] = st.selectbox(group, options, index=options.index(current) if current in options else 0, key=f"simple_{group}")

    f_names = list(FACTIONS.keys())
    st.session_state.faction = st.selectbox("Faction preset", f_names, index=f_names.index(st.session_state.faction))
    faction = FACTIONS[st.session_state.faction]
    st.markdown(
        f'<div class="gf-summary"><strong>{html.escape(st.session_state.faction)}</strong> · '
        f'{html.escape(faction["motif"])}<br><span class="gf-muted">{html.escape(faction["army"])} · '
        f'{html.escape(faction["rule"])} · {html.escape(faction["palette"])}</span></div>',
        unsafe_allow_html=True,
    )

    st.session_state.title = st.text_input("Episode title", st.session_state.title)
    st.session_state.enemy = st.text_input("Enemy force", st.session_state.enemy)
    st.session_state.commander = st.text_input("Commander", st.session_state.commander)
    st.session_state.objective = st.text_area("Objective", st.session_state.objective, height=80)

    summary_bits = [st.session_state.presets[g] for g in PRESETS]
    st.markdown(
        '<div class="gf-summary"><strong>Selected:</strong> ' +
        " · ".join(f'<span class="gf-badge">{html.escape(x)}</span>' for x in summary_bits) +
        f'<span class="gf-badge">{html.escape(st.session_state.faction)}</span></div>',
        unsafe_allow_html=True,
    )

    if st.button("🔥 FORGE WAR EPISODE", type="primary", use_container_width=True):
        st.session_state.episode = make_episode(
            st.session_state.title,
            st.session_state.presets,
            st.session_state.faction,
            st.session_state.enemy,
            st.session_state.commander,
            st.session_state.objective,
            st.session_state.custom_minutes,
            st.session_state.scene_count,
        )
        st.success("Playable animatic forged below.")

else:
    tabs = st.tabs([
        "War Bible", "Factions", "Story", "Battle Map / Geography", "Scenes",
        "Shots / Takes", "Continuity", "Sound", "Episode Player",
        "Reference Lens", "Rights", "Export",
    ])
    with tabs[0]:
        st.session_state.title = st.text_input("Title", st.session_state.title, key="pro_title")
        premise = st.text_area("Premise", "A fortress-city must survive until a failing moon-gate closes.", height=90)
        logline = st.text_area("Logline", f"{st.session_state.commander} must {st.session_state.objective.lower()}", height=90)
        stakes = st.text_area("Stakes", "If the city falls, the enemy gains the only winter crossing for a hundred leagues.", height=90)
    with tabs[1]:
        f_names = list(FACTIONS.keys())
        st.session_state.faction = st.selectbox("Faction", f_names, index=f_names.index(st.session_state.faction), key="pro_faction")
        st.session_state.enemy = st.text_input("Enemy force", st.session_state.enemy, key="pro_enemy")
        st.session_state.commander = st.text_input("Commander", st.session_state.commander, key="pro_commander")
        st.text_input("Hero units", "Ash Guard, Fifth Gate Engineers")
        st.text_input("Monsters", "None")
        st.text_input("Siege engines", "Three ember rams, chain trebuchets")
        st.number_input("Army size", 12, 100000, 4200, step=50)
        st.text_input("Formations", "Layered shield walls, reserve wedge, engineer counter-battery")
    with tabs[2]:
        st.session_state.custom_minutes = st.slider("Runtime (minutes)", 1, 30, st.session_state.custom_minutes)
        st.session_state.scene_count = st.slider("Scene count", 5, 14, st.session_state.scene_count)
        st.session_state.objective = st.text_area("Objective", st.session_state.objective, key="pro_objective")
        for group in ["War Fantasy Flavor", "Battle Type", "Story Structure", "Visual Scale", "Narration", "Violence"]:
            opts = PRESETS[group]
            cur = st.session_state.presets.get(group, opts[0])
            st.session_state.presets[group] = st.selectbox(group, opts, index=opts.index(cur) if cur in opts else 0, key=f"pro_{group}")
        st.text_area("Beat sheet", "Oath → approach → first clash → tactical success → reversal → cost → final push → aftermath", height=120)
    with tabs[3]:
        st.text_area("Battlefield geography", "North: ridge batteries. East: river. South: drowned ward. West: retreat road. Main gate faces east.", height=130)
        st.selectbox("Dominant friendly screen direction", ["Left → Right", "Right → Left"])
        st.checkbox("Re-establish geography after reversals", value=True)
        st.checkbox("Lock cardinal map", value=True)
    with tabs[4]:
        if st.session_state.episode:
            for scene in st.session_state.episode.scenes:
                with st.expander(f"{scene.id} · {scene.title} · {scene.duration}s"):
                    st.text_area("Visual", scene.visual, key=f"v_{scene.id}")
                    st.text_area("Narration", scene.narration, key=f"n_{scene.id}")
                    st.text_area("Dialogue", scene.dialogue, key=f"d_{scene.id}")
        else:
            st.info("Forge an episode to edit generated scenes.")
    with tabs[5]:
        st.slider("Average shot duration (seconds)", 1.0, 12.0, 4.5, 0.5)
        st.selectbox("Shot size", ["EWS", "WS", "MLS", "MS", "MCU", "CU", "ECU"])
        st.selectbox("Lens", ["18mm", "24mm", "35mm", "50mm", "85mm", "135mm", "Custom"])
        st.selectbox("Camera height", ["Ground", "Waist", "Eye", "Elevated", "Aerial"])
        st.selectbox("Movement", ["Locked", "Pan", "Track", "Push", "Crane", "Handheld", "Drone-like"])
        st.selectbox("Screen direction", ["L→R", "R→L", "Neutral", "Axis break"])
        st.markdown("**Take review**")
        st.radio("Take A", ["Keep", "Maybe", "Reject"], horizontal=True)
        st.radio("Take B", ["Keep", "Maybe", "Reject"], horizontal=True)
        st.checkbox("Mark selected take as Golden Fragment")
    with tabs[6]:
        for item in ["Character identity", "Wardrobe", "Props", "Heraldry", "Faction colors", "Terrain", "Time of day", "Damage / injury state", "Army positions"]:
            st.checkbox(item, value=True, key=f"lock_{item}")
    with tabs[7]:
        for lane, default in [("Dialogue",-3),("Foley",-8),("Ambience",-14),("Impacts",-5),("Room tone",-20),("Music",-16)]:
            st.slider(lane, -36, 3, default, key=f"lane_{lane}")
        st.slider("Target loudness (LUFS)", -24, -10, -16)
        st.checkbox("Duck music under dialogue", True)
        st.checkbox("Limiter / clipping check", True)
    with tabs[8]:
        st.info("The full Episode Player appears below the studio after an episode is forged.")
    with tabs[9]:
        st.session_state.lens_name = st.selectbox("Reference lens", list(REFERENCE_LENSES.keys()), index=list(REFERENCE_LENSES.keys()).index(st.session_state.lens_name), key="pro_lens")
        st.json(REFERENCE_LENSES[st.session_state.lens_name])
    with tabs[10]:
        st.radio("Rights basis", ["Original / generated original", "Owned", "Licensed", "Permission received", "Unknown"], index=0)
        st.text_area("Attribution / source notes", "Reference video used only for broad cinematic mechanics.")
        st.checkbox("I understand transformation does not itself guarantee fair use", value=True)
    with tabs[11]:
        st.selectbox("Aspect ratio", ["16:9", "2.39:1", "9:16", "1:1"])
        st.selectbox("Frame rate intent", [24, 25, 30, 60])
        st.selectbox("Quality", ["Highest available", "Balanced", "Fast preview"])
        st.checkbox("Captions", True)
        st.caption("Highest available means the best settings a connected provider actually supports.")

    if st.button("🔥 FORGE / REFORGE EPISODE", type="primary", use_container_width=True):
        st.session_state.episode = make_episode(
            st.session_state.title,
            st.session_state.presets,
            st.session_state.faction,
            st.session_state.enemy,
            st.session_state.commander,
            st.session_state.objective,
            st.session_state.custom_minutes,
            st.session_state.scene_count,
        )
        st.success("Playable animatic reforged.")

episode = st.session_state.episode
if episode is None:
    st.divider()
    st.subheader("Demo Episode")
    if st.button("▶ Load & Play The Siege of Hollow Meridian", use_container_width=True):
        st.session_state.episode = make_episode(
            st.session_state.title,
            st.session_state.presets,
            st.session_state.faction,
            st.session_state.enemy,
            st.session_state.commander,
            st.session_state.objective,
            st.session_state.custom_minutes,
            st.session_state.scene_count,
        )
        st.rerun()
else:
    st.divider()
    st.subheader("Playable Animatic")
    st.markdown(
        f'<div class="gf-summary"><strong>{html.escape(episode.title)}</strong><br>'
        f'<span class="gf-muted">{html.escape(episode.logline)}</span><br>'
        f'<span class="gf-badge">PLAYABLE ANIMATIC</span>'
        f'<span class="gf-badge">Story target {round(episode.runtime_seconds/60,1)} min</span>'
        f'<span class="gf-badge">FINAL FULL-MOTION RENDER · provider not connected</span></div>',
        unsafe_allow_html=True,
    )

    scenes_json = json.dumps([
        {
            "id": s.id, "act": s.act, "title": s.title,
            "duration": max(5, min(14, round(s.duration / max(1, episode.runtime_seconds) * 80))),
            "narration": s.narration, "dialogue": s.dialogue,
            "visual": s.visual, "camera": s.camera, "sound": s.sound,
            "continuity": s.continuity, "palette": s.palette, "intensity": s.intensity,
        } for s in episode.scenes
    ])
    player_html = f"""
    <html><head><style>
    body{{margin:0;background:#080909;color:#eee8dc;font-family:Arial,sans-serif}}
    #frame{{position:relative;aspect-ratio:16/9;border:1px solid #524327;border-radius:16px;overflow:hidden;
      background:radial-gradient(circle at 55% 35%,#58301d 0,#1d1812 33%,#080909 72%);}}
    .fog{{position:absolute;inset:-30%;background:conic-gradient(from 20deg,#0000,#79502b22,#0000,#2d8b7e18,#0000);animation:spin 18s linear infinite}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    .top{{position:absolute;top:14px;left:14px;right:14px;display:flex;justify-content:space-between;z-index:3}}
    .pill{{padding:6px 9px;border:1px solid #806330;background:#090909bb;border-radius:999px;color:#e5c47d;font-size:12px}}
    .center{{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:9%;z-index:2}}
    .center h2{{font-family:Georgia,serif;font-size:34px;margin:0 0 10px}}
    .center p{{max-width:880px;color:#d6cec1;line-height:1.5}}
    .quote{{font-family:Georgia,serif;color:#e5c47d;font-size:18px;margin-top:8px}}
    .notes{{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}}
    .note{{border:1px solid #302d27;background:#10110f;border-radius:10px;padding:9px;color:#aaa39a;font-size:12px}}
    .controls{{display:flex;gap:7px;justify-content:center;margin:11px 0;flex-wrap:wrap}}
    button{{background:#171713;color:#eee;border:1px solid #51452f;padding:9px 12px;border-radius:10px;cursor:pointer}}
    #play{{background:linear-gradient(135deg,#b88935,#7b2f20);font-weight:bold}}
    .bar{{height:6px;background:#29251e;border-radius:999px;overflow:hidden}} #prog{{height:100%;width:0;background:linear-gradient(90deg,#c59b49,#9b3a22)}}
    .timeline{{display:flex;gap:6px;overflow:auto;margin-top:10px}} .timeline button{{min-width:118px;text-align:left;font-size:11px}}
    .timeline button.active{{border-color:#c59b49;color:#f0d59e}}
    </style></head><body>
    <div id="frame"><div class="fog"></div><div class="top"><span id="act" class="pill"></span><span id="count" class="pill"></span></div>
      <div class="center"><h2 id="title"></h2><p id="visual"></p><p id="narration"></p><div id="dialogue" class="quote"></div></div></div>
    <div class="controls"><button onclick="prev()">◀ Prev</button><button id="play" onclick="toggle()">▶ Play episode</button><button onclick="next()">Next ▶</button></div>
    <div class="bar"><div id="prog"></div></div>
    <div class="timeline" id="timeline"></div>
    <div class="notes"><div class="note" id="camera"></div><div class="note" id="sound"></div><div class="note" id="continuity"></div><div class="note" id="status">Playable animatic · not final MP4</div></div>
    <script>
    const scenes={scenes_json}; let i=0, playing=false, elapsed=0, timer=null;
    function render(){{
      const s=scenes[i]; document.getElementById('act').textContent=s.act; document.getElementById('count').textContent=(i+1)+' / '+scenes.length;
      document.getElementById('title').textContent=s.title; document.getElementById('visual').textContent=s.visual;
      document.getElementById('narration').textContent=s.narration; document.getElementById('dialogue').textContent=s.dialogue?('“'+s.dialogue+'”'):'';
      document.getElementById('camera').textContent='CAMERA · '+s.camera; document.getElementById('sound').textContent='SOUND · '+s.sound;
      document.getElementById('continuity').textContent='CONTINUITY · '+s.continuity; elapsed=0; document.getElementById('prog').style.width='0%';
      [...document.querySelectorAll('.timeline button')].forEach((b,n)=>b.classList.toggle('active',n===i));
    }}
    function tick(){{ if(!playing)return; const s=scenes[i]; elapsed++; document.getElementById('prog').style.width=Math.min(100,elapsed/s.duration*100)+'%';
      if(elapsed>=s.duration){{ if(i<scenes.length-1){{i++;render();}}else{{playing=false;document.getElementById('play').textContent='▶ Replay episode';clearInterval(timer);}} }} }}
    function toggle(){{ playing=!playing; document.getElementById('play').textContent=playing?'⏸ Pause episode':'▶ Play episode'; if(playing){{clearInterval(timer);timer=setInterval(tick,1000);}}else clearInterval(timer); }}
    function prev(){{i=Math.max(0,i-1);render();}} function next(){{i=Math.min(scenes.length-1,i+1);render();}}
    const tl=document.getElementById('timeline'); scenes.forEach((s,n)=>{{const b=document.createElement('button');b.textContent=s.id+' · '+s.title;b.onclick=()=>{{i=n;render();}};tl.appendChild(b);}});
    render();
    </script></body></html>
    """
    components.html(player_html, height=760, scrolling=False)

    with st.expander("Episode structure & production notes"):
        st.write(episode.synopsis)
        for s in episode.scenes:
            st.markdown(
                f'<div class="gf-scene"><h4>{html.escape(s.id)} · {html.escape(s.title)} · {s.duration}s</h4>'
                f'<div class="gf-muted">{html.escape(s.visual)}</div></div>',
                unsafe_allow_html=True,
            )

    st.subheader("Final Render Queue")
    queue_rows = [
        ("Episode structure", "Ready"),
        ("Playable animatic", "Ready"),
        ("Reference rights boundary", "Ready"),
        ("Full-motion video generation", "Not connected"),
        ("Premium voice performance", "Not connected"),
        ("Music / SFX generation", "Not connected"),
        ("Continuity render QC", "Waiting"),
        ("Final MP4", "Waiting"),
    ]
    st.table({"Stage": [x[0] for x in queue_rows], "Status": [x[1] for x in queue_rows]})

st.caption("GrimForge War Theater · original war-fantasy production workspace · GitHub/Streamlit build")
