import socket


def send(host: str, port: int, request: bytes) -> None:
    """Send raw bytes to a server and print whatever comes back."""
    with socket.create_connection((host, port)) as s:
        s.sendall(request)
        chunks = []
        while True:
            data = s.recv(4096)
            if not data:
                break
            chunks.append(data)
    print(b"".join(chunks).decode("utf-8", errors="replace"))


if __name__ == "__main__":
    # A GET request, typed out by hand.
    # Every line ends in \r\n, and a blank line ends the headers.
    get_request = (
        b"GET /hello HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"X-Made-Up: typed-by-hand\r\n"
        b"\r\n"
    )

    # A POST request with a body.
    body = b"name=John&surname=Doe"
    post_request = (
        b"POST /form HTTP/1.1\r\n"
        b"Host: 127.0.0.1\r\n"
        b"Content-Type: application/x-www-form-urlencoded\r\n"
        + f"Content-Length: {len(body)}\r\n".encode("ascii")
        + b"\r\n"
        + body
    )

    print("=== GET ===")
    send("127.0.0.1", 9000, get_request)

    print("=== POST ===")
    send("127.0.0.1", 9000, post_request)