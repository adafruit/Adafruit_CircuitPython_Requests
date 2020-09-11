from unittest import mock
import mocket
import json
import adafruit_requests

ip = "1.2.3.4"
host = "httpbin.org"
response = {"Date": "July 25, 2019"}
encoded = json.dumps(response).encode("utf-8")
# Padding here tests the case where a header line is exactly 32 bytes buffered by
# aligning the Content-Type header after it.
headers = "HTTP/1.0 200 OK\r\npadding: 000\r\nContent-Type: application/json\r\nContent-Length: {}\r\n\r\n".format(
    len(encoded)
).encode(
    "utf-8"
)


def test_json():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    r = s.get("http://" + host + "/get")
    sock.connect.assert_called_once_with((ip, 80))
    assert r.json() == response
