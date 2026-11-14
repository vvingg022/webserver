import socket
import typing

HOST = "127.0.0.1"
PORT = 9000

RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
Content-type: text/plain
Content-length: 11

Bad Request""".replace(b"\n", b"\r\n")

NOT_FOUND_RESPONSE = b"""\
HTTP/1.1 404 Not Found
Content-type: text/plain
Content-length: 9

Not Found""".replace(b"\n", b"\r\n")

METHOD_NOT_ALLOWED_RESPONSE = b"""\
HTTP/1.1 405 Method Not Allowed
Allow: GET
Content-type: text/plain
Content-length: 18

Method Not Allowed""".replace(b"\n", b"\r\n")


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
    headers: typing.Mapping[str, str]

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

        headers = {}
        for line in lines:
            name, sep, value = line.decode("ascii").partition(":")
            if not sep:
                raise ValueError(f"Malformed header line {line!r}.")

            headers[name.lower()] = value.lstrip()

        return cls(method=method.upper(), path=path, headers=headers)


with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"Received connection from {client_addr}...")
        try:
            with client_sock:
                try:
                    request = Request.from_socket(client_sock)
                    print(request)

                    if request.method != "GET":
                        client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    elif request.path == "/":
                        client_sock.sendall(RESPONSE)   # temporary, removed in Step 5
                    else:
                        client_sock.sendall(NOT_FOUND_RESPONSE)
                except ValueError as e:
                    print(f"Failed to parse request: {e}")
                    client_sock.sendall(BAD_REQUEST_RESPONSE)
        except OSError as e:
            print(f"Connection problem: {e}")