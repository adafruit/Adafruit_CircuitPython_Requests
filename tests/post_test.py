# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Post Tests """

from unittest import mock
import json
import mocket
import adafruit_requests

IP = "1.2.3.4"
HOST = "httpbin.org"
RESPONSE = {}
ENCODED = json.dumps(RESPONSE).encode("utf-8")
HEADERS = "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n".format(len(ENCODED)).encode(
    "utf-8"
)


def test_method():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    requests_session.post("http://" + HOST + "/post")
    sock.connect.assert_called_once_with((IP, 80))

    sock.send.assert_has_calls(
        [
            mock.call(b"POST"),
            mock.call(b" /"),
            mock.call(b"post"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(b"httpbin.org"),
        ]
    )


def test_string():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    data = "31F"
    requests_session.post("http://" + HOST + "/post", data=data)
    sock.connect.assert_called_once_with((IP, 80))
    sock.send.assert_called_with(b"31F")


def test_form():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    data = {"Date": "July 25, 2019"}
    requests_session.post("http://" + HOST + "/post", data=data)
    sock.connect.assert_called_once_with((IP, 80))
    sock.send.assert_called_with(b"Date=July 25, 2019")


def test_json():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    pool.socket.return_value = sock

    requests_session = adafruit_requests.Session(pool)
    json_data = {"Date": "July 25, 2019"}
    requests_session.post("http://" + HOST + "/post", json=json_data)
    sock.connect.assert_called_once_with((IP, 80))
    sock.send.assert_called_with(b'{"Date": "July 25, 2019"}')
