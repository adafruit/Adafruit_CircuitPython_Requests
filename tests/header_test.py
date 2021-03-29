# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Header Tests """

import mocket
import adafruit_requests

IP = "1.2.3.4"
HOST = "httpbin.org"
RESPONSE_HEADERS = b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n"


def test_json():
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
    sent = b"".join(sent).lower()
    assert b"user-agent: blinka/1.0.0\r\n" in sent
    # The current implementation sends two user agents. Fix it, and uncomment below.
    # assert sent.count(b"user-agent:") == 1
