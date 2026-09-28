# Forge Systems Lab

A parallel teaching/control app for the shared ServiceBridge Local Runtime.

It reads the **actual runtime modules** and teaches:
- Creditless network policy
- hardware detection
- local service discovery
- local OpenAI-compatible model calls
- content-addressed caching
- SQLite job queues
- local transcription
- local narration
- local ComfyUI workflows
- deterministic FFmpeg rendering

It also provides a live runtime status page and a safe policy simulator.

Run:

```bash
python -m pip install -e .
python -m pip install -r apps/forge-systems-lab/requirements.txt
streamlit run apps/forge-systems-lab/app.py
```
