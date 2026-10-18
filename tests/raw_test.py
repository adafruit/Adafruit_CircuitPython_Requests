# SPDX-FileCopyrightText: 2026 Vladimir Smitka
#
# SPDX-License-Identifier: Unlicense

"""Raw Tests"""

import mocket

import adafruit_requests

BODY = bytes(range(256)) * 4
LENGTH_RESPONSE = b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n" % len(BODY) + BODY


def _chunked(body, split):
    out = b""
    for i in range(0, len(body), split):
        piece = body[i : i + split]
        out += hex(len(piece))[2:].encode() + b"\r\n" + piece + b"\r\n"
    return b"HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n" + out + b"0\r\n\r\n"


def _get(response, **kw):
    pool = mocket.MocketPool()
    pool.socket.return_value = mocket.Mocket(response)
    requests_session = adafruit_requests.Session(pool)
    return requests_session.get("http://" + mocket.MOCK_ENDPOINT_1, **kw)


def _read_all(raw, size):
    buf = bytearray(size)
    out = b""
    while True:
        read = raw.readinto(buf)
        if read == 0:
            return out
        out += buf[:read]


def test_readinto_content_length():
    with _get(LENGTH_RESPONSE, stream=True) as response:
        assert _read_all(response.raw, 100) == BODY


def test_readinto_chunked():
    with _get(_chunked(BODY, 300), stream=True) as response:
        assert _read_all(response.raw, 64) == BODY


def test_read_includes_bytes_read_with_the_headers():
    with _get(LENGTH_RESPONSE, stream=True) as response:
        # The headers are parsed from 32-byte reads, so the start of the body is buffered.
        buffered = response._received_length
        assert buffered > 0
        first = response.raw.read(100)
        assert first == BODY[:buffered]
        assert first + _read_all(response.raw, 100) == BODY


def test_read_stops_at_content_length():
    with _get(LENGTH_RESPONSE + b"trailing", stream=True) as response:
        assert _read_all(response.raw, 100) == BODY
        assert response.raw.read(10) == b""


def test_json_uses_raw():
    body = b'{"a": 1}'
    response = b"HTTP/1.1 200 OK\r\nContent-Length: %d\r\n\r\n" % len(body) + body
    with _get(response) as response:
        assert response.json() == {"a": 1}
