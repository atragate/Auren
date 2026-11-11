#!/usr/bin/env bash
set -euo pipefail
auren_project=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
exec python3 "$auren_project/auren.py" "$@"
