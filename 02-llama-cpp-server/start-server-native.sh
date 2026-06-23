#!/usr/bin/env bash
# Launch the NATIVE llama.cpp `llama-server` binary WITH Prometheus /metrics on :8080.
#
# Why this exists: the Python server (`make serve` / start-server.sh, i.e.
# `python -m llama_cpp.server`) is the zero-build path for chat + load, but it has
# NO /metrics endpoint. The observability step (§2/§3 — /metrics,
# n_busy_slots_per_decode, requests_processing) needs this native binary instead.
#
# Build it first:  make build-llama   (clones + cmake-builds llama.cpp for your HW)
# Linux + macOS. Windows: run the binary under BONUS-.../llama.cpp/build/bin/ directly.
set -euo pipefail
cd "$(dirname "$0")/.."

BIN="BONUS-llama-cpp-optimization/llama.cpp/build/bin/llama-server"
if [ ! -x "$BIN" ]; then
  echo "ERROR: native llama-server not found at $BIN" >&2
  echo "Build it first:  make build-llama   (clones + cmake-builds llama.cpp)" >&2
  exit 1
fi

MODEL=$(python -c 'import json; print(json.load(open("models/active.json"))["primary_model"])')
THREADS=$(python -c 'import json; hw=json.load(open("hardware.json")); print(hw["cpu"].get("cores_physical") or 4)')
NGL="${LAB_N_GPU_LAYERS:-99}"
PARALLEL="${LAB_PARALLEL:-4}"
CTX="${LAB_N_CTX:-2048}"

echo "==> Starting NATIVE llama-server (with --metrics) on http://0.0.0.0:8080"
echo "    binary  : $BIN"
echo "    model   : $MODEL"
echo "    parallel: $PARALLEL   ctx: $CTX   ngl: $NGL"
echo "    metrics : http://localhost:8080/metrics  (n_busy_slots_per_decode, requests_processing, tokens_predicted_total)"
echo

exec "$BIN" \
    -m "$MODEL" \
    --host 0.0.0.0 --port 8080 \
    -t "$THREADS" \
    -ngl "$NGL" \
    --parallel "$PARALLEL" --cont-batching \
    --ctx-size "$CTX" \
    --metrics
