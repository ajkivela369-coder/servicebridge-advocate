from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request

APPS = {
    "Main portfolio": "https://aj-kivela-portfolio.lovable.app/",
    "SearchSignal Interview": "https://searchsignal-geisel-interview.vercel.app/",
    "SearchSignal": "https://forgesearcher.floot.app/",
    "AJ Job Fisher": "https://aj-job-fisher-a2507o.v2.appdeploy.ai/",
    "CiteGuard": "https://citeguard-06vkq0.v2.appdeploy.ai/",
    "Elias Evidence Assistant": "https://elias-evidence-assistant-simscb.v2.appdeploy.ai/",
    "GrimForge Studio": "https://grimforge-studio-xtkoo5.v2.appdeploy.ai/",
    "NeuroEval": "https://neuroeval-t6k31i.v2.appdeploy.ai/",
    "HealthQA Auditor": "https://healthqa-auditor-k719sh.v2.appdeploy.ai/",
    "PairRank": "https://pairrank-eid08f.v2.appdeploy.ai/",
    "StudyForge": "https://studyforge-zitb2u.v2.appdeploy.ai/",
    "WildTake Studio": "https://wildtake-studio-i0atj8.v2.appdeploy.ai/",
}

UA = "AJ-Portfolio-QC/1.0 (+https://github.com/ajkivela369-coder/servicebridge-advocate)"


def request(url: str, *, data: bytes | None = None, method: str | None = None):
    last: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url,
                data=data,
                method=method,
                headers={"User-Agent": UA, "Content-Type": "application/json"},
            )
            return urllib.request.urlopen(req, timeout=20)
        except Exception as exc:
            last = exc
            if attempt < 2:
                time.sleep(2 * (attempt + 1))
    assert last is not None
    raise last


def read_html(name: str, url: str) -> str:
    with request(url) as response:
        status = getattr(response, "status", None)
        ctype = response.headers.get("Content-Type", "")
        body = response.read(2_000_000).decode("utf-8", errors="replace")
    if status != 200:
        raise AssertionError(f"{name}: HTTP {status}")
    if "html" not in ctype.lower():
        raise AssertionError(f"{name}: unexpected Content-Type {ctype!r}")
    title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
    if not title or not re.sub(r"\s+", " ", title.group(1)).strip():
        raise AssertionError(f"{name}: missing title")
    if not re.search(r'<meta[^>]+name=["\']viewport["\']', body, re.I):
        raise AssertionError(f"{name}: missing viewport metadata")
    if not re.search(r'<meta[^>]+name=["\']description["\']', body, re.I):
        raise AssertionError(f"{name}: missing description metadata")
    if re.search(r"application error|internal server error|uncaught exception", body, re.I):
        raise AssertionError(f"{name}: obvious error text in HTML")

    refs = re.findall(r'<(?:script|link)[^>]+(?:src|href)=["\']([^"\']+)["\']', body, re.I)
    local_assets = []
    for ref in refs:
        absolute = urllib.parse.urljoin(url, ref)
        if urllib.parse.urlparse(absolute).netloc != urllib.parse.urlparse(url).netloc:
            continue
        if not (re.search(r"\.(?:js|css)(?:\?|$)", absolute, re.I) or "/assets/" in absolute or "/_assets/" in absolute):
            continue
        local_assets.append(absolute)
    for asset in local_assets[:6]:
        with request(asset) as response:
            if getattr(response, "status", None) != 200:
                raise AssertionError(f"{name}: asset failed {asset}")
            response.read(256)
    return body


for name, url in APPS.items():
    read_html(name, url)
    print(f"PASS {name}: {url}")

audit_body = json.dumps({"json": {"url": "https://example.com/"}}).encode()
with request("https://forgesearcher.floot.app/_api/audit", data=audit_body, method="POST") as response:
    audit_text = response.read().decode("utf-8", errors="replace")
    if getattr(response, "status", None) != 200 or "seoScore" not in audit_text or "geoScore" not in audit_text:
        raise AssertionError("SearchSignal: live audit endpoint did not return SEO/GEO scores")
print("PASS SearchSignal audit endpoint")

private_body = json.dumps({"json": {"url": "http://127.0.0.1/"}}).encode()
try:
    request("https://forgesearcher.floot.app/_api/audit", data=private_body, method="POST")
    raise AssertionError("SearchSignal: private-network target was unexpectedly accepted")
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    if exc.code != 400 or not re.search(r"private|local", body, re.I):
        raise
print("PASS SearchSignal private-network rejection")

INTERVIEW = "https://searchsignal-geisel-interview.vercel.app"

interview_audit = json.dumps({"url": "https://example.com/"}).encode()
with request(INTERVIEW + "/api/audit", data=interview_audit, method="POST") as response:
    payload = json.loads(response.read().decode("utf-8"))
    if getattr(response, "status", None) != 200:
        raise AssertionError("SearchSignal Interview: audit endpoint failed")
    if not isinstance(payload.get("scores", {}).get("seo"), int) or not isinstance(payload.get("scores", {}).get("geo"), int):
        raise AssertionError("SearchSignal Interview: audit endpoint missing SEO/GEO scores")
print("PASS SearchSignal Interview audit endpoint")

site_body = json.dumps({"url": "https://example.com/", "limit": 2}).encode()
with request(INTERVIEW + "/api/site-scan", data=site_body, method="POST") as response:
    payload = json.loads(response.read().decode("utf-8"))
    if getattr(response, "status", None) != 200 or payload.get("summary", {}).get("pagesCrawled", 0) < 1:
        raise AssertionError("SearchSignal Interview: site scan did not return a page inventory")
print("PASS SearchSignal Interview site scan")

redirect_body = json.dumps({"url": "https://example.com/"}).encode()
with request(INTERVIEW + "/api/redirect-check", data=redirect_body, method="POST") as response:
    payload = json.loads(response.read().decode("utf-8"))
    if getattr(response, "status", None) != 200 or not payload.get("chain"):
        raise AssertionError("SearchSignal Interview: redirect validator returned no chain")
print("PASS SearchSignal Interview redirect validator")

interview_private = json.dumps({"url": "http://127.0.0.1/"}).encode()
try:
    request(INTERVIEW + "/api/audit", data=interview_private, method="POST")
    raise AssertionError("SearchSignal Interview: private-network target was unexpectedly accepted")
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    if exc.code != 400 or not re.search(r"private|blocked|local", body, re.I):
        raise
print("PASS SearchSignal Interview private-network rejection")
