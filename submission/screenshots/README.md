# Required screenshots

Drop the following PNG/JPG files into this folder before submitting. Filenames are suggested, not required — grader reads `REFLECTION.md` to map screenshots to evidence.

## Minimum (6 shots)

1. **`01-hardware-probe.png`** — terminal output of `python 00-setup/detect-hardware.py`. Must show CPU, RAM, accelerator, recommended model tier.
2. **`02-quickstart-bench.png`** — terminal output of `python 01-llama-cpp-quickstart/benchmark.py` showing the per-prompt TTFT/TPOT/E2E table.
3. **`03-server-running.png`** — the server running (terminal showing it listening on `http://0.0.0.0:8080`, from `make serve`). The `/metrics` excerpt is separate evidence (rubric item 6) and comes from the **native** server (`make serve-native`) — the Python server has no `/metrics`.
4. **`04-locust-10.png`** — locust headless summary table after `-u 10 -t 1m`. Must show RPS + P50/P95/P99.
5. **`05-locust-50.png`** — same but `-u 50 -t 1m`.
6. **`06-bonus-sweep.png`** — at least one chart or terminal table from `BONUS-llama-cpp-optimization/benchmarks/*.py` (thread / quant / ctx-len / gpu-offload / batch-size). Pick the one with the most interesting result on your hardware.

## Optional (extra credit, mentioned in `rubric.md`)

7. **`07-grafana-or-prom.png`** — if you ran the optional Prometheus container, show a Grafana panel or the Prometheus query UI with `llamacpp:n_busy_slots_per_decode` (or `requests_processing`) plotted.
8. **`08-mlx-vs-llamacpp.png`** — Apple Silicon students who ran the MLX bonus.
9. **`09-pipeline-output.png`** — `python 03-milestone-integration/pipeline.py` end-to-end output.

## Tips

- Crop tight — full-screen browser shots get rejected. The grader wants to see the data, not your wallpaper.
- Dark or light terminal both fine; just make sure text is readable.
- For load-test screenshots, include the locust *Type · Name · # reqs · Median · Avg · 95%ile · 99%ile* row — that's the rubric evidence.
