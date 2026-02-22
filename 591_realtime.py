#!/usr/bin/env python3
"""
591 土地 - 即時攔截請求
讓使用者手動點擊，我來攔截 API
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_apis.json"

api_log = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 即時攔截
        page.on("response", lambda resp: asyncio.create_task(handle_response(resp)))
        
        async def handle_response(response):
            url = response.url
            if "bff" in url or "land" in url or "map" in url:
                try:
                    data = await response.json()
                    if data.get("data"):
                        info = {"url": url, "status": response.status, "data": data["data"]}
                        api_log.append(info)
                        print(f"✅ {response.status} {url[40:100]}...")
                except:
                    pass
        
        # 直接用 keyword URL
        url = "https://land.591.com.tw/map?region_id=21&mode=tenor&keyword=%E6%AD%A6%E6%B7%B5%E4%BA%8C%E6%AE%B5"
        
        print(f"\n🌐 前往: {url}")
        await page.goto(url, wait_until="networkidle")
        
        print("\n" + "="*60)
        print("  請手動操作:")
        print("  1. 點擊列表中的土地")
        print("  2. 查看詳細資料")
        print("  3. 滾動繼續點擊更多")
        print("\n  我會即時攔截 API 請求")
        print("="*60 + "\n")
        
        # 持續監聽
        for i in range(60):  # 60秒
            await asyncio.sleep(1)
            if i % 10 == 0:
                print(f"⏰ 已攔截 {len(api_log)} 個 API 請求...")
        
        # 儲存
        print(f"\n💾 儲存 {len(api_log)} 個 API...")
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(api_log, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 完成! -> {OUTPUT_FILE}")
        
        # 顯示結果
        print("\n📊 攔截到的 API:")
        for i, api in enumerate(api_log[:10]):
            print(f"  {i+1}. {api['url'][50:120]}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
