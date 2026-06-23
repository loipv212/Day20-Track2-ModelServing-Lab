# Day 20 Lab — Model Serving & Inference Optimization (Track 2)

Lab cho **AICB-P2T2 · Ngày 20 · Model Serving & Inference Optimization**.
Build + tune một inference stack với llama.cpp trên laptop cá nhân của bạn, đo TTFT / TPOT / P50 / P95 / P99, và viết personal report về một thay đổi tối ưu mang lại speedup lớn nhất.

> **Lab này dành cho laptop cá nhân của bạn.** Mỗi học viên chạy lab trên máy mình, với spec của mình. Số liệu của bạn **không so sánh được** với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính độ rõ ràng của setup + tuning + writeup, **không** phải tốc độ tuyệt đối. Một bạn dùng laptop Air M1 8 GB và một bạn dùng workstation RTX 4090 cùng có thể đạt điểm tối đa nếu cả hai đều rubric đầy đủ + writeup mạch lạc.

> **One runtime, every laptop.** Lab dùng **llama.cpp** end-to-end — chạy trên Windows, macOS (Intel + Apple Silicon), Linux, có hoặc không GPU. Cùng model file, cùng metrics, không cần Docker. Tại sao không vLLM/SGLang? Những engine đó cần CUDA GPU + 16+ GB VRAM — phù hợp slide deck, không phù hợp lớp 30 laptop hỗn hợp. llama.cpp cho bạn cùng teaching surface (GGUF quantization, paged KV cache, continuous batching, OpenAI-compat API, Prometheus metrics) trên bất cứ phần cứng nào bạn có.

## Trước khi bắt đầu

1. Mở **[`rubric.md`](rubric.md)** — biết trước grader chấm gì để bạn tập trung đúng chỗ.
2. Mở **[`HARDWARE-GUIDE.md`](HARDWARE-GUIDE.md)** — xác định path nào phù hợp với laptop bạn.

---

## Quick Start

```bash
git clone https://github.com/<your-username>/Day20-Track2-ModelServing-Lab.git
cd Day20-Track2-ModelServing-Lab

make probe          # Probe hardware → hardware.json
make setup          # Auto-detect OS + install + download model (~5–15 min)
make bench          # Track 01 — TTFT/TPOT/P95 baseline
make serve &        # Track 02 — llama-server on :8080 (background)
make load-10        # Track 02 — locust 10 users, 1 min
make load-50        # Track 02 — locust 50 users, 1 min
make pipeline       # Track 03 — RAG → llama-server pipeline
make verify         # Sanity-check submission readiness
```

**Yêu cầu:** Python ≥ 3.10. Không cần Docker. Không cần OpenAI key.

**Windows:** `make` không native — chạy `pwsh -ExecutionPolicy Bypass -File 00-setup/windows-setup.ps1` rồi gọi từng script Python trực tiếp. Mọi script Python đều chạy trên Windows.

### Tất cả lệnh `make`

```
make probe          Probe hardware → hardware.json
make setup          Install deps + build llama-cpp-python + download model
make bench          Track 01 — TTFT/TPOT baseline + Q4_K_M vs Q2_K
make serve          Track 02 — llama-server on :8080 (foreground)
make serve-native   Track 02 (observability) — native server WITH /metrics (needs make build-llama)
make smoke          Track 02 — smoke-test the running server
make load-10        Track 02 — locust 10 users, 1 min
make load-50        Track 02 — locust 50 users, 1 min
make metrics        Track 02 (observability) — record /metrics 60s (needs make serve-native)
make pipeline       Track 03 — RAG → llama-server pipeline
make build-llama    Bonus — clone + build llama.cpp from source
make sweep-thread   Bonus — sweep -t (thread count)
make sweep-quant    Bonus — sweep GGUF quantizations
make sweep-ctx      Bonus — sweep context length
make sweep-batch    Bonus — sweep batch sizes
make sweep-gpu      Bonus — sweep GPU offload (CUDA/Metal/Vulkan/ROCm)
make mlx-compare    Bonus (Apple Silicon) — MLX vs llama.cpp Metal
make serve-embed    Bonus §5 — embedding server (llama-server --embedding) :8081
make embed-demo     Bonus §5 — embedding/reranker serving demo
make semantic-cache Bonus §5 — semantic cache (3-cache stack) demo
make verify         Pre-submission sanity check (run before push!)
make clean          Wipe generated artifacts (keep models, REFLECTION, screenshots)
```

---

## Track map

