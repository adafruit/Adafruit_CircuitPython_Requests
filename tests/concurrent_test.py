from unittest import mock
import mocket
import pytest
import errno
import adafruit_requests

ip = "1.2.3.4"
host = "wifitest.adafruit.com"
host2 = "wifitest2.adafruit.com"
path = "/testwifi/index.html"
text = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
response = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + text


def test_second_connect_fails_memoryerror():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    sock2 = mocket.Mocket(response)
    sock3 = mocket.Mocket(response)
    pool.socket.call_count = 0  # Reset call count
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = MemoryError()

    ssl = mocket.SSLContext()

    s = adafruit_requests.Session(pool, ssl)
    r = s.get("https://" + host + path)

    sock.send.assert_has_calls(
        [mock.call(b"testwifi/index.html"),]
    )

    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(b"wifitest.adafruit.com"), mock.call(b"\r\n"),]
    )
    assert r.text == str(text, "utf-8")

    host2 = "test.adafruit.com"
    s.get("https://" + host2 + path)

    sock.connect.assert_called_once_with((host, 443))
    sock2.connect.assert_called_once_with((host2, 443))
    sock3.connect.assert_called_once_with((host2, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert pool.socket.call_count == 3


def test_second_connect_fails_oserror():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    sock2 = mocket.Mocket(response)
    sock3 = mocket.Mocket(response)
    pool.socket.call_count = 0  # Reset call count
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = OSError(errno.ENOMEM)

    ssl = mocket.SSLContext()

    s = adafruit_requests.Session(pool, ssl)
    r = s.get("https://" + host + path)

    sock.send.assert_has_calls(
        [mock.call(b"testwifi/index.html"),]
    )

    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(b"wifitest.adafruit.com"), mock.call(b"\r\n"),]
    )
    assert r.text == str(text, "utf-8")

    host2 = "test.adafruit.com"
    s.get("https://" + host2 + path)

    sock.connect.assert_called_once_with((host, 443))
    sock2.connect.assert_called_once_with((host2, 443))
    sock3.connect.assert_called_once_with((host2, 443))
    # Make sure that the socket is closed after send fails.
    sock.close.assert_called_once()
    sock2.close.assert_called_once()
    assert sock3.close.call_count == 0
    assert pool.socket.call_count == 3
