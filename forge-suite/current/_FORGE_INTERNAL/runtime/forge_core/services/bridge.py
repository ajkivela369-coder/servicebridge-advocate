from __future__ import annotations
from datetime import datetime, timezone

def bridge_config():
    return {'name':'Forge Bridge','version':'0.5.2','loopback':'http://127.0.0.1:8787','mode':'local-companion','timestamp':datetime.now(timezone.utc).isoformat(),'contract':{'cloud_ui_may_detect_local_node':True,'no_cloud_required':True,'published_https_note':'If browser policy blocks direct loopback access, launch the app through Forge Launcher/local companion instead of weakening browser security.'},'endpoints':{'health':'/api/health','capabilities':'/api/capabilities','vault':'/api/vault/items','teach':'/api/teach/render','medforge':'/api/medforge/lesson','grimforge':'/api/grimforge/storyboard','learning':'/api/learning/manifest'}}
