"""Round 3: probe OpenRouter free models now that the poisoned key is removed."""
import json, urllib.request, time, sys

BASE = "http://localhost:20128"
TOOLS = [{"type": "function", "function": {
    "name": "get_weather", "description": "Get the current weather for a city",
    "parameters": {"type": "object",
                   "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}]
MSG = [{"role": "user", "content": "Use the get_weather tool to check the weather in Paris. Call the tool."}]


def chat(model, timeout=70):
    p = {"model": model, "messages": MSG, "tools": TOOLS, "max_tokens": 256, "stream": False}
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(p).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            b = json.loads(r.read())
        m = (b.get("choices") or [{}])[0].get("message") or {}
        tool = bool(m.get("tool_calls"))
        ok = tool or bool((m.get("content") or "").strip())
        return {"ok": ok, "tool": tool, "secs": round(time.time() - t0, 1), "err": None}
    except Exception as e:
        try:
            err = e.read().decode(errors="replace")[:150]
        except Exception:
            err = str(e)[:120]
        return {"ok": False, "tool": False, "secs": round(time.time() - t0, 1),
                "err": f"{getattr(e,'code','ERR')} {err}"}


OR_FREE = [
    "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
    "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter/nvidia/nemotron-3-nano-30b-a3b:free",
    "openrouter/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
    "openrouter/nvidia/nemotron-nano-9b-v2:free",
    "openrouter/nvidia/nemotron-nano-12b-v2-vl:free",
    "openrouter/inclusionai/ling-3.0-flash:free",
    "openrouter/poolside/laguna-s-2.1:free",
    "openrouter/poolside/laguna-xs-2.1:free",
    "openrouter/cohere/north-mini-code:free",
    "openrouter/google/gemma-4-31b-it:free",
    "openrouter/google/gemma-4-26b-a4b-it:free",
    "openrouter/openai/gpt-oss-20b:free",
    "openrouter/openrouter/free",
    "openrouter/stepfun/step-3.7-flash:free",
]

results = {}
print(f"ROUND 3: {len(OR_FREE)} OpenRouter free routes (poisoned key removed)\n")
sys.stdout.flush()
for i, m in enumerate(OR_FREE, 1):
    r = chat(m)
    results[m] = r
    flag = "TOOL" if r["tool"] else ("TEXT" if r["ok"] else "FAIL")
    print(f"[{i:2}/{len(OR_FREE)}] {flag:4} {r['secs']:>5}s  {m}"
          + (f"   :: {r['err']}" if r["err"] else ""))
    sys.stdout.flush()
    json.dump(results, open(r"C:\Users\jonat\or_verify3_results.json", "w"), indent=1)
    time.sleep(8)

tool_ok = [m for m, r in results.items() if r["tool"]]
print(f"\n=== ROUND3 TOOL-CAPABLE: {len(tool_ok)} ===")
for m in tool_ok:
    print(" ", m)
