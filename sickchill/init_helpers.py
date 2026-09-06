import argparse
import gettext
import logging
import os
import re
import sys
from importlib.metadata import Distribution, PackageNotFoundError
from pathlib import Path
from typing import Union

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

# locale_dir = sickchill_dir / "locale"
pid_file: Union[Path, None] = None


sickchill_dir = Path(__file__).parent
locale_dir = sickchill_dir / "locale"
pyproject_file = sickchill_dir.parent / "pyproject.toml"
git_folder = sickchill_dir.parent / ".git"


def setup_gettext(language: str | None = None) -> None:
    languages = [language] if language else None
    if not [key for key in ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG") if os.environ.get(key)]:
        os.environ["LC_MESSAGES"] = "en_US.UTF-8"
    gt = gettext.translation("messages", locale_dir, languages=languages, fallback=True)
    gt.install(names=["ngettext"])


def maybe_daemonize():
    """
    Fork off as a daemon
    """
    if sys.platform == "win32":
        return

    args = argparse.ArgumentParser(add_help=False)
    args.add_argument("-d", "--daemon", action="store_true")
    args.add_argument("--pidfile")
    args, extra = args.parse_known_args(sys.argv)

    if not args.daemon:
        return

    global pid_file
    if args.pidfile:
        pid_file = Path(args.pidfile).resolve()

    if pid_file:
        if pid_file.is_file():
            # If the pid file already exists, SickChill may still be running, so exit
            raise SystemExit(f"PID file: {pid_file} already exists. Exiting.")
        pid_dir = pid_file.parent
        if not os.access(pid_dir, os.F_OK):
            raise SystemExit(f"PID dir: {pid_dir} doesn't exist. Exiting.")
        if not os.access(pid_dir, os.W_OK):
            raise SystemExit(f"PID dir: {pid_dir} must be writable (write permissions). Exiting.")

    # Make a non-session-leader child process
    try:
        pid = os.fork()  # @UndefinedVariable - only available in UNIX
        if pid != 0:
            os._exit(0)
    except OSError as error:
        raise SystemExit(f"fork #1 failed: {error}\n")

    os.setsid()  # @UndefinedVariable - only available in UNIX

    # https://github.com/SickChill/SickChill/issues/2969
    # http://www.microhowto.info/howto/cause_a_process_to_become_a_daemon_in_c.html#idp23920
    # https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch06s08.html
    # Previous code simply set the umask to whatever it was because it was ANDing instead of OR-ing
    # Daemons traditionally run with umask 0 anyways and this should not have repercussions
    os.umask(0)

    # Make the child a session-leader by detaching from the terminal
    try:
        pid = os.fork()
        if pid != 0:
            os._exit(0)
    except OSError as error:
        raise SystemExit(f"fork #2 failed: {error}\n")

    # Write pid
    if pid_file:
        pid = os.getpid()

        logger.info(f"Writing PID: {pid} to {pid_file}\n")
        try:
            pid_file.write_text(f"{pid}\n")
        except EnvironmentError as error:
            raise SystemExit(f"Unable to write PID file: {pid_file} Error {error}")

    # Redirect all output
    sys.stdout.flush()
    sys.stderr.flush()

    devnull = getattr(os, "devnull", "/dev/null")
    stdin = open(devnull)
    stdout = open(devnull, "a+")
    stderr = open(devnull, "a+")

    os.dup2(stdin.fileno(), getattr(sys.stdin, "device", sys.stdin).fileno())
    os.dup2(stdout.fileno(), getattr(sys.stdout, "device", sys.stdout).fileno())
    os.dup2(stderr.fileno(), getattr(sys.stderr, "device", sys.stderr).fileno())


def remove_pid_file():
    """
    Remove pid file

    :return:
    """
    try:
        if pid_file and pid_file.exists():
            pid_file.unlink()
    except EnvironmentError:
        pass


def get_distribution() -> Union[Distribution, None]:
    try:
        distribution = Distribution.from_name(__package__)
    except PackageNotFoundError:
        return None

    return distribution


def check_installed() -> bool:
    if pyproject_file.is_file() or git_folder.is_dir():
        return False

    return get_distribution() is not None


def get_current_version() -> str:
    fallback_version = "0.0.0"
    matcher = re.compile(r'\s*version\s*=\s*["\']([.0-9a-z-+]+)["\']\s*$')
    if pyproject_file.is_file():
        for line in pyproject_file.open():
            match = matcher.match(line)
            if match:
                return match.group(1)
        return fallback_version

    try:
        return get_distribution().version
    except PackageNotFoundError:
        return fallback_version


_revision_cache: tuple[str, str] | None = None
_revision_file = sickchill_dir / "_revision.txt"


def _git_output(*args: str, cwd: Path | None = None) -> str | None:
    """Run a git command; return stripped stdout or None on any failure."""
    import subprocess

    try:
        return (
            subprocess.check_output(
                ["git", *args],
                cwd=str(cwd) if cwd else None,
                stderr=subprocess.DEVNULL,
                timeout=5,
                text=True,
            ).strip()
            or None
        )
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None


def _normalize_revision(branch: str, sha: str) -> tuple[str, str]:
    """Drop placeholder values so Help does not show a fake revision."""
    branch = (branch or "").strip()
    sha = (sha or "").strip()
    if branch in ("", "unknown"):
        branch = ""
    if sha in ("", "unknown"):
        # No real commit → hide the whole Revision row (do not show "develop@")
        return "", ""
    return branch, sha


def _parse_revision_file(path: Path) -> tuple[str, str]:
    """Parse ``branch sha`` or a single ``sha`` from a bake file."""
    try:
        text = path.read_text(encoding="utf-8").strip()
    except OSError:
        return "", ""
    if not text:
        return "", ""
    parts = text.split()
    if len(parts) >= 2:
        return _normalize_revision(parts[0], parts[1])
    return _normalize_revision("", parts[0])


def _revision_from_git() -> tuple[str, str] | None:
    """Return (branch, sha) from a live checkout, or None if not a git tree.

    ``git_folder`` may be a directory *or* a file (worktree / ``gitdir:``
    pointer). Only ``exists()`` is required — do not use ``is_dir()``.
    """
    if not git_folder.exists():
        return None
    repo_root = git_folder.parent
    if _git_output("-C", str(repo_root), "rev-parse", "--git-dir") is None:
        return None
    sha = _git_output("-C", str(repo_root), "rev-parse", "HEAD")
    if not sha:
        return None
    branch = _git_output("-C", str(repo_root), "rev-parse", "--abbrev-ref", "HEAD") or "HEAD"
    return branch, sha


def _revision_from_env() -> tuple[str, str]:
    sha = os.environ.get("SICKCHILL_SHA") or os.environ.get("GIT_SHA") or ""
    branch = os.environ.get("SICKCHILL_BRANCH") or os.environ.get("GIT_BRANCH") or ""
    return _normalize_revision(branch, sha)


def _branch_from_requested_revision(requested: str, commit_id: str) -> str:
    """Use requested_revision as branch unless it is clearly a commit-ish."""
    req = (requested or "").strip()
    if not req:
        return ""
    # pip records the ref the user asked for; when that is a SHA, do not show "sha@sha"
    if commit_id and (req == commit_id or commit_id.startswith(req)):
        return ""
    return req


def _revision_from_direct_url() -> tuple[str, str] | None:
    """
    PEP 610 ``direct_url.json`` written by pip for VCS installs, e.g.::

        pip install "git+https://github.com/SickChill/SickChill.git@develop"

    Yields ``vcs_info.commit_id`` and optional ``requested_revision`` (branch/tag).
    Editable local checkouts use ``dir_info`` only — those return None here.
    """
    import json

    try:
        dist = get_distribution()
        if dist is None:
            return None
        text = dist.read_text("direct_url.json")
        if not text:
            return None
        data = json.loads(text)
    except Exception:
        # Missing dist, missing file, bad JSON, etc. — never fail Help/startup
        return None

    vcs = data.get("vcs_info")
    if not isinstance(vcs, dict):
        return None
    sha = (vcs.get("commit_id") or "").strip()
    branch = _branch_from_requested_revision(vcs.get("requested_revision") or "", sha)
    normalized = _normalize_revision(branch, sha)
    if not normalized[1]:
        return None
    return normalized


def get_git_revision() -> tuple[str, str]:
    """
    Return ``(branch, sha)`` for the running code.

    Resolution order: live git checkout → ``sickchill/_revision.txt`` →
    PEP 610 ``direct_url.json`` (pip ``git+https://…@branch``) → env
    (``SICKCHILL_SHA`` / ``GIT_SHA``, ``SICKCHILL_BRANCH`` / ``GIT_BRANCH``).
    Result is cached for the process lifetime.
    """
    global _revision_cache
    if _revision_cache is not None:
        return _revision_cache

    result = _revision_from_git()
    if result is None and _revision_file.is_file():
        result = _parse_revision_file(_revision_file)
        if result == ("", ""):
            result = None
    if result is None:
        result = _revision_from_direct_url()
    if result is None:
        result = _revision_from_env()
        if result == ("", ""):
            result = ("", "")

    _revision_cache = result
    return _revision_cache


def format_git_revision(short: int = 12) -> str:
    """Return ``branch@sha12`` or ``sha12`` or empty string for logs/UI helpers."""
    branch, sha = get_git_revision()
    if not sha:
        return f"{branch}@" if branch else ""
    short_sha = sha[:short] if short else sha
    if branch and branch != "HEAD":
        return f"{branch}@{short_sha}"
    return short_sha
