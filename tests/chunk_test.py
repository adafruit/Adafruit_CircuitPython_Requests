# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Chunk Tests """

from unittest import mock

import mocket

import adafruit_requests

IP = "1.2.3.4"
HOST = "wifitest.adafruit.com"
PATH = "/testwifi/index.html"
TEXT = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
HEADERS = b"HTTP/1.0 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"
HEADERS_EXTRA_SPACE = b"HTTP/1.0 200 OK\r\nTransfer-Encoding:  chunked\r\n\r\n"


def _chunk(response, split, extra=b""):
    i = 0
    chunked = b""
    while i < len(response):
        remaining = len(response) - i
        chunk_size = split
        if remaining < chunk_size:
            chunk_size = remaining
        new_i = i + chunk_size
        chunked += (
            hex(chunk_size)[2:].encode("ascii")
            + extra
            + b"\r\n"
            + response[i:new_i]
            + b"\r\n"
        )
        i = new_i
    # The final chunk is zero length.
    chunked += b"0\r\n\r\n"
    return chunked


def do_test_get_text(
    extra=b"",
):
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    chunk = _chunk(TEXT, 33, extra)
    print(chunk)
    sock = mocket.Mocket(HEADERS + chunk)
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
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    assert response.text == str(TEXT, "utf-8")


def test_get_text():
    do_test_get_text()


def test_get_text_extra():
    do_test_get_text(b";blahblah; blah")


def do_test_close_flush(
    extra=b"",
):
    """Test that a chunked response can be closed even when the
    request contents were not accessed."""
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    chunk = _chunk(TEXT, 33, extra)
    print(chunk)
    sock = mocket.Mocket(HEADERS + chunk)
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
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )

    response.close()


def test_close_flush():
    do_test_close_flush()


def test_close_flush_extra():
    do_test_close_flush(b";blahblah; blah")


def do_test_get_text_extra_space(
    extra=b"",
):
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    chunk = _chunk(TEXT, 33, extra)
    print(chunk)
    sock = mocket.Mocket(HEADERS_EXTRA_SPACE + chunk)
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
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    assert response.text == str(TEXT, "utf-8")
