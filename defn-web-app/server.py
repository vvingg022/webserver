import mimetypes
import os
import socket
import typing
from pathlib import Path
from urllib.parse import unquote, urlsplit

HOST = "127.0.0.1"
PORT = 9000

# Serve files from the "www" folder next to this script,
# no matter which folder you start the server from.
SERVER_ROOT = (Path(__file__).parent / "www").resolve()

# Windows can have wrong file types in its registry, so set the important ones.
mimetypes.add_type("text/css", ".css")
mimetypes.add_type("text/javascript", ".js")

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

FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")


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


def serve_file(sock: socket.socket, path: str) -> None:
    """Send the file at `path` (relative to SERVER_ROOT) to the socket,
    or a 404 if it doesn't exist or lives outside SERVER_ROOT.
    """
    # Drop any ?query part and decode %20-style escapes.
    path = unquote(urlsplit(path).path)
    if path == "/":
        path = "/index.html"

    try:
        abspath = (SERVER_ROOT / path.lstrip("/")).resolve()
    except (ValueError, OSError):
        sock.sendall(NOT_FOUND_RESPONSE)
        return

    # Refuse anything outside www, and anything that isn't a plain file.
    if not abspath.is_relative_to(SERVER_ROOT) or not abspath.is_file():
        sock.sendall(NOT_FOUND_RESPONSE)
        return

    content_type, _ = mimetypes.guess_type(str(abspath))
    if content_type is None:
        content_type = "application/octet-stream"
    if content_type.startswith("text/"):
        content_type += "; charset=utf-8"

    try:
        with abspath.open("rb") as f:
            size = os.fstat(f.fileno()).st_size
            headers = FILE_RESPONSE_TEMPLATE.format(
                content_type=content_type,
                content_length=size,
            ).encode("ascii")

            sock.sendall(headers)
            sock.sendfile(f)
    except FileNotFoundError:
        sock.sendall(NOT_FOUND_RESPONSE)


with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")
    print(f"Serving files from {SERVER_ROOT}")

    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"Received connection from {client_addr}...")
        try:
            with client_sock:
                try:
                    request = Request.from_socket(client_sock)
                    print(request.method, request.path)

                    if request.method != "GET":
                        client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    else:
                        serve_file(client_sock, request.path)
                except ValueError as e:
                    print(f"Failed to parse request: {e}")
                    client_sock.sendall(BAD_REQUEST_RESPONSE)
        except OSError as e:
            print(f"Connection problem: {e}")