"""Round 4 — FIXED probe: send a browser User-Agent so Cloudflare doesn't
1010-block the request. Re-tests every provider that previously 403'd.
"""
import json, urllib.request, time, sys, itertools

BASE = "http://localhost:20128"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

TOOLS = [{"type": "function", "function": {
    "name": "get_weather", "description": "Get the current weather for a city",
    "parameters": {"type": "object",
                   "properties": {"city": {"type": "string"}},
                   "required": ["city"]}}}]
MSG = [{"role": "user", "content": "Use the get_weather tool to check the weather in Paris. Call the tool."}]


def chat(model, timeout=70):
    p = {"model": model, "messages": MSG, "tools": TOOLS, "max_tokens": 256, "stream": False}
    req = urllib.request.Request(
        BASE + "/v1/chat/completions", data=json.dumps(p).encode(), method="POST",
        headers={"Content-Type": "application/json", "User-Agent": UA,
                 "Accept": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode(errors="replace")
        dt = round(time.time() - t0, 1)
        # handle SSE-style responses
        if raw.lstrip().startswith("data:"):
            tool = '"tool_calls"' in raw
            txt = '"content":"' in raw
            return {"ok": tool or txt, "tool": tool, "secs": dt, "err": None}
        b = json.loads(raw)
        m = (b.get("choices") or [{}])[0].get("message") or {}
        tool = bool(m.get("tool_calls"))
        ok = tool or bool((m.get("content") or "").strip())
        return {"ok": ok, "tool": tool, "secs": dt, "err": None}
    except Exception as e:
        try:
            err = e.read().decode(errors="replace")[:130]
        except Exception:
            err = str(e)[:110]
        return {"ok": False, "tool": False, "secs": round(time.time() - t0, 1),
                "err": f"{getattr(e,'code','ERR')} {err}"}


BY_VENDOR = {
    "groq": [
        "groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant",
        "groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b",
        "groq/qwen/qwen3.6-27b", "groq/groq/compound", "groq/groq/compound-mini",
        "groq/allam-2-7b",
    ],
    "cerebras": [
        "cerebras/gpt-oss-120b", "cerebras/gemma-4-31b", "cerebras/zai-glm-4.7",
    ],
    "opencode": [
        "opencode/big-pickle", "opencode/nemotron-3-ultra-free",
        "opencode/north-mini-code-free", "opencode/deepseek-v4-flash-free",
        "opencode/minimax-m3-free", "opencode/minimax-m2.5-free",
        "opencode/ling-2.6-1t-free", "opencode/trinity-large-preview-free",
        "opencode/nemotron-3-super-free", "opencode/qwen3.6-plus-free",
        "opencode/grok-code", "opencode/code-supernova",
    ],
    "pollinations": [
        "pollinations/openai-fast", "pollinations/openai", "pollinations/openai-large",
        "pollinations/qwen-coder", "pollinations/mistral", "pollinations/gemini",
        "pollinations/gemini-fast", "pollinations/deepseek", "pollinations/glm",
        "pollinations/nova-fast", "pollinations/nova", "pollinations/grok",
        "pollinations/claude-fast", "pollinations/kimi", "pollinations/minimax",
    ],
    "gitlawb": ["gitlawb/mimo-v2.5-pro", "gitlawb/mimo-v2.5", "gitlawb/mimo-v2-flash"],
    "gitlawb-gmi": [
        "gitlawb-gmi/openai/gpt-4o-mini", "gitlawb-gmi/deepseek-ai/DeepSeek-V4-Flash",
        "gitlawb-gmi/XiaomiMiMo/MiMo-V2.5",
    ],
    "hackclub": [
        "hackclub/meta-llama/llama-3.3-70b-instruct",
        "hackclub/mistralai/mistral-7b-instruct",
    ],
}

lists = [list(v) for v in BY_VENDOR.values()]
order = [m for m in itertools.chain.from_iterable(itertools.zip_longest(*lists)) if m]

results = {}
print(f"ROUND 4 (browser UA): {len(order)} routes across {len(BY_VENDOR)} vendors\n")
sys.stdout.flush()
for i, m in enumerate(order, 1):
    r = chat(m)
    results[m] = r
    flag = "TOOL" if r["tool"] else ("TEXT" if r["ok"] else "FAIL")
    print(f"[{i:3}/{len(order)}] {flag:4} {r['secs']:>5}s  {m}"
          + (f"   :: {r['err']}" if r["err"] else ""))
    sys.stdout.flush()
    json.dump(results, open(r"C:\Users\jonat\or_verify4_results.json", "w"), indent=1)
    time.sleep(3)

tool_ok = [m for m, r in results.items() if r["tool"]]
text_ok = [m for m, r in results.items() if r["ok"] and not r["tool"]]
print(f"\n=== ROUND4 TOOL-CAPABLE: {len(tool_ok)} ===")
for m in tool_ok:
    print(" ", m)
print(f"\n=== ROUND4 TEXT-ONLY: {len(text_ok)} ===")
for m in text_ok:
    print(" ", m)
