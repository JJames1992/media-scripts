"""Verify candidate free routes with REAL tool-calling chat requests.

Interleaves across providers (round-robin by vendor) and spaces requests so a
burst against one free tier doesn't produce false negatives.
Writes or_verify_results.json.
"""
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


def chat(model, timeout=75):
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
        ch = (body.get("choices") or [{}])[0]
        msg = ch.get("message") or {}
        has_tool = bool(msg.get("tool_calls"))
        content = (msg.get("content") or "")
        ok = has_tool or bool(content.strip())
        return {"ok": ok, "tool": has_tool, "secs": dt,
                "resolved": body.get("model"), "err": None}
    except Exception as e:
        dt = round(time.time() - t0, 1)
        body = ""
        try:
            body = e.read().decode(errors="replace")[:200]
        except Exception:
            pass
        return {"ok": False, "tool": False, "secs": dt, "resolved": None,
                "err": f"{getattr(e,'code','ERR')} {body or str(e)[:150]}"}


# Candidate routes grouped by vendor. Only free / free-tier models.
BY_VENDOR = {
    "groq": [
        "groq/llama-3.3-70b-versatile", "groq/llama-3.1-8b-instant",
        "groq/openai/gpt-oss-120b", "groq/openai/gpt-oss-20b",
        "groq/qwen/qwen3.6-27b", "groq/groq/compound-mini",
    ],
    "cerebras": [
        "cerebras/gpt-oss-120b", "cerebras/gemma-4-31b", "cerebras/zai-glm-4.7",
    ],
    "nvidia": [
        "nvidia/deepseek-ai/deepseek-v4-flash", "nvidia/meta/llama-3.3-70b-instruct",
        "nvidia/google/gemma-4-31b-it", "nvidia/qwen/qwen3-coder-480b-a35b-instruct",
        "nvidia/nvidia/llama-3.3-nemotron-super-49b-v1.5",
        "nvidia/moonshotai/kimi-k2-instruct",
    ],
    "mistral": [
        "mistral/mistral-small-latest", "mistral/devstral-medium-latest",
        "mistral/codestral-latest", "mistral/ministral-8b-latest",
        "mistral/mistral-medium-2508", "mistral/magistral-small-latest",
    ],
    "openrouter": [
        "openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
        "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
        "openrouter/nvidia/nemotron-3-nano-30b-a3b:free",
        "openrouter/inclusionai/ling-3.0-flash:free",
        "openrouter/poolside/laguna-s-2.1:free",
        "openrouter/poolside/laguna-xs-2.1:free",
        "openrouter/cohere/north-mini-code:free",
        "openrouter/google/gemma-4-31b-it:free",
        "openrouter/google/gemma-4-26b-a4b-it:free",
        "openrouter/openai/gpt-oss-20b:free",
        "openrouter/nvidia/nemotron-nano-9b-v2:free",
    ],
    "opencode": [
        "opencode/nemotron-3-ultra-free", "opencode/north-mini-code-free",
        "opencode/big-pickle", "opencode/deepseek-v4-flash-free",
        "opencode/minimax-m3-free", "opencode/minimax-m2.5-free",
        "opencode/ling-2.6-1t-free", "opencode/trinity-large-preview-free",
        "opencode/nemotron-3-super-free", "opencode/qwen3.6-plus-free",
    ],
    "huggingchat": [
        "huggingchat/openai/gpt-oss-120b", "huggingchat/openai/gpt-oss-20b",
        "huggingchat/Qwen/Qwen3.5-397B-A17B", "huggingchat/Qwen/Qwen3.6-27B",
        "huggingchat/deepseek-ai/DeepSeek-V4-Flash",
        "huggingchat/google/gemma-4-31B-it", "huggingchat/zai-org/GLM-5.2",
        "huggingchat/MiniMaxAI/MiniMax-M3", "huggingchat/moonshotai/Kimi-K2.6",
        "huggingchat/nvidia/NVIDIA-Nemotron-3-Ultra-550B-A55B-NVFP4",
    ],
    "hackclub": [
        "hackclub/meta-llama/llama-3.3-70b-instruct",
        "hackclub/mistralai/mistral-7b-instruct",
        "hackclub/deepseek-ai/deepseek-coder-33b",
    ],
    "gitlawb": [
        "gitlawb/mimo-v2.5-pro", "gitlawb/mimo-v2.5", "gitlawb/mimo-v2-flash",
    ],
    "gitlawb-gmi": [
        "gitlawb-gmi/openai/gpt-5.4-mini", "gitlawb-gmi/deepseek-ai/DeepSeek-V4-Flash",
        "gitlawb-gmi/XiaomiMiMo/MiMo-V2.5", "gitlawb-gmi/openai/gpt-4o-mini",
    ],
    "auggie": [
        "auggie/haiku4.5", "auggie/gpt5.4-mini", "auggie/sonnet4.6", "auggie/glm-5.2",
    ],
    "pollinations": [
        "pollinations/openai-fast", "pollinations/openai", "pollinations/qwen-coder",
        "pollinations/mistral", "pollinations/gemini-fast", "pollinations/deepseek",
        "pollinations/glm", "pollinations/nova-fast",
    ],
}

# Round-robin interleave so consecutive requests hit different vendors.
lists = [list(v) for v in BY_VENDOR.values()]
order = [m for m in itertools.chain.from_iterable(itertools.zip_longest(*lists)) if m]

print(f"probing {len(order)} routes across {len(BY_VENDOR)} vendors\n")
sys.stdout.flush()

results = {}
for i, model in enumerate(order, 1):
    r = chat(model)
    results[model] = r
    flag = "TOOL" if r["tool"] else ("TEXT" if r["ok"] else "FAIL")
    print(f"[{i:3}/{len(order)}] {flag:4} {r['secs']:>5}s  {model}"
          + (f"   :: {r['err']}" if r["err"] else ""))
    sys.stdout.flush()
    json.dump(results, open(r"C:\Users\jonat\or_verify_results.json", "w"), indent=1)
    time.sleep(3)

tool_ok = [m for m, r in results.items() if r["tool"]]
text_ok = [m for m, r in results.items() if r["ok"] and not r["tool"]]
print(f"\n=== TOOL-CAPABLE: {len(tool_ok)} ===")
for m in tool_ok:
    print(" ", m)
print(f"\n=== TEXT-ONLY (no tool_call): {len(text_ok)} ===")
for m in text_ok:
    print(" ", m)
