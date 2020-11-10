from unittest import mock
import mocket
import adafruit_requests

ip = "1.2.3.4"
host = "wifitest.adafruit.com"
path = "/testwifi/index.html"
text = b"This is a test of Adafruit WiFi!\r\nIf you can read this, its working :)"
headers = b"HTTP/1.0 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n"


def _chunk(response, split, extra=b""):
    i = 0
    chunked = b""
    while i < len(response):
        remaining = len(response) - i
        chunk_size = split
        if remaining < chunk_size:
            chunk_size = remaining
        new_i = i + chunk_size
        chunked += (
            hex(chunk_size)[2:].encode("ascii")
            + extra
            + b"\r\n"
            + response[i:new_i]
            + b"\r\n"
        )
        i = new_i
    # The final chunk is zero length.
    chunked += b"0\r\n\r\n"
    return chunked


def do_test_get_text(extra=b""):
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    c = _chunk(text, 33, extra)
    print(c)
    sock = mocket.Mocket(headers + c)
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


def test_get_text():
    do_test_get_text()


def test_get_text_extra():
    do_test_get_text(b";blahblah; blah")


def do_test_close_flush(extra=b""):
    """Test that a chunked response can be closed even when the request contents were not accessed."""
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    c = _chunk(text, 33, extra)
    print(c)
    sock = mocket.Mocket(headers + c)
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


def test_close_flush():
    do_test_close_flush()


def test_close_flush_extra():
    do_test_close_flush(b";blahblah; blah")
