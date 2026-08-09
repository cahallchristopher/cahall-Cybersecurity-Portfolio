#!/bin/bash
# PrivateGPT Red Team KB -- Start Script
cd ~/privategpt-data

# CRITICAL: unset path -- empty string is NOT the same as unset
unset PGPT_QDRANT_PATH

export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_EMBEDDING_API_BASE=http://localhost:11434/v1
export PGPT_LLM_DEFAULT=nous-hermes2:10.7b
export PGPT_EMBEDDING_DEFAULT=mxbai-embed-large:latest
export PGPT_QDRANT_URL=http://localhost:6333
export PGPT_QDRANT_PREFER_GRPC=false
export PGPT_LOCAL_DATA_FOLDER=/home/$USER/privategpt-data/local_data
export PORT=8080

echo "Starting PrivateGPT..."
echo "  LLM:       $PGPT_LLM_DEFAULT"
echo "  Embedding: $PGPT_EMBEDDING_DEFAULT"
echo "  Qdrant:    $PGPT_QDRANT_URL"
echo "  Port:      $PORT"
echo ""
private-gpt serve
