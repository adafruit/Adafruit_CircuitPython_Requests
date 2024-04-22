# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: Unlicense

""" Post Tests """
# pylint: disable=line-too-long

from unittest import mock

import mocket
import pytest

"""
For building tests, you can use CPython requests with logging to see what should actuall get sent.

import logging
import http.client
import requests

def httpclient_logging_patch(level=logging.DEBUG):
    logging.basicConfig(level=level)

    httpclient_logger = logging.getLogger("http.client")

    def httpclient_log(*args):
        httpclient_logger.log(level, " ".join(args))

    http.client.print = httpclient_log
    http.client.HTTPConnection.debuglevel = 1

httpclient_logging_patch()

URL = "https://httpbin.org/post"

with open("tests/files/red_green.png", "rb") as file_1:
    file_data = {
        "file_1": (
            "red_green.png",
            file_1,
            "image/png",
            {
                "Key_1": "Value 1",
                "Key_2": "Value 2",
                "Key_3": "Value 3",
            },
        ),
    }

    print(requests.post(URL, files=file_data).json())
"""


def test_post_files_text(sock, requests):
    file_data = {
        "key_4": (None, "Value 5"),
    }

    requests._build_boundary_string = mock.Mock(
        return_value="8cd45159712eeb914c049c717d3f4d75"
    )
    requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(
                b"multipart/form-data; boundary=8cd45159712eeb914c049c717d3f4d75"
            ),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(
                b'--8cd45159712eeb914c049c717d3f4d75\r\nContent-Disposition: form-data; name="key_4"\r\n\r\n'
            ),
            mock.call(b"Value 5\r\n"),
            mock.call(b"--8cd45159712eeb914c049c717d3f4d75--\r\n"),
        ]
    )


def test_post_files_file(sock, requests):
    with open("tests/files/red_green.png", "rb") as file_1:
        file_data = {
            "file_1": (
                "red_green.png",
                file_1,
                "image/png",
                {
                    "Key_1": "Value 1",
                    "Key_2": "Value 2",
                    "Key_3": "Value 3",
                },
            ),
        }

        requests._build_boundary_string = mock.Mock(
            return_value="e663061c5bfcc53139c8f68d016cbef3"
        )
        requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(
                b"multipart/form-data; boundary=e663061c5bfcc53139c8f68d016cbef3"
            ),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(
                b'--e663061c5bfcc53139c8f68d016cbef3\r\nContent-Disposition: form-data; name="file_1"; filename="red_green.png"\r\nContent-Type: image/png\r\nKey_1: Value 1\r\nKey_2: Value 2\r\nKey_3: Value 3\r\n\r\n'
            ),
            mock.call(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00\xfd\xd4\x9a"
            ),
            mock.call(
                b"s\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00"
            ),
            mock.call(
                b"\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x10IDAT\x18Wc\xf8\xcf"
            ),
            mock.call(
                b"\xc0\x00\xc5\xff\x19\x18\x00\x1d\xf0\x03\xfd\x8fk\x13|\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            mock.call(b"\r\n"),
            mock.call(b"--e663061c5bfcc53139c8f68d016cbef3--\r\n"),
        ]
    )


def test_post_files_complex(sock, requests):
    with open("tests/files/red_green.png", "rb") as file_1, open(
        "tests/files/green_red.png", "rb"
    ) as file_2:
        file_data = {
            "file_1": (
                "red_green.png",
                file_1,
                "image/png",
                {
                    "Key_1": "Value 1",
                    "Key_2": "Value 2",
                    "Key_3": "Value 3",
                },
            ),
            "key_4": (None, "Value 5"),
            "file_2": (
                "green_red.png",
                file_2,
                "image/png",
            ),
            "key_6": (None, "Value 6"),
        }

        requests._build_boundary_string = mock.Mock(
            return_value="e663061c5bfcc53139c8f68d016cbef3"
        )
        requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)

    sock.connect.assert_called_once_with((mocket.MOCK_POOL_IP, 80))
    sock.send.assert_has_calls(
        [
            mock.call(b"Content-Type"),
            mock.call(b": "),
            mock.call(
                b"multipart/form-data; boundary=e663061c5bfcc53139c8f68d016cbef3"
            ),
            mock.call(b"\r\n"),
        ]
    )
    sock.send.assert_has_calls(
        [
            mock.call(
                b'--e663061c5bfcc53139c8f68d016cbef3\r\nContent-Disposition: form-data; name="file_1"; filename="red_green.png"\r\nContent-Type: image/png\r\nKey_1: Value 1\r\nKey_2: Value 2\r\nKey_3: Value 3\r\n\r\n'
            ),
            mock.call(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00\xfd\xd4\x9a"
            ),
            mock.call(
                b"s\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00"
            ),
            mock.call(
                b"\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x10IDAT\x18Wc\xf8\xcf"
            ),
            mock.call(
                b"\xc0\x00\xc5\xff\x19\x18\x00\x1d\xf0\x03\xfd\x8fk\x13|\x00\x00\x00\x00IEND\xaeB`\x82"
            ),
            mock.call(b"\r\n"),
            mock.call(
                b'--e663061c5bfcc53139c8f68d016cbef3\r\nContent-Disposition: form-data; name="key_4"\r\n\r\n'
            ),
            mock.call(b"Value 5\r\n"),
            mock.call(
                b'--e663061c5bfcc53139c8f68d016cbef3\r\nContent-Disposition: form-data; name="file_2"; filename="green_red.png"\r\nContent-Type: image/png\r\n\r\n'
            ),
            mock.call(
                b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x02\x00\x00\x00\x02\x08\x02\x00\x00\x00\xfd\xd4\x9a"
            ),
            mock.call(
                b"s\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00\x00"
            ),
            mock.call(
                b"\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x12IDAT\x18Wc`\xf8"
            ),
            mock.call(
                b'\x0f\x84 \x92\x81\xe1?\x03\x00\x1d\xf0\x03\xfd\x88"uS\x00\x00\x00\x00IEND\xaeB`\x82'
            ),
            mock.call(b"\r\n"),
            mock.call(
                b'--e663061c5bfcc53139c8f68d016cbef3\r\nContent-Disposition: form-data; name="key_6"\r\n\r\n'
            ),
            mock.call(b"Value 6\r\n"),
            mock.call(b"--e663061c5bfcc53139c8f68d016cbef3--\r\n"),
        ]
    )


def test_post_files_not_binary(requests):
    with open("tests/files/red_green.png", "r") as file_1:
        file_data = {
            "file_1": (
                "red_green.png",
                file_1,
                "image/png",
            ),
        }

        with pytest.raises(AttributeError) as context:
            requests.post("http://" + mocket.MOCK_HOST_1 + "/post", files=file_data)
        assert "Files must be opened in binary mode" in str(context)
