#!/usr/bin/env bash
# Launch a DEDICATED embedding server on :8081  (Day 20 §5 Serving Regimes).
# Embedding serving runs in embedding/pooling mode — keep it separate from the
# chat server on :8080. Reuses the active GGUF (zero extra download); for real
# retrieval quality use a dedicated embedding model (Qwen3-Embedding, BGE-M3).
# Linux + macOS. Windows: run the python -m llama_cpp.server line directly.
set -euo pipefail
cd "$(dirname "$0")/.."

MODEL=$(python -c 'import json; print(json.load(open("models/active.json"))["primary_model"])')
THREADS=$(python -c 'import json; hw=json.load(open("hardware.json")); print(hw["cpu"].get("cores_physical") or 4)')

echo "==> Starting embedding server (prefill-only) on http://0.0.0.0:8081"
echo "    model   : $MODEL"
echo "    threads : $THREADS"
echo

# If your llama-cpp-python version rejects '--embedding true', use '--embedding' alone.
exec python -m llama_cpp.server \
    --model "$MODEL" \
    --embedding true \
    --host 0.0.0.0 --port 8081 \
    --n_threads "$THREADS"
