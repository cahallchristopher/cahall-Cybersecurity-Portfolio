#!/usr/bin/env bash
set -e

echo "[1/4] Running resume agent"
python agent/agent_rag.py

echo "[2/4] Running self-critique"
./self_critique.sh

echo "[3/4] Merging best bullets"
./merge_best_bullets.sh

echo "[4/4] Pipeline complete"
echo "Review outputs/final_resume.txt and outputs/best_bullets.txt"
