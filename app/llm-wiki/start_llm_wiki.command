#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="llm-wiki-sciverse"
HOST="${LLM_WIKI_HOST:-127.0.0.1}"
PORT="${LLM_WIKI_PORT:-8765}"

cd "$ROOT_DIR"

TOKEN="$(security find-generic-password -a "$USER" -s "$SERVICE_NAME" -w 2>/dev/null || true)"
if [ -n "$TOKEN" ]; then
  export SCIVERSE_API_TOKEN="$TOKEN"
  echo "Loaded Sciverse token from macOS Keychain."
else
  echo "Sciverse token not found in Keychain service: $SERVICE_NAME"
  echo "You can still use the Web UI and paste a token in the Sciverse panel."
  echo "To store a token, run: scripts/store_sciverse_token.command"
fi

if lsof -ti tcp:"$PORT" >/dev/null 2>&1; then
  echo "Port $PORT is already in use."
  echo "Stop the existing server, or start with another port:"
  echo "  LLM_WIKI_PORT=8766 $0"
  exit 1
fi

echo "Starting LLM Wiki Web UI: http://$HOST:$PORT"
python3 scripts/wiki_web.py --host "$HOST" --port "$PORT"
