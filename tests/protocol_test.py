# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

from unittest import mock
import mocket
import pytest
import adafruit_requests

IP = "1.2.3.4"
HOST = "wifitest.adafruit.com"
PATH = "/testwifi/index.html"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_get_https_no_ssl():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    with pytest.raises(RuntimeError):
        requests_session.get("https://" + HOST + PATH)


def test_get_https_text():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock
    ssl = mocket.SSLContext()

    requests_session = adafruit_requests.Session(pool, ssl)
    response = requests_session.get("https://" + HOST + PATH)

    sock.connect.assert_called_once_with((HOST, 443))

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    assert response.text == str(TEXT, "utf-8")

    # Close isn't needed but can be called to release the socket early.
    response.close()


def test_get_http_text():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    response = requests_session.get("http://" + HOST + PATH)

    sock.connect.assert_called_once_with((IP, 80))

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    assert response.text == str(TEXT, "utf-8")


def test_get_close():
    """Test that a response can be closed without the contents being accessed."""
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    response = requests_session.get("http://" + HOST + PATH)

    sock.connect.assert_called_once_with((IP, 80))

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    response.close()
