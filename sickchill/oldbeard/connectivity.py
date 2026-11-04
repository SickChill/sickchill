"""Internet connectivity probe and high-priority queue item for hung network work."""

from __future__ import annotations

import socket
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from sickchill import logger, settings
from sickchill.oldbeard.generic_queue import QueueItem, QueuePriorities

if TYPE_CHECKING:
    from sickchill.oldbeard.generic_queue import GenericQueue

DEFAULT_HOSTS = (("1.1.1.1", 53), ("8.8.8.8", 53), ("1.1.1.1", 443))
STAGED_DELAYS = (15, 30, 90, 300)
LONG_DELAY = 1800
STAGED_ATTEMPTS = 1 + len(STAGED_DELAYS)


class _ProbeAttempt:
    """Minimal object so handle_connectivity_failure can read .attempt."""

    def __init__(self, attempt: int):
        self.attempt = attempt


def parse_connectivity_hosts(value: str | None = None) -> list[tuple[str, int]]:
    raw = value if value is not None else getattr(settings, "CONNECTIVITY_HOSTS", "") or ""
    hosts: list[tuple[str, int]] = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        host, sep, port = part.rpartition(":")
        if not sep:
            host, port = part, "53"
        try:
            hosts.append((host, int(port)))
        except (TypeError, ValueError):
            continue
    return hosts or list(DEFAULT_HOSTS)


def _proxy_endpoint(proxy: str) -> tuple[str, int] | None:
    parsed = urlparse(proxy if "://" in proxy else f"http://{proxy}")
    host = parsed.hostname
    if not host:
        return None
    if parsed.port:
        return host, parsed.port
    scheme = (parsed.scheme or "http").lower()
    if scheme == "https":
        return host, 443
    if scheme.startswith("socks"):
        return host, 1080
    return host, 80


def probe_connectivity(hosts: list[tuple[str, int]] | None = None, timeout: float | None = None) -> bool:
    """Return True if any configured host:port accepts a TCP connect."""
    if timeout is None:
        timeout = float(getattr(settings, "CONNECTIVITY_CHECK_TIMEOUT", 3) or 3)
    proxy = str(getattr(settings, "PROXY_SETTING", "") or "").strip()
    if proxy:
        endpoint = _proxy_endpoint(proxy)
        if endpoint is None:
            return True
        try:
            with socket.create_connection(endpoint, timeout=timeout):
                return True
        except (OSError, ValueError, OverflowError):
            return False
    for host, port in hosts or parse_connectivity_hosts():
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (OSError, ValueError, OverflowError):
            continue
    return False


def run_connectivity_probe(queue: GenericQueue, attempt: int = 1) -> None:
    """Probe once and resume or record a failed attempt. Any probe error is a failure."""
    try:
        reachable = probe_connectivity()
    except Exception as error:
        logger.debug(f"Connectivity probe raised {type(error).__name__}: {error}")
        reachable = False
    if reachable:
        logger.info("Connectivity restored; resuming queue")
        queue.resume_after_connectivity()
    else:
        queue.handle_connectivity_failure(_ProbeAttempt(attempt))


def delay_after_failure(attempt: int) -> int:
    """Seconds to wait after this many failed probes."""
    if attempt < 1:
        return STAGED_DELAYS[0]
    if attempt <= len(STAGED_DELAYS):
        return STAGED_DELAYS[attempt - 1]
    return LONG_DELAY


_CONNECTIVITY_ERROR_NAMES = frozenset(
    {
        "ConnectionError",
        "ConnectTimeout",
        "ConnectTimeoutError",
        "NameResolutionError",
        "NewConnectionError",
        "ReadTimeout",
        "ReadTimeoutError",
        "Timeout",
        "TimeoutError",
    }
)

_CONNECTIVITY_ERROR_TEXT = (
    "name resolution",
    "failed to resolve",
    "nodename nor servname",
    "timed out",
    "read timeout",
    "connect timeout",
)


def is_connectivity_error(error: BaseException | None) -> bool:
    """True for DNS/connect/timeout failures (not HTTP 4xx or TLS problems)."""
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        seen.add(id(current))
        if type(current).__name__ in _CONNECTIVITY_ERROR_NAMES:
            return True
        if isinstance(current, (socket.gaierror, TimeoutError)):
            return True
        message = str(current).lower()
        if any(fragment in message for fragment in _CONNECTIVITY_ERROR_TEXT):
            return True
        current = current.__cause__ or current.__context__
    return False


def iter_network_queues():
    """Search and show queues that should pause while internet is down."""
    queues = []
    for name in ("searchQueueScheduler", "showQueueScheduler"):
        action = getattr(getattr(settings, name, None), "action", None)
        if action is not None:
            queues.append(action)
    return queues


def maybe_request_connectivity_check(error: BaseException | None, reason: str | None = None) -> None:
    """Enqueue a SearchQueue connectivity probe after a DNS/connect failure."""
    if not is_connectivity_error(error):
        return
    if not getattr(settings, "CONNECTIVITY_CHECK", True):
        return
    scheduler = getattr(settings, "searchQueueScheduler", None)
    queue = getattr(scheduler, "action", None) if scheduler is not None else None
    request = getattr(queue, "request_connectivity_check", None)
    if not callable(request):
        return
    request(reason or type(error).__name__)


class ConnectivityCheckQueueItem(QueueItem):
    def __init__(self, queue: GenericQueue, attempt: int = 1):
        super().__init__("Connectivity Check", 0)
        self.priority = QueuePriorities.CONNECTIVITY
        self.queue_ref = queue
        self.attempt = max(1, int(attempt))

    def run(self):
        super().run()
        try:
            run_connectivity_probe(self.queue_ref, self.attempt)
        finally:
            super().finish()
            self.finish()
