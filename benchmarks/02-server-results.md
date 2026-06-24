# 02 — llama-server Load Test Results

Server: `llama-server` (OpenAI-compat) on `:8080`, model `qwen2.5-1.5b-instruct-q4_k_m.gguf`,
CUDA backend (`-DGGML_CUDA=on`), RTX 3050 Ti Laptop GPU (4 GiB).

Load generator: `locust -f 02-llama-cpp-server/load-test.py --headless -u <N> -r 1 -t 1m`.

| Concurrency | Total RPS | TTFB P50 (ms) | E2E P95 (ms) | E2E P99 (ms) | Failures |
|--:|--:|--:|--:|--:|--:|
| 10 | 1.44 | 5700 | 6700 | 7600 | 0 |
| 50 | 1.36 | 11000 | 24000 | 25000 | 0 |

## Continuous-batching observation

Khi tăng tải từ 10 → 50 users, throughput tổng (RPS) gần như không đổi
(1.44 → 1.36) và **0 failures** — server hấp thụ hết request nhờ continuous
batching. Cái giá phải trả là độ trễ per-request: P50 E2E tăng 5.7s → 11s,
P95 tăng vọt 6.7s → 24s. Đây đúng là dấu hiệu của một hệ thống **đã bão hòa
(saturated)**: tổng băng thông giữ nguyên (giới hạn bởi compute/VRAM của một
GPU 4 GiB), nhưng các request mới phải xếp hàng → queueing delay đẩy tail
latency lên. Đây là minh hoạ trực tiếp cho luận điểm goodput@SLO của deck §8:
RPS thô vẫn ổn ở 50 users, nhưng nếu SLO là "P95 < 8s" thì goodput thực tế
đã sụp đổ ở mức tải này.

> Ghi chú: số `/metrics` (`llamacpp:n_busy_slots_per_decode`,
> `requests_processing`) cần chạy native server (`make serve-native` +
> `make metrics`). Nếu chạy được, paste CSV `02-server-metrics.csv` vào đây.
