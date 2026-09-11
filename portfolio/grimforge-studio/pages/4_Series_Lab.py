from __future__ import annotations

import json
import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from series_engine import SERIES_DEFAULT, VOICE_SCORE_FIELDS, VOICE_TRIALS, build_series_plan, rank_voice_trials

st.set_page_config(page_title="GrimForge Series Lab", page_icon="🎬", layout="wide")

st.markdown("""
<style>
.block-container{max-width:1550px;padding-top:1rem;padding-bottom:3rem}
.hero{border-radius:24px;padding:1.5rem 1.6rem;background:radial-gradient(circle at 82% 10%,rgba(214,174,89,.18),transparent 30%),linear-gradient(135deg,#0b1018,#172234 62%,#241d18);border:1px solid rgba(214,174,89,.22);color:#f7f1e7;margin-bottom:1rem}
.k{font-size:.68rem;letter-spacing:.16em;text-transform:uppercase;color:#d6ae59;font-weight:800}.t{font-size:2.4rem;font-weight:900;line-height:1.05;margin:.2rem 0 .45rem}.s{color:#c7ced8;max-width:980px;line-height:1.5}
.ep{border:1px solid rgba(140,155,180,.17);border-radius:17px;padding:.9rem 1rem;margin:.45rem 0;background:rgba(100,115,140,.035)}
.num{display:inline-grid;place-items:center;width:34px;height:34px;border-radius:50%;background:rgba(214,174,89,.12);border:1px solid rgba(214,174,89,.28);color:#d6ae59;font-weight:900;margin-right:.55rem}.voice{display:inline-block;padding:.18rem .48rem;border-radius:999px;border:1px solid rgba(105,200,190,.25);color:#65c7c1;font-size:.72rem;font-weight:750}.micro{font-size:.78rem;opacity:.65;line-height:1.42}.winner{border-left:4px solid #d6ae59}.score{font-size:1.8rem;font-weight:900;color:#d6ae59}
</style>
""", unsafe_allow_html=True)

st.markdown("""<div class="hero"><div class="k">GrimForge v0.2 · Series Lab</div><div class="t">Build one story across ten five-minute films.</div><div class="s">Plan continuity, hooks, payoffs, visual motifs and cliffhangers across a complete season—while running a six-episode narrator tournament before locking the house voice.</div></div>""", unsafe_allow_html=True)

c1,c2=st.columns([1.35,1],gap="large")
with c1:
    series_title=st.text_input("Series title",value=SERIES_DEFAULT["title"])
    premise=st.text_area("Series premise",value=SERIES_DEFAULT["premise"],height=105)
with c2:
    world=st.selectbox("World mode",["Grimdark Galaxy","Old World Dark Fantasy"],index=0)
    duration=st.slider("Episode length",4,8,5,1,format="%d min")
    st.info("House rule: every part must satisfy on its own, but the final 15–25 seconds should create a clean reason to watch the next part.")

plan=build_series_plan(series_title,premise,world,duration)

series_tab, voice_tab, quality_tab, export_tab=st.tabs(["Season Board","Voice Tournament","Quality Gate","Export"])

with series_tab:
    st.markdown("### Ten-part season board")
    for ep in plan:
        st.markdown(f'<div class="ep"><span class="num">{ep.number}</span><b>{ep.title}</b> &nbsp; <span class="voice">{ep.voice}</span><br><br><b>Thesis:</b> {ep.thesis}<br><b>Hook:</b> {ep.hook}<br><b>Visual motif:</b> {ep.visual_motif}<br><b>Payoff:</b> {ep.payoff}<br><b>Next-part bridge:</b> {ep.next_part_bridge}</div>',unsafe_allow_html=True)

with voice_tab:
    st.markdown("### Six-episode narrator tournament")
    st.caption("Episodes 1–6 deliberately use different original or properly licensed voices. Score only after listening to the finished narration in context.")
    if "gf_voice_trials" not in st.session_state:
        st.session_state.gf_voice_trials=[]
    for trial in VOICE_TRIALS:
        with st.expander(f"Episode {trial['episode']} · {trial['voice']}",expanded=trial['episode']==1):
            st.write(trial["direction"])
            cols=st.columns(4)
            scores={}
            for idx,field in enumerate(VOICE_SCORE_FIELDS):
                with cols[idx%4]:
                    scores[field]=st.slider(field.replace("_"," ").title(),0.0,10.0,7.5,0.5,key=f"v{trial['episode']}_{field}")
            note=st.text_input("Listening note",key=f"note_{trial['episode']}",placeholder="e.g. fantastic gravitas, slightly tiring over dense exposition")
            existing=[x for x in st.session_state.gf_voice_trials if x["episode"]!=trial["episode"]]
            existing.append({"episode":trial["episode"],"voice":trial["voice"],"scores":scores,"note":note})
            st.session_state.gf_voice_trials=existing
    ranked=rank_voice_trials(st.session_state.gf_voice_trials)
    st.divider()
    st.markdown("#### Live ranking")
    for rank,row in enumerate(ranked,1):
        cls="winner" if rank==1 else ""
        st.markdown(f'<div class="ep {cls}"><b>#{rank} · {row["voice"]}</b><br><span class="score">{row["weighted_score"]:.2f}</span> / 10<br><span class="micro">Episode {row["episode"]} · {row.get("note","") or "No listening note yet"}</span></div>',unsafe_allow_html=True)
    st.caption("Episode 7 should use the strongest voice or a refined hybrid direction only after the first six samples have been heard and scored.")

with quality_tab:
    st.markdown("### Five-minute episode quality gate")
    checks={
        "Hook lands by 0:20": st.checkbox("Hook lands by 0:20",value=True),
        "One clear thesis": st.checkbox("One clear thesis",value=True),
        "Canon vs interpretation labeled": st.checkbox("Canon vs interpretation labeled",value=True),
        "At least one visual mode change": st.checkbox("At least one visual mode change",value=True),
        "No static shot overstays": st.checkbox("No static shot overstays its usefulness",value=True),
        "Humor fits the scene": st.checkbox("Humor releases tension rather than derailing it",value=True),
        "Audio has breathing room": st.checkbox("Narration, score and effects have breathing room",value=True),
        "Final bridge earns Part 2": st.checkbox("Final bridge earns the next click",value=True),
    }
    passed=sum(checks.values())
    st.metric("Quality gate",f"{passed}/{len(checks)}")
    if passed==len(checks): st.success("Ready for final human watch-through.")
    else: st.warning("Hold publication until the failed checks are resolved.")

with export_tab:
    payload={
        "series":{"title":series_title,"premise":premise,"world":world,"episode_minutes":duration},
        "episodes":[ep.to_dict() for ep in plan],
        "voice_trials":rank_voice_trials(st.session_state.get("gf_voice_trials",[])),
    }
    st.download_button("Download season plan JSON",json.dumps(payload,indent=2),file_name="grimforge_season_plan.json",mime="application/json",use_container_width=True)
    st.code(json.dumps(payload["episodes"][:2],indent=2),language="json")

st.caption("GrimForge is an original production-planning tool. Reference channels inform high-level craft analysis only; do not copy creator scripts, jokes, artwork, footage or unauthorized voice likenesses.")
