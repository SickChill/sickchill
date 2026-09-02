#!/bin/bash
# shellcheck disable=SC2317
set -euo pipefail

# SickChill Docker entrypoint.sh (NAS-friendly)
# - Persistent venv in datadir (/data/.venv) — accessible on the NAS share
# - Minimal PUID/PGID support via gosu
# - Auto-update when image GIT_SHA / .image_revision changes (aligned with develop bake)

echo "==> SickChill container starting..."

# Environment / Defaults
PUID=${PUID:-1000}
PGID=${PGID:-1000}
DATADIR=${DATADIR:-/data}
UMASK=${UMASK:-002}
PORT=${PORT:-8081}
VENV_IMAGE="/opt/sickchill/.venv"
VENV_PERSISTENT="${DATADIR}/.venv"
IMAGE_REV_FILE="/sickchill/.image_revision"

umask "$UMASK"
mkdir -p "$DATADIR"

# Resolve the running image's revision (prefer env from develop bake, else marker file)
image_revision() {
    if [ -n "${SICKCHILL_SHA:-}" ] && [ "${SICKCHILL_SHA}" != "unknown" ]; then
        printf '%s\n' "$SICKCHILL_SHA"
    elif [ -f "$IMAGE_REV_FILE" ]; then
        tr -d '[:space:]' <"$IMAGE_REV_FILE"
    else
        printf 'unknown\n'
    fi
}

write_persistent_revision() {
    image_revision >"$VENV_PERSISTENT/.image_revision"
}

# Persistent venv initialization / update
if [ ! -x "$VENV_PERSISTENT/bin/sickchill" ]; then
    echo "==> First run or missing venv: copying pre-built Python environment to $VENV_PERSISTENT"
    rm -rf "$VENV_PERSISTENT"
    cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"
    write_persistent_revision

    # First run: chown the whole datadir
    if [ "$(id -u)" = "0" ]; then
        chown -R "$PUID:$PGID" "$DATADIR" || true
    fi
    echo "==> Persistent venv initialized (revision $(image_revision))."

else
    # Compare image revision for auto-update detection
    CURRENT="$(image_revision)"
    PREVIOUS="unknown"
    if [ -f "$VENV_PERSISTENT/.image_revision" ]; then
        PREVIOUS="$(tr -d '[:space:]' <"$VENV_PERSISTENT/.image_revision")"
    fi

    if [ "$CURRENT" != "unknown" ] && [ "$CURRENT" != "$PREVIOUS" ]; then
        echo "==> New image revision detected ($PREVIOUS → $CURRENT) — updating persistent venv..."
        rm -rf "$VENV_PERSISTENT"
        cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"
        write_persistent_revision

        if [ "$(id -u)" = "0" ]; then
            chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
        fi
        echo "==> Persistent venv updated."
    else
        # Ensure marker exists even on older persistent venvs
        if [ ! -f "$VENV_PERSISTENT/.image_revision" ]; then
            write_persistent_revision
        fi
    fi
fi

# Launch SickChill from the NAS-accessible persistent venv
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
