from http.server import BaseHTTPRequestHandler, HTTPServer

class RequestHandler(BaseHTTPRequestHandler):
    Page = '''\
<html>
<body>
<table>
<tr><td>Date and time</td><td>{date_time}</td></tr>
<tr><td>Client host</td><td>{client_host}</td></tr>
<tr><td>Client port</td><td>{client_port}</td></tr>
<tr><td>Command</td><td>{command}</td></tr>
<tr><td>Path</td><td>{path}</td></tr>
</table>
</body>
</html>
'''

    def do_GET(self):
        page = self.create_page()
        self.send_page(page)

    def create_page(self):
        values = {
            'date_time':   self.date_time_string(),
            'client_host': self.client_address[0],
            'client_port': self.client_address[1],
            'command':     self.command,
            'path':        self.path,
        }
        return self.Page.format(**values)

    def send_page(self, page):
        body = page.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

if __name__ == '__main__':
    server = HTTPServer(('', 8000), RequestHandler)
    server.serve_forever()