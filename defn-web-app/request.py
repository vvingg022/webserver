import io
import socket
import typing

from headers import Headers


class BodyReader(io.IOBase):
    """A read-only file-like object for a request body.

    It reads from the socket only when you ask, so the server can
    decide how much of the body it wants.
    """

    def __init__(self, sock: socket.socket, *, buff: bytes = b"", bufsize: int = 16_384) -> None:
        self._sock = sock
        self._buff = buff
        self._bufsize = bufsize

    def readable(self) -> bool:
        return True

    def read(self, n: int) -> bytes:
        """Read up to n bytes from the request body."""
        while len(self._buff) < n:
            data = self._sock.recv(self._bufsize)
            if not data:
                break

            self._buff += data

        res, self._buff = self._buff[:n], self._buff[n:]
        return res


def iter_lines(sock: socket.socket, bufsize: int = 16_384) -> typing.Generator[bytes, None, bytes]:
    """Read from a socket and yield each CRLF-separated line.
    Stops at the first empty line (the end of the headers) and
    returns whatever extra data was already read after it.
    """
    buff = b""
    while True:
        data = sock.recv(bufsize)
        if not data:
            return b""

        buff += data
        while True:
            try:
                i = buff.index(b"\r\n")
                line, buff = buff[:i], buff[i + 2:]
                if not line:
                    return buff

                yield line
            except ValueError:
                break


class Request(typing.NamedTuple):
    method: str
    path: str
    headers: Headers
    body: BodyReader

    @classmethod
    def from_socket(cls, sock: socket.socket) -> "Request":
        """Read and parse the request from a socket object.

        Raises:
          ValueError: When the request cannot be parsed.
        """
        lines = iter_lines(sock)

        try:
            request_line = next(lines).decode("ascii")
        except StopIteration:
            raise ValueError("Request line missing.")

        try:
            method, path, _ = request_line.split(" ")
        except ValueError:
            raise ValueError(f"Malformed request line {request_line!r}.")

        headers = Headers()
        buff = b""
        while True:
            try:
                line = next(lines)
            except StopIteration as e:
                # A generator's return value is stored in StopIteration.value.
                # Here it's any body bytes that were read along with the headers.
                buff = e.value
                break

            name, sep, value = line.decode("ascii").partition(":")
            if not sep:
                raise ValueError(f"Malformed header line {line!r}.")

            headers.add(name, value.lstrip())

        body = BodyReader(sock, buff=buff)
        return cls(method=method.upper(), path=path, headers=headers, body=body)