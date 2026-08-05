import json, time, urllib.request, sys

BASE = 'http://localhost:20128/v1'
PROMPT = 'Explain what a circuit breaker does in 3 sentences.'
MODELS = [
    'felo/felo-chat',
    'aug/glm-5.2',
    'ddgw/claude-haiku-4-5',
    'tllm/gemini_3_flash',
    'mcode/mimo-auto',
    'pepper/pepper-1',
    'auto/best-free',
    'auto/smart',
]
N = 10

def call(model):
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 200,
        "stream": False,
    }).encode()
    req = urllib.request.Request(BASE + '/chat/completions', data=body,
                                 headers={'Content-Type': 'application/json'})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.load(r)
            elapsed = time.time() - t0
            content = (resp.get('choices') or [{}])[0].get('message', {}).get('content', '')
            ok = bool(content and content.strip())
            return elapsed, ok, (content.strip()[:60].replace('\n', ' ') if ok else 'EMPTY')
    except Exception as e:
        return time.time() - t0, False, f'ERR {type(e).__name__}: {str(e)[:60]}'

print(f'Benchmark {time.strftime("%H:%M:%S")} | prompt: {PROMPT[:40]}... | {N} reqs per model', flush=True)
for m in MODELS:
    times, okc = [], 0
    first_note = ''
    for i in range(N):
        t, ok, note = call(m)
        times.append(t)
        if ok:
            okc += 1
        if i == 0:
            first_note = note
    avg = sum(times) / len(times)
    print(f'{m}: {okc}/{N} ok | avg {avg:.1f}s | min {min(times):.1f}s | max {max(times):.1f}s | first: {first_note}', flush=True)
print('DONE', flush=True)
