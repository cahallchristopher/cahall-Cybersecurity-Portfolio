#!/usr/bin/env bash
set -euo pipefail

MODEL="qwen2.5:7b"
BATCH_SIZE=10
MAX=150   # total iterations to critique

cd "$(dirname "$0")"

for ((start=0; start<MAX; start+=BATCH_SIZE)); do
  end=$((start + BATCH_SIZE - 1))

  echo "=============================="
  echo "Processing batch $start to $end"
  echo "=============================="

  for i in $(seq -f "%03g" $start $end); do
    FILE="outputs/iteration_${i}.txt"
    OUT="outputs/iteration_${i}_critique.txt"

    [ -f "$FILE" ] || continue
    [ -f "$OUT" ] && echo "Skipping iteration_$i (already critiqued)" && continue

    echo "Critiquing iteration_$i"

    OLLAMA_NUM_THREADS=4 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    OLLAMA_KEEP_ALIVE=0 \
    ollama run "$MODEL" "
You are reviewing a resume rewrite.

CONTENT:
$(sed -n '1,200p' "$FILE")

TASK:
1) Score this from 1–10 for SOC Analyst I readiness
2) List 3 weaknesses
3) Rewrite ONE bullet to be more defensible
" > "$OUT"
  done

  echo "Batch $start to $end complete."
  echo "Sleeping 10 seconds to cool down..."
  sleep 10
done

echo "All self-critiques complete."

