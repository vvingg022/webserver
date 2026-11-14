import socket
import typing

from headers import Headers


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
        for line in lines:
            name, sep, value = line.decode("ascii").partition(":")
            if not sep:
                raise ValueError(f"Malformed header line {line!r}.")

            headers.add(name, value.lstrip())

        return cls(method=method.upper(), path=path, headers=headers)