# Cheat Sheet

## The big idea
A web server waits for a request and sends back a response.

```
wait -> receive request -> work out what it wants -> build response -> send -> repeat
```

## Key terms
| Term | Meaning |
|---|---|
| HTTP | The text format browsers and servers use to talk |
| Request | The browser's message: method + path (`GET /hello`) |
| Response | Status code + headers + body |
| Status code | 200 = OK, 404 = not found, 500 = server error |
| Port | A numbered door on your computer (8000, 8888) |
| Socket | One end of a network connection |
| localhost | "This computer" |
| Static | A file sent as-is |
| Dynamic | A response built by code on each request |

## Project 1: AOSA server (`aosa-web-server/`)
| Step | Built | Core idea |
|---|---|---|
| 1 | Fixed "Hello, web!" page | `do_GET` runs on each GET request |
| 2 | Page showing request info | Fill a template with `.format()` |
| 3 | Serve real files + 404 | URL path maps to a file on disk |
| 4 | Folder listings + `index.html` | Case handlers: `test()` and `act()` |
| 5 | Run `.py` files (CGI) | Run a script, send back its output |
| 6 | Refactor with `base_case` | Shared helpers live in a parent class |

- **CGI:** a standard way for a server to run another program and return its output.
- **Case-handler pattern:** each rule is its own class. To add a feature, write one class and add it to the `Cases` list.
- **Safety:** this server runs any `.py` file asked for, so never expose it publicly.

## Project 2: Spivak servers (`spivak-web-server/`)

### Part 1: raw sockets
```
listen -> accept -> recv (read request) -> sendall (reply) -> close
```
A request and a response are just plain text.

### Part 2: WSGI
WSGI is a standard agreement between servers and Python apps.

```python
def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [b'Hello']
```
- `environ`: a dictionary describing the request
- `start_response`: how the app reports status and headers
- Return value: the response body

### Flask bonus
```python
app = flask_app.wsgi_app
```
Flask exposes a WSGI function, so `python webserver2.py flaskapp:app` runs it on the same unchanged server. Any WSGI server can run any WSGI app.

### Part 3: concurrency
| Idea | In simple words |
|---|---|
| Iterative server | Serves one client at a time; the others wait |
| Concurrent server | Serves several clients at once |
| Thread | A worker inside one process |
| Process | A running program |
| PID / PPID | A process's ID and its parent's ID |
| File descriptor | The number the OS uses to track an open file or socket |
| Backlog | The waiting-room queue for connections (`listen(5)`) |
| Ephemeral port | A short-lived port the OS gives a client |
| `fork()` | Linux/macOS call that clones a process; returns 0 in the child |
| Zombie | A finished child process the parent never waited on |
| SIGCHLD | Signal sent to a parent when a child exits |

- **Fix used here:** the main loop hands each visitor to a new thread, then goes straight back to `accept()`.
- **Why threads:** `fork()` doesn't exist on Windows, and threads avoid duplicate sockets and zombies.
- **fork lessons:** close duplicate descriptors, and reap children with `waitpid` in a `SIGCHLD` handler.

## Git commands
```
git add .                 # stage the changes
git commit -m "message"   # save a snapshot locally
git push                  # upload to GitHub
git status                # see what changed
```
- **Commit** saves on your computer only. **Push** uploads it to GitHub.
- **`.gitignore`** lists things Git should skip (`__pycache__/`, `venv/`).

## Commands for running things (Windows)
| Task | Command |
|---|---|
| Run AOSA server | `cd aosa-web-server` then `python server.py` |
| Run WSGI server | `cd spivak-web-server` then `python webserver2.py wsgiapp:app` |
| Run with Flask | `python webserver2.py flaskapp:app` |
| Test with curl | `curl.exe -v http://localhost:8888/hello` |
| Stop a server | Ctrl+C, or the trash-can icon in the terminal panel |

## Problems hit along the way
| Symptom | Cause and fix |
|---|---|
| `WinError 10013` | Windows blocked the port, so use another one |
| "Site can't be reached" | The server isn't running, so start it first |
| Old behavior after editing | The file wasn't saved, or an old server was still running |
| `No module named 'flask'` | The venv isn't active; look for `(venv)` in the prompt |
| "No such file" for `webserver2.py` | Wrong folder; `cd` into `spivak-web-server` |

## Ideas for next time
- Serve CSS and images with correct file types (`mimetypes`)
- Pass URL parameters to CGI scripts
- Block `../` paths so visitors can't escape the folder
- Make `webserver2.py` concurrent with threads
- Build a small Flask app, then learn POST, cookies, and Nginx/Gunicorn
