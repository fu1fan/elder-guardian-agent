#!/bin/sh
set -eu

: "${GUARDIAN_API_BASE:=http://localhost:8000}"

cat > /usr/share/nginx/html/config.js <<EOF
window.__ELDER_GUARDIAN_CONFIG__ = {
  GUARDIAN_API_BASE: "${GUARDIAN_API_BASE}"
};
EOF

