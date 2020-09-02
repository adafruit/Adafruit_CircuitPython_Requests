from unittest import mock
import mocket
import pytest
import adafruit_requests

ip = "1.2.3.4"
host = "wifitest.adafruit.com"
host2 = "wifitest2.adafruit.com"
path = "/testwifi/index.html"
text = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
response = b"HTTP/1.0 200 OK\r\nContent-Length: 70\r\n\r\n" + text

# def test_get_twice():
#     pool = mocket.MocketPool()
#     pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
#     sock = mocket.Mocket(response + response)
#     pool.socket.return_value = sock
#     ssl = mocket.SSLContext()

#     s = adafruit_requests.Session(pool, ssl)
#     r = s.get("https://" + host + path)

#     sock.send.assert_has_calls(
#         [
#             mock.call(b"GET /testwifi/index.html HTTP/1.1\r\n"),
#             mock.call(b"Host: wifitest.adafruit.com\r\n"),
#         ]
#     )
#     assert r.text == str(text, "utf-8")

#     r = s.get("https://" + host + path + "2")
#     sock.send.assert_has_calls(
#         [
#             mock.call(b"GET /testwifi/index.html2 HTTP/1.1\r\n"),
#             mock.call(b"Host: wifitest.adafruit.com\r\n"),
#         ]
#     )

#     assert r.text == str(text, "utf-8")
#     sock.connect.assert_called_once_with((host, 443))
#     pool.socket.assert_called_once()


def test_get_twice_after_second():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response + response)
    pool.socket.return_value = sock
    ssl = mocket.SSLContext()

    s = adafruit_requests.Session(pool, ssl)
    r = s.get("https://" + host + path)

    sock.send.assert_has_calls(
        [
            mock.call(b"GET /testwifi/index.html HTTP/1.1\r\n"),
            mock.call(b"Host: wifitest.adafruit.com\r\n"),
        ]
    )

    r2 = s.get("https://" + host + path + "2")
    sock.send.assert_has_calls(
        [
            mock.call(b"GET /testwifi/index.html2 HTTP/1.1\r\n"),
            mock.call(b"Host: wifitest.adafruit.com\r\n"),
        ]
    )
    sock.connect.assert_called_once_with((host, 443))
    pool.socket.assert_called_once()

    with pytest.raises(RuntimeError):
        r.text == str(text, "utf-8")


def test_connect_out_of_memory():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response)
    sock2 = mocket.Mocket(response)
    sock3 = mocket.Mocket(response)
    pool.socket.side_effect = [sock, sock2, sock3]
    sock2.connect.side_effect = MemoryError()
    ssl = mocket.SSLContext()

    s = adafruit_requests.Session(pool, ssl)
    r = s.get("https://" + host + path)

    sock.send.assert_has_calls(
        [
            mock.call(b"GET /testwifi/index.html HTTP/1.1\r\n"),
            mock.call(b"Host: wifitest.adafruit.com\r\n"),
        ]
    )
    assert r.text == str(text, "utf-8")

    r = s.get("https://" + host2 + path)
    sock3.send.assert_has_calls(
        [
            mock.call(b"GET /testwifi/index.html HTTP/1.1\r\n"),
            mock.call(b"Host: wifitest2.adafruit.com\r\n"),
        ]
    )

    assert r.text == str(text, "utf-8")
    sock.close.assert_called_once()
    sock.connect.assert_called_once_with((host, 443))
    sock3.connect.assert_called_once_with((host2, 443))
