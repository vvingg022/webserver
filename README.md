# Web Server Learning Project

Two small web servers built from scratch in Python to understand how the web works underneath frameworks like Flask. Built on Windows with Python 3.

For a quick recap of the ideas, see [NOTES.md](NOTES.md).

## What's inside

```
webserver/
├── aosa-web-server/     # Project 1: a file-serving web server
├── spivak-web-server/   # Project 2: sockets, WSGI, concurrency, Flask
├── NOTES.md             # Cheat sheet of key ideas
└── README.md
```

## Project 1: `aosa-web-server/`

Based on the chapter [A Simple Web Server](https://aosabook.org/en/500L/a-simple-web-server.html) from *500 Lines or Less*. It uses Python's built-in `http.server` library.

**What it does**
- Serves static files from the folder it runs in
- Returns a proper 404 error page for missing files
- Serves `index.html` for folders, or a file listing if there isn't one
- Runs `.py` files and returns their output (CGI)

**Design:** every kind of request is handled by a small "case handler" class with `test()` and `act()` methods. Adding a feature means adding one class to a list.

**Run it**
```
cd aosa-web-server
python server.py
```
Then open http://localhost:8000/hello.html

> Warning: this server runs any `.py` file it is asked for. Use it on your own machine only, never on the public internet.

**Changes from the original chapter:** ported from Python 2 to Python 3 (`http.server`, `subprocess` instead of `os.popen2`, bytes encoding).

## Project 2: `spivak-web-server/`

Based on Ruslan Spivak's series [Let's Build A Web Server](https://ruslanspivak.com/lsbaws-part1/). It uses raw sockets with no helper library.

| File | What it shows |
|---|---|
| `webserver1.py` | Part 1: a bare socket server that always replies "Hello, World!" |
| `webserver2.py` | Part 2: a WSGI server that can run any WSGI app |
| `wsgiapp.py` | A tiny hand-written WSGI app with simple routing |
| `flaskapp.py` | A Flask app running on the custom server, with no server changes |
| `webserver3b.py` | Part 3: an iterative server that shows requests waiting in line |
| `webserver3c_threads.py` | Part 3: a threaded server that handles requests concurrently |

**Run the WSGI server with the tiny app**
```
cd spivak-web-server
python webserver2.py wsgiapp:app
```
Then open http://localhost:8888/hello

**Run it with Flask**
```
pip install flask
python webserver2.py flaskapp:app
```

**Changes from the original series:** Part 3 uses `fork()`, which only exists on Linux and macOS. On Windows this project uses threads instead.

## Requirements
- Python 3.8 or newer
- Flask (only for `flaskapp.py`)

## What I learned
- How a request and response look as plain text over HTTP
- How a socket server listens, accepts, reads, replies, and closes
- How the case-handler pattern keeps a server easy to extend
- What CGI does, and why running arbitrary scripts is risky
- What WSGI is, and why one server can run Flask, Django, or a hand-written app
- Why iterative servers make visitors wait, and how threads fix it
- Git basics: add, commit, push, and `.gitignore`

## Credits
- "A Simple Web Server", from *500 Lines or Less* (aosabook.org)
- Ruslan Spivak, *Let's Build A Web Server*
