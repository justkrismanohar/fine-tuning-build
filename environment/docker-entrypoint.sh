#!/bin/bash
# Seed notebooks if the Windows mount was empty, load baked OLMo/Phi, start Jupyter.
set -euo pipefail

if [ ! -f /civicdesk/tier1/day1/civicdesk_lab.py ]; then
  echo "Seeding /civicdesk from the image (mount was empty or missing)."
  mkdir -p /civicdesk
  cp -a /opt/civicdesk/. /civicdesk/
fi

cd /civicdesk
mkdir -p /civicdesk/tier1/day1/logs

MODELS_DIR="${CIVICDESK_MODELS_DIR:-/models}"
LOAD="${CIVICDESK_LOAD_MODELS:-olmo,phi}"
SERVER="${CIVICDESK_SERVER:-/civicdesk/tier1/day1/hf_openai_server.py}"

start_one() {
  local key="$1"
  local port="$2"
  local path="${MODELS_DIR}/${key}"
  if [ ! -d "${path}" ]; then
    echo "No baked weights at ${path}; skip ${key}."
    return 0
  fi
  echo "Loading ${key} from ${path} on :${port} ..."
  python "${SERVER}" --model "${path}" --port "${port}" --host 0.0.0.0 \
    > "/tmp/${key}_server.log" 2>&1 &
  echo $! > "/tmp/${key}_server.pid"
}

wait_one() {
  local port="$1"
  local name="$2"
  local i=0
  until curl -sf "http://127.0.0.1:${port}/v1/models" >/dev/null; do
    i=$((i + 1))
    if [ "${i}" -gt 90 ]; then
      echo "Timed out waiting for ${name} on :${port}. Last log:"
      tail -n 40 "/tmp/${name}_server.log" || true
      return 1
    fi
    sleep 4
  done
  echo "${name} is up on :${port}"
}

if echo ",${LOAD}," | grep -q ",olmo,"; then
  start_one olmo 8000
fi
if echo ",${LOAD}," | grep -q ",phi,"; then
  start_one phi 8001
fi

if echo ",${LOAD}," | grep -q ",olmo,"; then
  wait_one 8000 olmo || true
fi
if echo ",${LOAD}," | grep -q ",phi,"; then
  wait_one 8001 phi || true
fi

python - <<'PY'
import json
from pathlib import Path
p = Path("/civicdesk/tier1/day1/logs/endpoint.json")
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(json.dumps({
    "backend": "local",
    "mode": "live",
    "engine": "hf",
    "olmo": {"base_url": "http://127.0.0.1:8000/v1", "model": "allenai/OLMo-2-0425-1B-Instruct", "port": 8000},
    "phi": {"base_url": "http://127.0.0.1:8001/v1", "model": "microsoft/Phi-4-mini-instruct", "port": 8001},
}, indent=2), encoding="utf-8")
print("wrote", p)
PY

if [ "$#" -eq 0 ]; then
  set -- jupyter lab \
    --ip=0.0.0.0 \
    --allow-root \
    --no-browser \
    --ServerApp.token='' \
    --ServerApp.password='' \
    --ServerApp.root_dir=/civicdesk
fi
exec "$@"
