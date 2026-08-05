#!/usr/bin/env python
"""Remove any opencode or openrouter models that cause empty choices from auto-best-free combo."""
import json, urllib.request

BASE = "http://localhost:20128"
COMBO_ID = "4b0f9f14-2d42-4a46-a2e1-5073505130b2"

def api(method, path, payload=None):
    req = urllib.request.Request(BASE + path, method=method,
                                 headers={"Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=15) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]

# Get current combo definition
st, combo_data = api("GET", "/api/combos")
if isinstance(combo_data, dict):
    combos = combo_data.get("combos", combo_data.get("data", []))
else:
    combos = combo_data
target = next(c for c in combos if c.get("id") == COMBO_ID)
models = target.get("models", [])
print("Current models count:", len(models))

# Identify models to remove: any model identifier containing 'big-pickle' or 'openrouter'
to_remove = [m for m in models if "big-pickle" in m.get("model", "").lower() or "openrouter" in m.get("model", "").lower()]
print("Models to remove:", [m.get("model") for m in to_remove])

if not to_remove:
    print("No offending models found – nothing to do.")
    exit(0)

# Filter them out
new_models = [m for m in models if m not in to_remove]
print(f"Before={len(models)} After={len(new_models)}")

# Update the combo
update_payload = {
    "id": COMBO_ID,
    "name": target["name"],
    "strategy": target.get("strategy", "priority"),
    "models": new_models
}
st, resp = api("PUT", f"/api/combos/{COMBO_ID}", update_payload)
print(f"PUT status={st}")
if st >= 400:
    print("Error from API:", resp)
    exit(1)

# Verify removal
st, updated_combo = api("GET", "/api/combos")
if isinstance(updated_combo, dict):
    combos2 = updated_combo.get("combos", updated_combo.get("data", []))
else:
    combos2 = updated_combo
t2 = next(c for c in combos2 if c.get("id") == COMBO_ID)
remaining_models = c2.get("models", [])
remaining_ids = [m.get("model") for m in remaining_models]
print("Remaining big-pickle/openrouter models:", [m for m in remaining_ids if "big-pickle" in m.lower() or "openrouter" in m.lower()])
print("All done.")