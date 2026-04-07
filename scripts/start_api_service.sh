#!/usr/bin/env bash
set -euo pipefail

link_runtime_libs() {
  local dir="$1"
  local stem="$2"
  local versioned=""
  local major=""

  versioned="$(find "$dir" -maxdepth 1 -type f -name "${stem}.so.*" | sort | head -n 1 || true)"
  if [[ -z "$versioned" ]]; then
    return 0
  fi

  ln -sf "$(basename "$versioned")" "$dir/${stem}.so"
  major="$(basename "$versioned" | sed -E 's/.*\.so\.([0-9]+)(\..*)?/\1/')"
  if [[ -n "$major" ]]; then
    ln -sf "$(basename "$versioned")" "$dir/${stem}.so.${major}"
  fi
}

for lib_dir in /app/util/llama/bin /app/util/fun_asr_gguf/inference/bin; do
  link_runtime_libs "$lib_dir" "libggml"
  link_runtime_libs "$lib_dir" "libggml-base"
  link_runtime_libs "$lib_dir" "libggml-cpu"
  link_runtime_libs "$lib_dir" "libllama"
done

export LD_LIBRARY_PATH="/app/util/llama/bin:/app/util/fun_asr_gguf/inference/bin:${LD_LIBRARY_PATH:-}"

python3 scripts/bootstrap_fun_asr_env.py

exec uvicorn capsweb.app:app \
  --host "${CW_HOST:-0.0.0.0}" \
  --port "${CW_PORT:-8000}"
