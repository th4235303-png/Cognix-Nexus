from __future__ import annotations

import socket
import unittest
from unittest.mock import patch

import httpx

from app.services.ssrf import (
    PinnedHTTPTransport,
    UnsafeDestination,
    assert_public_url,
)


def _dns_result(address: str):
    family = socket.AF_INET6 if ":" in address else socket.AF_INET
    sockaddr = (address, 443, 0, 0) if family == socket.AF_INET6 else (address, 443)
    return [(family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr)]


class SSRFPolicyTests(unittest.TestCase):
    def test_public_http_and_https_urls_are_accepted(self):
        with patch("app.services.ssrf.socket.getaddrinfo", return_value=_dns_result("93.184.216.34")):
            assert_public_url("http://research.example/article")
            assert_public_url("https://research.example/article")
        assert_public_url("https://[2606:4700:4700::1111]/")

    def test_rejects_localhost_and_non_public_ip_literals(self):
        unsafe_urls = [
            "http://localhost/",
            "https://LOCALHOST./",
            "http://127.0.0.1/",
            "http://0.0.0.0/",
            "http://10.0.0.1/",
            "http://172.16.0.1/",
            "http://192.168.1.1/",
            "http://169.254.1.1/",
            "http://224.0.0.1/",
            "http://240.0.0.1/",
            "http://192.0.2.1/",
            "http://[::1]/",
            "http://[::]/",
            "http://[fc00::1]/",
            "http://[fe80::1]/",
            "http://[ff02::1]/",
            "http://[2001:db8::1]/",
            "http://[::ffff:127.0.0.1]/",
        ]
        for url in unsafe_urls:
            with self.subTest(url=url), self.assertRaises(UnsafeDestination):
                assert_public_url(url)

    def test_rejects_hostnames_resolving_to_private_or_mixed_addresses(self):
        private = _dns_result("10.1.2.3")
        public = _dns_result("93.184.216.34")
        for results in (private, public + private):
            with self.subTest(results=results), patch(
                "app.services.ssrf.socket.getaddrinfo",
                return_value=results,
            ), self.assertRaisesRegex(UnsafeDestination, "not public"):
                assert_public_url("https://research.example/")

    def test_noncanonical_ipv4_hostname_is_blocked_after_resolution(self):
        with patch(
            "app.services.ssrf.socket.getaddrinfo",
            return_value=_dns_result("127.0.0.1"),
        ):
            with self.assertRaises(UnsafeDestination):
                assert_public_url("http://2130706433/")

    def test_rejects_unsupported_malformed_and_credential_urls(self):
        credential_url = "https://user" + ":" + "password" + "@research.example/"
        invalid_urls = [
            "file:///etc/passwd",
            "ftp://research.example/file",
            credential_url,
            "https://research.example:invalid/",
            "https:///",
            "https://research.example:0/",
        ]
        for url in invalid_urls:
            with self.subTest(url=url), self.assertRaises(UnsafeDestination):
                assert_public_url(url)

    def test_transport_connects_to_the_validated_ip_but_keeps_host_and_tls_name(self):
        request = httpx.Request("GET", "https://research.example:8443/path")
        response = httpx.Response(200, request=request)
        with (
            patch(
                "app.services.ssrf.socket.getaddrinfo",
                return_value=_dns_result("93.184.216.34"),
            ),
            patch("httpx.HTTPTransport.handle_request", return_value=response) as send,
        ):
            result = PinnedHTTPTransport().handle_request(request)

        pinned_request = send.call_args.args[0]
        self.assertEqual(result.status_code, 200)
        self.assertEqual(pinned_request.url.host, "93.184.216.34")
        self.assertEqual(pinned_request.headers["host"], "research.example:8443")
        self.assertEqual(pinned_request.extensions["sni_hostname"], "research.example")

    def test_safe_resolution_followed_by_private_resolution_is_blocked_before_connect(self):
        request = httpx.Request("GET", "https://research.example/")
        response = httpx.Response(200, request=request)
        with (
            patch(
                "app.services.ssrf.socket.getaddrinfo",
                side_effect=[
                    _dns_result("93.184.216.34"),
                    _dns_result("127.0.0.1"),
                ],
            ),
            patch("httpx.HTTPTransport.handle_request", return_value=response) as send,
        ):
            transport = PinnedHTTPTransport()
            transport.handle_request(request)
            with self.assertRaises(UnsafeDestination):
                transport.handle_request(request)
        self.assertEqual(send.call_count, 1)


if __name__ == "__main__":
    unittest.main()
