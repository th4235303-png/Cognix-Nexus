from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass
from urllib.parse import urlsplit

import httpx


class UnsafeDestination(ValueError):
    """A request target violates the public HTTP destination policy."""


@dataclass(frozen=True)
class PublicDestination:
    scheme: str
    hostname: str
    port: int
    addresses: tuple[str, ...]


def _validate_url_syntax(url: str | httpx.URL) -> tuple[str, str, int]:
    try:
        parsed = urlsplit(str(url))
        scheme = parsed.scheme.lower()
        hostname = parsed.hostname
        port = parsed.port
    except (TypeError, ValueError):
        raise UnsafeDestination("Source URL is invalid") from None

    if scheme not in {"http", "https"} or not hostname:
        raise UnsafeDestination("Only public HTTP(S) source URLs are allowed")
    if parsed.username is not None or parsed.password is not None:
        raise UnsafeDestination("Source URLs must not contain credentials")
    if any(ord(char) < 32 or ord(char) == 127 for char in str(url)):
        raise UnsafeDestination("Source URL is invalid")

    hostname = hostname.rstrip(".")
    if not hostname or "%" in hostname or "\\" in hostname:
        raise UnsafeDestination("Source URL is invalid")
    try:
        ipaddress.ip_address(hostname)
        normalized_hostname = hostname
    except ValueError:
        try:
            normalized_hostname = hostname.encode("idna").decode("ascii").lower()
        except UnicodeError:
            raise UnsafeDestination("Source URL is invalid") from None
        if not normalized_hostname or normalized_hostname == "localhost" or normalized_hostname.endswith(".localhost"):
            raise UnsafeDestination("Source destination is not public")

    default_port = 443 if scheme == "https" else 80
    selected_port = port if port is not None else default_port
    if selected_port == 0:
        raise UnsafeDestination("Source URL is invalid")
    return scheme, normalized_hostname, selected_port


def resolve_public_destination(url: str | httpx.URL) -> PublicDestination:
    scheme, hostname, port = _validate_url_syntax(url)
    try:
        literal = ipaddress.ip_address(hostname)
    except ValueError:
        literal = None

    if literal is not None:
        addresses = (str(literal),)
    else:
        try:
            results = socket.getaddrinfo(
                hostname,
                port,
                type=socket.SOCK_STREAM,
            )
        except (OSError, UnicodeError):
            raise UnsafeDestination("Source destination could not be resolved safely") from None
        addresses = tuple(sorted({result[4][0] for result in results}))

    if not addresses:
        raise UnsafeDestination("Source destination could not be resolved safely")
    for address in addresses:
        try:
            parsed_address = ipaddress.ip_address(address)
        except ValueError:
            raise UnsafeDestination("Source destination is not public") from None
        if (
            not parsed_address.is_global
            or parsed_address.is_private
            or parsed_address.is_loopback
            or parsed_address.is_link_local
            or parsed_address.is_multicast
            or parsed_address.is_unspecified
            or parsed_address.is_reserved
        ):
            raise UnsafeDestination("Source destination is not public")

    return PublicDestination(scheme, hostname, port, addresses)


def assert_public_url(url: str | httpx.URL) -> None:
    resolve_public_destination(url)


class PinnedHTTPTransport(httpx.HTTPTransport):
    """Resolve, validate, and connect to the same public address per request."""

    def __init__(self) -> None:
        super().__init__(
            trust_env=False,
            retries=0,
            limits=httpx.Limits(max_keepalive_connections=0),
        )

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        destination = resolve_public_destination(request.url)
        address = destination.addresses[0]
        original_host = request.url.host
        host_header = original_host
        if request.url.port != (443 if destination.scheme == "https" else 80):
            host_header = f"{host_header}:{request.url.port}"
        if ":" in original_host and not original_host.startswith("["):
            host_header = f"[{host_header}]"
        headers = [
            (name, value)
            for name, value in request.headers.raw
            if name.lower() != b"host"
        ]
        headers.append((b"Host", host_header.encode("ascii")))
        extensions = dict(request.extensions)
        if destination.scheme == "https":
            extensions["sni_hostname"] = destination.hostname

        pinned_request = httpx.Request(
            method=request.method,
            url=request.url.copy_with(host=address),
            headers=headers,
            stream=request.stream,
            extensions=extensions,
        )
        return super().handle_request(pinned_request)