| Path | When to take it | Time |
|---|---|---|
| **00-setup** | Always — detect hardware, install platform-specific tooling | 20 min |
| **01-llama-cpp-quickstart** | Everyone — Python library benchmark | 30 min |
| **02-llama-cpp-server** | Everyone — OpenAI-compat HTTP API + observability + load test | 60 min |
| **03-milestone-integration** | M1 deliverable — connect to N16–N19 | 30 min |
| **BONUS-llama-cpp-optimization** | Optional, deeper. Weaker laptops benefit *more* | 60–120 min |
| **BONUS-mlx-macos** | Optional, Apple Silicon only | 30 min |

Total core path: ~2.5 giờ. Bonus tracks thêm 1–3 giờ.

---

## Slide → Track mapping

Mỗi track tương ứng với một phần của deck Day 20. Pass condition lấy từ `rubric.md`.

| Slide section (Day 20 deck) | Lab track | Skill | Pass when |
|---|---|---|---|
| §0 Latency Taxonomy (TTFT/TPOT/Goodput) | 01-quickstart | Đo TTFT/TPOT/P95 trên laptop của mình | Có bảng P50/P95/P99 cho 2 quantizations |
| §1 Quantization (FP8/AWQ/GGUF/NVFP4) | 01-quickstart + bonus quant-sweep | So sánh Q2_K → Q8_0, RAM vs latency | Side-by-side numbers committed |
| §2 KV Cache & PagedAttention | 02-server: `make serve-native` (`--metrics`, `--cache-type-k/-v`, `--parallel`) | Continuous batching qua native `/metrics` dưới load | Peak `n_busy_slots_per_decode` / `requests_processing` reported |
| §2 Spec Decoding (EAGLE-3 / MTP) | bonus challenge **C1** (`--draft-model`) | Draft+target speedup; llama.cpp merged MTP (2026) | tokens/s with vs without spec-decode |
| §3 Single-Node Serving (vLLM, SGLang, llama.cpp) | 02-server (`llama_cpp.server`) | Stand up OpenAI-compat HTTP server | locust 10 + 50 user runs committed |
| §3 Production Tuning (memory, scheduling, observability) | 02-server tuning + bonus thread-sweep | Đo P95 thay đổi khi tune `--parallel`, `-t`, `--ctx-size` | Sweep table + reflection paragraph |
| §3 Backend Selection (FA3/FA4/FlashInfer) | bonus build-from-source + gpu-offload | Build llama.cpp với backend đúng cho phần cứng | `bin/llama-bench --version` chạy + speedup quantified |
| §4 Distributed (TP/PP/EP/DP) | (concept-only — out of scope cho lab này) | — | — |
| §5 Serving Regimes — Embedding / Reranker | bonus **`embedding-serving.py`** (`make serve-embed`) | Prefill-bound serving, no KV cache; cosine retrieval | embedding endpoint ranks a corpus |
| §5 Serving Regimes — Semantic Caching | bonus challenge **C8** (`semantic-cache-demo.py`) | Meaning-based cache above the KV cache | hit-rate + calls-saved table |
| §5 Serving Regimes — VLM / Routing / Power / Confidential | (concept-only — datacenter-shaped) | — | — |
| §6 Auto-scaling & Operations | (concept-only) | — | — |
| §7 Edge & Hardware | bonus quant-sweep + 03-integration | Pick model tier theo RAM | Recommended tier khớp với hardware.json |
| §8 Production SLA (Goodput@SLO) | submission/REFLECTION.md | Set SLO target và đo gap | "Single change that mattered most" paragraph |

---

## Hardware guide

Xem [`HARDWARE-GUIDE.md`](HARDWARE-GUIDE.md) cho:
- Bảng chọn model theo RAM (TinyLlama-1.1B → Qwen2.5-7B)
- Bảng llama.cpp backend theo accelerator (CUDA / Metal / Vulkan / ROCm / CPU)
- Decision tree cho laptop của bạn

---

## Vibe-coding tips

Day 19 đã dạy bạn **vibe-coding** dạng general — bạn ép spec rõ, prompt LLM
viết boilerplate, review diff, accept hoặc rollback. Tốt cho greenfield code.

Day 20 giới thiệu **BMAD method** (Breakthrough Method for Agile AI-Driven
Development) — structured persona prompting cho task decision-driven, không
chỉ "viết code". Xem [`VIBE-CODING.md`](VIBE-CODING.md) (5–10 phút) — general
primer cover:

