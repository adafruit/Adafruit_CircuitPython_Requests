# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Legacy Tests """

from unittest import mock
import json
import legacy_mocket as mocket
import adafruit_requests

IP = "1.2.3.4"
HOST = "httpbin.org"
RESPONSE = {"Date": "July 25, 2019"}
ENCODED = json.dumps(RESPONSE).encode("utf-8")
HEADERS = "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n".format(len(ENCODED)).encode(
    "utf-8"
)


def test_get_json():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    response = adafruit_requests.get("http://" + HOST + "/get")

    sock.connect.assert_called_once_with((IP, 80))
    assert response.json() == RESPONSE
    response.close()


def test_tls_mode():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    response = adafruit_requests.get("https://" + HOST + "/get")

    sock.connect.assert_called_once_with((HOST, 443), mocket.interface.TLS_MODE)
    assert response.json() == RESPONSE
    response.close()


def test_post_string():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    data = "31F"
    response = adafruit_requests.post("http://" + HOST + "/post", data=data)
    sock.connect.assert_called_once_with((IP, 80))
    sock.send.assert_called_with(b"31F")
    response.close()


def test_second_tls_send_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    sock2 = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2]

    adafruit_requests.set_socket(mocket, mocket.interface)
    response = adafruit_requests.get("https://" + HOST + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(HOST.encode("utf-8")),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(ENCODED, "utf-8")

    sock.fail_next_send = True
    adafruit_requests.get("https://" + HOST + "/get2")

    sock.connect.assert_called_once_with((HOST, 443), mocket.interface.TLS_MODE)
    sock2.connect.assert_called_once_with((HOST, 443), mocket.interface.TLS_MODE)
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert mocket.socket.call_count == 2


def test_second_send_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    sock2 = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2]

    adafruit_requests.set_socket(mocket, mocket.interface)
    response = adafruit_requests.get("http://" + HOST + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(HOST.encode("utf-8")),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(ENCODED, "utf-8")

    sock.fail_next_send = True
    adafruit_requests.get("http://" + HOST + "/get2")

    sock.connect.assert_called_once_with((IP, 80))
    sock2.connect.assert_called_once_with((IP, 80))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert mocket.socket.call_count == 2


def test_first_read_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(b"")
    sock2 = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2]

    adafruit_requests.set_socket(mocket, mocket.interface)
    adafruit_requests.get("http://" + HOST + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(HOST.encode("utf-8")),
            mock.call(b"\r\n"),
        ]
    )

    sock2.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(HOST.encode("utf-8")),
            mock.call(b"\r\n"),
        ]
    )

    sock.connect.assert_called_once_with((IP, 80))
    sock2.connect.assert_called_once_with((IP, 80))
    # Make sure that the socket is closed after the first receive fails.
    sock.close.assert_called_once()
    assert mocket.socket.call_count == 2


def test_second_tls_connect_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (IP, 80)),)
    sock = mocket.Mocket(HEADERS + ENCODED)
    sock2 = mocket.Mocket(HEADERS + ENCODED)
    sock3 = mocket.Mocket(HEADERS + ENCODED)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = RuntimeError("error connecting")

    adafruit_requests.set_socket(mocket, mocket.interface)
    response = adafruit_requests.get("https://" + HOST + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [
            mock.call(b"testwifi/index.html"),
        ]
    )

    sock.send.assert_has_calls(
        [
            mock.call(b"Host: "),
            mock.call(HOST.encode("utf-8")),
            mock.call(b"\r\n"),
        ]
    )
    assert response.text == str(ENCODED, "utf-8")

    host2 = "test.adafruit.com"
    response = adafruit_requests.get("https://" + host2 + "/get2")

    sock.connect.assert_called_once_with((HOST, 443), mocket.interface.TLS_MODE)
    sock2.connect.assert_called_once_with((host2, 443), mocket.interface.TLS_MODE)
    sock3.connect.assert_called_once_with((host2, 443), mocket.interface.TLS_MODE)
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert mocket.socket.call_count == 3
