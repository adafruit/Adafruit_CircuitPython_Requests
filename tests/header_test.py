# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""Header Tests"""

import mocket
import pytest

import adafruit_requests


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (b"Motor", "Motor"),
        (b"M\xc3\xb6tor", "M\u00f6tor"),
        (b"\xe2\x82\xac", "\u20ac"),
        (b"M\xf6tor", "M\u00f6tor"),
        (b"\xff", "\u00ff"),
        (b"\xc3\xb6\xff", "\u00c3\u00b6\u00ff"),
        (bytes(range(0x80, 0x100)), bytes(range(0x80, 0x100)).decode("latin-1")),
        (b"M\xf6tor:west", "M\u00f6tor:west"),
    ),
)
def test_response_header_value_octets(pool, value, expected):
    sock = mocket.Mocket(
        b"HTTP/1.1 200 OK\r\nX-Sensor-Name: " + value + b"\r\nContent-Length: 2\r\n\r\nok"
    )
    pool.socket.return_value = sock
    with adafruit_requests.Session(pool).get("http://" + mocket.MOCK_HOST_1 + "/get") as response:
        assert response.headers["x-sensor-name"] == expected
        assert response.headers["content-length"] == "2"
        assert response.content == b"ok"


def test_response_opaque_header_with_chunked_body(pool):
    sock = mocket.Mocket(
        b"HTTP/1.1 200 OK\r\nX-Sensor-Name: M\xf6tor\r\n"
        b"Transfer-Encoding: chunked\r\n\r\n2\r\nhe\r\n3\r\nllo\r\n0\r\n\r\n"
    )
    pool.socket.return_value = sock
    with adafruit_requests.Session(pool).get("http://" + mocket.MOCK_HOST_1 + "/get") as response:
        assert response.headers["x-sensor-name"] == "M\u00f6tor"
        assert response.content == b"hello"


def test_response_opaque_duplicate_cookies(pool):
    sock = mocket.Mocket(
        b"HTTP/1.1 200 OK\r\nSet-Cookie: a=M\xf6tor\r\nSet-Cookie: b=2\r\n"
        b"Content-Length: 2\r\n\r\nok"
    )
    pool.socket.return_value = sock
    with adafruit_requests.Session(pool).get("http://" + mocket.MOCK_HOST_1 + "/get") as response:
        assert response.headers["set-cookie"] == "a=M\u00f6tor, b=2"
        assert response.content == b"ok"


def test_response_opaque_header_preserves_utf8_body(pool):
    sock = mocket.Mocket(
        b"HTTP/1.1 200 OK\r\nX-Sensor-Name: \xff\r\nContent-Length: 5\r\n\r\ncaf\xc3\xa9"
    )
    pool.socket.return_value = sock
    with adafruit_requests.Session(pool).get("http://" + mocket.MOCK_HOST_1 + "/get") as response:
        assert response.headers["x-sensor-name"] == "\u00ff"
        assert response.text == "caf\u00e9"


def test_response_invalid_utf8_header_name_is_still_rejected(pool):
    sock = mocket.Mocket(b"HTTP/1.1 200 OK\r\nX-\xff: value\r\nContent-Length: 2\r\n\r\nok")
    pool.socket.return_value = sock
    with pytest.raises(UnicodeError):
        adafruit_requests.Session(pool).get("http://" + mocket.MOCK_HOST_1 + "/get")


@pytest.mark.parametrize(
    "header",
    (
        b"Content-Length: \xa03",
        b"Content-Length: 3\xff",
        b"Transfer-Encoding: \xa0chunked",
        b"Transfer-Encoding: chunked\xff",
    ),
)
def test_response_non_utf8_framing_is_still_rejected(pool, header):
    sock = mocket.Mocket(b"HTTP/1.1 200 OK\r\n" + header + b"\r\n\r\nabc")
    pool.socket.return_value = sock
    with pytest.raises(UnicodeError):
        adafruit_requests.Session(pool).get("http://" + mocket.MOCK_HOST_1 + "/get")


def test_check_headers_not_dict(requests):
    with pytest.raises(TypeError) as context:
        requests._check_headers("")
    assert "Headers must be in dict format" in str(context)


def test_check_headers_not_valid(requests):
    with pytest.raises(TypeError) as context:
        requests._check_headers({"Good1": "a", "Good2": b"b", "Good3": None, "Bad1": True})
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


def test_host_with_port(pool, sock, requests):
    headers = {}
    requests.get("http://" + mocket.MOCK_HOST_1 + ":8080/get", headers=headers)

    pool.getaddrinfo.assert_called_once_with(mocket.MOCK_HOST_1, 8080, 0, pool.SOCK_STREAM)
    sent = b"".join(sock.sent_data)
    assert b"Host: wifitest.adafruit.com:8080\r\n" in sent


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
