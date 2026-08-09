#!/bin/bash
# PrivateGPT Red Team KB -- One-Command Setup
set -e

echo ""
echo "============================================"
echo "  PrivateGPT Red Team KB -- Setup"
echo "============================================"
echo ""

echo "[1/6] Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.bashrc

echo ""
echo "[2/6] Installing PrivateGPT v1.0.1..."
uv tool install --python 3.11   --find-links https://wheels.privategpt.dev/packages/   "private-gpt[core]"

echo ""
echo "[3/6] Patching built-in settings.yaml..."
SETTINGS=$(find ~/.local/share/uv -name "settings.yaml" 2>/dev/null | grep site-packages | head -1)
if [ -n "$SETTINGS" ]; then
  sed -i "s|path: \${PGPT_QDRANT_PATH:local_data/qdrant}|path: \${PGPT_QDRANT_PATH:}|" "$SETTINGS"
  echo "  Patched: $SETTINGS"
fi

echo ""
echo "[4/6] Pulling Ollama models..."
ollama pull nous-hermes2:10.7b
ollama pull mxbai-embed-large

echo ""
echo "[5/6] Deploying Qdrant..."
mkdir -p ~/privategpt-data/qdrant_storage
docker rm -f qdrant 2>/dev/null || true
docker run -d   --name qdrant   --restart unless-stopped   -p 6333:6333   -p 6334:6334   -v ~/privategpt-data/qdrant_storage:/qdrant/storage   qdrant/qdrant
sleep 3
curl -s http://localhost:6333/healthz && echo "  Qdrant healthy"

echo ""
echo "[6/6] Creating KB structure..."
mkdir -p ~/redteam-kb/{cves,exploits,tools,payloads,scripts}
mkdir -p ~/privategpt-data/local_data

echo ""
echo "============================================"
echo "  Setup complete!"
echo "  Start: ~/privategpt-data/start.sh"
echo "  UI:    http://localhost:8080/ui"
echo "============================================"
