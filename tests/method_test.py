# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""Post Tests"""

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

    sent = b"".join(sock.sent_data)
    assert sent.startswith(bytes(f"{call} /{call.lower()} HTTP/1.1\r\n", "utf-8"))
    assert b"\r\nHost: wifitest.adafruit.com\r\n" in sent


def test_post_string(sock, requests):
    data = "31F"
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", data=data)
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert sent.endswith(b"\r\n\r\n31F")


def test_post_form(sock, requests):
    data = {
        "Date": "July 25, 2019",
        "Time": "12:00",
    }
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", data=data)
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"\r\nContent-Type: application/x-www-form-urlencoded\r\n" in sent
    assert sent.endswith(b"\r\n\r\nDate=July 25, 2019&Time=12:00")


def test_post_json(sock, requests):
    json_data = {
        "Date": "July 25, 2019",
        "Time": "12:00",
    }
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", json=json_data)
    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"\r\nContent-Type: application/json\r\n" in sent
    assert sent.endswith(b'\r\n\r\n{"Date": "July 25, 2019", "Time": "12:00"}')
