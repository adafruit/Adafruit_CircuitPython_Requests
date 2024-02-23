# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-FileCopyrightText: 2024 Justin Myers for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Mock Socket """

from unittest import mock

MOCK_POOL_IP = "10.10.10.10"
MOCK_HOST_1 = "wifitest.adafruit.com"
MOCK_HOST_2 = "wifitest2.adafruit.com"
MOCK_PATH_1 = "/testwifi/index.html"
MOCK_ENDPOINT_1 = MOCK_HOST_1 + MOCK_PATH_1
MOCK_ENDPOINT_2 = MOCK_HOST_2 + MOCK_PATH_1
MOCK_RESPONSE_TEXT = (
    b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
)
MOCK_RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + MOCK_RESPONSE_TEXT


class MocketPool:  # pylint: disable=too-few-public-methods
    """Mock SocketPool"""

    SOCK_STREAM = 0

    # pylint: disable=unused-argument
    def __init__(self, radio=None):
        self.getaddrinfo = mock.Mock()
        self.getaddrinfo.return_value = ((None, None, None, None, (MOCK_POOL_IP, 80)),)
        self.socket = mock.Mock()


class Mocket:  # pylint: disable=too-few-public-methods
    """Mock Socket"""

    def __init__(self, response=MOCK_RESPONSE):
        self.settimeout = mock.Mock()
        self.close = mock.Mock()
        self.connect = mock.Mock()
        self.send = mock.Mock(side_effect=self._send)
        self.readline = mock.Mock(side_effect=self._readline)
        self.recv = mock.Mock(side_effect=self._recv)
        self.recv_into = mock.Mock(side_effect=self._recv_into)
        # Test helpers
        self._response = response
        self._position = 0
        self.fail_next_send = False
        self.sent_data = []

    def _send(self, data):
        if self.fail_next_send:
            self.fail_next_send = False
            return 0
        self.sent_data.append(data)
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
    """Mock SSL Context"""

    def __init__(self):
        self.wrap_socket = mock.Mock(side_effect=self._wrap_socket)

    def _wrap_socket(
        self, sock, server_hostname=None
    ):  # pylint: disable=no-self-use,unused-argument
        return sock


# pylint: disable=too-few-public-methods
class MockRadio:
    class Radio:
        pass

    class ESP_SPIcontrol:
        TLS_MODE = 2

    class WIZNET5K:
        pass

    class Unsupported:
        pass
