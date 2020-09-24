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
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    r = s.post("http://" + host + "/post")
    sock.connect.assert_called_once_with((ip, 80))

    sock.send.assert_has_calls(
        [
            mock.call(b"POST"),
            mock.call(b" /"),
            mock.call(b"post"),
            mock.call(b" HTTP/1.1\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [mock.call(b"Host: "), mock.call(b"httpbin.org"),]
    )


def test_string():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    data = "31F"
    r = s.post("http://" + host + "/post", data=data)
    sock.connect.assert_called_once_with((ip, 80))
    sock.send.assert_called_with(b"31F")


def test_form():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    data = {"Date": "July 25, 2019"}
    r = s.post("http://" + host + "/post", data=data)
    sock.connect.assert_called_once_with((ip, 80))
    sock.send.assert_called_with(b"Date=July 25, 2019")


def test_json():
    pool = mocket.MocketPool()
    pool.getaddrinfo.return_value = ((None, None, None, None, (ip, 80)),)
    sock = mocket.Mocket(headers + encoded)
    pool.socket.return_value = sock

    s = adafruit_requests.Session(pool)
    json_data = {"Date": "July 25, 2019"}
    r = s.post("http://" + host + "/post", json=json_data)
    sock.connect.assert_called_once_with((ip, 80))
    sock.send.assert_called_with(b'{"Date": "July 25, 2019"}')
