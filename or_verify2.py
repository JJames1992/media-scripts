"""Round 2: deep-probe the two providers that answered (nvidia, mistral) across
their chat catalogs, plus a spaced re-test of the VPN-suspect providers."""
import json, urllib.request, time, sys, itertools

BASE = "http://localhost:20128"

TOOLS = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string", "description": "City name"}},
            "required": ["city"],
        },
    },
}]
MESSAGES = [{"role": "user",
             "content": "Use the get_weather tool to check the weather in Paris. Call the tool."}]


def chat(model, timeout=60):
    payload = {"model": model, "messages": MESSAGES, "tools": TOOLS,
               "max_tokens": 256, "stream": False}
    req = urllib.request.Request(BASE + "/v1/chat/completions",
                                 data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read())
        dt = round(time.time() - t0, 1)
        msg = (body.get("choices") or [{}])[0].get("message") or {}
        has_tool = bool(msg.get("tool_calls"))
        ok = has_tool or bool((msg.get("content") or "").strip())
        return {"ok": ok, "tool": has_tool, "secs": dt, "err": None}
    except Exception as e:
        dt = round(time.time() - t0, 1)
        body = ""
        try:
            body = e.read().decode(errors="replace")[:160]
        except Exception:
            pass
        return {"ok": False, "tool": False, "secs": dt,
                "err": f"{getattr(e,'code','ERR')} {body or str(e)[:120]}"}


NVIDIA = [
    "nvidia/nvidia/nemotron-3-ultra-550b-a55b",
    "nvidia/nvidia/nemotron-3-super-120b-a12b",
    "nvidia/nvidia/nemotron-3-nano-30b-a3b",
    "nvidia/nvidia/nemotron-nano-3-30b-a3b",
    "nvidia/nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
    "nvidia/nvidia/llama-3.3-nemotron-super-49b-v1",
    "nvidia/nvidia/llama-3.1-nemotron-70b-instruct",
    "nvidia/nvidia/llama-3.1-nemotron-ultra-253b-v1",
    "nvidia/nvidia/llama-3.1-nemotron-51b-instruct",
    "nvidia/nvidia/nvidia-nemotron-nano-9b-v2",
    "nvidia/nvidia/llama-3.1-nemotron-nano-8b-v1",
    "nvidia/nvidia/nemotron-mini-4b-instruct",
    "nvidia/nvidia/nemotron-4-340b-instruct",
    "nvidia/openai/gpt-oss-120b",
    "nvidia/openai/gpt-oss-20b",
    "nvidia/deepseek-ai/deepseek-v4-pro",
    "nvidia/meta/llama-3.1-70b-instruct",
    "nvidia/meta/llama-3.1-8b-instruct",
    "nvidia/meta/llama-3.2-3b-instruct",
    "nvidia/z-ai/glm-5.2",
    "nvidia/minimaxai/minimax-m3",
    "nvidia/moonshotai/kimi-k2.6",
    "nvidia/stepfun-ai/step-3.7-flash",
    "nvidia/thinkingmachines/inkling",
    "nvidia/poolside/laguna-xs-2.1",
    "nvidia/mistralai/mistral-medium-3.5-128b",
    "nvidia/mistralai/mistral-nemotron",
    "nvidia/mistralai/mistral-large-2-instruct",
    "nvidia/qwen/qwen3-next-80b-a3b-instruct",
    "nvidia/microsoft/phi-3.5-moe-instruct",
    "nvidia/ai21labs/jamba-1.5-large-instruct",
    "nvidia/writer/palmyra-creative-122b",
    "nvidia/databricks/dbrx-instruct",
    "nvidia/01-ai/yi-large",
]

MISTRAL = [
    "mistral/mistral-large-latest",
    "mistral/mistral-medium-latest",
    "mistral/mistral-medium-3.5",
    "mistral/mistral-small-2603",
    "mistral/devstral-latest",
    "mistral/devstral-2512",
    "mistral/codestral-2508",
    "mistral/ministral-3b-latest",
    "mistral/ministral-14b-latest",
    "mistral/mistral-code-latest",
    "mistral/mistral-code-agent-latest",
    "mistral/mistral-vibe-cli-with-tools",
    "mistral/mistral-vibe-cli-fast",
    "mistral/labs-leanstral-1-5-1",
    "mistral/mistral-large-2512",
]

# spaced re-test of VPN-suspect providers (Cloudflare 1010 / 403)
RETEST = [
    "groq/llama-3.3-70b-versatile",
    "cerebras/gpt-oss-120b",
    "opencode/big-pickle",
    "opencode/nemotron-3-ultra-free",
]

lists = [NVIDIA, MISTRAL]
order = [m for m in itertools.chain.from_iterable(itertools.zip_longest(*lists)) if m]

results = {}
print(f"ROUND 2: {len(order)} deep routes + {len(RETEST)} spaced re-tests\n")
sys.stdout.flush()

for i, model in enumerate(order, 1):
    r = chat(model)
    results[model] = r
    flag = "TOOL" if r["tool"] else ("TEXT" if r["ok"] else "FAIL")
    print(f"[{i:3}/{len(order)}] {flag:4} {r['secs']:>5}s  {model}"
          + (f"   :: {r['err']}" if r["err"] else ""))
    sys.stdout.flush()
    json.dump(results, open(r"C:\Users\jonat\or_verify2_results.json", "w"), indent=1)
    time.sleep(2)

print("\n--- spaced re-test of 403/VPN-suspect routes (25s apart) ---")
for model in RETEST:
    time.sleep(25)
    r = chat(model)
    results[model] = r
    flag = "TOOL" if r["tool"] else ("TEXT" if r["ok"] else "FAIL")
    print(f"  {flag:4} {r['secs']:>5}s  {model}" + (f"   :: {r['err']}" if r["err"] else ""))
    sys.stdout.flush()

json.dump(results, open(r"C:\Users\jonat\or_verify2_results.json", "w"), indent=1)
tool_ok = [m for m, r in results.items() if r["tool"]]
print(f"\n=== ROUND2 TOOL-CAPABLE: {len(tool_ok)} ===")
for m in tool_ok:
    print(" ", m)
