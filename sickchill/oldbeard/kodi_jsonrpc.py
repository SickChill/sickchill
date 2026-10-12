from __future__ import annotations

from itertools import count
from typing import Any

import requests

from sickchill.helper.common import USER_AGENT

DEFAULT_PORT = 8080
DEFAULT_TIMEOUT = 10


class KodiRPCError(Exception):
    """HTTP or JSON-RPC transport failure talking to Kodi."""


class _KodiNamespace:
    def __init__(self, client: KodiClient, name: str) -> None:
        self._client = client
        self._name = name

    def __getattr__(self, method: str):
        rpc_method = f"{self._name}.{method}"

        def call(**params: Any) -> dict:
            return self._client.call(rpc_method, params)

        return call


class KodiClient:
    """HTTP JSON-RPC client for Kodi (`POST /jsonrpc`).

    Dotted calls match the previous kodipydent API used by the Kodi notifier,
    e.g. ``client.GUI.ShowNotification(title=..., message=...)``.
    """

    def __init__(
        self, hostname: str, username: str | None = None, password: str | None = None, port: int = DEFAULT_PORT, timeout: float = DEFAULT_TIMEOUT
    ) -> None:
        self.host = hostname
        self.port = int(port) if port else DEFAULT_PORT
        self.username = username or ""
        self.password = password or ""
        self.name = hostname
        self.timeout = timeout
        self._ids = count(1)
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": USER_AGENT, "Content-Type": "application/json"})
        if self.username or self.password:
            self._session.auth = (self.username, self.password)

    @property
    def url(self) -> str:
        return f"http://{self.host}:{self.port}/jsonrpc"

    def call(self, method: str, params: dict | None = None) -> dict:
        payload: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "id": next(self._ids)}
        if params:
            payload["params"] = params
        try:
            response = self._session.post(self.url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            body = response.json()
            if isinstance(body, dict) and body.get("error"):
                raise KodiRPCError(f"JSON-RPC error from Kodi at {self.host}:{self.port}: {body['error']}")
            return body
        except requests.Timeout as error:
            raise KodiRPCError(f"Timeout talking to Kodi at {self.host}:{self.port}") from error
        except (requests.RequestException, ValueError) as error:
            raise KodiRPCError(f"Failed talking to Kodi at {self.host}:{self.port}: {error}") from error

    def ping(self) -> dict:
        return self.call("JSONRPC.Ping")

    def __getattr__(self, namespace: str) -> _KodiNamespace:
        if namespace.startswith("_"):
            raise AttributeError(namespace)
        return _KodiNamespace(self, namespace)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, KodiClient):
            return NotImplemented
        return (self.host, self.port) == (other.host, other.port)

    def __hash__(self) -> int:
        return hash((self.host, self.port))
