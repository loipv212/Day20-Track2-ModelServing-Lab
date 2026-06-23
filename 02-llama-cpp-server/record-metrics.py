#!/usr/bin/env python3
"""Poll the native llama-server's /metrics every N seconds during a load run, write CSV.

NOTE: only the native llama.cpp `llama-server` binary exposes /metrics. The Python
server (`make serve`) does NOT. Start the native one first: `make build-llama` then
`make serve-native` (it boots on :8080 with --metrics).

Usage:
    # Terminal 1: make serve-native      # native server WITH /metrics on :8080
    # Terminal 2: make load-10           # drive some traffic
    # Terminal 3: python 02-llama-cpp-server/record-metrics.py --duration 60
"""
from __future__ import annotations

import argparse
import csv
import re
import sys
import time
from pathlib import Path

import httpx

INTERESTING = {
    "llamacpp:n_decode_total",
    "llamacpp:n_busy_slots_per_decode",
    "llamacpp:tokens_predicted_total",
    "llamacpp:prompt_tokens_total",
    "llamacpp:requests_processing",
    "llamacpp:requests_deferred",
}

LINE = re.compile(r"^([a-z_:]+)(?:\{[^}]*\})?\s+([0-9eE.+-]+)$")


def scrape(url: str) -> dict[str, float]:
    out: dict[str, float] = {}
    try:
        text = httpx.get(url, timeout=3.0).text
    except httpx.HTTPError:
        return out
    for raw in text.splitlines():
        if raw.startswith("#"):
            continue
        m = LINE.match(raw.strip())
        if not m:
            continue
        name, val = m.group(1), m.group(2)
        if name in INTERESTING:
            try:
                out[name] = float(val)
            except ValueError:
                pass
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8080/metrics")
    parser.add_argument("--duration", type=int, default=60, help="seconds to record")
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between scrapes")
    parser.add_argument("--out", default="benchmarks/02-server-metrics.csv")
    args = parser.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    deadline = time.time() + args.duration
    rows: list[dict] = []
    fails = 0
    print(f"==> Recording {args.url} for {args.duration}s, every {args.interval}s")
    while time.time() < deadline:
        sample = scrape(args.url)
        if sample:
            sample["t"] = round(time.time(), 1)
            rows.append(sample)
            print(
                f"   t={sample['t']:.0f}  "
                f"reqs_proc={sample.get('llamacpp:requests_processing', 0):.0f}  "
                f"deferred={sample.get('llamacpp:requests_deferred', 0):.0f}  "
                f"busy_slots={sample.get('llamacpp:n_busy_slots_per_decode', 0):.2f}  "
                f"tok_pred={sample.get('llamacpp:tokens_predicted_total', 0):.0f}"
            )
        else:
            fails += 1
            print("   (scrape failed — is llama-server running with --metrics?)")
            if not rows and fails >= 3:
                print("   3 scrapes failed with nothing on the endpoint — stopping early.")
                break
        time.sleep(args.interval)

    if not rows:
        print(f"ERROR: no /metrics samples collected from {args.url}.", file=sys.stderr)
        print("  The Python server (`make serve`) has NO /metrics endpoint.", file=sys.stderr)
        print("  Use the NATIVE llama.cpp server instead:", file=sys.stderr)
        print("    make build-llama      # one-time: build llama-server from source", file=sys.stderr)
        print("    make serve-native     # starts it WITH --metrics on :8080", file=sys.stderr)
        print("  then drive load (make load-10) and re-run `make metrics`.", file=sys.stderr)
        return 1

    fieldnames = sorted({k for r in rows for k in r.keys()})
    with out_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    print(f"\n==> Wrote {out_path} ({len(rows)} samples)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
