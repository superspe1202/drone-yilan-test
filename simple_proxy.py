#!/usr/bin/env python3
"""
簡單的 HTTP 代理伺服器 - 攔截 591 API 請求
"""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# 儲存攔截到的請求
captured_requests = []

class ProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request("GET")
    
    def do_POST(self):
        self.handle_request("POST")
    
    def handle_request(self, method):
        url = self.path
        parsed = urlparse(url)
        
        # 只記錄 591 相關的請求
        if "591" in url or "bff" in url:
            req_info = {
                "method": method,
                "url": url,
                "path": parsed.path,
            }
            
            # 記錄
            captured_requests.append(req_info)
            print(f"📥 {method} {url[:100]}")
        
        # 轉發請求（這裡只是範例，需要正確的轉發邏輯）
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{}')
    
    def log_message(self, format, *args):
        pass  # 抑制日誌輸出

def run_proxy(port=8888):
    server = HTTPServer(('127.0.0.1', port), ProxyHandler)
    print(f"🌐 代理伺服器啟動: http://127.0.0.1:{port}")
    print("請將瀏覽器代理設定為此地址")
    print("按 Ctrl+C 停止並顯示結果\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n📊 攔截到的請求:")
        for i, req in enumerate(captured_requests):
            print(f"{i+1}. {req['method']} {req['path']}")
        
        # 儲存
        with open("/Users/superspe/.openclaw/workspace/591_proxied.json", "w") as f:
            json.dump(captured_requests, f, indent=2)
        
        print(f"\n✅ 已儲存至 591_proxied.json")
        
        server.shutdown()

if __name__ == "__main__":
    run_proxy()
