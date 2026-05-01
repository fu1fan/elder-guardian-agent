#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR/apps/guardian-core"

echo "Starting guardian-core on http://localhost:8000"
echo
echo "In other terminals you can run:"
echo "  docker compose up mosquitto"
echo "  python scripts/simulate_device.py"
echo "  python scripts/simulate_sensor.py --event co2_high"
echo "  python scripts/simulate_vision.py --event long_static"
echo "  pnpm --filter web-dashboard dev"
echo "  pnpm --filter elder-hmi dev"
echo

export PYTHONPATH="$ROOT_DIR/packages/guardian-shared:$PYTHONPATH"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

