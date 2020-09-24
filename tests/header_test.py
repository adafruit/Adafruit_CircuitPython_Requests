from unittest import mock
import mocket
import json
import adafruit_requests

ip = "1.2.3.4"
host = "httpbin.org"
response_headers = b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n"


def test_json():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response_headers)
    pool.socket.return_value = sock
    sent = []

    def _send(data):
        sent.append(data)
        return len(data)

    sock.send.side_effect = _send

    s = adafruit_requests.Session(pool)
    headers = {"user-agent": "blinka/1.0.0"}
    r = s.get("http://" + host + "/get", headers=headers)

    sock.connect.assert_called_once_with((ip, 80))
    sent = b"".join(sent).lower()
    assert b"user-agent: blinka/1.0.0\r\n" in sent
    # The current implementation sends two user agents. Fix it, and uncomment below.
    # assert sent.count(b"user-agent:") == 1
