import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import ssl

PORT = 8081

# Disable SSL verification for Proxy
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/proxy/591'):
            self.handle_591_proxy()
        elif self.path.startswith('/api/land'):
            self.handle_land_query()
        else:
            super().do_GET()

    def handle_591_proxy(self):
        # Format: /proxy/591/{z}/{y}/{x}
        try:
            parts = self.path.split('/')
            z, y, x = parts[-3], parts[-2], parts[-1]
            
            # 591 Tile URL
            target_url = f"https://maptiles.591.com.tw/S_Maps/wmts/DMAPS/default/GoogleMapsCompatible/{z}/{y}/{x}"
            
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://land.591.com.tw/"
            }
            
            req = urllib.request.Request(target_url, headers=headers)
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                if response.status == 200:
                    content = response.read()
                    self.send_response(200)
                    self.send_header('Content-type', 'image/png')
                    self.end_headers()
                    self.wfile.write(content)
                else:
                    self.send_error(response.status)
        except Exception as e:
            # print(f"Proxy Error: {e}")
            self.send_error(404)

    def handle_land_query(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'lat' not in params or 'lng' not in params:
            self.send_error(400, "Missing lat/lng")
            return
            
        lat = params['lat'][0]
        lng = params['lng'][0]
        
        # Mock Response (Since real API is blocked)
        response_data = {
            "status": "success",
            "lat": lat,
            "lng": lng,
            "note": "請搭配紅線圖層使用",
            "section": "查詢中...",
            "lot": "請參考地圖"
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

Handler = ProxyHTTPRequestHandler

print(f"Serving on port {PORT} with 591 Proxy...")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()