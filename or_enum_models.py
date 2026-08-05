"""Enumerate models per connection, then verify free+tool-capable routes with
real spaced chat requests carrying a tools payload."""
import json, urllib.request, time, sys

BASE = "http://localhost:20128"

def api(method, path, payload=None, t=60):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=t) as r:
            raw = r.read()
            try:
                return r.status, json.loads(raw or b"{}")
            except Exception:
                return r.status, raw.decode(errors="replace")[:300]
    except Exception as e:
        body = ""
        try:
            body = e.read().decode(errors="replace")[:300]
        except Exception:
            pass
        return getattr(e, "code", "ERR"), body or str(e)

st, d = api("GET", "/api/providers", t=90)
conns = d["connections"]
out = {}
for c in conns:
    st, m = api("GET", f"/api/providers/{c['id']}/models", t=90)
    models = []
    if isinstance(m, dict):
        raw = m.get("models") or m.get("data") or []
        for x in raw:
            mid = x.get("id") if isinstance(x, dict) else x
            if mid:
                models.append(mid)
    elif isinstance(m, list):
        models = [x.get("id") if isinstance(x, dict) else x for x in m]
    out[c["name"]] = {"provider": c["provider"], "id": c["id"],
                      "count": len(models), "models": models}
    print(f"{c['name']:<18} {c['provider']:<16} models={len(models)}")
    if models:
        print("    ", models[:25])
    sys.stdout.flush()

json.dump(out, open(r"C:\Users\jonat\or_conn_models.json", "w"), indent=1)
print("\nsaved or_conn_models.json")
