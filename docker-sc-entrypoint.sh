#!/bin/bash
# shellcheck disable=SC2317
set -euo pipefail

# SickChill Docker entrypoint.sh
# - Makes the Python venv persistent inside your datadir (e.g. /data/.venv)
#   so the entire Python environment lives alongside config, cache, logs etc.
#   Perfect for NAS backups and universal installs.
# - Supports PUID/PGID (standard for Synology, Unraid, etc.)
# - Auto-copies pre-built venv from image on first start
# - Auto-updates venv when Docker image is upgraded (detects via BUILD_INFO)
# - Drops root privileges after setup using gosu

echo "==> SickChill container starting..."

# -----------------------------
# Environment / Defaults
# -----------------------------
PUID=${PUID:-1000}
PGID=${PGID:-1000}
DATADIR=${DATADIR:-/data}
UMASK=${UMASK:-002}
PORT=${PORT:-8081}
VENV_IMAGE="/opt/sickchill/.venv"
VENV_PERSISTENT="${DATADIR}/.venv"

# Apply umask for any files created
umask "$UMASK"

# Ensure datadir exists
mkdir -p "$DATADIR"

# -----------------------------
# PUID/PGID handling (run as root to setup)
# -----------------------------
if [ "$(id -u)" = "0" ]; then
    echo "==> Configuring permissions for PUID=$PUID PGID=$PGID"

    # Group
    if getent group "$PGID" >/dev/null 2>&1; then
        groupmod -g "$PGID" sickchill 2>/dev/null || true
    else
        groupadd -g "$PGID" sickchill
    fi

    # User
    if id -u "$PUID" >/dev/null 2>&1; then
        usermod -u "$PUID" -g "$PGID" -d "$DATADIR" sickchill 2>/dev/null || true
    else
        useradd -u "$PUID" -g "$PGID" -d "$DATADIR" -s /bin/bash sickchill
    fi

    # Fix ownership of datadir (where .venv, config.ini, cache/ will live)
    # Only chown what we control - do NOT recursively chown /tv or /downloads
    # if they are large media libraries (can take forever or cause issues)
    chown -R "$PUID:$PGID" "$DATADIR" || true
fi

# -----------------------------
# Persistent venv initialization / update
# -----------------------------
if [ ! -x "$VENV_PERSISTENT/bin/sickchill" ]; then
    echo "==> First run or missing venv: copying pre-built Python environment to $VENV_PERSISTENT"
    echo "    (This puts the full venv + sickchill + all dependencies inside your persistent NAS folder)"
    rm -rf "$VENV_PERSISTENT"
    cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"

    # Copy build metadata so we can detect future image updates
    if [ -f /sickchill/BUILD_INFO ]; then
        cp /sickchill/BUILD_INFO "$VENV_PERSISTENT/BUILD_INFO"
    fi

    if [ "$(id -u)" = "0" ]; then
        chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
    fi
    echo "==> Persistent venv initialized successfully."
else
    # Check if image was updated (new BUILD_INFO) and refresh venv automatically
    if [ -f "$VENV_PERSISTENT/BUILD_INFO" ] && [ -f /sickchill/BUILD_INFO ]; then
        if ! cmp -s "$VENV_PERSISTENT/BUILD_INFO" /sickchill/BUILD_INFO; then
            echo "==> New SickChill Docker image detected - updating persistent venv..."
            rm -rf "$VENV_PERSISTENT"
            cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"
            cp /sickchill/BUILD_INFO "$VENV_PERSISTENT/BUILD_INFO"
            if [ "$(id -u)" = "0" ]; then
                chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
            fi
            echo "==> Persistent venv updated to match new image."
        fi
    fi
fi

# -----------------------------
# Launch SickChill from the persistent venv
# -----------------------------
SICKCHILL_BIN="$VENV_PERSISTENT/bin/sickchill"

if [ ! -x "$SICKCHILL_BIN" ]; then
    echo "ERROR: Could not find sickchill in persistent venv at $SICKCHILL_BIN"
    echo "Try removing $VENV_PERSISTENT and restarting the container to re-initialize."
    exit 1
fi

echo "==> Launching sickchill from persistent venv ($VENV_PERSISTENT)"

# Drop to non-root user if we started as root and PUID != 0
if [ "$(id -u)" = "0" ] && [ "$PUID" != "0" ]; then
    exec gosu "$PUID:$PGID" "$SICKCHILL_BIN" --nolaunch --datadir "$DATADIR" --port "$PORT" "$@"
else
    exec "$SICKCHILL_BIN" --nolaunch --datadir "$DATADIR" --port "$PORT" "$@"
fi
