#!/bin/bash
# shellcheck disable=SC2317
set -euo pipefail

# SickChill Docker entrypoint.sh
# - Makes the Python venv persistent inside your datadir (e.g. /data/.venv)
#   so the entire Python environment lives alongside config, cache, logs etc.
#   Perfect for NAS backups and universal installs.
# - Minimal PUID/PGID support (only chown on datadir)
# - Auto-copies pre-built venv from image on first start
# - Auto-updates venv when Docker image is upgraded (via BUILD_INFO)

echo "==> SickChill container starting..."

# Environment / Defaults
PUID=${PUID:-1000}
PGID=${PGID:-1000}
DATADIR=${DATADIR:-/data}
UMASK=${UMASK:-002}
PORT=${PORT:-8081}
VENV_IMAGE="/opt/sickchill/.venv"
VENV_PERSISTENT="${DATADIR}/.venv"

umask "$UMASK"
mkdir -p "$DATADIR"

# PUID/PGID — only chown datadir
if [ "$(id -u)" = "0" ]; then
    echo "==> Setting ownership on $DATADIR to PUID=$PUID PGID=$PGID"
    chown -R "$PUID:$PGID" "$DATADIR" || true
fi

# Persistent venv initialization / update
if [ ! -x "$VENV_PERSISTENT/bin/sickchill" ]; then
    echo "==> First run or missing venv: copying pre-built Python environment to $VENV_PERSISTENT"
    rm -rf "$VENV_PERSISTENT"
    cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"

    if [ -f /sickchill/BUILD_INFO ]; then
        cp /sickchill/BUILD_INFO "$VENV_PERSISTENT/BUILD_INFO"
    fi
    echo "==> Persistent venv initialized successfully."
else
    if [ -f "$VENV_PERSISTENT/BUILD_INFO" ] && [ -f /sickchill/BUILD_INFO ]; then
        if ! cmp -s "$VENV_PERSISTENT/BUILD_INFO" /sickchill/BUILD_INFO; then
            echo "==> New image detected - updating persistent venv..."
            rm -rf "$VENV_PERSISTENT"
            cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"
            cp /sickchill/BUILD_INFO "$VENV_PERSISTENT/BUILD_INFO"
            echo "==> Persistent venv updated."
        fi
    fi
fi

# Ensure correct ownership on the (possibly newly copied) venv
if [ "$(id -u)" = "0" ]; then
    chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
fi

# Launch SickChill
echo "==> Launching sickchill from persistent venv ($VENV_PERSISTENT)"

export VIRTUAL_ENV="$VENV_PERSISTENT"
export PATH="$VENV_PERSISTENT/bin:$PATH"

SICKCHILL_BIN="$VENV_PERSISTENT/bin/sickchill"

if [ ! -x "$SICKCHILL_BIN" ]; then
    echo "ERROR: sickchill not found in $VENV_PERSISTENT"
    echo "Try: rm -rf $VENV_PERSISTENT && docker restart sickchill"
    exit 1
fi

# Drop privileges + exec CMD
if [ "$(id -u)" = "0" ] && [ "$PUID" != "0" ]; then
    echo "==> Dropping privileges to $PUID:$PGID..."
    exec gosu "$PUID:$PGID" "$@"
else
    echo "==> Starting as $(id -u):$(id -g)..."
    exec "$@"
fi
