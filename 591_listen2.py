#!/usr/bin/env python3
"""
591 土地 - 修正版持續監聽
"""

import asyncio
import json
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/591_apis.json"
api_log = []

async def handle_response(response):
    url = response.url
    if "bff" in url and "land" in url:
        try:
            data = await response.json()
            if data.get("data"):
                info = {"url": url, "data": data["data"]}
                api_log.append(info)
                print(f"✅ {url[40:80]}")
        except:
            pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 註冊攔截
        page.on("response", handle_response)
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await asyncio.sleep(2)
        
        print("\n" + "="*50)
        print("  請現在開始操作:")
        print("  1. 選擇 武淵二段")
        print("  2. 點擊土地查看詳情")
        print("  3. 滾動點擊更多")
        print("\n  我會一直監聽，直到你回覆 'done'")
        print("="*50 + "\n")
        
        # 持續監聽
        try:
            while True:
                await asyncio.sleep(5)
                print(f"⏰ 監聽中... 已收到 {len(api_log)} 個 API")
        except KeyboardInterrupt:
            pass
        
        # 儲存
        print(f"\n💾 儲存 {len(api_log)} 個 API...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(api_log, f, ensure_ascii=False, indent=2)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
