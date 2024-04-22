# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Post Tests """

from unittest import mock

import mocket
import pytest


@pytest.mark.parametrize(
    "call",
    (
        "DELETE",
        "GET",
        "HEAD",
        "OPTIONS",
        "PATCH",
        "POST",
        "PUT",
    ),
)
def test_methods(call, sock, requests):
    method = getattr(requests, call.lower())
    method("http://" + mocket.MOCK_HOST_1 + "/" + call.lower())
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))

    sock.send.assert_has_calls(
        [
            mock.call(bytes(call, "utf-8")),
            mock.call(b" /"),
            mock.call(bytes(call.lower(), "utf-8")),
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


def test_post_string(sock, requests):
    data = "31F"
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", data=data)
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_called_with(b"31F")


def test_post_form(sock, requests):
    data = {
        "Date": "July 25, 2019",
        "Time": "12:00",
    }
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", data=data)
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(b"application/x-www-form-urlencoded"),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_called_with(b"Date=July 25, 2019&Time=12:00")


def test_post_json(sock, requests):
    json_data = {
        "Date": "July 25, 2019",
        "Time": "12:00",
    }
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", json=json_data)
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(b"application/json"),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_called_with(b'{"Date": "July 25, 2019", "Time": "12:00"}')
