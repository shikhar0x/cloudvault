#!/usr/bin/env bash
# Seed the CloudVault database with demo data (development only).
#
# Usage (from the repository root):
#   bash scripts/seed.sh
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
exec "$PYTHON" database/seeds/seed.py
