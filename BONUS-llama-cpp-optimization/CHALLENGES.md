# Bonus Challenges — Pick One, Go Deep

The sweeps in `benchmarks/` are the warm-up. Pick **one** of these challenges if you have time and want to push further. Each is sized for an extra hour or two.

## C1. Speculative decoding on YOUR laptop

llama.cpp supports speculative decoding via `--draft-model`. Pair a tiny draft (e.g. Qwen2.5-0.5B) with a slightly larger target (Qwen2.5-1.5B or 3B). Measure tokens/sec with and without spec-decode at different temperatures.

Why it's interesting: the deck claims EAGLE-3 gets 3–6.5×. With a vanilla draft model, you'll probably see 1.3–1.8× — explain the gap, and what kind of draft architecture (matched-vocabulary, MTP, etc.) closes it.

> **2026 update:** llama.cpp merged native **MTP (Multi-Token Prediction)** speculative decoding (May 2026) — the same idea DeepSeek-V3 ships. If your target model has an MTP head, try it instead of a separate `--draft-model` and compare acceptance rates. And mind the deck's caveat: spec-decode is a *latency* tool — at batch ≥24 the verify overhead can make it net-negative, so engines auto-disable it under load (`--speculative-disable-by-batch-size`).

```bash
llama-server -m TARGET.gguf --draft-model DRAFT.gguf --draft-max 8 ...
```

## C2. KV-cache quantization

llama.cpp lets you quantize the KV cache: `--cache-type-k q8_0 --cache-type-v q8_0`. This is the "FP8 KV" of the deck (FA3 / FlashInfer support FP8 KV) but for CPU/Metal/Vulkan.

Measure RAM saved, latency change, and—**critically**—any quality drop on a small eval set (5–10 prompts you can grade by eye, or use a JSON-extraction task you can grade automatically).

## C3. Multi-LoRA serving

llama.cpp's `--lora` flag accepts multiple LoRA adapters. Find or train two small LoRAs (one for SQL, one for tool-calling — Hugging Face has plenty), serve both on top of the same base, and benchmark per-request adapter switching cost.

This maps directly to the deck §4 Multi-LoRA Serving frame (Punica / S-LoRA).

## C4. Build a tiny "best of N" decoder

Use llama-cpp-python to send the same prompt N times in parallel (different seeds), then pick the best response with a small reranker (could be a 1B model, or even just a length/repetition heuristic). Measure end-to-end latency and quality vs single-shot.

Why interesting: shows you that "throughput" can be reframed — you can spend tokens/sec on parallel sampling instead of unique requests.

## C5. The "weakest laptop" challenge

If you're on the slowest laptop in the room: see how small a model you can run usefully. Try TinyLlama-1.1B at Q2_K vs a fine-tuned 0.5B at Q4_K_M. Measure both speed and a hand-graded quality on 5 prompts. Submit a writeup arguing which one is more useful at *your* RAM ceiling.

## C6. Vulkan vs CUDA on the same machine

If you have an NVIDIA GPU: build llama.cpp twice, once with CUDA and once with Vulkan. Benchmark both. The CUDA build should be 1.3–2× faster — quantify the gap and explain *why* the deck's vLLM/SGLang stacks bother with vendor-specific kernels (FA3, FA4, FlashMLA, TRTLLM-MHA) instead of using Vulkan.

## C7. CPU instruction set archaeology

On Linux, recompile llama.cpp with `-DGGML_NATIVE=OFF` (forces a generic baseline build) and compare to `-DGGML_NATIVE=ON`. Then go further: identify your CPU's specific extensions (`/proc/cpuinfo`) and try `-DGGML_AVX2=ON` or `-DGGML_AVX512=ON` explicitly. Make a table of "build flag" vs "tokens/sec".

This is the same kind of decision the cloud-side deck makes when picking FA3 (Hopper) vs FA4 (Blackwell) vs FlashInfer (A100): match the kernel to the silicon.

## C8. Semantic caching — the cache above the KV cache

Deck §5 argues the serving stack is *three caches deep*: a **semantic cache** (meaning-based) sits above the prefix/KV cache. A hit returns a stored answer to a *paraphrased* prompt with **zero** compute (no prefill, no decode).

`semantic-cache-demo.py` puts a tiny semantic cache in front of your chat server: it embeds each prompt (via an embedding server, `make serve-embed`), cosine-matches it against past prompts, and only calls the LLM on a miss.

```bash
make serve &            # chat       on :8080
make serve-embed &      # embeddings on :8081
python BONUS-llama-cpp-optimization/semantic-cache-demo.py --threshold 0.85
# no servers? logic demo + threshold sweep:
python BONUS-llama-cpp-optimization/semantic-cache-demo.py --offline --sweep
```

Report your hit rate, the threshold you picked, and one paraphrase that *should* have hit but didn't (a real embedder catches "TTFT" ≈ "time to first token"; bag-of-words can't). Security caveat: shared semantic/KV caches leak prompts across users via timing (NDSS'25) — salt the cache per tenant.

## C9. Embedding & reranker serving — the retrieval half

Deck §5: embedding serving is a *different regime* — prefill-bound, no KV cache, no decode loop; throughput comes from large static batches. Start a dedicated embedding server and measure how its latency scales with batch size (pure prefill), unlike the decode-bound chat server.

```bash
make serve-embed &      # llama-server --embedding on :8081
python BONUS-llama-cpp-optimization/embedding-serving.py
```

Compare its throughput curve to your `02-server` decode numbers and explain why an embedding endpoint and a chat endpoint want different batching strategies (static vs continuous).

---

## How to write up

Whatever you pick, the deliverable is a single section in `benchmarks/results.md`:

- **Setup**: what hardware + what you changed
- **Numbers**: a table with before vs after
- **One paragraph**: what the result tells you that the deck didn't already say. Be honest if a result didn't match what you expected — those are the most interesting writeups.

Don't try to do more than one challenge in your first pass. A deeply-explained C5 beats a shallow C1+C2+C3.
