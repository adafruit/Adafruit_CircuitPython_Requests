from unittest import mock
import mocket
import json
import adafruit_requests

ip = "1.2.3.4"
host = "httpbin.org"
response = {"Date": "July 25, 2019"}
encoded = json.dumps(response).encode("utf-8")
headers = "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n".format(len(encoded)).encode(
    "utf-8"
)


def test_json():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.get("http://" + host + "/get")
    sock.connect.assert_called_once_with((ip, 80), mocket.interface.TCP_MODE)
    assert r.json() == response
