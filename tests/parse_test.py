# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

"""  Parse Tests """

import json
import mocket
import adafruit_requests

IP = "1.2.3.4"
HOST = "httpbin.org"
RESPONSE = {"Date": "July 25, 2019"}
ENCODED = json.dumps(RESPONSE).encode("utf-8")
# Padding here tests the case where a header line is exactly 32 bytes buffered by
# aligning the Content-Type header after it.
HEADERS = (
    (
        "HTTP/1.0 200 OK\r\npadding: 000\r\n"
        "Content-Type: application/json\r\nContent-Length: {}\r\n\r\n"
    )
    .format(len(ENCODED))
    .encode("utf-8")
)


def test_json():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    response = requests_session.get("http://" + HOST + "/get")
    sock.connect.assert_called_once_with((IP, 80))
    assert response.json() == RESPONSE
