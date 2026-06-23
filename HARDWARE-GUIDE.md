# Hardware Guide — Pick Your Path

> **Your laptop's spec is the lab.** Lab này không có shared sandbox — mỗi học viên chạy trên máy mình. Grading rubric thưởng độ rõ ràng của *your own before/after*, không phải absolute throughput. Một bạn dùng Air M1 8 GB và một bạn dùng RTX 4090 đều có thể đạt full marks. Đừng so số liệu của bạn với bạn cùng lớp — so với chính `make bench` lần đầu của bạn.

Use this chart to pick a model, a quantization, and a llama.cpp backend that will actually run on **your** hardware.

## 1. Model size by RAM

| Available RAM | Recommended model (GGUF) | Quantization | File size |
|---|---|---|---|
| 4 GB | TinyLlama-1.1B | Q4_K_M | ≈ 0.7 GB |
| 8 GB | Qwen2.5-1.5B-Instruct | Q4_K_M | ≈ 1.0 GB |
| 16 GB | Llama-3.2-3B-Instruct | Q4_K_M | ≈ 2.0 GB |
| 32 GB+ | Qwen2.5-7B-Instruct | Q4_K_M | ≈ 4.7 GB |

Rule of thumb: **GGUF Q4_K_M file size ≤ ½ × free RAM**. The other half holds OS, browser, KV cache, and headroom.

> **2026 model options:** the tiers above are safe defaults. Newer open-weight small models drop in at the same RAM tiers — **Qwen3** (1.7B / 4B / 8B), **Gemma 3** (1B / 4B, with QAT-INT4 builds), **Llama-3.3**, and **gpt-oss-20B** (MXFP4, MoE 3.6B active, ~16 GB) for 32 GB+ laptops. Same GGUF + llama.cpp path — just swap the Hugging Face repo id in `00-setup/download-model.py`.

`00-setup/download-model.py` reads `hardware.json` (from `detect-hardware.py`) and pulls the right tier automatically.

## 2. llama.cpp backend by hardware

| Accelerator | Build flag | OS support | Notes |
|---|---|---|---|
| **CPU only** | (default) | All | Always works. Bonus track tunes AVX2/AVX-512/NEON. |
| **NVIDIA CUDA** | `-DGGML_CUDA=on` | Linux, Windows, WSL2 | Needs CUDA Toolkit 12+. `-ngl 99` offloads all layers to GPU. |
| **Apple Metal** | `-DGGML_METAL=on` | macOS Apple Silicon only | Default on M1–M4. Free, no setup. |
| **AMD ROCm/HIP** | `-DGGML_HIPBLAS=on` | Linux | RDNA2+ GPUs. Pinned to specific ROCm versions. |
| **Vulkan** | `-DGGML_VULKAN=on` | Linux, Windows | Works on Intel Arc, AMD discrete, NVIDIA, Apple (via MoltenVK). Slower than vendor-native but universal. |
| **OpenCL / SYCL** | `-DGGML_SYCL=on` | Linux, Windows | Intel oneAPI path; mostly useful for Intel Arc. |

`00-setup/detect-hardware.py` picks the backend with the best speed-vs-setup-cost ratio for what it finds.

## 3. Decision tree

```
Do you have an NVIDIA GPU with ≥ 4 GB VRAM?
├─ Yes (Linux or Windows) → CUDA build (full GPU offload)
└─ No
   ├─ Apple Silicon Mac (M1+)? → Metal build (zero setup, just works)
   ├─ AMD discrete on Linux? → Vulkan build (simpler) or ROCm build (faster, fragile)
   ├─ Intel Arc / modern iGPU? → Vulkan build
   └─ Older Mac / weak iGPU / unsure → CPU build, focus on bonus track AVX/NEON tuning
```

The bonus track is where weaker hardware shines — every CPU optimization (proper thread count, AVX2 vs AVX-512 build, batch sizing) shows up as a measurable speedup.

## 4. Disk space

- Setup downloads ~500 MB Python deps + ~1–5 GB model weights (depends on RAM tier).
- Bonus track adds ~1 GB for llama.cpp source build artifacts + extra quantizations to compare.
- Plan for **8 GB free** before starting.

## 5. Network

- Hugging Face downloads can stall behind university firewalls. The setup script tries Hugging Face, then a mirror list. If both fail, see `00-setup/MANUAL-DOWNLOAD.md` for browser instructions.
- No Docker pulls needed — that was the whole point of dropping the vLLM track.

## 6. What about MLX, MLC, ExecuTorch, etc.?

MLX is offered as `BONUS-mlx-macos/` for Apple Silicon students who want a side-by-side runtime comparison. The other Apple/mobile-first runtimes (MLC LLM, ExecuTorch, Core ML) are mentioned in the deck but not built into the lab — pick one as a stretch project if you finish early.
