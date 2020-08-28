from unittest import mock
import mocket
import adafruit_requests

ip = "1.2.3.4"
host = "wifitest.adafruit.com"
path = "/testwifi/index.html"
text = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
response = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + text


def test_get_https_text():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("https://" + host + path)

    sock.connect.assert_called_once_with((host, 443), mocket.interface.TLS_MODE)
    sock.send.assert_has_calls(
        [
            mock.call(b"GET /testwifi/index.html HTTP/1.0\r\n"),
            mock.call(b"Host: wifitest.adafruit.com\r\n"),
        ]
    )
    assert r.text == str(text, "utf-8")


def test_get_http_text():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("http://" + host + path)

    sock.connect.assert_called_once_with((ip, 80), mocket.interface.TCP_MODE)
    sock.send.assert_has_calls(
        [
            mock.call(b"GET /testwifi/index.html HTTP/1.0\r\n"),
            mock.call(b"Host: wifitest.adafruit.com\r\n"),
        ]
    )
    assert r.text == str(text, "utf-8")


# Add a chunked response test when we support HTTP 1.1
