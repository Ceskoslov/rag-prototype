#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null
docker compose version >/dev/null
if [ ! -f .env ]; then
  cp .env.example .env
fi
docker compose up --build -d --wait
printf 'Universal RAG is available at http://localhost:3000\n'
printf 'Offline defaults check wiring. Configure real LLM and embeddings for quality evaluation.\n'
