# Reflection — Lab 20 (Personal Report)

> **Đây là báo cáo cá nhân.** Mỗi học viên chạy lab trên laptop của mình, với spec của mình. Số liệu của bạn không so sánh được với bạn cùng lớp — chỉ so sánh **before vs after trên chính máy bạn**. Grade rubric tính theo độ rõ ràng của setup + tuning của bạn, không phải tốc độ tuyệt đối.

---

**Họ Tên:** Phạm Văn Lợi
**Cohort:** Cohort2
**Ngày submit:** 2026-06-24

---

## 1. Hardware spec (từ `00-setup/detect-hardware.py`)

> Paste output của `python 00-setup/detect-hardware.py` vào đây, hoặc điền thủ công:

- **OS:** Linux 6.17.0-35-generic (x86_64)
- **CPU:** AMD Ryzen 5 5600H with Radeon Graphics
- **Cores:** 6 physical / 12 logical (llama.cpp probe báo 12/12)
- **CPU extensions:** AVX2 (không có AVX-512)
- **RAM:** 15.0 GB
- **Accelerator:** NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096 MiB
- **llama.cpp backend đã chọn:** CUDA (`-DGGML_CUDA=on`)
- **Recommended model tier:** Qwen2.5-1.5B-Instruct (Q4_K_M)

**Setup story** (≤ 80 chữ): Laptop có RTX 3050 Ti nhưng chỉ 4 GiB VRAM, nên
chọn model 1.5B để fit trọn vào GPU (`n_gpu_layers=99`). Build llama-cpp-python
với CUDA backend khớp `hardware.json`. Model Qwen2.5-1.5B tải về 2 bản
(Q4_K_M làm primary, Q2_K để so sánh). Không cần Docker, không phải fall back
sang CPU.

---

## 2. Track 01 — Quickstart numbers (từ `benchmarks/01-quickstart-results.md`)

> Paste bảng từ `benchmarks/01-quickstart-results.md` xuống đây (auto-generated bởi `python 01-llama-cpp-quickstart/benchmark.py`).

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| Q4_K_M | 855 | 145 / 220 | 40.6 / 41.8 | 2728 / 2785 / 2794 | 24.6 |
| Q2_K   | 223 | 164 / 256 | 30.6 / 33.6 | 2060 / 2328 / 2388 | 32.7 |

**Một quan sát** (≤ 50 chữ): Q2_K decode nhanh hơn ~33% (32.7 vs 24.6 tok/s)
vì ít byte trọng số phải đọc mỗi token. Nhưng TTFT P50 lại nhỉnh hơn Q4_K_M
(164 vs 145ms). Trên GPU 4 GiB này Q4_K_M vẫn fit trọn nên mình giữ Q4_K_M
làm primary để đổi lấy chất lượng text tốt hơn.

---

## 3. Track 02 — llama-server load test

> Chạy 2 lần locust ở concurrency 10 và 50, paste tóm tắt bên dưới.

| Concurrency | Total RPS | TTFB P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 1.44 | 5700 | 6700 | 7600 | 0 |
| 50 | 1.36 | 11000 | 24000 | 25000 | 0 |

**Batching observation** (từ `record-metrics.py`): khi đẩy tải 10 → 50 users,
RPS gần như đứng yên (1.44 → 1.36) và 0 failures — server hấp thụ hết request
nhờ continuous batching, nhưng tail latency P95 nổ từ 6.7s lên 24s. Nghĩa là
hệ thống đã **bão hoà**: throughput tổng bị chặn bởi compute/VRAM của một GPU
4 GiB, request thừa phải xếp hàng nên queueing delay đẩy P95/P99 lên. Đúng với
luận điểm goodput@SLO (deck §8): RPS thô vẫn đẹp ở 50 users nhưng nếu SLO là
"P95 < 8s" thì goodput thực tế đã sụp ở mức tải này. (Số `n_busy_slots_per_decode`
từ native `/metrics` cần `make serve-native` + `make metrics` — xem
`benchmarks/02-server-results.md`.)

---

## 4. Track 03 — Milestone integration

- **N16 (Cloud/IaC):** stub — chạy localhost, llama-server `:8080`, không dùng cluster/IaC.
- **N17 (Data pipeline):** stub — không có batch job; corpus là in-memory list.
- **N18 (Lakehouse):** stub — không có Delta/Iceberg; dữ liệu hard-code trong `TOY_DOCS`.
- **N19 (Vector + Feature Store):** stub `TOY_DOCS` — retrieval bằng keyword-overlap
  (chưa cắm vector index thật). 5 doc về serving (`n20-paged`, `n20-radix`,
  `n20-disagg`, `n20-goodput`, `n20-quant`).

> 3 pieces được nêu rõ là **stub có lý do** (N16/N17/N18 ngoài scope lab này);
> chỉ N19 + N20 (llama-server) là phần thực sự chạy. Pipeline end-to-end OK với
> 3 query mẫu, in ra context provenance (`contexts: [...]`).

