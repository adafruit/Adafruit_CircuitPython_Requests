from unittest import mock
import mocket
import pytest
import adafruit_requests

ip = "1.2.3.4"
host = "wifitest.adafruit.com"
path = "/testwifi/index.html"
text = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
response = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + text


def test_get_https_no_ssl():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    with pytest.raises(RuntimeError):
        r = s.get("https://" + host + path)


def test_get_https_text():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    pool.socket.return_value = sock
    ssl = mocket.SSLContext()

    s = adafruit_requests.Session(pool, ssl)
    r = s.get("https://" + host + path)

    sock.connect.assert_called_once_with((host, 443))

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(b"wifitest.adafruit.com"),]
    )
    assert r.text == str(text, "utf-8")

    # Close isn't needed but can be called to release the socket early.
    r.close()


def test_get_http_text():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    r = s.get("http://" + host + path)

    sock.connect.assert_called_once_with((ip, 80))

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(b"wifitest.adafruit.com"),]
    )
    assert r.text == str(text, "utf-8")


def test_get_close():
    """Test that a response can be closed without the contents being accessed."""
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    r = s.get("http://" + host + path)

    sock.connect.assert_called_once_with((ip, 80))

    sock.send.assert_has_calls(
        [
            mock.call(b"GET"),
            mock.call(b" /"),
            mock.call(b"testwifi/index.html"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(b"wifitest.adafruit.com"),]
    )
    r.close()
