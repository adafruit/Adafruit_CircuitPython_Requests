# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Header Tests """

import mocket
import adafruit_requests

IP = "1.2.3.4"
HOST = "httpbin.org"
RESPONSE_HEADERS = b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n"


def test_host():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_requests.Session(pool)
    headers = {}
    requests_session.get("http://" + HOST + "/get", headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent)
    assert b"Host: httpbin.org\r\n" in sent


def test_host_replace():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_requests.Session(pool)
    headers = {"host": IP}
    requests_session.get("http://" + HOST + "/get", headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent)
    assert b"host: 1.2.3.4\r\n" in sent
    assert b"Host: httpbin.org\r\n" not in sent
    assert sent.lower().count(b"host:") == 1


def test_user_agent():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_requests.Session(pool)
    headers = {}
    requests_session.get("http://" + HOST + "/get", headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent)
    assert b"User-Agent: Adafruit CircuitPython\r\n" in sent


def test_user_agent_replace():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_requests.Session(pool)
    headers = {"user-agent": "blinka/1.0.0"}
    requests_session.get("http://" + HOST + "/get", headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent)
    assert b"user-agent: blinka/1.0.0\r\n" in sent
    assert b"User-Agent: Adafruit CircuitPython\r\n" not in sent
    assert sent.lower().count(b"user-agent:") == 1


def test_content_type():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_requests.Session(pool)
    headers = {}
    data = {"test": True}
    requests_session.post("http://" + HOST + "/get", data=data, headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent)
    assert b"Content-Type: application/x-www-form-urlencoded\r\n" in sent


def test_content_type_replace():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(RESPONSE_HEADERS)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)  # pylint: disable=no-member
        return len(data)

    sock.send.side_effect = _send

    requests_session = adafruit_requests.Session(pool)
    headers = {"content-type": "application/test"}
    data = {"test": True}
    requests_session.post("http://" + HOST + "/get", data=data, headers=headers)

    sock.connect.assert_called_once_with((IP, 80))
    sent = b"".join(sent)
    assert b"content-type: application/test\r\n" in sent
    assert b"Content-Type: application/x-www-form-urlencoded\r\n" not in sent
    assert sent.lower().count(b"content-type:") == 1
