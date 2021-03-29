# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Reuse Tests """

from unittest import mock
import mocket
import pytest
import adafruit_requests

IP = "1.2.3.4"
HOST = "wifitest.adafruit.com"
HOST2 = "wifitest2.adafruit.com"
PATH = "/testwifi/index.html"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
RESPONSE = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + TEXT


def test_get_twice():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE + RESPONSE)
    pool.socket.return_value = sock
    ssl = mocket.SSLContext()

    requests_session = adafruit_requests.Session(pool, ssl)
    response = requests_session.get("https://" + HOST + PATH)

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

    response = requests_session.get("https://" + HOST + PATH + "2")

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html2"),
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
    sock.connect.assert_called_once_with((HOST, 443))
    pool.socket.assert_called_once()


def test_get_twice_after_second():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE + RESPONSE)
    pool.socket.return_value = sock
    ssl = mocket.SSLContext()

    requests_session = adafruit_requests.Session(pool, ssl)
    response = requests_session.get("https://" + HOST + PATH)

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

    requests_session.get("https://" + HOST + PATH + "2")

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html2"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    sock.connect.assert_called_once_with((HOST, 443))
    pool.socket.assert_called_once()

    with pytest.raises(RuntimeError):
        response.text == str(TEXT, "utf-8")  # pylint: disable=expression-not-assigned


def test_connect_out_of_memory():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    sock2 = mocket.Mocket(RESPONSE)
    sock3 = mocket.Mocket(RESPONSE)
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = MemoryError()
    ssl = mocket.SSLContext()

    requests_session = adafruit_requests.Session(pool, ssl)
    response = requests_session.get("https://" + HOST + PATH)

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

    response = requests_session.get("https://" + HOST2 + PATH)
    sock3.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock3.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"wifitest2.adafruit.com"),
        ]
    )

    assert response.text == str(TEXT, "utf-8")
    sock.close.assert_called_once()
    sock.connect.assert_called_once_with((HOST, 443))
    sock3.connect.assert_called_once_with((HOST2, 443))


def test_second_send_fails():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    sock2 = mocket.Mocket(RESPONSE)
    pool.socket.side_effect = [sock, sock2]

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

    sock.fail_next_send = True
    requests_session.get("https://" + HOST + PATH + "2")

    sock.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with((HOST, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert pool.socket.call_count == 2


def test_second_send_lies_recv_fails():  # pylint: disable=invalid-name
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE)
    sock2 = mocket.Mocket(RESPONSE)
    pool.socket.side_effect = [sock, sock2]

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

    requests_session.get("https://" + HOST + PATH + "2")

    sock.connect.assert_called_once_with((HOST, 443))
    sock2.connect.assert_called_once_with((HOST, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert pool.socket.call_count == 2
