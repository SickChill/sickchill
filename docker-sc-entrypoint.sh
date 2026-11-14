#!/bin/bash
# shellcheck disable=SC2317
set -euo pipefail

# SickChill Docker entrypoint.sh (NAS-friendly, Python 3.14 image)
# - Persistent mount at /.venv, beside /data. The environment is /.venv/venv.
# - Minimal PUID/PGID support via gosu
# - Auto-update when image GIT_SHA changes. An unknown revision uses a content id of the template venv.
# - Launch via the persistent interpreter (avoids relocated console-script shebangs)

echo "==> SickChill container starting..."

# Environment / Defaults
PUID=${PUID:-1000}
PGID=${PGID:-1000}
DATADIR=${DATADIR:-/data}
UMASK=${UMASK:-002}
VENV_IMAGE="${VENV_IMAGE_PATH:-/opt/sickchill/.venv}"
IMAGE_REV_FILE="/sickchill/.image_revision"
TEMPLATE_CONTENT_ID=""

# /.venv is the sibling of /data and is the persistent mount. Never rename it.
# The environment, staging directory, and backup live inside that mount.
# An explicit VENV_RUNTIME_PATH still names the mount.
VENV_MOUNT="${VENV_RUNTIME_PATH:-/.venv}"
VENV_MOUNT="${VENV_MOUNT%/}"
VENV_PERSISTENT="${VENV_MOUNT}/venv"

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
# final persistent interpreter. $2 is that path when $1 is still a staging dir.
fix_venv_shebangs() {
    local venv="$1"
    local target="${2:-$1}"
    local shebang="#!${target}/bin/python"
    local script
    for script in "$venv"/bin/*; do
        [ -f "$script" ] && [ ! -L "$script" ] || continue
        # Only rewrite Python shebang scripts
        if head -n 1 "$script" 2>/dev/null | grep -q '^#!.*python'; then
            sed -i "1c${shebang}" "$script"
            chmod a+x "$script"
        fi
    done
}

# Stable id of the image template. Git SHA "unknown" must not count as "current".
template_content_id() {
    if [ -z "$TEMPLATE_CONTENT_ID" ]; then
        TEMPLATE_CONTENT_ID="$(
            find "$VENV_IMAGE" -type f \
                ! -name '.image_revision' \
                ! -name '.image_content_id' \
                -printf '%P %s %T@\n' \
                | sort \
                | sha256sum \
                | awk '{print $1}'
        )"
    fi
    printf '%s\n' "$TEMPLATE_CONTENT_ID"
}

persistent_content_id() {
    if [ -f "$VENV_PERSISTENT/.image_content_id" ]; then
        tr -d '[:space:]' <"$VENV_PERSISTENT/.image_content_id"
    fi
}

# Root start: if a tree is not the requested identity, fix it before exec.
repair_ownership() {
    local path="$1"
    [ "$(id -u)" = "0" ] || return 0
    [ "$PUID" = "0" ] && return 0
    [ -d "$path" ] || return 0
    local uid gid
    uid="$(stat -c '%u' "$path")"
    gid="$(stat -c '%g' "$path")"
    if [ "$uid" != "$PUID" ] || [ "$gid" != "$PGID" ]; then
        echo "==> $path ownership ${uid}:${gid} does not match ${PUID}:${PGID} — repairing"
        chown -R "$PUID:$PGID" "$path" || true
    fi
}

# Copy the image venv inside the mount, validate SickChill import, then replace
# the venv subdirectory. On any failure, leave the existing venv in place.
install_persistent_venv() {
    local tmp old
    tmp="${VENV_MOUNT}/.venv.new.$$"
    old="${VENV_MOUNT}/.venv.old.$$"

    echo "==> Installing persistent venv at $VENV_PERSISTENT"
    mkdir -p "$VENV_MOUNT"
    rm -rf "$tmp" "$old"

    if ! cp -a "$VENV_IMAGE" "$tmp"; then
        echo "ERROR: failed to copy image venv to $tmp — keeping existing persistent venv (if any)"
        rm -rf "$tmp"
        return 1
    fi

    # Shebangs name the final path, not the staging directory that is removed after mv.
    fix_venv_shebangs "$tmp" "$VENV_PERSISTENT"
    # Stamp markers on the staged tree before swap (only committed if validation passes)
    image_revision >"$tmp/.image_revision"
    template_content_id >"$tmp/.image_content_id"

    if [ ! -x "$tmp/bin/python" ] || ! "$tmp/bin/python" -c 'import SickChill'; then
        echo "ERROR: staged venv failed SickChill import check — keeping existing persistent venv (if any)"
        rm -rf "$tmp"
        return 1
    fi

    if [ -e "$VENV_PERSISTENT" ]; then
        if ! mv "$VENV_PERSISTENT" "$old"; then
            echo "ERROR: could not move aside existing venv — keeping it"
            rm -rf "$tmp"
            return 1
        fi
        if ! mv "$tmp" "$VENV_PERSISTENT"; then
            echo "ERROR: could not install staged venv — restoring previous"
            mv "$old" "$VENV_PERSISTENT" || true
            rm -rf "$tmp"
            return 1
        fi
        rm -rf "$old"
    elif ! mv "$tmp" "$VENV_PERSISTENT"; then
        echo "ERROR: could not install staged venv at $VENV_PERSISTENT"
        rm -rf "$tmp"
        return 1
    fi

    return 0
}

# Persistent venv initialization / update
if [ ! -x "$VENV_PERSISTENT/bin/python" ]; then
    echo "==> First run or missing venv: copying pre-built Python environment to $VENV_PERSISTENT"
    install_persistent_venv

    # First run: chown the whole datadir
    if [ "$(id -u)" = "0" ]; then
        chown -R "$PUID:$PGID" "$DATADIR" "$VENV_PERSISTENT" || true
    fi
    echo "==> Persistent venv initialized (revision $(image_revision))."

else
    # Compare image revision for auto-update detection
    CURRENT="$(image_revision)"
    PREVIOUS="unknown"
    if [ -f "$VENV_PERSISTENT/.image_revision" ]; then
        PREVIOUS="$(tr -d '[:space:]' <"$VENV_PERSISTENT/.image_revision")"
    fi

    if [ ! -f "$VENV_PERSISTENT/.image_revision" ]; then
        # Unmarked legacy venv: reinstall from image; do not stamp current rev onto the old tree
        echo "==> Persistent venv missing .image_revision — reinstalling from image..."
        install_persistent_venv
        if [ "$(id -u)" = "0" ]; then
            chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
        fi
        echo "==> Persistent venv reinstalled (revision $(image_revision))."
    elif [ "$CURRENT" != "unknown" ] && [ "$CURRENT" != "$PREVIOUS" ]; then
        echo "==> New image revision detected ($PREVIOUS → $CURRENT) — updating persistent venv..."
        install_persistent_venv

        if [ "$(id -u)" = "0" ]; then
            chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
        fi
        echo "==> Persistent venv updated."
    elif [ "$CURRENT" = "unknown" ] && [ "$(template_content_id)" != "$(persistent_content_id)" ]; then
        echo "==> Image revision is unknown and the template venv changed — updating persistent venv..."
        install_persistent_venv

        if [ "$(id -u)" = "0" ]; then
            chown -R "$PUID:$PGID" "$VENV_PERSISTENT" || true
        fi
        echo "==> Persistent venv updated."
    else
        fix_venv_shebangs "$VENV_PERSISTENT"
        repair_ownership "$DATADIR"
        repair_ownership "$VENV_PERSISTENT"
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
    launch_args=()
    has_datadir=0
    for arg in "$@"; do
        case "$arg" in
            --datadir | --datadir=*) has_datadir=1 ;;
        esac
        launch_args+=("$arg")
    done
    # Datadir default comes from DATADIR. --port is left to the process and compose publish.
    if [ "$has_datadir" -eq 0 ]; then
        launch_args+=(--datadir "$DATADIR")
    fi
    set -- "$PYTHON_BIN" -c 'import sys; sys.argv[0] = "sickchill"; from SickChill import main; raise SystemExit(main())' "${launch_args[@]}"
fi

# Drop privileges + exec CMD
if [ "$(id -u)" = "0" ] && [ "$PUID" != "0" ]; then
    echo "==> Dropping privileges to $PUID:$PGID..."
    exec gosu "$PUID:$PGID" "$@"
else
    echo "==> Starting as $(id -u):$(id -g)..."
    exec "$@"
fi
