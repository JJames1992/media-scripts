#!/usr/bin/env python
"""Prune opencode/big-pickle (empty-stream route) from auto-best-free combo."""
import json, urllib.request

BASE = "http://localhost:20128"
COMBO_ID = "4b0f9f14-2d42-4a46-a2e1-5073505130b2"
DROP = "opencode/big-pickle"

def api(method, path, payload=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 headers={"Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

# 1. Read current combo
st, combo = api("GET", "/api/combos")
combos = combo if isinstance(combo, list) else combo.get("combos", combo.get("data", []))
target = next(c for c in combos if c.get("id") == COMBO_ID)
models = target.get("models", [])
before = len(models)
kept = [m for m in models if m.get("model") != DROP]
dropped = before - len(kept)
print(f"before={before} after={len(kept)} dropped={dropped}")

# 2. PUT combo without the empty-stream route
st, res = api("PUT", f"/api/combos/{COMBO_ID}",
              {"name": target["name"], "strategy": target.get("strategy", "priority"),
               "models": kept})
print(f"PUT status={st}")
if st >= 400:
    print("ERR:", res)
    raise SystemExit(1)

# 3. Verify
st, combo2 = api("GET", "/api/combos")
combos2 = combo2 if isinstance(combo2, list) else combo2.get("combos", combo2.get("data", []))
t2 = next(c for c in combos2 if c.get("id") == COMBO_ID)
still = [m.get("model") for m in t2.get("models", [])]
print(f"verify: count={len(still)} big-pickle present={'opencode/big-pickle' in still}")
print("first 6:", still[:6])
