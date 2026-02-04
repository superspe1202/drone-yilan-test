from http.server import BaseHTTPRequestHandler
from urllib import parse, request
import ssl

# Vercel Python Runtime
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Disable SSL verification
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        try:
            # Parse params: /api/proxy?z=..&x=..&y=..
            query = parse.urlparse(self.path).query
            params = parse.parse_qs(query)
            
            z = params.get('z', [''])[0]
            x = params.get('x', [''])[0]
            y = params.get('y', [''])[0]
            
            if not (z and x and y):
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing params")
                return

            target_url = f"https://maptiles.591.com.tw/S_Maps/wmts/DMAPS/default/GoogleMapsCompatible/{z}/{y}/{x}"
            
            headers = {
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://land.591.com.tw/"
            }
            
            req = request.Request(target_url, headers=headers)
            with request.urlopen(req, context=ctx, timeout=5) as response:
                self.send_response(200)
                self.send_header('Content-type', 'image/png')
                self.send_header('Cache-Control', 'public, max-age=86400')
                self.end_headers()
                self.wfile.write(response.read())
                
        except Exception as e:
            self.send_response(404)
            self.end_headers()