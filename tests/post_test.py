from unittest import mock
import mocket
import json
import adafruit_requests

ip = "1.2.3.4"
host = "httpbin.org"
response = {}
encoded = json.dumps(response).encode("utf-8")
headers = "HTTP/1.0 200 OK\r\nContent-Length: {}\r\n\r\n".format(len(encoded)).encode(
    "utf-8"
)


def test_method():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    r = adafruit_requests.post("http://" + host + "/post")
    sock.connect.assert_called_once_with((ip, 80), mocket.interface.TCP_MODE)
    sock.send.assert_has_calls(
        [mock.call(b"POST /post HTTP/1.0\r\n"), mock.call(b"Host: httpbin.org\r\n")]
    )


def test_string():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    data = "31F"
    r = adafruit_requests.post("http://" + host + "/post", data=data)
    sock.connect.assert_called_once_with((ip, 80), mocket.interface.TCP_MODE)
    sock.send.assert_called_with(b"31F")


def test_json():
    mocket.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    mocket.socket.return_value = sock

    adafruit_requests.set_socket(mocket, mocket.interface)
    json_data = {"Date": "July 25, 2019"}
    r = adafruit_requests.post("http://" + host + "/post", json=json_data)
    sock.connect.assert_called_once_with((ip, 80), mocket.interface.TCP_MODE)
    sock.send.assert_called_with(b'{"Date": "July 25, 2019"}')
