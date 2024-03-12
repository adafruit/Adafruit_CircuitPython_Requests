# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Reuse Tests """

from unittest import mock

import mocket
import pytest


def test_get_twice(pool, requests_ssl):
    sock = mocket.Mocket(mocket.MOCK_RESPONSE + mocket.MOCK_RESPONSE)
    pool.socket.return_value = sock

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1)

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

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1 + "2")

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
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )

    assert response.text == str(mocket.MOCK_RESPONSE_TEXT, "utf-8")
    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    pool.socket.assert_called_once()


def test_get_twice_after_second(pool, requests_ssl):
    sock = mocket.Mocket(
        b"H"
        b"TTP/1.0 200 OK\r\nContent-Length: "
        b"70\r\n\r\nHTTP/1.0 2"
        b"H"
        b"TTP/1.0 200 OK\r\nContent-Length: "
        b"70\r\n\r\nHTTP/1.0 2"
    )
    pool.socket.return_value = sock

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1)

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

    requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1 + "2")

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
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest.adafruit.com"),
        ]
    )
    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    pool.socket.assert_called_once()

    with pytest.raises(RuntimeError) as context:
        result = response.text  # pylint: disable=unused-variable
    assert "Newer Response closed this one. Use Responses immediately." in str(context)


def test_connect_out_of_memory(pool, requests_ssl):
    sock = mocket.Mocket()
    sock2 = mocket.Mocket()
    sock3 = mocket.Mocket()
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = MemoryError()

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1)

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

    response = requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_2)
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
            mock.call(b"Host"),
            mock.call(b": "),
            mock.call(b"wifitest2.adafruit.com"),
        ]
    )

    assert response.text == str(mocket.MOCK_RESPONSE_TEXT, "utf-8")
    sock.close.assert_called_once()
    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    sock3.connect.assert_called_once_with((mocket.MOCK_HOST_2, 443))


def test_second_send_fails(pool, requests_ssl):
    sock = mocket.Mocket()
    sock2 = mocket.Mocket()
    pool.socket.side_effect = [sock, sock2]

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

    sock.fail_next_send = True
    requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1 + "2")

    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    sock2.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert pool.socket.call_count == 2


def test_second_send_lies_recv_fails(pool, requests_ssl):
    sock = mocket.Mocket()
    sock2 = mocket.Mocket()
    pool.socket.side_effect = [sock, sock2]

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

    requests_ssl.get("https://" + mocket.MOCK_ENDPOINT_1 + "2")

    sock.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    sock2.connect.assert_called_once_with((mocket.MOCK_HOST_1, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert pool.socket.call_count == 2
