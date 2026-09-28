"""A release cannot pass on HTML markers or synthetic engine fixtures."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REQUIRED=('elias_real_conversation_document','evidence_five_files_pdf','grimforge_3d_episode','grimforge_25d_episode','grimforge_2d_episode','grimforge_generated_motion_voice_mp4','medforge_analysis_visual_export','medforge_blender_3d','learn_live_feature_coverage','windows_upgrade_preserves_vault','visual_icon_parity')
def check(path=None):
    source=Path(path) if path else ROOT/'acceptance.json'
    report=json.loads(source.read_text()) if source.exists() else {}
    checks=report.get('checks',{})
    blocked=[]
    for name in REQUIRED:
        row=checks.get(name,{})
        # A reviewer records actual workflow evidence and an artifact reference.
        if row.get('status')!='passed' or row.get('fixture_only',True) or not row.get('evidence'):
            blocked.append(name)
    return {'release':'0.5.6','ok':not blocked,'blocked':blocked,'rule':'Required workflows need real-engine evidence; fixture tests and structural checks do not count as completion.'}
if __name__=='__main__':
    result=check();print(json.dumps(result,indent=2));raise SystemExit(0 if result['ok'] else 1)
