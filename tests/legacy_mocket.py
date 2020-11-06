from unittest import mock

SOCK_STREAM = 0

set_interface = mock.Mock()
interface = mock.MagicMock()
getaddrinfo = mock.Mock()
socket = mock.Mock()


class Mocket:
    def __init__(self, response):
        self.settimeout = mock.Mock()
        self.close = mock.Mock()
        self.connect = mock.Mock()
        self.send = mock.Mock(side_effect=self._send)
        self.readline = mock.Mock(side_effect=self._readline)
        self.recv = mock.Mock(side_effect=self._recv)
        self.fail_next_send = False
        self._response = response
        self._position = 0

    def _send(self, data):
        if self.fail_next_send:
            self.fail_next_send = False
            raise RuntimeError("Send failed")
        return None

    def _readline(self):
        i = self._response.find(b"\r\n", self._position)
        r = self._response[self._position : i + 2]
        self._position = i + 2
        return r

    def _recv(self, count):
        end = self._position + count
        r = self._response[self._position : end]
        self._position = end
        print(r)
        return r
