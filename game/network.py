from __future__ import annotations

import json
import socket
import time
from dataclasses import dataclass
from typing import Any


DEFAULT_PORT = 50007
PROTOCOL_VERSION = 1
CLIENT_TIMEOUT = 8.0


@dataclass
class NetworkMessage:
    kind: str
    data: dict[str, Any]
    address: tuple[str, int] | None = None


def get_lan_ip() -> str:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("8.8.8.8", 80))
        return probe.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        probe.close()


class NetworkSession:
    def __init__(self, mode: str = "local", host: str = "", port: int = DEFAULT_PORT) -> None:
        self.mode = mode
        self.host = host
        self.port = port
        self.client_address: tuple[str, int] | None = None
        self.last_client_seen = 0.0
        self.last_server_seen = 0.0
        self.socket: socket.socket | None = None

        if mode == "host":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            self.socket.bind(("", port))
        elif mode == "client":
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setblocking(False)
            self.server_address = (host, port)
            self.send("hello", {"version": PROTOCOL_VERSION})

    @property
    def is_networked(self) -> bool:
        return self.mode in {"host", "client"}

    @property
    def is_host(self) -> bool:
        return self.mode == "host"

    @property
    def is_client(self) -> bool:
        return self.mode == "client"

    @property
    def has_peer(self) -> bool:
        now = time.monotonic()
        if self.is_host:
            return self.client_address is not None and now - self.last_client_seen < CLIENT_TIMEOUT
        if self.is_client:
            return now - self.last_server_seen < CLIENT_TIMEOUT
        return False

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def send(self, kind: str, data: dict[str, Any] | None = None, address: tuple[str, int] | None = None) -> None:
        if self.socket is None:
            return
        if self.is_host:
            target = address or self.client_address
        elif self.is_client:
            target = getattr(self, "server_address", None)
        else:
            target = None
        if target is None:
            return

        payload = {"kind": kind, "version": PROTOCOL_VERSION, "data": data or {}}
        try:
            self.socket.sendto(json.dumps(payload, separators=(",", ":")).encode("utf-8"), target)
        except OSError:
            return

    def receive(self) -> list[NetworkMessage]:
        if self.socket is None:
            return []

        messages: list[NetworkMessage] = []
        while True:
            try:
                raw_data, address = self.socket.recvfrom(65535)
            except BlockingIOError:
                break
            except OSError:
                break

            try:
                payload = json.loads(raw_data.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                continue

            if payload.get("version") != PROTOCOL_VERSION:
                continue

            kind = str(payload.get("kind", ""))
            data = payload.get("data", {})
            if not isinstance(data, dict):
                data = {}

            if self.is_host:
                self.client_address = address
                self.last_client_seen = time.monotonic()
            elif self.is_client:
                self.last_server_seen = time.monotonic()

            messages.append(NetworkMessage(kind=kind, data=data, address=address))

        return messages
