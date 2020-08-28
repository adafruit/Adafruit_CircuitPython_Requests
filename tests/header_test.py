from unittest import mock
import mocket
import json
import adafruit_requests

ip = "1.2.3.4"
host = "httpbin.org"
response_headers = b"HTTP/1.0 200 OK\r\nContent-Length: 0\r\n\r\n"


def test_json():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(response_headers)
    mocket.socket.return_value = sock
    sent = []
    sock.send.side_effect = sent.append

    adafruit_requests.set_socket(mocket, mocket.interface)
    headers = {"user-agent": "blinka/1.0.0"}
    r = adafruit_requests.get("http://" + host + "/get", headers=headers)

    sock.connect.assert_called_once_with((ip, 80), mocket.interface.TCP_MODE)
    sent = b"".join(sent).lower()
    assert b"user-agent: blinka/1.0.0\r\n" in sent
    # The current implementation sends two user agents. Fix it, and uncomment below.
    # assert sent.count(b"user-agent:") == 1
