from http.server import HTTPServer, SimpleHTTPRequestHandler, BaseHTTPRequestHandler
import ssl
import websockets
import asyncio

async def handler(websocket, path):
    
        data = await websocket.recv()
    
        reply = f"Data recieved as:  {data}!"
    
        await websocket.send(reply)


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):


 

    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b'Hello, world!')

    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        self.send_response(200)
        self.end_headers()
        response = BytesIO()
        response.write(b'This is POST request. ')
        response.write(b'Received: ')
        response.write(body)
        self.wfile.write(response.getvalue())



httpd = HTTPServer(("127.0.0.1", 8080), handler)
httpd.socket = ssl.wrap_socket(httpd.socket, keyfile="./key.pem", certfile="./cert.pem", server_side=True)
httpd.serve_forever()

