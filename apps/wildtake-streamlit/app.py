import streamlit as st
from dataclasses import dataclass
from pathlib import Path
import subprocess
import sys
import tempfile

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from servicebridge.local_runtime import RuntimeMode, discover_services
from servicebridge.local_runtime.workers import worker_capabilities
from local_pipeline import WildTakeBeat, render_wildtake_local

st.set_page_config(page_title="WildTake Studio", page_icon="🦘", layout="wide")

st.markdown("""
<style>
.block-container {max-width: 1500px; padding-top: 1.1rem;}
[data-testid="stSidebar"] {min-width: 300px;}
.wt-card {border:1px solid rgba(255,255,255,.12); border-radius:18px; padding:16px; background:rgba(255,255,255,.03); margin-bottom:12px;}
.wt-muted {opacity:.72;}
.wt-good {border-left:4px solid #36c276; padding-left:10px;}
.wt-warn {border-left:4px solid #e0a93b; padding-left:10px;}
</style>
""", unsafe_allow_html=True)

NARRATORS = {
    "Aussie Wildlife Commentator": "Original Australian-accented narrator: quick observational wit, cheeky irreverence, playful sports-commentary energy, escalating reactions, punchy payoff. Not an Ozzy Man imitation.",
    "Deadpan Naturalist": "Dry documentary delivery with understated jokes.",
    "Sports Desk": "Fast play-by-play with match-call structure.",
    "Chaotic Mate": "High-energy friend reacting in real time.",
    "Family Friendly": "Playful, clean, all-ages animal commentary.",
}

@dataclass
class Beat:
    timestamp: str
    description: str
    punchline: str = ""

def ffmpeg_available():
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=False, timeout=2)
        return True
    except Exception:
        return False

def provider_badge(name, connected, note):
    cls = "wt-good" if connected else "wt-warn"
    state = "Connected" if connected else "Not connected"
    st.markdown(
        f'<div class="wt-card {cls}"><b>{name}</b><br>{state}<br><span class="wt-muted">{note}</span></div>',
        unsafe_allow_html=True,
    )

if "beats" not in st.session_state:
    st.session_state.beats = [
        Beat("00:02", "Animal notices something off-camera", "Confidence enters the chat."),
        Beat("00:05", "Animal approaches", "Bold strategy."),
        Beat("00:08", "Other animal reacts", "And there goes the plan."),
        Beat("00:10", "Retreat / reversal", "Immediate tactical withdrawal."),
    ]
if "queue" not in st.session_state:
    st.session_state.queue = []
if "runtime_mode" not in st.session_state:
    st.session_state.runtime_mode = RuntimeMode.CREDITLESS.value
if "local_runtime_status" not in st.session_state:
    st.session_state.local_runtime_status = []
if "local_worker_status" not in st.session_state:
    st.session_state.local_worker_status = []
if "final_video_bytes" not in st.session_state:
    st.session_state.final_video_bytes = b""
if "final_render_meta" not in st.session_state:
    st.session_state.final_render_meta = {}

st.title("WildTake Studio")
st.caption("Original animal-commentary Shorts. Upload → analyze → script → narrate → caption → mix → export.")

with st.sidebar:
    st.subheader("Mode")
    mode = st.radio("Workflow", ["Simple", "Pro"], horizontal=True)
    st.markdown("**Runtime**")
    runtime_options = [x.value for x in RuntimeMode]
    st.session_state.runtime_mode = st.selectbox(
        "Execution policy",
        runtime_options,
        index=runtime_options.index(st.session_state.runtime_mode)
        if st.session_state.runtime_mode in runtime_options else 0,
        help="Creditless uses only local engines and blocks automatic paid/cloud fallback.",
    )
    if st.button("Scan local engines", use_container_width=True, key="wildtake_scan_local"):
        st.session_state.local_runtime_status = [x.to_dict() for x in discover_services()]
        st.session_state.local_worker_status = [x.to_dict() for x in worker_capabilities()]
    if st.session_state.runtime_mode == RuntimeMode.CREDITLESS.value:
        st.caption("Creditless: manual/local analysis + local voice/render workers only.")
    st.divider()
    st.subheader("Providers")
    local_by_id = {x["service_id"]: x for x in st.session_state.local_runtime_status}
    local_workers = {x["worker_id"]: x for x in st.session_state.local_worker_status}
    local_llm_ready = bool(local_by_id.get("llama_cpp", {}).get("healthy") or local_by_id.get("ollama", {}).get("healthy"))
    local_piper_ready = bool(local_by_id.get("piper", {}).get("healthy"))
    local_kokoro_ready = bool(local_workers.get("kokoro", {}).get("available"))
    local_tts_ready = local_kokoro_ready or local_piper_ready
    provider_badge(
        "Local vision / analysis",
        local_llm_ready,
        "llama.cpp/Ollama can become the local analysis lane when a compatible VLM is loaded.",
    )
    provider_badge(
        "Local TTS",
        local_tts_ready,
        "Local Auto tries offline Kokoro first, then a configured Piper voice. If neither works, WildTake can still render captions + silence.",
    )
    provider_badge("Render engine", ffmpeg_available(), "FFmpeg is the always-local deterministic renderer.")
    st.caption("WildTake never labels preview/demo content as a completed AI render.")

