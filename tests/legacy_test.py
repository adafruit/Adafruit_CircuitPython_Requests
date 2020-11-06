from unittest import mock
import legacy_mocket as mocket
import json
import pytest
import adafruit_requests

ip = "1.2.3.4"
host = "httpbin.org"
response = {"Date": "July 25, 2019"}
encoded = json.dumps(response).encode("utf-8")
headers = "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n".format(len(encoded)).encode(
    "utf-8"
)


def test_get_json():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("http://" + host + "/get")

    sock.connect.assert_called_once_with((ip, 80))
    assert r.json() == response
    r.close()


def test_tls_mode():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("https://" + host + "/get")

    sock.connect.assert_called_once_with((host, 443), mocket.interface.TLS_MODE)
    assert r.json() == response
    r.close()


def test_post_string():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    data = "31F"
    r = adafruit_requests.post("http://" + host + "/post", data=data)
    sock.connect.assert_called_once_with((ip, 80))
    sock.send.assert_called_with(b"31F")
    r.close()


def test_second_tls_send_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    sock2 = mocket.Mocket(headers + encoded)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2]

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("https://" + host + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [mock.call(b"testwifi/index.html"),]
    )

    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(host.encode("utf-8")), mock.call(b"\r\n"),]
    )
    assert r.text == str(encoded, "utf-8")

    sock.fail_next_send = True
    adafruit_requests.get("https://" + host + "/get2")

    sock.connect.assert_called_once_with((host, 443), mocket.interface.TLS_MODE)
    sock2.connect.assert_called_once_with((host, 443), mocket.interface.TLS_MODE)
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert mocket.socket.call_count == 2


def test_second_send_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    sock2 = mocket.Mocket(headers + encoded)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2]

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("http://" + host + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [mock.call(b"testwifi/index.html"),]
    )

    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(host.encode("utf-8")), mock.call(b"\r\n"),]
    )
    assert r.text == str(encoded, "utf-8")

    sock.fail_next_send = True
    adafruit_requests.get("http://" + host + "/get2")

    sock.connect.assert_called_once_with((ip, 80))
    sock2.connect.assert_called_once_with((ip, 80))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    assert sock2.close.call_count == 0
    assert mocket.socket.call_count == 2


def test_first_read_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(b"")
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock]

    adafruit_requests.set_socket(mocket, mocket.interface)

    with pytest.raises(RuntimeError):
        r = adafruit_requests.get("http://" + host + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [mock.call(b"testwifi/index.html"),]
    )

    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(host.encode("utf-8")), mock.call(b"\r\n"),]
    )

    sock.connect.assert_called_once_with((ip, 80))
    # Make sure that the socket is closed after the first receive fails.
    sock.close.assert_called_once()
    assert mocket.socket.call_count == 1


def test_second_tls_connect_fails():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    sock2 = mocket.Mocket(headers + encoded)
    sock3 = mocket.Mocket(headers + encoded)
    mocket.socket.call_count = 0  # Reset call count
    mocket.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = RuntimeError("error connecting")

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("https://" + host + "/testwifi/index.html")

    sock.send.assert_has_calls(
        [mock.call(b"testwifi/index.html"),]
    )

    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(host.encode("utf-8")), mock.call(b"\r\n"),]
    )
    assert r.text == str(encoded, "utf-8")

    host2 = "test.adafruit.com"
    r = adafruit_requests.get("https://" + host2 + "/get2")

    sock.connect.assert_called_once_with((host, 443), mocket.interface.TLS_MODE)
    sock2.connect.assert_called_once_with((host2, 443), mocket.interface.TLS_MODE)
    sock3.connect.assert_called_once_with((host2, 443), mocket.interface.TLS_MODE)
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert mocket.socket.call_count == 3
