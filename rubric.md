# Day 20 Lab — Grading Rubric (100 pts core + 20 bonus)

Track-2 Daily Lab weight = 30%.

> **Personal report.** Lab này dành cho laptop cá nhân của học viên. Số liệu của bạn không so sánh được với bạn cùng lớp — grade phụ thuộc **độ rõ ràng của setup + tuning của bạn trên chính máy bạn**, không phải tốc độ tuyệt đối. Một bạn dùng laptop Air M1 8 GB và một bạn dùng workstation RTX 4090 cùng được điểm tối đa nếu cả hai đều có rubric output đầy đủ + writeup mạch lạc.

Submit screenshots + artifacts in repo. The rubric is checked against **what's actually committed**, not what you say you did.

---

## Core (100 pts)

| # | Track | Criterion | Evidence | Pts |
|---|---|---|---|---:|
| 1 | 00-setup | `hardware.json` committed; `detect-hardware.py` ran clean | `submission/screenshots/01-hardware-probe.png` + `hardware.json` in repo | 5 |
| 2 | 00-setup | `models/active.json` committed; primary GGUF file path resolves | `models/active.json` shows valid path; can be either auto-downloaded or manual per `MANUAL-DOWNLOAD.md` | 5 |
| 3 | 01-quickstart | `benchmark.py` produces a P50/P95/P99 table for **both** Q4_K_M and Q2_K | `benchmarks/01-quickstart-results.md` exists, has 2-row table | 10 |
| 4 | 01-quickstart | TTFT and TPOT reported separately (not just E2E) | Same file; values plausible (TTFT > 0, TPOT > 0) | 5 |
| 5 | 02-server | `llama-server` runs and serves OpenAI-compat `/v1/chat/completions` | `submission/screenshots/03-server-running.png` showing both server log and a successful `curl` | 10 |
| 6 | 02-server | `/metrics` from the **native** server (`make serve-native`) shows non-zero `llamacpp:tokens_predicted_total` after a request | `curl :8080/metrics` excerpt (Python `make serve` has no /metrics — build via `make build-llama`) | 5 |
| 7 | 02-server | locust load run at `-u 10` for 60s, P95 reported | `submission/screenshots/04-locust-10.png` + table in REFLECTION.md §3 | 10 |
| 8 | 02-server | locust load run at `-u 50` for 60s, P95 reported | `submission/screenshots/05-locust-50.png` + table in REFLECTION.md §3 | 10 |
| 9 | 02-server | Continuous-batching observation under load (peak `llamacpp:n_busy_slots_per_decode` / `requests_processing`) from the native server reported in writeup | REFLECTION.md §3 — observation paragraph; CSV from `make metrics` (needs `make serve-native`) optional but recommended | 5 |
| 10 | 03-integration | `pipeline.py` runs end-to-end (3 example queries) and prints retrieved-context provenance | Terminal screenshot or paste in REFLECTION.md §4 | 10 |
| 11 | 03-integration | At least 3 of N16/N17/N18/N19 wired (or explicitly stubbed with reason) | REFLECTION.md §4 enumerates which pieces are real vs stubbed | 5 |
| 12 | submission | REFLECTION.md filled — every section has student-supplied content (not just template placeholders) | `make verify` exit code 0 | 10 |
| 13 | submission | "Single change that mattered most" paragraph (REFLECTION.md §5) — explains WHY, not just numbers | Section 5 reads as a coherent argument, not bullet dump | 10 |
| 14 | repo | Reproducibility — from clean clone, `make setup && make bench && make verify` produces the numbers in REFLECTION.md | Reviewable from commit history + `make verify` output | 10 |
|   |   | **Core total** |  | **100** |

---

## Bonus (20 pts, optional)

| Criterion | Evidence | Pts |
|---|---|---:|
| Built llama.cpp from source for your hardware (any backend) | `BONUS-llama-cpp-optimization/llama.cpp/build/bin/llama-bench --version` runs | 4 |
| Ran at least one sweep (`thread / quant / ctx-len / batch-size / gpu-offload`) and committed `benchmarks/bonus-*.md` | File exists in repo with non-trivial table | 4 |
| Bonus speedup quantified — before/after numbers in REFLECTION.md §5 | "before: X tok/s, after: Y tok/s, speedup: Z×" pattern | 4 |
| Attempted at least one open challenge from `BONUS-llama-cpp-optimization/CHALLENGES.md` (C1–C7) | Writeup section in REFLECTION.md or extra file `bonus/<challenge>.md` | 4 |
| MLX comparison run (Apple Silicon only) | `benchmarks/bonus-mlx-vs-llama-cpp.md` committed | 4 |
|  | **Bonus total** | **20** |

The bonus does **not** affect your core grade negatively; missing it is fine. A **strong** bonus submission gets a substantive instructor written review focused on reasoning quality (not raw numbers).

---

## Submission

**KHÔNG cần PR — chỉ submit GitHub URL công khai vào VinUni LMS.**

1. Fork hoặc copy repo này lên GitHub account của bạn, set repo **public**.
2. Hoàn thành 4 tracks (`00-setup` → `01-quickstart` → `02-server` → `03-integration`).
3. Add screenshots vào `submission/screenshots/` (xem danh sách trong `submission/screenshots/README.md`).
4. Điền `submission/REFLECTION.md` đầy đủ.
5. Chạy `make verify` ở root — đảm bảo exit code 0.
6. Push lên public repo.
7. Paste public GitHub URL vào ô submission của Day 20 trong VinUni LMS.

**Quan trọng:** Repo phải **public** đến khi điểm được công bố. Nếu private, grader không xem được → 0 điểm.

---

## Late policy / regrade

Standard Track-2 policy applies — see `INDEX-Track2.md` ở repo course material.

---

## How the grader runs your repo

The grader does roughly this on your committed repo:

```bash
git clone https://github.com/<you>/Day20-Track2-ModelServing-Lab
cd Day20-Track2-ModelServing-Lab
cat hardware.json                                        # Q1, Q2 evidence
cat benchmarks/01-quickstart-results.md                  # Q3, Q4
ls submission/screenshots/                               # Q5–Q11 visual evidence
cat submission/REFLECTION.md                             # Q12, Q13
make verify                                              # Q14 — exits 0?
ls benchmarks/bonus-*.md                                 # bonus
```

If `make verify` exits non-zero, the grader may deduct Q14's 10 pts even if the rest is fine — so run it before you push.
