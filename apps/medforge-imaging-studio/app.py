import base64
import io
import json
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from PIL import Image

from med_io import load_medical_image_bytes
from med_export import build_render_bundle
from med_masks import load_mask_upload, mask_alignment_note, mask_mpr
from med_volume import (
    build_dicom_volume,
    downsample_volume,
    expand_dicom_blobs,
    inspect_dicom_series,
    mpr_slices,
    window_to_pil,
)
from med_segmentation import (
    SEGMENTATION_ENGINES,
    monai_label_job_spec,
    percentile_mask,
    summarize_mask,
    totalsegmentator_job_spec,
)
from med_engine import (
    ANALYSIS_ENGINES,
    EVIDENCE_LANES,
    MECHANISM_TYPES,
    ImageLabel,
    build_mechanism_steps,
    build_medical_vlm_prompt,
    build_render_manifest,
    label_from_dict,
    mechanism_step_from_dict,
)

st.set_page_config(
    page_title="MedForge Imaging Studio",
    page_icon="🩻",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
:root { --med:#58a9b8; --gold:#c79a43; --ink:#071012; }
.block-container {max-width:1500px;padding-top:1rem;padding-bottom:4rem}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 88% 0%, rgba(88,169,184,.17), transparent 28%),
    radial-gradient(circle at 4% 5%, rgba(199,154,67,.11), transparent 22%),
    #071012;
}
[data-testid="stSidebar"] {background:#0a1416;border-right:1px solid #263438}
.mf-eyebrow {font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;font-weight:800;color:#88a4a8}
.mf-title {font-family:Georgia,serif;font-size:2.0rem;font-weight:800;line-height:1.05;margin:0}
.mf-card {border:1px solid #294047;background:rgba(10,22,25,.93);border-radius:18px;padding:15px;margin:9px 0}
.mf-muted {color:#9eb0b3;font-size:.85rem}
.mf-badge {display:inline-block;border:1px solid #315963;background:#0c252b;color:#a9e1e9;padding:5px 9px;border-radius:999px;font-size:.72rem;margin:2px}
.mf-warn {display:inline-block;border:1px solid #66532e;background:#211b0e;color:#e1c278;padding:5px 9px;border-radius:999px;font-size:.72rem;margin:2px}
.mf-orb {
 position:fixed;right:24px;bottom:22px;z-index:9999;width:58px;height:58px;border-radius:50%;
 display:flex;align-items:center;justify-content:center;
 background:radial-gradient(circle at 35% 30%,#7ed5df,#225561 48%,#1a3439 76%,#061013);
 border:1px solid #68b3c2;box-shadow:0 0 0 5px rgba(88,169,184,.08),0 12px 35px #000b;
 color:#e6fbff;font-weight:900;font-size:10px;letter-spacing:.05em;pointer-events:none
}
</style>
<div class="mf-orb">MED<br>FORGE</div>
""",
    unsafe_allow_html=True,
)


def init(name, value):
    if name not in st.session_state:
        st.session_state[name] = value


for key, value in {
    "project_title": "Medical Imaging Mechanism Study",
    "source_name": "",
    "source_data_uri": "",
    "source_mime": "",
    "source_modality": "Unknown / image",
    "source_region": "",
    "labels": [],
    "mechanism_steps": [],
    "mechanism_type": "Dynamic / positional narrowing",
    "mechanism_motion": "",
    "mechanism_structures": "",
    "mechanism_hypothesis": "",
    "analysis_engine": "Manual / source-faithful",
    "analysis_question": "",
    "rights_note": "User-provided / owned, permitted, or otherwise authorized for review",
    "strip_phi": True,
    "dicom_blobs": [],
    "dicom_series_infos": [],
    "selected_series_uid": "",
    "volume_study": None,
    "imported_masks": [],
    "selected_mask_name": "",
}.items():
    init(key, value)


def pil_to_data_uri(image: Image.Image, fmt="PNG"):
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/{fmt.lower()};base64,{encoded}"


def load_source(uploaded):
    if uploaded is None:
        return
    try:
        loaded = load_medical_image_bytes(uploaded.getvalue(), uploaded.name)
    except Exception as exc:
        st.error(f"Could not read this medical image: {exc}")
        return
    st.session_state.source_data_uri = pil_to_data_uri(loaded.image)
    st.session_state.source_mime = "image/png"
    st.session_state.source_name = loaded.source_name
    if loaded.modality:
        st.session_state.source_modality = loaded.modality


def project_payload():
    return {
        "schema_version": 1,
        "app": "MedForge Imaging Studio",
        "title": st.session_state.project_title,
        "source": {
            "name": st.session_state.source_name,
            "data_uri": st.session_state.source_data_uri,
            "mime": st.session_state.source_mime,
            "modality": st.session_state.source_modality,
            "region": st.session_state.source_region,
            "rights_note": st.session_state.rights_note,
            "phi_stripped_from_export_metadata": bool(st.session_state.strip_phi),
        },
        "labels": [x.to_dict() for x in st.session_state.labels],
        "mechanism": {
            "type": st.session_state.mechanism_type,
            "motion": st.session_state.mechanism_motion,
            "structures": st.session_state.mechanism_structures,
            "hypothesis": st.session_state.mechanism_hypothesis,
            "steps": [x.to_dict() for x in st.session_state.mechanism_steps],
        },
        "analysis": {
            "engine": st.session_state.analysis_engine,
            "question": st.session_state.analysis_question,
        },
        "volume": st.session_state.volume_study.safe_summary() if st.session_state.volume_study else None,
        "imported_masks": [
            m.safe_summary() for m in st.session_state.imported_masks
        ],
    }


def load_project(data):
    st.session_state.project_title = data.get("title", st.session_state.project_title)
    source = data.get("source", {})
    st.session_state.source_name = source.get("name", "")
    st.session_state.source_data_uri = source.get("data_uri", "")
    st.session_state.source_mime = source.get("mime", "")
    st.session_state.source_modality = source.get("modality", "Unknown / image")
    st.session_state.source_region = source.get("region", "")
    st.session_state.rights_note = source.get("rights_note", st.session_state.rights_note)
    st.session_state.strip_phi = bool(source.get("phi_stripped_from_export_metadata", True))
    st.session_state.labels = [label_from_dict(x) for x in data.get("labels", [])]
    mechanism = data.get("mechanism", {})
    st.session_state.mechanism_type = mechanism.get("type", st.session_state.mechanism_type)
    st.session_state.mechanism_motion = mechanism.get("motion", "")
    st.session_state.mechanism_structures = mechanism.get("structures", "")
    st.session_state.mechanism_hypothesis = mechanism.get("hypothesis", "")
    st.session_state.mechanism_steps = [mechanism_step_from_dict(x) for x in mechanism.get("steps", [])]
    analysis = data.get("analysis", {})
    st.session_state.analysis_engine = analysis.get("engine", st.session_state.analysis_engine)
    st.session_state.analysis_question = analysis.get("question", "")


with st.sidebar:
    st.markdown('<div class="mf-eyebrow">SOURCE-FAITHFUL MEDICAL VISUALIZATION</div><div class="mf-title">MedForge</div>', unsafe_allow_html=True)
    st.caption("Imaging Studio · forked from the Forge engine")
    st.session_state.project_title = st.text_input("Project title", st.session_state.project_title)

    st.markdown("**Project file**")
    st.download_button(
        "⬇ Export MedForge project",
        data=json.dumps(project_payload(), indent=2),
        file_name="medforge-project.json",
        mime="application/json",
        use_container_width=True,
    )
    imported = st.file_uploader("Import project JSON", type=["json"], key="project_import", label_visibility="collapsed")
    if imported is not None and st.button("Load project", use_container_width=True):
        try:
            load_project(json.load(imported))
            st.success("Project loaded.")
            st.rerun()
        except Exception as exc:
            st.error(f"Could not load project: {exc}")

    st.divider()
    st.markdown("**Analysis engines**")
    for name, meta in ANALYSIS_ENGINES.items():
        status = "CONNECTED" if meta["status"] == "connected" else "PLANNED"
        st.caption(f"{name} · {status}")
    st.divider()
    st.checkbox("Strip patient-identifying metadata from exports", key="strip_phi")
    st.caption("MedForge stores only the rendered source image in the project file; raw DICOM headers are not exported.")
    st.text_area("Rights / source note", key="rights_note", height=90)


left, right = st.columns([0.68, 0.32])
with left:
    st.markdown('<div class="mf-eyebrow">Evidence before interpretation</div>', unsafe_allow_html=True)
    st.title("MedForge Imaging Studio")
    st.caption("Source image → observations → labels / measurements → possible mechanisms → illustrative reconstruction")
with right:
    st.markdown(
        '<div class="mf-card"><span class="mf-badge">SOURCE LOCK</span>'
        '<span class="mf-badge">EVIDENCE LANES</span><span class="mf-warn">NOT A DIAGNOSTIC DEVICE</span>'
        '<div class="mf-muted" style="margin-top:8px">Reconstruction must stay visually distinct from the original image.</div></div>',
        unsafe_allow_html=True,
    )

st.info(
    "MedForge is designed for evidence review, education, and mechanism visualization. "
    "It should not convert a single image into a definitive diagnosis or proof of causation."
)

tabs = st.tabs([
    "1 · Source",
    "2 · DICOM Study",
    "3 · MPR & 3D",
    "4 · Label & Observe",
    "5 · Image Understanding",
    "6 · Mechanism Synthesizer",
    "7 · Animatic",
    "8 · Export",
])

with tabs[0]:
    st.subheader("Source-locked medical image")
    uploaded = st.file_uploader(
        "Upload PNG, JPG/JPEG, WebP, or a single DICOM image",
        type=["png", "jpg", "jpeg", "webp", "dcm"],
        key="medical_source",
    )
    if uploaded is not None:
        load_source(uploaded)

    c1, c2 = st.columns(2)
    with c1:
        st.session_state.source_modality = st.text_input("Modality / source type", st.session_state.source_modality, placeholder="MRI, CT, X-ray, ultrasound, DMX, photo...")
    with c2:
        st.session_state.source_region = st.text_input("Region / anatomy", st.session_state.source_region, placeholder="Cervical spine, shoulder girdle, chest wall...")

    if st.session_state.source_data_uri:
        st.image(st.session_state.source_data_uri, caption=st.session_state.source_name or "Source image", use_container_width=True)
        st.success("Source is locked. Labels and reconstructions can be layered over it without changing the original pixels.")
    else:
        st.warning("Upload an image to begin.")

with tabs[1]:
    st.subheader("DICOM study / series loader")
    st.caption(
        "Upload multiple DICOM instances or a ZIP containing a study. "
        "MedForge groups series using SeriesInstanceUID but does not export raw DICOM headers."
    )
    study_uploads = st.file_uploader(
        "DICOM instances or ZIP",
        type=["dcm", "dicom", "zip"],
        accept_multiple_files=True,
        key="dicom_study_upload",
    )
    if study_uploads and st.button("Inspect DICOM study", type="primary", key="inspect_dicom_study"):
        try:
            raw_blobs = [(u.name, u.getvalue()) for u in study_uploads]
            st.session_state.dicom_blobs = expand_dicom_blobs(raw_blobs)
            infos = inspect_dicom_series(st.session_state.dicom_blobs)
            st.session_state.dicom_series_infos = [x.to_dict() for x in infos]
            if infos:
                st.session_state.selected_series_uid = infos[0].series_uid
                st.success(f"Found {len(infos)} DICOM series across {len(st.session_state.dicom_blobs)} files.")
            else:
                st.warning("No readable DICOM series were found.")
        except Exception as exc:
            st.error(f"Could not inspect this study: {exc}")

    infos = st.session_state.dicom_series_infos
    if infos:
        options = [x["series_uid"] for x in infos]
        selected = st.selectbox(
            "Series",
            options,
            index=options.index(st.session_state.selected_series_uid)
            if st.session_state.selected_series_uid in options else 0,
            format_func=lambda uid: next(
                (
                    f'{x["modality"]} · {x["description"] or "Unnamed series"} · '
                    f'{x["instance_count"]} instance(s)'
                )
                for x in infos if x["series_uid"] == uid
            ),
        )
        st.session_state.selected_series_uid = selected
        st.dataframe(
            [
                {
                    "Modality": x["modality"],
                    "Description": x["description"],
                    "Instances": x["instance_count"],
                    "Rows": x["rows"],
                    "Columns": x["columns"],
                }
                for x in infos
            ],
            use_container_width=True,
            hide_index=True,
        )

        if st.button("Build source-locked volume", type="primary", key="build_dicom_volume"):
            try:
                study = build_dicom_volume(st.session_state.dicom_blobs, selected)
                st.session_state.volume_study = study
                st.session_state.source_modality = study.modality
                st.session_state.source_name = (
                    f'DICOM series · {study.description}' if study.description else "DICOM series"
                )
                mid = study.volume.shape[0] // 2
                st.session_state.source_data_uri = pil_to_data_uri(window_to_pil(study.volume[mid]))
                st.session_state.source_mime = "image/png"
                st.success(
                    f"Volume built: {study.shape[0]} × {study.shape[1]} × {study.shape[2]} voxels. "
                    "The raw DICOM Dataset objects are not included in project export."
                )
            except Exception as exc:
                st.error(f"Could not assemble this DICOM series: {exc}")

    if st.session_state.volume_study:
        st.markdown("**Current volume**")
        st.json(st.session_state.volume_study.safe_summary())
        if st.session_state.volume_study.decode_warnings:
            with st.expander("Decode warnings"):
                for warning in st.session_state.volume_study.decode_warnings:
                    st.write(warning)


with tabs[2]:
    st.subheader("Multiplanar reconstruction + 3D volume preview")
    study = st.session_state.volume_study
    if study is None:
        st.info("Build a DICOM volume in the DICOM Study tab first.")
    else:
        volume = study.volume
        zc, yc, xc = volume.shape[0] // 2, volume.shape[1] // 2, volume.shape[2] // 2
        s1, s2, s3 = st.columns(3)
        z = s1.slider("Axial slice (Z)", 0, volume.shape[0] - 1, zc)
        y = s2.slider("Coronal position (Y)", 0, volume.shape[1] - 1, yc)
        x = s3.slider("Sagittal position (X)", 0, volume.shape[2] - 1, xc)

        axial, coronal, sagittal = mpr_slices(volume, z, y, x)
        v1, v2, v3 = st.columns(3)
        v1.image(window_to_pil(axial), caption=f"Axial · Z {z}", use_container_width=True)
        v2.image(window_to_pil(coronal), caption=f"Coronal · Y {y}", use_container_width=True)
        v3.image(window_to_pil(sagittal), caption=f"Sagittal · X {x}", use_container_width=True)

        st.caption(
            "These views are reconstructed from the same source-locked voxel volume. "
            "They are display reformats, not new imaging acquisitions."
        )

        st.markdown("**3D intensity preview**")
        st.caption(
            "This is a downsampled voxel-intensity visualization for orientation and software testing—not anatomy segmentation."
        )
        preview = downsample_volume(volume, max_axis=42)
        finite = preview[np.isfinite(preview)]
        if finite.size:
            lo, hi = np.percentile(finite, (65, 99.5))
            zz, yy, xx = np.mgrid[
                0:preview.shape[0],
                0:preview.shape[1],
                0:preview.shape[2],
            ]
            fig = go.Figure(
                data=go.Volume(
                    x=xx.flatten(),
                    y=yy.flatten(),
                    z=zz.flatten(),
                    value=preview.flatten(),
                    isomin=float(lo),
                    isomax=float(hi),
                    opacity=0.08,
                    surface_count=12,
                )
            )
            fig.update_layout(
                height=620,
                margin=dict(l=0, r=0, t=30, b=0),
                scene=dict(aspectmode="data"),
            )
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Segmentation pipeline test**")
        percentile = st.slider("Exploratory high-intensity percentile", 50, 99, 85)
        mask = percentile_mask(volume, percentile)
        mask_summary = summarize_mask(mask)
        m1, m2 = st.columns([0.45, 0.55])
        m1.image(
            Image.fromarray((mask[z].astype(np.uint8) * 255)).convert("RGB"),
            caption="Exploratory mask · axial",
            use_container_width=True,
        )
        m2.json(mask_summary.to_dict())
        st.warning(
            "The threshold mask has no anatomical or diagnostic meaning. It only proves that a 3D mask can pass "
            "through the MedForge viewer/render pipeline."
        )

        with st.expander("Planned anatomy segmentation adapters"):
            st.json({
                "engines": SEGMENTATION_ENGINES,
                "TotalSegmentator job contract": totalsegmentator_job_spec(),
                "MONAI Label job contract": monai_label_job_spec(),
            })

        st.markdown("**Import reviewed/generated anatomy masks**")
        st.caption(
            "Bring back .nii/.nii.gz masks—or the ZIP produced by the free TotalSegmentator Colab worker. "
            "MedForge keeps these as DERIVED segmentation data, separate from the source scan."
        )
        mask_upload = st.file_uploader(
            "NIfTI mask or segmentation ZIP",
            type=["nii", "gz", "zip"],
            key="segmentation_mask_upload",
            help="For .nii.gz, select the file even if your browser labels it as .gz.",
        )
        if mask_upload is not None and st.button("Import segmentation masks", key="import_masks"):
            try:
                loaded_masks = load_mask_upload(
                    mask_upload.getvalue(),
                    mask_upload.name,
                    provenance="Imported segmentation output",
                )
                st.session_state.imported_masks = loaded_masks
                st.session_state.selected_mask_name = loaded_masks[0].name if loaded_masks else ""
                st.success(f"Imported {len(loaded_masks)} mask volume(s).")
            except Exception as exc:
                st.error(f"Could not import masks: {exc}")

        if st.session_state.imported_masks:
            names = [m.name for m in st.session_state.imported_masks]
            selected_mask_name = st.selectbox(
                "Segmentation mask",
                names,
                index=names.index(st.session_state.selected_mask_name)
                if st.session_state.selected_mask_name in names else 0,
                key="selected_mask_control",
            )
            st.session_state.selected_mask_name = selected_mask_name
            selected_mask = next(m for m in st.session_state.imported_masks if m.name == selected_mask_name)
            st.json(selected_mask.safe_summary())

            mz, my, mx = [s // 2 for s in selected_mask.shape]
            ma, mc, ms = mask_mpr(selected_mask.data, mz, my, mx)
            q1, q2, q3 = st.columns(3)
            q1.image(Image.fromarray((ma.astype(np.uint8) * 255)).convert("RGB"), caption="Mask axial", use_container_width=True)
            q2.image(Image.fromarray((mc.astype(np.uint8) * 255)).convert("RGB"), caption="Mask coronal", use_container_width=True)
            q3.image(Image.fromarray((ms.astype(np.uint8) * 255)).convert("RGB"), caption="Mask sagittal", use_container_width=True)

            alignment = mask_alignment_note(
                selected_mask,
                study.volume.shape if study is not None else None,
            )
            st.json(alignment)
            st.warning(
                "MedForge does not overlay an imported NIfTI mask on the DICOM source until spatial affine/orientation "
                "validation is implemented. Matching array dimensions alone are not enough to prove alignment."
            )

            mask_preview = downsample_volume(selected_mask.data.astype(np.float32), max_axis=42)
            zz2, yy2, xx2 = np.mgrid[
                0:mask_preview.shape[0],
                0:mask_preview.shape[1],
                0:mask_preview.shape[2],
            ]
            fig_mask = go.Figure(
                data=go.Isosurface(
                    x=xx2.flatten(),
                    y=yy2.flatten(),
                    z=zz2.flatten(),
                    value=mask_preview.flatten(),
                    isomin=0.5,
                    isomax=1.0,
                    surface_count=1,
                    caps=dict(x_show=False, y_show=False, z_show=False),
                )
            )
            fig_mask.update_layout(
                height=560,
                margin=dict(l=0, r=0, t=30, b=0),
                scene=dict(aspectmode="data"),
            )
            st.plotly_chart(fig_mask, use_container_width=True)
            st.caption(
                "This 3D surface is generated from the imported mask. Its anatomical label still depends on the "
                "segmentation source and human review; MedForge does not promote the filename into a diagnosis."
            )


with tabs[3]:
    st.subheader("Evidence lanes and labels")
    st.caption("Every note is assigned to a lane so observation, measurement, and hypothesis do not blur together.")

    lane = st.selectbox("Evidence lane", list(EVIDENCE_LANES.keys()))
    name = st.text_input("Label / structure", placeholder="C1 lateral mass, jugular vein, clavicle, scapula...")
    note = st.text_area("What should this label say?", placeholder="Describe what is visible or what the cited record says.")
    confidence = st.selectbox("Confidence / support", ["Unspecified", "Directly visible", "Measured", "Record-backed", "Hypothesis only"])
    p1, p2 = st.columns(2)
    x = p1.slider("Horizontal position", 0, 100, 50)
    y = p2.slider("Vertical position", 0, 100, 50)
    source_ref = st.text_input("Source citation / record note", placeholder="Radiology report p. 3, operative note, image slice, etc.")

    if st.button("＋ Add label", type="primary"):
        if not name.strip():
            st.error("Add a label or structure name first.")
        else:
            label_id = f"L{len(st.session_state.labels)+1:02d}"
            st.session_state.labels.append(
                ImageLabel(
                    id=label_id,
                    name=name.strip(),
                    lane=lane,
                    note=note.strip(),
                    x=x,
                    y=y,
                    confidence=confidence,
                    source_ref=source_ref.strip(),
                )
            )
            st.success(f"Added {label_id}.")

    if st.session_state.source_data_uri and st.session_state.labels:
        labels_json = json.dumps([x.to_dict() for x in st.session_state.labels])
        src_json = json.dumps(st.session_state.source_data_uri)
        viewer = f"""
        <html><head><style>
        body{{margin:0;background:#071012;color:white;font-family:Arial}}
        #wrap{{position:relative;width:100%;aspect-ratio:16/10;overflow:hidden;border:1px solid #315963;border-radius:15px;background:#020607}}
        #img{{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}}
        .pin{{position:absolute;transform:translate(-50%,-50%);width:28px;height:28px;border-radius:50%;border:2px solid white;background:#0c5664dd;
          display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;box-shadow:0 3px 12px #000}}
        .tip{{position:absolute;min-width:170px;max-width:280px;background:#071012ee;border:1px solid #315963;border-radius:10px;padding:8px 10px;font-size:12px;line-height:1.35}}
        .lane{{color:#9edce5;font-size:10px;text-transform:uppercase;letter-spacing:.08em}}
        </style></head><body><div id="wrap"><img id="img"></div>
        <script>
        const src={src_json}; const labels={labels_json}; const w=document.getElementById('wrap');
        document.getElementById('img').src=src;
        labels.forEach((l,idx)=>{{
          const p=document.createElement('div'); p.className='pin'; p.style.left=l.x+'%'; p.style.top=l.y+'%'; p.textContent=idx+1; w.appendChild(p);
          const t=document.createElement('div'); t.className='tip'; t.style.left=Math.min(72,l.x+3)+'%'; t.style.top=Math.min(82,l.y+3)+'%';
          t.innerHTML='<div class="lane">'+l.lane+'</div><b>'+l.name+'</b><br>'+ (l.note||'') +'<br><small>'+l.confidence+'</small>'; w.appendChild(t);
        }});
        </script></body></html>
        """
        components.html(viewer, height=650, scrolling=False)

    if st.session_state.labels:
        st.markdown("**Current labels**")
        for idx, item in enumerate(st.session_state.labels):
            with st.expander(f"{item.id} · {item.name} · {item.lane}"):
                st.write(item.note or "No note.")
                st.caption(f"Support: {item.confidence} · Source: {item.source_ref or 'not entered'}")
                if st.button("Remove", key=f"remove_{item.id}"):
                    st.session_state.labels.pop(idx)
                    st.rerun()

with tabs[4]:
    st.subheader("Image understanding")
    engine_names = list(ANALYSIS_ENGINES.keys())
    st.session_state.analysis_engine = st.selectbox(
        "Analysis path",
        engine_names,
        index=engine_names.index(st.session_state.analysis_engine) if st.session_state.analysis_engine in engine_names else 0,
    )
    meta = ANALYSIS_ENGINES[st.session_state.analysis_engine]
    st.markdown(f"**{meta['role']}**")
    st.caption(meta["notes"])

    st.session_state.analysis_question = st.text_area(
        "Question for the image-review assistant",
        st.session_state.analysis_question,
        placeholder="What structures are visible? What would need to be measured to assess narrowing? What imaging limitations matter?",
    )
    prompt = build_medical_vlm_prompt(
        st.session_state.source_modality,
        st.session_state.source_region,
        st.session_state.analysis_question,
    )
    st.text_area("Provider-neutral medical VLM prompt", prompt, height=280)
    st.download_button(
        "⬇ Export image-analysis prompt",
        data=prompt,
        file_name="medforge-image-analysis-prompt.txt",
        mime="text/plain",
    )
    if st.session_state.analysis_engine != "Manual / source-faithful":
        st.warning("This analysis engine is architected but not connected to a live inference endpoint in this build yet.")

with tabs[5]:
    st.subheader("Potential injury / pathology mechanism")
    st.caption("This creates an illustrative hypothesis sequence. It does not change an observation into a proven mechanism.")
    st.session_state.mechanism_structures = st.text_input(
        "Structures involved",
        st.session_state.mechanism_structures,
        placeholder="C1, C2, jugular vein, vagus nerve, scapula, brachial plexus...",
    )
    st.session_state.mechanism_type = st.selectbox(
        "Mechanism family",
        MECHANISM_TYPES,
        index=MECHANISM_TYPES.index(st.session_state.mechanism_type) if st.session_state.mechanism_type in MECHANISM_TYPES else 0,
    )
    st.session_state.mechanism_motion = st.text_area(
        "Proposed motion / loading condition",
        st.session_state.mechanism_motion,
        placeholder="Rotation, extension, downward traction, scapular depression, impact vector...",
    )
    st.session_state.mechanism_hypothesis = st.text_area(
        "Potential effect to illustrate",
        st.session_state.mechanism_hypothesis,
        placeholder="Possible dynamic narrowing, traction on a nerve, altered joint relationship, tissue compression...",
    )

    if st.button("Build mechanism storyboard", type="primary"):
        st.session_state.mechanism_steps = build_mechanism_steps(
            st.session_state.source_region,
            st.session_state.mechanism_structures,
            st.session_state.mechanism_type,
            st.session_state.mechanism_motion,
            st.session_state.mechanism_hypothesis,
            st.session_state.source_name,
        )
        st.success("Mechanism storyboard created.")

    for step in st.session_state.mechanism_steps:
        with st.expander(f"{step.id} · {step.title} · {step.epistemic_status}"):
            st.write(step.narration)
            st.caption(step.visual)

with tabs[6]:
    st.subheader("Playable mechanism animatic")
    if not st.session_state.mechanism_steps:
        st.info("Build a mechanism storyboard first.")
    else:
        steps_json = json.dumps([x.to_dict() for x in st.session_state.mechanism_steps])
        src_json = json.dumps(st.session_state.source_data_uri)
        animatic = f"""
        <html><head><style>
        body{{margin:0;background:#071012;color:#edf7f8;font-family:Arial}}
        #frame{{position:relative;aspect-ratio:16/9;border:1px solid #315963;border-radius:16px;overflow:hidden;background:#030708}}
        #source{{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;opacity:.72;transition:transform 1.2s ease,opacity .6s ease}}
        .shade{{position:absolute;inset:0;background:linear-gradient(180deg,#00101555,#00101522 45%,#001015bb)}}
        .top{{position:absolute;top:14px;left:14px;right:14px;display:flex;justify-content:space-between}}
        .pill{{background:#071012dd;border:1px solid #4b7e88;color:#b8e8ef;border-radius:999px;padding:6px 9px;font-size:11px}}
        .center{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:8%;text-align:center}}
        h2{{font-family:Georgia,serif;font-size:36px;margin:0 0 8px}} p{{max-width:900px;line-height:1.5}}
        .status{{color:#f0d28b;font-size:13px;font-weight:bold;letter-spacing:.08em}}
        .controls{{display:flex;justify-content:center;gap:8px;margin:10px}}
        button{{background:#0d2024;border:1px solid #315963;color:white;border-radius:9px;padding:9px 12px;cursor:pointer}}
        </style></head><body>
        <div id="frame"><img id="source"><div class="shade"></div><div class="top"><span class="pill">ILLUSTRATIVE RECONSTRUCTION</span><span id="count" class="pill"></span></div>
        <div class="center"><div id="status" class="status"></div><h2 id="title"></h2><p id="narration"></p><p id="visual"></p></div></div>
        <div class="controls"><button onclick="prev()">◀ Prev</button><button onclick="toggle()" id="play">▶ Play</button><button onclick="next()">Next ▶</button></div>
        <script>
        const steps={steps_json}; const source={src_json}; let i=0,playing=false,timer=null;
        const img=document.getElementById('source'); if(source) img.src=source;
        function render(){{
          const s=steps[i]; document.getElementById('count').textContent=(i+1)+' / '+steps.length;
          document.getElementById('status').textContent=s.epistemic_status;
          document.getElementById('title').textContent=s.title; document.getElementById('narration').textContent=s.narration;
          document.getElementById('visual').textContent=s.visual;
          img.style.transform='scale('+(1 + Math.min(.16,i*.025))+')';
          img.style.opacity=(i===0||i===steps.length-1)?'.88':'.58';
          if('speechSynthesis' in window && playing){{speechSynthesis.cancel(); const u=new SpeechSynthesisUtterance(s.narration);u.rate=.92;speechSynthesis.speak(u);}}
        }}
        function next(){{i=Math.min(steps.length-1,i+1);render()}} function prev(){{i=Math.max(0,i-1);render()}}
        function toggle(){{playing=!playing;document.getElementById('play').textContent=playing?'⏸ Pause':'▶ Play';clearInterval(timer);
          if(playing){{render();timer=setInterval(()=>{{if(i<steps.length-1){{i++;render()}}else{{playing=false;clearInterval(timer);document.getElementById('play').textContent='▶ Replay'}}}},8000)}}else if('speechSynthesis' in window) speechSynthesis.cancel();
        }} render();
        </script></body></html>
        """
        components.html(animatic, height=700, scrolling=False)
        st.caption("This preview animates the explanation and source framing. A later renderer can replace hypothetical steps with dedicated anatomy illustrations or 3D scenes.")

with tabs[7]:
    st.subheader("Evidence-aware export")
    manifest = build_render_manifest(
        st.session_state.project_title,
        st.session_state.source_name,
        st.session_state.labels,
        st.session_state.mechanism_steps,
    )
    manifest["volume_summary"] = (
        st.session_state.volume_study.safe_summary() if st.session_state.volume_study else None
    )
    manifest["segmentation_adapters"] = {
        "TotalSegmentator": totalsegmentator_job_spec(),
        "MONAI Label": monai_label_job_spec(),
    }
    manifest["imported_masks"] = [
        m.safe_summary() for m in st.session_state.imported_masks
    ]
    st.download_button(
        "⬇ Download mechanism render manifest",
        data=json.dumps(manifest, indent=2),
        file_name="medforge-mechanism-render-manifest.json",
        mime="application/json",
        use_container_width=True,
    )

    st.markdown("**Forge handoff bundle**")
    include_preview = st.checkbox(
        "Include rendered source preview in bundle",
        value=False,
        help=(
            "Off by default for privacy. Raw DICOM is never added. "
            "A rendered preview may still contain burned-in identifiers, so review it before sharing."
        ),
        key="bundle_include_preview",
    )
    bundle_bytes = build_render_bundle(
        manifest=manifest,
        masks=st.session_state.imported_masks,
        source_preview_data_uri=st.session_state.source_data_uri,
        include_source_preview=include_preview,
    )
    st.download_button(
        "⬇ Download MedForge → Forge render bundle",
        data=bundle_bytes,
        file_name="medforge-forge-render-bundle.zip",
        mime="application/zip",
        use_container_width=True,
    )
    st.caption(
        "The bundle carries the render manifest and derived NIfTI masks with their affine geometry. "
        "It never contains raw DICOM files or DICOM headers."
    )
    st.json({
        "stage": manifest["stage"],
        "source": manifest["source_name"],
        "label_count": len(manifest["labels"]),
        "mechanism_step_count": len(manifest["mechanism_steps"]),
        "render_rules": manifest["render_rules"],
    })
    st.markdown(
        '<div class="mf-card"><b>Next renderer contract</b><br>'
        '<span class="mf-muted">Original source remains unchanged. Any synthesized anatomy or motion must be visually identified as an illustrative reconstruction. '
        'Every conclusion should remain traceable to its evidence lane and source note.</span></div>',
        unsafe_allow_html=True,
    )

st.caption("MedForge Imaging Studio · source-faithful evidence visualization · Forge-derived prototype")
