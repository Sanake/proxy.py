# -*- coding: utf-8 -*-
"""
    proxy.py
    ~~~~~~~~
    ⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on
    Network monitoring, controls & Application development, testing, debugging.

    :copyright: (c) 2013-present by Abhinav Singh and contributors.
    :license: BSD, see LICENSE for more details.
"""
import os
import socket
import tempfile
import unittest

from unittest import mock

import pytest

from proxy.core.acceptor import Listener
from proxy.common._compat import IS_WINDOWS  # noqa: WPS436
from proxy.common.flag import FlagParser


class TestListener(unittest.TestCase):

    @mock.patch('socket.socket')
    def test_setup_and_teardown(self, mock_socket: mock.Mock) -> None:
        sock = mock_socket.return_value
        flags = FlagParser.initialize(port=0)
        listener = Listener(flags)
        listener.setup()
        mock_socket.assert_called_with(
            socket.AF_INET6 if flags.hostname.version == 6 else socket.AF_INET,
            socket.SOCK_STREAM,
        )
        self.assertEqual(sock.setsockopt.call_count, 2)
        self.assertEqual(
            sock.setsockopt.call_args_list[0][0],
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
        )
        self.assertEqual(
            sock.setsockopt.call_args_list[1][0],
            (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
        )
        sock.bind.assert_called_with(
            (str(flags.hostname), 0),
        )
        sock.listen.assert_called_with(flags.backlog)
        sock.setblocking.assert_called_with(False)

        listener.shutdown()
        sock.close.assert_called_once()

    # FIXME: Ignore is necessary for as long as pytest hasn't figured out
    # FIXME: typing for their fixtures.
    # Refs:
    # * https://github.com/pytest-dev/pytest/issues/7469#issuecomment-918345196
    # * https://github.com/pytest-dev/pytest/issues/3342
    @pytest.mark.skipif(
        IS_WINDOWS,
        reason='AF_UNIX not available on Windows',
    )  # type: ignore[misc]
    @mock.patch('os.remove')
    @mock.patch('socket.socket')
    def test_unix_path_listener(self, mock_socket: mock.Mock, mock_remove: mock.Mock) -> None:
        sock = mock_socket.return_value
        sock_path = os.path.join(tempfile.gettempdir(), 'proxy.sock')
        flags = FlagParser.initialize(unix_socket_path=sock_path)
        listener = Listener(flags)
        listener.setup()

        mock_socket.assert_called_with(
            socket.AF_UNIX,
            socket.SOCK_STREAM,
        )
        self.assertEqual(sock.setsockopt.call_count, 2)
        self.assertEqual(
            sock.setsockopt.call_args_list[0][0],
            (socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
        )
        self.assertEqual(
            sock.setsockopt.call_args_list[1][0],
            (socket.IPPROTO_TCP, socket.TCP_NODELAY, 1),
        )
        sock.bind.assert_called_with(sock_path)
        sock.listen.assert_called_with(flags.backlog)
        sock.setblocking.assert_called_with(False)

        listener.shutdown()
        mock_remove.assert_called_once_with(sock_path)
        sock.close.assert_called_once()