left, right = st.columns([1.08, 0.92], gap="large")

with left:
    st.subheader("1 · Source footage")
    uploaded = st.file_uploader("Upload an animal/wildlife clip", type=["mp4", "mov", "m4v", "webm"])
    if uploaded:
        st.video(uploaded)
        st.caption(f"{uploaded.name} · {uploaded.size/1024/1024:.1f} MB")
    else:
        st.info("Upload footage you own, licensed footage, or footage you have permission to use.")

    st.subheader("2 · Rights Preflight")
    rights = st.radio("What is your right to use this footage?", [
        "I own this footage", "Licensed", "Permission received", "Other / Unknown"
    ])
    credit = st.text_input("Source / attribution (optional)", placeholder="Creator, license, source URL, permission note…")
    if rights == "Other / Unknown":
        st.warning("Unknown provenance is flagged. Commentary or transformation does not itself guarantee fair use.")

    st.subheader("3 · Narrator")
    narrator = st.selectbox("Preset", list(NARRATORS.keys()))
    st.caption(NARRATORS[narrator])

    if mode == "Pro":
        c1, c2, c3 = st.columns(3)
        with c1:
            joke_density = st.slider("Joke density", 1, 10, 7)
        with c2:
            energy = st.slider("Energy", 1, 10, 8)
        with c3:
            language = st.selectbox("Language", ["Clean", "Mild", "Unfiltered"])
    else:
        joke_density, energy, language = 7, 8, "Mild"

    st.subheader("4 · Action beats")
    st.caption("Manual beats work now. Connect vision analysis later for automatic detection.")
    updated = []
    for i, beat in enumerate(st.session_state.beats):
        a, b, c = st.columns([0.16, 0.50, 0.34])
        ts = a.text_input("Time", beat.timestamp, key=f"ts_{i}", label_visibility="collapsed")
        desc = b.text_input("Action", beat.description, key=f"desc_{i}", label_visibility="collapsed")
        joke = c.text_input("Comedy angle", beat.punchline, key=f"joke_{i}", label_visibility="collapsed")
        updated.append(Beat(ts, desc, joke))
    st.session_state.beats = updated

    if st.button("＋ Add beat"):
        st.session_state.beats.append(Beat("00:00", "Describe the action", "Comedy angle"))
        st.rerun()

    st.subheader("5 · Commentary script")
    default_script = "\n".join([f"[{b.timestamp}] {b.punchline or b.description}" for b in st.session_state.beats])
    script = st.text_area("Script", value=default_script, height=220)
    st.caption("This starter does not pretend to generate AI commentary until a real model is connected.")

