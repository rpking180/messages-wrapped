import http.server, ssl, socketserver, os

PORT = 8443
os.chdir(os.path.dirname(__file__))  # serve current folder

handler = http.server.SimpleHTTPRequestHandler

# Use SSLContext API (works on Python 3.7+ and recommended for 3.12+)
context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
context.load_cert_chain(certfile="cert.pem", keyfile="key.pem")

with socketserver.TCPServer(("0.0.0.0", PORT), handler) as httpd:
    httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
    print(f"Serving HTTPS on https://localhost:{PORT}")
    httpd.serve_forever()