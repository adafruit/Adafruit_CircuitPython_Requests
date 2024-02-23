# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Concurrent Tests """

import errno
from unittest import mock

import mocket


def test_second_connect_fails_memoryerror(pool, requests_ssl):
    sock = mocket.Mocket()
    sock2 = mocket.Mocket()
    sock3 = mocket.Mocket()
    pool.socket.call_count = 0  # Reset call count
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = MemoryError()

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1)

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(mocket.MOCK_RESPONSE_TEXT, "utf-8")

    requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_2)

    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    sock2.connect.assert_called_once_with((mocket.MOCK_HOST_2, 443))
    sock3.connect.assert_called_once_with((mocket.MOCK_HOST_2, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert pool.socket.call_count == 3


def test_second_connect_fails_oserror(pool, requests_ssl):
    sock = mocket.Mocket()
    sock2 = mocket.Mocket()
    sock3 = mocket.Mocket()
    pool.socket.call_count = 0  # Reset call count
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = OSError(errno.ENOMEM)

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1)

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(mocket.MOCK_RESPONSE_TEXT, "utf-8")

    requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_2)

    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    sock2.connect.assert_called_once_with((mocket.MOCK_HOST_2, 443))
    sock3.connect.assert_called_once_with((mocket.MOCK_HOST_2, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert pool.socket.call_count == 3
