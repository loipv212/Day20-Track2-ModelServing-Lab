# 02 — llama-server (OpenAI-compat + Prometheus + locust)

Step up from "Python library" to "real serving stack". You'll launch `llama-server` (the HTTP daemon shipped with llama.cpp), confirm the OpenAI-compat API, scrape its `/metrics` endpoint, and drive 10 / 50 concurrent users at it via locust.

This is the same shape of stack the deck talks about with vLLM and SGLang — just on a model and runtime small enough to fit on a laptop.

> **Two servers, one job each.** `make serve` (the `llama-cpp-python` module) is the zero-build path for chat + load testing — but it has **no `/metrics` endpoint**. The observability step (`/metrics`, batching gauges like `n_busy_slots_per_decode`) needs the **native** `llama-server` binary: `make build-llama` once, then `make serve-native`. Both speak the same OpenAI-compatible API on :8080.

## What you'll see

- `POST /v1/chat/completions` works with the OpenAI Python SDK pointed at `http://localhost:8080/v1`
- `GET /metrics` returns Prometheus text including `llamacpp:tokens_predicted_total`, `llamacpp:prompt_tokens_total`, `llamacpp:n_decode_total`, `llamacpp:n_busy_slots_per_decode`, `llamacpp:requests_processing`
- `--parallel N --cont-batching` enables continuous batching (see deck §2)
- Locust runs P50/P95/P99 under load and emits a histogram

## Run

There are two ways to launch `llama-server`:

### A. Python server — chat + load, zero build (`make serve`, NO /metrics)

```bash
# from repo root, .venv activated
python -m llama_cpp.server --model "$(jq -r .primary_model models/active.json)" \
    --host 0.0.0.0 --port 8080 \
    --n_threads "$(python -c 'import json,os; print(json.load(open("hardware.json"))["cpu"]["cores_physical"] or 4)')" \
    --n_gpu_layers 99
```

### B. Native server — observability with `/metrics` (`make build-llama`, then `make serve-native`)

The native binary is the **only** one that serves `/metrics`. Build it once (`make build-llama`), then `make serve-native` (or run it directly):

```bash
./BONUS-llama-cpp-optimization/llama.cpp/build/bin/llama-server \
    -m "$(jq -r .primary_model models/active.json)" \
    --host 0.0.0.0 --port 8080 \
    -t $(python -c 'import json; print(json.load(open("hardware.json"))["cpu"]["cores_physical"] or 4)') \
    -ngl 99 \
    --parallel 4 --cont-batching \
    --metrics
```

Either way, leave it running in one terminal. In a second terminal:

```bash
# Smoke-test the OpenAI API
python 02-llama-cpp-server/smoke-test.py

# Scrape metrics once (server B / `make serve-native` only — server A has no /metrics)
curl -s http://localhost:8080/metrics | head -40

# Run the load test
locust -f 02-llama-cpp-server/load-test.py --headless \
    -u 10 -r 1 -t 1m --host http://localhost:8080
```

After 1 min locust prints P50/P95/P99 in the table at the bottom. Re-run with `-u 50` to see how the numbers shift under contention.

## Files in this track

- `smoke-test.py` — one-shot OpenAI-SDK call to confirm the endpoint
- `start-server.sh` / `start-server.ps1` — convenience launchers that read `models/active.json`
- `load-test.py` — locust scenarios: 80% short prompts (chat-style), 20% long prompts (RAG-style)
- `prometheus.yml` — minimal scrape config if you want to spin up a local Prometheus
- `record-metrics.py` — polls `/metrics` every 5s during a load run and writes a CSV

## Knobs to try

| Flag | Effect | What to measure |
|---|---|---|
| `--parallel N` | Max concurrent slots (continuous batching width) | Throughput vs `N=1,2,4,8` |
| `--cont-batching` | Enable in-flight (continuous) batching | P95 with vs without, at -u 50 |
| `--ctx-size 4096` | Larger context window per slot | Process RSS (RAM) as ctx grows (`ps` / Activity Monitor) |
| `--cache-type-k q8_0` `--cache-type-v q8_0` | Quantize KV cache (memory ↓, slight quality ↓) | RAM saved vs quality |
| `--metrics` | Enable Prometheus endpoint | (must be on for everything else here) |

## Deliverable

With the **native** server running (`make serve-native`), drive load (`make load-10`) and in a third terminal run `make metrics` (`record-metrics.py --duration 60`) to capture `llamacpp:n_busy_slots_per_decode` / `requests_processing` etc. into `benchmarks/02-server-metrics.csv`. Re-run under `make load-50` for a contended sample.

## Deck mapping

- §0 Latency Taxonomy → locust's TTFT (time-to-first-byte) and end-to-end percentiles
- §3 PagedAttention deep-dive → `--parallel` and `--cont-batching` are llama.cpp's analogues of vLLM's continuous batching
- §3 Production Tuning → `--ctx-size`, `--cache-type-k/v`, `-t`, `-ngl` map 1:1 to the SGLang/vLLM knobs in the deck
- §3 Observability → `/metrics` is the same Prometheus pattern the deck describes for SGLang's `:30000/metrics`