- BMAD vs vibe-coding (Day 19) — khi nào dùng cái nào
- 5 personas chính: PM/Spec, Architect, Developer, QA/Verify, Ops/Reflect
- Prompt template cho mỗi persona
- "Fail-soft vs fail-loud" rule (vẫn từ Day 19, BMAD's QA persona là chỗ đánh nó)
- 3 anti-patterns (skip PM, skip QA, BMAD-as-bureaucracy)

---

## Bonus tracks (optional, +20 pts)

> **Laptop yếu lại là lợi thế ở đây.** Bonus track lột bỏ abstraction: bạn build llama.cpp từ source với CPU-instruction-set flags đúng, sweep thread count, sweep quantization, sweep context length, sweep GPU offload — và đo speedup *trên chính máy bạn*. Một laptop M1 Air 8 GB hay một workstation RTX 4090 đều có thể tăng tốc 2–4× sau bonus track. Cái khác nhau chỉ là **knob nào quan trọng** trên hardware nào — và đó là phần grader thưởng điểm.

### Track A — `BONUS-llama-cpp-optimization/` (~60–120 phút)

Build llama.cpp từ source và đo cái gì matters trên *your* hardware.

**Setup:**

```bash
make build-llama       # clone + cmake + build cho backend phù hợp
                       # (CUDA / Metal / Vulkan / ROCm / CPU — auto từ hardware.json)
```

**5 sweep scripts** — chọn cái phù hợp với laptop của bạn (đừng chạy hết, chọn 1–2 cái nói lên nhiều nhất):

| `make` target | Script | Khi nào dùng | Insight |
|---|---|---|---|
| `make sweep-thread` | `thread-sweep.py` | **CPU-only laptop** — dễ thấy curve nhất | Curve tokens/s thường peak ở physical-core count rồi *drop* khi chạy vào hyperthreads — memory-bandwidth ceiling. |
| `make sweep-quant` | `quant-sweep.py` | **Tight RAM** | So sánh Q2_K → Q4_K_M → Q5_K_M → Q6_K → Q8_0: file size vs decode tok/s vs quality. |
| `make sweep-ctx` | `ctx-len-sweep.py` | **Long-context workload** (RAG, document QA) | Prefill scales ~O(N²) — đây là TTFT trong long-context. Chính là motivation cho disaggregated P/D ở deck §3. |
| `make sweep-batch` | `batch-size-sweep.py` | **Server với multiple slots** | `--batch-size` / `--ubatch-size` = chunked prefill — đánh đổi throughput vs TTFT. |
| `make sweep-gpu` | `gpu-offload-sweep.py` | **Có GPU** (CUDA / Metal / Vulkan / ROCm) | `-ngl 0,8,16,...,99` — khi nào partial offload thắng full offload (model không fit VRAM). |

**7 open challenges** in [`BONUS-llama-cpp-optimization/CHALLENGES.md`](BONUS-llama-cpp-optimization/CHALLENGES.md) — pick **một** cái để go deep:

- **C1** Speculative decoding (`--draft-model` + small draft + larger target)
- **C2** KV-cache quantization (`--cache-type-k q8_0 --cache-type-v q8_0`) — quality vs RAM tradeoff
- **C3** Multi-LoRA serving (`--lora` repeated, per-request adapter switching)
- **C4** Best-of-N parallel sampling + reranker
- **C5** "Weakest laptop" challenge — tìm model nhỏ nhất *vẫn useful* trên hardware bạn
- **C6** Vulkan vs CUDA head-to-head trên cùng một NVIDIA GPU
- **C7** CPU instruction-set archaeology (`-DGGML_NATIVE=ON` vs OFF, AVX2 vs AVX-512)

### Track B — `BONUS-mlx-macos/` (~30 phút, Apple Silicon only)

So sánh MLX (Apple's unified-memory ML framework) với llama.cpp Metal trên cùng 10 prompts. Trên M1/M2/M3/M4, MLX thường nhanh hơn 1.3–1.8× ở decode — đo trên máy bạn để confirm.

```bash
pip install mlx mlx-lm
make mlx-compare
```

### Track C — Serving regimes (§5, runnable on a laptop)

Deck §5 ("Serving Regimes & Cross-Cutting Concerns 2026") is mostly datacenter-shaped — but two of its regimes run fine on your laptop with llama.cpp:

```bash
make serve-embed &      # embedding server (llama-server --embedding) on :8081
make embed-demo         # §5 Embedding/reranker: prefill-bound, no KV cache, cosine retrieval

make serve &            # chat server on :8080  (semantic cache needs both)
make semantic-cache     # §5 Semantic caching: meaning-based cache above the KV cache
```

Both scripts also run with `--offline` (synthetic embeddings, no server) so you can read the logic on any machine. Write-up hook: semantic caching is the cache *above* the KV cache — report your hit rate and the threshold tradeoff. Full detail in [`BONUS-llama-cpp-optimization/CHALLENGES.md`](BONUS-llama-cpp-optimization/CHALLENGES.md) (C8, C9).

### Cách viết bonus writeup

Trong `submission/REFLECTION.md` §5 ("The single change that mattered most"), pick **một** thay đổi từ bonus track:

```
Change: <vd: rebuild llama.cpp với -DGGML_NATIVE=ON -DGGML_BLAS=ON>
Before: <số liệu>
After:  <số liệu>
Speedup: ~<X.Y>×
Tại sao nó work (1–2 đoạn): <giải thích bằng mental model về memory bandwidth /
                             cache / compute, không phải "vibes-based">
```

Đừng cố làm hết 5 sweeps + 7 challenges. **Một insight rõ ràng > năm sweeps lủng củng.**

### Bonus pts

- Build llama.cpp từ source thành công (any backend): **4 pts**
- Ít nhất 1 sweep với `benchmarks/bonus-*.md` committed: **4 pts**
- Bonus speedup quantified với before/after numbers: **4 pts**
- Ít nhất 1 challenge từ CHALLENGES.md attempted: **4 pts**
- MLX comparison run (Apple Silicon only): **4 pts**

Total **20 pts**. Bonus does **not** affect core grade negatively — missing nó là OK. Strong bonus submission gets a written instructor review focused on judgment quality, not raw numbers. Đầy đủ trong [`rubric.md`](rubric.md).

---

## Submission

**KHÔNG cần PR — chỉ submit GitHub URL công khai vào VinUni LMS.**

1. Fork hoặc copy repo này lên GitHub account của bạn, set repo **public**.
2. Hoàn thành 4 core tracks (`00-setup` → `01-quickstart` → `02-server` → `03-integration`).
3. Add screenshots vào `submission/screenshots/` — xem danh sách trong [`submission/screenshots/README.md`](submission/screenshots/README.md).
4. Điền **`submission/REFLECTION.md`** — đây là personal report grader đọc kỹ nhất.
5. Chạy `make verify` ở repo root — đảm bảo exit code 0.
6. Push lên public repo.
7. Paste public GitHub URL vào ô submission của Day 20 trong VinUni LMS.

**Quan trọng:** Repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.

Đầy đủ pass conditions + bonus pts xem [`rubric.md`](rubric.md).

---

## Repo structure

```
Day20-Track2-ModelServing-Lab/
├── README.md                          ← this file
├── HARDWARE-GUIDE.md                  ← model + backend pick chart
├── VIBE-CODING.md                     ← BMAD method intro (5–10 min pre-read)
├── rubric.md                          ← 100-pt core + 20-pt bonus
├── Makefile                           ← `make probe / setup / bench / serve / verify / ...`
├── pyproject.toml + requirements.txt  ← Python deps
├── .env.example                       ← tunable knobs
├── 00-setup/                          ← detect-hardware + platform setup scripts
├── 01-llama-cpp-quickstart/           ← Track 01 baseline
├── 02-llama-cpp-server/               ← Track 02 OpenAI-compat + locust + Prometheus
├── 03-milestone-integration/          ← Track 03 RAG pipeline skeleton
├── BONUS-llama-cpp-optimization/      ← source build + 5 sweeps + 7 challenges
├── BONUS-mlx-macos/                   ← Apple Silicon MLX comparison
├── benchmarks/                        ← (generated) results files
├── scripts/verify.py                  ← pre-submission sanity check
└── submission/                        ← personal report + screenshots (you fill these in)
    ├── REFLECTION.md
    └── screenshots/
```

---

## Why this lab matters

Day 20 deck argues **goodput@SLO** (không phải peak throughput) là production metric. Lab này là chỗ bạn đo cả hai trên laptop của mình, thấy gap, và tune gap đó nhỏ lại. Bonus track lột bỏ abstraction: bạn build llama.cpp từ source, chọn CPU instructions, và xem một model 1B parameters tăng tốc 2–4× mà không cần đổi model. Intuition đó áp dụng được cho mọi serving engine trong deck.
