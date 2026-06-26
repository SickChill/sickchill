#!/bin/bash
# shellcheck disable=SC2317
set -euo pipefail

# SickChill Docker entrypoint.sh
# - Persistent venv in datadir
# - Minimal PUID/PGID support
# - Auto-update detection via image revision marker

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

# Persistent venv initialization / update
if [ ! -x "$VENV_PERSISTENT/bin/sickchill" ]; then
    echo "==> First run or missing venv: copying pre-built Python environment to $VENV_PERSISTENT"
    rm -rf "$VENV_PERSISTENT"
    cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"

    # First run: chown the whole datadir
    if [ "$(id -u)" = "0" ]; then
        chown -R "$PUID:$PGID" "$DATADIR" || true
    fi
    echo "==> Persistent venv initialized successfully."

else
    # Compare image revision for auto-update detection
    if [ -f "/sickchill/.image_revision" ] && [ -f "$VENV_PERSISTENT/.image_revision" ]; then
        if ! cmp -s "/sickchill/.image_revision" "$VENV_PERSISTENT/.image_revision"; then
            echo "==> New image revision detected — updating persistent venv..."
            rm -rf "$VENV_PERSISTENT"
            cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"

            if [ "$(id -u)" = "0" ]; then
                chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
            fi
            echo "==> Persistent venv updated."
        fi
    fi
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
