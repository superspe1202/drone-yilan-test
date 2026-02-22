#!/usr/bin/env python3
"""
591 土地 - 持續監聽 API
"""

import asyncio
import json
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/591_apis.json"
api_log = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 攔截
        page.on("response", lambda resp: asyncio.create_task(handle_response(resp)))
        
        async def handle_response(response):
            url = response.url
            if "bff" in url and "land" in url:
                try:
                    data = await response.json()
                    if data.get("data"):
                        info = {"url": url, "data": data["data"]}
                        api_log.append(info)
                        print(f"✅ {url[40:80]}... -> {list(data['data'].keys())[:3]}")
                except:
                    pass
        
        url = "https://land.591.com.tw/map?region_id=21&mode=tenor"
        
        print(f"\n🌐 前往 591...")
        await page.goto(url)
        await page.wait_for_timeout(3000)
        
        print("\n" + "="*50)
        print("請手动选择：武淵二段")
        print("然後點擊土地項目")
        print("我會持續監聽 3 分鐘")
        print("="*50)
        
        # 監聽 3 分鐘
        for i in range(180):
            await asyncio.sleep(1)
            if i % 30 == 0 and i > 0:
                print(f"⏰ {i}秒過去了, 收到 {len(api_log)} 個 API")
        
        # 儲存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(api_log, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存 {len(api_log)} 個 API -> {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