with right:
    st.subheader("9:16 Output")
    st.markdown("""
    <div class="wt-card">
      <div style="aspect-ratio:9/16; max-height:640px; margin:auto; border-radius:18px;
                  background:linear-gradient(180deg,#151515,#050505); display:flex;
                  align-items:center; justify-content:center; text-align:center; padding:28px;">
        <div>
          <div style="font-size:28px;font-weight:700;">WildTake Preview</div>
          <div class="wt-muted">1080 × 1920 target</div><br>
          <div class="wt-muted">Creditless final render: local narration when available, captions, and FFmpeg assembly.</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("Audio lanes")
    for lane, state in [
        ("Narration", "Local TTS ready" if local_tts_ready else "Captions + silence fallback"),
        ("Source ambience", "Preserve / duck under voice"),
        ("Music", "Optional"),
        ("SFX", "Optional"),
    ]:
        st.markdown(f'<div class="wt-card"><b>{lane}</b><br><span class="wt-muted">{state}</span></div>', unsafe_allow_html=True)

    if mode == "Pro":
        st.subheader("Pro render controls")
        aspect = st.selectbox("Aspect", ["9:16 · Shorts", "16:9 · Landscape", "1:1 · Square"])
        fps = st.selectbox("FPS", [24, 25, 30, 60], index=2)
        quality = st.selectbox("Quality", ["Highest available", "Balanced", "Fast preview"])
        bitrate = st.select_slider("Video bitrate target", options=["6 Mbps", "10 Mbps", "16 Mbps", "24 Mbps"], value="16 Mbps")
        captions = st.selectbox("Captions", ["Phrase pop", "Word highlight", "Clean subtitle", "Off"])
        loudness = st.select_slider("Narration loudness target", options=["-18 LUFS", "-16 LUFS", "-14 LUFS"], value="-16 LUFS")

    st.subheader("Quality control")
    qc = [
        ("Rights preflight", rights != "Other / Unknown"),
        ("Source clip", uploaded is not None),
        ("Narration provider", local_tts_ready),
        ("Render engine", ffmpeg_available()),
        ("Caption overflow", None),
        ("Audio clipping", None),
        ("Black frames", None),
    ]
    for name, status in qc:
        icon = "✅" if status is True else ("⚠️" if status is False else "○")
        st.write(f"{icon} {name}")

st.divider()
st.subheader("Creditless production")
st.caption(
    "This path does not call a hosted video or voice API. On a local deployment, the source stays on that machine. "
    "If local TTS is unavailable, the render continues with captions and silence."
)

render_disabled = rights == "Other / Unknown" or uploaded is None or not ffmpeg_available()
if st.button(
    "MAKE MY VIDEO · LOCAL",
    type="primary",
    use_container_width=True,
    disabled=render_disabled,
):
    st.session_state.final_video_bytes = b""
    st.session_state.final_render_meta = {}
    beats_for_render = [
        WildTakeBeat(
            timestamp=b.timestamp,
            text=b.punchline or b.description,
        )
        for b in st.session_state.beats
    ]
    try:
        with tempfile.TemporaryDirectory(prefix="wildtake-creditless-") as tmp:
            result = render_wildtake_local(
                uploaded.getvalue(),
                uploaded.name,
                beats=beats_for_render,
                narration_text=script,
                output_dir=tmp,
                use_local_tts=True,
                fps=int(fps if mode == "Pro" else 30),
                width=1080,
                height=1920,
            )
            final_path = Path(result["output_path"])
            st.session_state.final_video_bytes = final_path.read_bytes()
            st.session_state.final_render_meta = result

        narration_state = (
            f'local {result["tts"]["provider"]}'
            if result.get("tts")
            else "captions + silence fallback"
        )
        st.session_state.queue = [
            ("Rights Preflight", "passed"),
            ("Action beats", "manual/local"),
            ("Commentary", "script locked"),
            ("Narration", narration_state),
            ("Captions", f'{result["caption_count"]} local cue(s)'),
            ("Render", "local FFmpeg complete"),
            ("Cloud credits", "0"),
        ]
        st.success("Local WildTake MP4 rendered.")
    except Exception as exc:
        st.session_state.queue = [("Local render", f"failed — {type(exc).__name__}: {exc}")]
        st.error(f"Could not finish the local render: {exc}")

if not ffmpeg_available():
    st.warning("Install local FFmpeg to enable the no-credit final MP4 renderer.")

if st.session_state.final_video_bytes:
    st.video(st.session_state.final_video_bytes)
    st.download_button(
        "⬇ Download WildTake MP4",
        data=st.session_state.final_video_bytes,
        file_name="wildtake-creditless.mp4",
        mime="video/mp4",
        use_container_width=True,
    )
    with st.expander("Local render details"):
        st.json(st.session_state.final_render_meta)

if st.session_state.queue:
    for step, state in st.session_state.queue:
        st.write(f"**{step}** — {state}")
else:
    st.caption("Nothing rendered yet.")

st.divider()
st.caption(
    "WildTake Studio is an original production tool. The Aussie Wildlife Commentator preset describes a broad accent/comedy style only; "
    "it does not imitate or reproduce Ozzy Man Reviews / Ethan Marrell's voice, persona, scripts, branding, or catchphrases."
)
