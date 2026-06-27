#!/bin/bash
set -euo pipefail

SERVICE_NAME="llm-wiki-sciverse"

echo "Store Sciverse API token in macOS Keychain."
echo "The token will not be written to project files."
echo
read -r -s -p "Sciverse API token: " TOKEN
echo

if [ -z "$TOKEN" ]; then
  echo "No token provided."
  exit 1
fi

security delete-generic-password -a "$USER" -s "$SERVICE_NAME" >/dev/null 2>&1 || true
security add-generic-password -a "$USER" -s "$SERVICE_NAME" -w "$TOKEN"

echo
echo "Saved token to Keychain service: $SERVICE_NAME"
