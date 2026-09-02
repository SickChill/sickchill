#!/bin/bash
# shellcheck disable=SC2317
set -euo pipefail

# SickChill Docker entrypoint.sh (NAS-friendly)
# - Persistent venv in datadir (/data/.venv) — accessible on the NAS share
# - Minimal PUID/PGID support via gosu
# - Auto-update when image GIT_SHA / .image_revision changes (aligned with develop bake)
# - Launch via the persistent interpreter (avoids relocated console-script shebangs)

echo "==> SickChill container starting..."

# Environment / Defaults
PUID=${PUID:-1000}
PGID=${PGID:-1000}
DATADIR=${DATADIR:-/data}
UMASK=${UMASK:-002}
PORT=${PORT:-8081}
VENV_IMAGE="${VENV_IMAGE_PATH:-/opt/sickchill/.venv}"
VENV_PERSISTENT="${VENV_RUNTIME_PATH:-${DATADIR}/.venv}"
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

# After cp -a, console scripts still shebang the image path. Point them at the
# persistent interpreter so PATH lookups and manual bin/* use stay consistent.
fix_venv_shebangs() {
    local venv="$1"
    local shebang="#!${venv}/bin/python"
    local script
    for script in "$venv"/bin/*; do
        [ -f "$script" ] && [ ! -L "$script" ] || continue
        # Only rewrite Python shebang scripts
        if head -n 1 "$script" 2>/dev/null | grep -q '^#!.*python'; then
            sed -i "1c${shebang}" "$script"
        fi
    done
}

install_persistent_venv() {
    echo "==> Installing persistent venv at $VENV_PERSISTENT"
    rm -rf "$VENV_PERSISTENT"
    cp -a "$VENV_IMAGE" "$VENV_PERSISTENT"
    fix_venv_shebangs "$VENV_PERSISTENT"
    write_persistent_revision
}

# Persistent venv initialization / update
if [ ! -x "$VENV_PERSISTENT/bin/python" ]; then
    echo "==> First run or missing venv: copying pre-built Python environment to $VENV_PERSISTENT"
    install_persistent_venv

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
        install_persistent_venv

        if [ "$(id -u)" = "0" ]; then
            chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
        fi
        echo "==> Persistent venv updated."
    else
        # Ensure marker exists even on older persistent venvs; refresh shebangs if needed
        if [ ! -f "$VENV_PERSISTENT/.image_revision" ]; then
            write_persistent_revision
        fi
        fix_venv_shebangs "$VENV_PERSISTENT"
    fi
fi

# Launch SickChill from the NAS-accessible persistent venv interpreter
echo "==> Launching sickchill via persistent interpreter ($VENV_PERSISTENT/bin/python)"

export VIRTUAL_ENV="$VENV_PERSISTENT"
export PATH="$VENV_PERSISTENT/bin:$PATH"

PYTHON_BIN="$VENV_PERSISTENT/bin/python"

if [ ! -x "$PYTHON_BIN" ]; then
    echo "ERROR: python not found in $VENV_PERSISTENT"
    echo "Try: rm -rf $VENV_PERSISTENT && docker restart sickchill"
    exit 1
fi

# Replace console-script CMD (sickchill/SickChill) with an explicit interpreter
# invocation so we never depend on image-path shebangs after the venv copy.
if [ "$#" -gt 0 ] && { [ "$1" = "sickchill" ] || [ "$1" = "SickChill" ]; }; then
    shift
    set -- "$PYTHON_BIN" -c 'import sys; sys.argv[0] = "sickchill"; from SickChill import main; raise SystemExit(main())' "$@"
fi

# Drop privileges + exec CMD
if [ "$(id -u)" = "0" ] && [ "$PUID" != "0" ]; then
    echo "==> Dropping privileges to $PUID:$PGID..."
    exec gosu "$PUID:$PGID" "$@"
else
    echo "==> Starting as $(id -u):$(id -g)..."
    exec "$@"
fi
