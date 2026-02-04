import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import ssl

PORT = 8081

class ProxyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/land'):
            self.handle_land_query()
        else:
            super().do_GET()

    def handle_land_query(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        
        if 'lat' not in params or 'lng' not in params:
            self.send_error(400, "Missing lat/lng")
            return
            
        lat = params['lat'][0]
        lng = params['lng'][0]
        
        # 嘗試串接真實的內政部 NLSC API
        # Endpoint: https://api.nlsc.gov.tw/other/ParcelQuery/{lng}/{lat}
        # 這是公開的查詢介面，回傳 XML 或 JSON
        
        target_url = f"https://api.nlsc.gov.tw/other/ParcelQuery/{lng}/{lat}"
        
        try:
            # Create SSL context to ignore cert errors if any
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(
                target_url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            with urllib.request.urlopen(req, context=ctx, timeout=5) as response:
                data = response.read().decode('utf-8')
                
                # NLSC API returns XML or JSON. Let's assume JSON for easier parsing if possible,
                # but standard is XML. Let's try to parse it.
                # Example return: <parcelQuery><status>1</status><region>...</region>...</parcelQuery>
                
                # For simplicity in this demo, we will construct a response.
                # If the API works, we parse it. If it returns 403/404, we fallback.
                
                # Note: Real NLSC API often requires coordinate to be strictly within a land parcel.
                
                # 簡單解析 XML (不引用 heavy library)
                section = self.extract_tag(data, "sectName") or "未知段"
                lot_no = self.extract_tag(data, "parcelNo") or "查詢中"
                
                # 處理地號格式 (12340000 -> 1234-0000 -> 1234號)
                if len(lot_no) == 8:
                    main_no = int(lot_no[:4])
                    sub_no = int(lot_no[4:])
                    if sub_no == 0:
                        lot_display = f"{main_no}號"
                    else:
                        lot_display = f"{main_no}-{sub_no}號"
                else:
                    lot_display = lot_no

                # 回傳給前端
                response_data = {
                    "status": "success",
                    "lat": lat,
                    "lng": lng,
                    "note": "資料來源：內政部國土測繪中心 (NLSC)",
                    "section": section,
                    "lot": lot_display,
                    "raw_data": data[:200] # Debug info
                }

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
                
        except Exception as e:
            # Fallback if API fails
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def extract_tag(self, xml, tag):
        start = xml.find(f"<{tag}>")
        end = xml.find(f"</{tag}>")
        if start != -1 and end != -1:
            return xml[start + len(tag) + 2 : end]
        return None

Handler = ProxyHTTPRequestHandler

print(f"Serving on port {PORT} with REAL NLSC API Proxy...")
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()