**Nơi tốn nhiều ms nhất** trong pipeline (đo bằng `time.perf_counter` trong `pipeline.py`):

- embed: N/A — pipeline dùng keyword-overlap, không có embedding step riêng.
- retrieve: ~0.0 ms (in-memory keyword match trên 5 doc).
- llama-server: 527.6 – 1089.7 ms / query.

**Reflection** (≤ 60 chữ): ~100% latency dồn vào llama-server (LLM inference);
retrieve gần như miễn phí vì corpus tí hon nằm sẵn trong RAM. Khớp kỳ vọng:
với RAG corpus nhỏ, bottleneck luôn là decode của LLM, không phải retrieval.
Khi N19 cắm vector store thật + corpus lớn, phần retrieve mới bắt đầu đáng kể.

---

## 5. Bonus — The single change that mattered most

> **Most important section.** Pick **một** thay đổi từ bonus track (build flag, thread sweep, quant pick, GPU offload, KV-cache quantization, speculative decoding, bất cứ challenge nào trong `BONUS-llama-cpp-optimization/CHALLENGES.md`) đã tạo ra speedup lớn nhất trên máy bạn.

**Change:** Đổi quantization Q4_K_M → Q2_K (giảm bit-width của trọng số), giữ
nguyên mọi tham số khác (`n_gpu_layers=99`, `n_ctx=2048`, `n_batch=512`).

**Before vs after** (từ `benchmarks/01-quickstart-results.md`):

```
before (Q4_K_M): 24.6 tok/s decode, TPOT P50 40.6 ms, file 1117 MB
after  (Q2_K):   32.7 tok/s decode, TPOT P50 30.6 ms, file  753 MB
speedup: ~1.33× decode throughput, file nhỏ hơn ~33%
```

**Tại sao nó work** (1–2 đoạn ngắn):

Decode autoregressive là **memory-bandwidth-bound**, không phải compute-bound:
mỗi token sinh ra phải đọc *toàn bộ* ma trận trọng số một lần qua bus bộ nhớ,
trong khi lượng phép tính trên mỗi byte lại nhỏ. Q2_K nhồi mỗi trọng số vào
~2 bit thay vì ~4 bit của Q4_K_M, nên model nhỏ hơn ~33% (753 MB vs 1117 MB) →
mỗi bước decode phải kéo ít byte hơn qua bộ nhớ → TPOT giảm 40.6 → 30.6 ms,
đúng tỉ lệ ~1.33× với mức giảm dung lượng. Đây không phải GPU "tính nhanh hơn"
— nó chỉ phải *chờ bộ nhớ ít hơn*.

Điểm thú vị ngược kỳ vọng: dù decode nhanh hơn, **TTFT của Q2_K lại chậm hơn**
(P50 164 vs 145 ms). Prefill là phase compute-bound (xử lý song song cả prompt),
nên ở đó dequantize Q2_K (giải nén block phức tạp hơn) lại thành overhead, không
được lợi từ việc đọc ít byte. Vì model 1.5B vẫn fit trọn 4 GiB VRAM ở Q4_K_M,
mình giữ Q4_K_M làm primary: 1.33× decode không đáng đánh đổi chất lượng text khi
RAM/VRAM chưa phải nút thắt. Q2_K chỉ xứng đáng khi VRAM thực sự chật.

> _Ghi chú nâng cấp:_ đây là "change" rút từ Track 01 (core). Nếu làm bonus
> (`make build-llama` + một sweep như `make sweep-thread` hoặc `make sweep-gpu`),
> có thể thay bằng một speedup mạnh hơn để ăn thêm 20 điểm bonus §5.

---

## 6. (Optional) Điều ngạc nhiên nhất

_(1–2 câu — không bắt buộc, nhưng người grader đọc tất cả)_

Bất ngờ nhất là continuous batching giữ RPS gần như không đổi khi tải tăng 5×
(10 → 50 users, 0 failures) nhưng tail latency P95 lại nổ gần 4× (6.7s → 24s) —
"throughput vẫn ổn" và "user vẫn vui" là hai chuyện hoàn toàn khác nhau, và đó
chính là lý do deck chọn goodput@SLO làm metric production thay vì throughput thô.

---

## 7. Self-graded checklist

- [x] `hardware.json` đã commit
- [x] `models/active.json` đã commit (hoặc paste path snapshot vào section 1)
- [x] `benchmarks/01-quickstart-results.md` đã commit
- [x] `benchmarks/02-server-results.md` (hoặc CSV từ `record-metrics.py`) đã commit
- [ ] `benchmarks/bonus-*.md` đã commit (ít nhất 1 sweep) — BONUS, chưa làm
- [ ] Ít nhất 6 screenshots trong `submission/screenshots/` (xem `submission/screenshots/README.md`) — CẦN CHỤP
- [ ] `make verify` exit 0 (chạy ngay trước khi push) — pass sau khi thêm screenshots
- [ ] Repo trên GitHub ở chế độ **public**
- [ ] Đã paste public repo URL vào VinUni LMS

---

**Quan trọng:** repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.
