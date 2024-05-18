# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Header Tests """

import mocket
import pytest


def test_check_headers_not_dict(requests):
    with pytest.raises(TypeError) as context:
        requests._check_headers("")
    assert "Headers must be in dict format" in str(context)


def test_check_headers_not_valid(requests):
    with pytest.raises(TypeError) as context:
        requests._check_headers(
            {"Good1": "a", "Good2": b"b", "Good3": None, "Bad1": True}
        )
    assert "Header part (True) from Bad1 must be of type str or bytes" in str(context)


def test_check_headers_valid(requests):
    requests._check_headers({"Good1": "a", "Good2": b"b", "Good3": None})
    assert True


def test_host(sock, requests):
    headers = {}
    requests.get("http://" + mocket.MOCK_HOST_1 + "/get", headers=headers)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"Host: wifitest.adafruit.com\r\n" in sent


def test_host_replace(sock, requests):
    headers = {"host": mocket.MOCK_POOL_IP}
    requests.get("http://" + mocket.MOCK_HOST_1 + "/get", headers=headers)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"host: 10.10.10.10\r\n" in sent
    assert b"Host: wifitest.adafruit.com\r\n" not in sent
    assert sent.lower().count(b"host:") == 1


def test_user_agent(sock, requests):
    headers = {}
    requests.get("http://" + mocket.MOCK_HOST_1 + "/get", headers=headers)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"User-Agent: Adafruit CircuitPython\r\n" in sent


def test_user_agent_replace(sock, requests):
    headers = {"user-agent": "blinka/1.0.0"}
    requests.get("http://" + mocket.MOCK_HOST_1 + "/get", headers=headers)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"user-agent: blinka/1.0.0\r\n" in sent
    assert b"User-Agent: Adafruit CircuitPython\r\n" not in sent
    assert sent.lower().count(b"user-agent:") == 1


def test_content_type(sock, requests):
    headers = {}
    data = {"test": True}
    requests.post("http://" + mocket.MOCK_HOST_1 + "/get", data=data, headers=headers)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"Content-Type: application/x-www-form-urlencoded\r\n" in sent


def test_content_type_replace(sock, requests):
    headers = {"content-type": "application/test"}
    data = {"test": True}
    requests.post("http://" + mocket.MOCK_HOST_1 + "/get", data=data, headers=headers)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sent = b"".join(sock.sent_data)
    assert b"content-type: application/test\r\n" in sent
    assert b"Content-Type: application/x-www-form-urlencoded\r\n" not in sent
    assert sent.lower().count(b"content-type:") == 1
