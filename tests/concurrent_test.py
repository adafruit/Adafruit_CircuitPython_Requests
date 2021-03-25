# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Concurrent Tests """

import errno
from unittest import mock
import mocket
import adafruit_requests

IP = "1.2.3.4"
HOST = "wifitest.adafruit.com"
HOST2 = "test.adafruit.com"
PATH = "/testwifi/index.html"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_second_connect_fails_memoryerror():  # pylint: disable=invalid-name
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    sock2 = mocket.Mocket(RESPONSE)
    sock3 = mocket.Mocket(RESPONSE)
    pool.socket.call_count = 0  # Reset call count
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = MemoryError()

    ssl = mocket.SSLContext()

    requests_session = adafruit_requests.Session(pool, ssl)
    response = requests_session.get("https://" + HOST + PATH)

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest.adafruit.com"),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(TEXT, "utf-8")

    requests_session.get("https://" + HOST2 + PATH)

    sock.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with((HOST2, 443))
    sock3.connect.assert_called_once_with((HOST2, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert pool.socket.call_count == 3


def test_second_connect_fails_oserror():  # pylint: disable=invalid-name
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    sock2 = mocket.Mocket(RESPONSE)
    sock3 = mocket.Mocket(RESPONSE)
    pool.socket.call_count = 0  # Reset call count
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = OSError(errno.ENOMEM)

    ssl = mocket.SSLContext()

    requests_session = adafruit_requests.Session(pool, ssl)
    response = requests_session.get("https://" + HOST + PATH)

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest.adafruit.com"),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(TEXT, "utf-8")

    requests_session.get("https://" + HOST2 + PATH)

    sock.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with((HOST2, 443))
    sock3.connect.assert_called_once_with((HOST2, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert pool.socket.call_count == 3
