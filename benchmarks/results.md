# Day 20 Lab — Numbers Scratchpad

> **This is NOT your graded report.** The graded report is **[`submission/REFLECTION.md`](../submission/REFLECTION.md)** — fill that out for the rubric.
>
> This file is a *scratchpad* for raw numbers as you generate them. Some of the lab scripts (`benchmark.py`, `record-metrics.py`, the bonus sweeps) auto-write derived markdown files under `benchmarks/01-quickstart-results.md`, `benchmarks/02-server-metrics.csv`, `benchmarks/bonus-*.md`. Use this `results.md` to keep loose notes / hand-copied numbers / observations as you work, then transfer the polished version into `submission/REFLECTION.md` at the end.

## Hardware

- Platform: Linux 6.17.0-35-generic (x86_64)
- CPU: AMD Ryzen 5 5600H with Radeon Graphics (12 physical · 12 logical cores)
- RAM (GB): 15.0 GB
- GPU/accelerator: NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096 MiB
- llama.cpp build backend: CUDA (-DGGML_CUDA=on)

## Track 01 — Quickstart

| Model | Load (ms) | TTFT P50/P95 (ms) | TPOT P50/P95 (ms) | E2E P50/P95/P99 (ms) | Decode rate (tok/s) |
|---|--:|--:|--:|--:|--:|
| (Q4_K_M) | 855 | 145 / 220 | 40.6 / 41.8 | 2728 / 2785 / 2794 | 24.6 |
| (Q2_K)   | 223 | 164 / 256 | 30.6 / 33.6 | 2060 / 2328 / 2388 | 32.7 |

**One observation:** Mặc dù bản lượng tử hóa Q4_K_M chậm hơn Q2_K (24.6 tok/s so với 32.7 tok/s) và mất nhiều thời gian tải hơn (855ms so với 223ms), nhưng thời gian phản hồi token đầu tiên (TTFT P50) của Q4_K_M lại hơi nhanh hơn Q2_K trên máy của tôi (145ms so với 164ms).

## Track 02 — llama-server load test

Run `locust -f 02-llama-cpp-server/load-test.py --headless -u N -r 1 -t 1m` for two values of N.

| Concurrency | RPS | P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 1.44 | 5700 | 6700 | 7600 | 0 |
| 50 | 1.36 | 11000 | 24000 | 25000 | 0 |

**Continuous-batching observation:** Khi tăng tải từ 10 lên 50 users, thông lượng RPS gần như được giữ nguyên (giảm nhẹ từ 1.44 xuống 1.36) và không có request nào bị lỗi (0 failures). Tuy nhiên, độ trễ E2E tăng mạnh (P50 tăng từ 5.7s lên 11s, P95 tăng vọt lên 24s). Điều này cho thấy cơ chế continuous batching hoạt động rất tốt trong việc duy trì tổng băng thông hệ thống, nhưng phải đánh đổi bằng độ trễ của từng request riêng lẻ khi hàng đợi bị dồn ứ.

## Track 03 — Milestone Integration

- N16 piece used: 
- N17 piece used: 
- N18 piece used: 
- N19 piece used: 
- One-paragraph reflection on where the latency goes (embed / retrieve / llama-server): Dựa trên kết quả chạy pipeline thực tế, thời gian truy xuất tài liệu (`retrieve`) gần như bằng 0 (0.0 ms), có thể do dữ liệu (các đoạn chunk như 'n20-paged', 'n20-radix') đã được nạp sẵn hoặc truy xuất từ bộ nhớ tạm. Toàn bộ độ trễ (latency) của hệ thống (100%) dồn vào khâu sinh văn bản của `llama-server` (`llm`), dao động từ khoảng 527.6 ms đến 1089.7 ms cho mỗi truy vấn. Điều này chứng tỏ bottleneck (điểm nghẽn) lớn nhất trong hệ thống RAG thực tế nằm ở sức mạnh xử lý inference của LLM.