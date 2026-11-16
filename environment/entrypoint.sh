#!/bin/bash
# Start JupyterLab for the CivicDesk course. Used by Docker and by local sh.
set -euo pipefail
cd "$(dirname "$0")/.."
/usr/bin/supervisord -c /etc/supervisor/supervisord.conf
jupyter labextension disable "@jupyterlab/apputils-extension:announcements" 2>/dev/null || true
exec jupyter lab \
  --ip=0.0.0.0 \
  --allow-root \
  --no-browser \
  --ServerApp.token='' \
  --ServerApp.password='' \
  --ServerApp.root_dir="$(pwd)"
