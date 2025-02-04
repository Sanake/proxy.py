# -*- coding: utf-8 -*-
"""
    proxy.py
    ~~~~~~~~
    ⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on
    Network monitoring, controls & Application development, testing, debugging.

    :copyright: (c) 2013-present by Abhinav Singh and contributors.
    :license: BSD, see LICENSE for more details.

    .. spelling::

       http
       url
"""
from typing import Optional, Tuple

from ..common.constants import COLON, SLASH, HTTP_URL_PREFIX, HTTPS_URL_PREFIX
from ..common.utils import text_


class Url:
    """``urllib.urlparse`` doesn't work for proxy.py, so we wrote a simple URL.

    Currently, URL only implements what is necessary for HttpParser to work.
    """

    def __init__(
            self,
            scheme: Optional[bytes] = None,
            hostname: Optional[bytes] = None,
            port: Optional[int] = None,
            remainder: Optional[bytes] = None,
    ) -> None:
        self.scheme: Optional[bytes] = scheme
        self.hostname: Optional[bytes] = hostname
        self.port: Optional[int] = port
        self.remainder: Optional[bytes] = remainder

    def __str__(self) -> str:
        url = ''
        if self.scheme:
            url += '{0}://'.format(text_(self.scheme))
        if self.hostname:
            url += text_(self.hostname)
        if self.port:
            url += ':{0}'.format(self.port)
        if self.remainder:
            url += text_(self.remainder)
        return url

    @classmethod
    def from_bytes(cls, raw: bytes) -> 'Url':
        """A URL within proxy.py core can have several styles,
        because proxy.py supports both proxy and web server use cases.

        Example:
        For a Web server, url is like ``/`` or ``/get`` or ``/get?key=value``
        For a HTTPS connect tunnel, url is like ``httpbin.org:443``
        For a HTTP proxy request, url is like ``http://httpbin.org/get``

        Further:
        1) URL may contain unicode characters
        2) URL may contain IPv4 and IPv6 format addresses instead of domain names

        We use heuristics based approach for our URL parser.
        """
        if raw[0] == 47:    # SLASH == 47
            return cls(remainder=raw)
        is_http = raw.startswith(HTTP_URL_PREFIX)
        is_https = raw.startswith(HTTPS_URL_PREFIX)
        if is_http or is_https:
            rest = raw[len(b'https://'):] \
                if is_https \
                else raw[len(b'http://'):]
            parts = rest.split(SLASH, 1)
            host, port = Url.parse_host_and_port(parts[0])
            return cls(
                scheme=b'https' if is_https else b'http',
                hostname=host,
                port=port,
                remainder=None if len(parts) == 1 else (
                    SLASH + parts[1]
                ),
            )
        host, port = Url.parse_host_and_port(raw)
        return cls(hostname=host, port=port)

    @staticmethod
    def parse_host_and_port(raw: bytes) -> Tuple[bytes, Optional[int]]:
        parts = raw.split(COLON, 2)
        num_parts = len(parts)
        port: Optional[int] = None
        # No port found
        if num_parts == 1:
            return parts[0], None
        # Host and port found
        if num_parts == 2:
            return COLON.join(parts[:-1]), int(parts[-1])
        # More than a single COLON i.e. IPv6 scenario
        try:
            # Try to resolve last part as an int port
            last_token = parts[-1].split(COLON)
            port = int(last_token[-1])
            host = COLON.join(parts[:-1]) + COLON + \
                COLON.join(last_token[:-1])
        except ValueError:
            # If unable to convert last part into port,
            # treat entire data as host
            host, port = raw, None
        # patch up invalid ipv6 scenario
        rhost = host.decode('utf-8')
        if COLON.decode('utf-8') in rhost and \
                rhost[0] != '[' and \
                rhost[-1] != ']':
            host = b'[' + host + b']'
        return host, port
