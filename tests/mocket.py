# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Mock Socket """

from unittest import mock


class MocketPool:  # pylint: disable=too-few-public-methods
    """ Mock SocketPool """

    SOCK_STREAM = 0

    def __init__(self):
        self.getaddrinfo = mock.Mock()
        self.socket = mock.Mock()


class Mocket:  # pylint: disable=too-few-public-methods
    """ Mock Socket """

    def __init__(self, response):
        self.settimeout = mock.Mock()
        self.close = mock.Mock()
        self.connect = mock.Mock()
        self.send = mock.Mock(side_effect=self._send)
        self.readline = mock.Mock(side_effect=self._readline)
        self.recv = mock.Mock(side_effect=self._recv)
        self.recv_into = mock.Mock(side_effect=self._recv_into)
        self._response = response
        self._position = 0
        self.fail_next_send = False

    def _send(self, data):
        if self.fail_next_send:
            self.fail_next_send = False
            return 0
        return len(data)

    def _readline(self):
        i = self._response.find(b"\r\n", self._position)
        response = self._response[self._position : i + 2]
        self._position = i + 2
        return response

    def _recv(self, count):
        end = self._position + count
        response = self._response[self._position : end]
        self._position = end
        return response

    def _recv_into(self, buf, nbytes=0):
        assert isinstance(nbytes, int) and nbytes >= 0
        read = nbytes if nbytes > 0 else len(buf)
        remaining = len(self._response) - self._position
        read = min(read, remaining)
        end = self._position + read
        buf[:read] = self._response[self._position : end]
        self._position = end
        return read


class SSLContext:  # pylint: disable=too-few-public-methods
    """ Mock SSL Context """

    def __init__(self):
        self.wrap_socket = mock.Mock(side_effect=self._wrap_socket)

    def _wrap_socket(
        self, sock, server_hostname=None
    ):  # pylint: disable=no-self-use,unused-argument
        return sock
