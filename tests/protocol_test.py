# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Protocol Tests """

from unittest import mock

import mocket
import pytest


def test_get_https_no_ssl(requests):
    with pytest.raises(ValueError):
        requests.get("https://" + mocket.MOCK_ENDPOINT_1)


def test_get_https_text(sock, requests_ssl):
    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1)

    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))

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
    assert response.text == str(mocket.MOCK_RESPONSE_TEXT, "utf-8")

    # Close isn't needed but can be called to release the socket early.
    response.close()


def test_get_http_text(sock, requests):
    response = requests.get("http://" + mocket.MOCK_ENDPOINT_1)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))

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
    assert response.text == str(mocket.MOCK_RESPONSE_TEXT, "utf-8")


def test_get_close(sock, requests):
    """Test that a response can be closed without the contents being accessed."""
    response = requests.get("http://" + mocket.MOCK_ENDPOINT_1)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))

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
