#!/usr/bin/env python3
"""
591 - 完整攔截請求和回應 v2
"""

import asyncio
import json
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/591_full_capture2.json"
captured = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 使用 route 來攔截並修改請求
        async def handle_route(route):
            request = route.request
            
            if "bff-business" in request.url and "land" in request.url:
                print(f"📤 {request.method} {request.url[:60]}")
                
                # 取得 headers
                headers = dict(request.headers)
                post_data = request.post_data
                
                print(f"   Headers: {list(headers.keys())[:5]}")
                print(f"   Post data: {post_data}")
                
                # 繼續請求
                response = await route.continue_()
                
                # 取得回應
                try:
                    body = await response.text()
                    if body:
                        try:
                            data = json.loads(body)
                            captured.append({
                                "url": request.url,
                                "method": request.method,
                                "headers": headers,
                                "post_data": post_data.decode() if post_data else None,
                                "response": data
                            })
                            print(f"   ✅ Response keys: {list(data.get('data', {}).keys())[:3]}")
                        except:
                            pass
                except:
                    pass
            else:
                await route.continue_()
        
        await page.route("**/*", handle_route)
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await asyncio.sleep(3)
        
        print("\n" + "="*50)
        print("請選擇武淵二段，點擊土地")
        print("="*50)
        
        for i in range(120):
            await asyncio.sleep(1)
            if i % 20 == 0:
                print(f"⏰ {i}秒, 捕獲 {len(captured)} 個")
        
        print(f"\n💾 儲存...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(captured, f, ensure_ascii=False, indent=2)
        
        print(f"✅ -> {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
