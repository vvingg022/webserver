import mimetypes
import os
import socket
from pathlib import Path
from urllib.parse import unquote, urlsplit

from request import Request

HOST = "127.0.0.1"
PORT = 9000

# Refuse request bodies bigger than this (5 MiB).
MAX_BODY = 5 * 1024 * 1024

SERVER_ROOT = (Path(__file__).parent / "www").resolve()

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

PAYLOAD_TOO_LARGE_RESPONSE = b"""\
HTTP/1.1 413 Payload Too Large
Content-type: text/plain
Content-length: 17

Payload Too Large""".replace(b"\n", b"\r\n")

FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")


def serve_file(sock: socket.socket, path: str) -> None:
    """Send the file at `path` (relative to SERVER_ROOT) to the socket,
    or a 404 if it doesn't exist or lives outside SERVER_ROOT.
    """
    path = unquote(urlsplit(path).path)
    if path == "/":
        path = "/index.html"

    try:
        abspath = (SERVER_ROOT / path.lstrip("/")).resolve()
    except (ValueError, OSError):
        sock.sendall(NOT_FOUND_RESPONSE)
        return

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
                # Don't wait forever for a client that goes quiet.
                client_sock.settimeout(10)
                try:
                    request = Request.from_socket(client_sock)
                    print(request.method, request.path)

                    try:
                        content_length = max(int(request.headers.get("content-length", "0")), 0)
                    except ValueError:
                        content_length = 0

                    # Refuse oversized bodies BEFORE inviting the client to send them.
                    if content_length > MAX_BODY:
                        client_sock.sendall(PAYLOAD_TOO_LARGE_RESPONSE)
                        continue

                    if "100-continue" in request.headers.get("expect", "").lower():
                        print("Sending 100 Continue")
                        client_sock.sendall(b"HTTP/1.1 100 Continue\r\n\r\n")

                    if content_length:
                        body = request.body.read(content_length)
                        print(f"Request body: {len(body)} bytes, starts with {body[:60]!r}")

                    if request.method != "GET":
                        client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                        continue

                    serve_file(client_sock, request.path)
                except ValueError as e:
                    print(f"Failed to parse request: {e}")
                    client_sock.sendall(BAD_REQUEST_RESPONSE)
        except OSError as e:
            print(f"Connection problem: {e}")