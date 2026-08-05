"""Create/replace the `auto-best-free` combo from the 49 verified tool-capable
free routes. Routes are vendor-interleaved so consecutive failover attempts hit
DIFFERENT providers (max robustness), with fastest routes first within a vendor.
"""
import json, urllib.request, re, itertools, sys

BASE = "http://localhost:20128"


def api(method, path, payload=None, t=90):
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
        try:
            return getattr(e, "code", "ERR"), e.read().decode(errors="replace")[:400]
        except Exception:
            return getattr(e, "code", "ERR"), str(e)[:300]


routes = json.load(open(r"C:\Users\jonat\or_verified_routes.json"))
lat = {}
for f in ["or_verify_results.json", "or_verify2_results.json",
          "or_verify3_results.json", "or_verify4_results.json"]:
    try:
        for k, v in json.load(open(rf"C:\Users\jonat\{f}")).items():
            if v.get("tool"):
                lat[k] = v["secs"]
    except Exception:
        pass

# group by vendor, sort each by latency
byv = {}
for r in routes:
    byv.setdefault(r.split("/")[0], []).append(r)
for v in byv:
    byv[v].sort(key=lambda m: lat.get(m, 999))

# interleave vendors round-robin -> consecutive failovers hit different providers
lists = [byv[v] for v in sorted(byv, key=lambda v: lat.get(byv[v][0], 999))]
ordered = [m for m in itertools.chain.from_iterable(itertools.zip_longest(*lists)) if m]

COMBO = "auto-best-free"


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


models = []
for i, full in enumerate(ordered, 1):
    provider = full.split("/")[0]
    model = full.split("/", 1)[1]
    models.append({
        "id": f"{COMBO}-model-{i}-{slug(provider)}-{slug(model)}",
        "kind": "model",
        "model": full,          # fully-qualified, matches free-tools convention
        "providerId": provider,
        "weight": 0,
    })

print(f"building '{COMBO}' with {len(models)} verified routes")
for m in models:
    print(f"  {m['providerId']:<11} {m['model']}")
sys.stdout.flush()

# delete existing combo of same name if present
st, d = api("GET", "/api/combos")
combos = d.get("combos", d) if isinstance(d, dict) else d
for c in combos:
    if c.get("name") == COMBO:
        print("deleting existing", c["id"])
        api("DELETE", "/api/combos/" + c["id"])

payload = {"name": COMBO, "models": models, "strategy": "priority"}
st, r = api("POST", "/api/combos", payload)
print("\nPOST /api/combos ->", st)
print(json.dumps(r, indent=1)[:600] if isinstance(r, dict) else str(r)[:600])

st, d = api("GET", "/api/combos")
combos = d.get("combos", d) if isinstance(d, dict) else d
for c in combos:
    print(f"  combo: {c['name']} routes={len(c.get('models') or [])} strategy={c.get('strategy')}")
