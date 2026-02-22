#!/usr/bin/env python3
"""
591 土地 - 攔截所有請求
"""

import asyncio
import json
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/591_all_requests.json"
all_requests = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 攔截所有請求
        page.on("request", lambda req: all_requests.append({"url": req.url, "method": req.method}))
        page.on("response", lambda resp: all_requests.append({"url": resp.url, "status": resp.status}))
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await asyncio.sleep(5)
        
        print(f"\n📊 總請求數: {len(all_requests)}")
        
        # 篩選相關
        related = [r for r in all_requests if "591" in r.get("url", "")]
        print(f"   591 相關: {len(related)}")
        
        # 顯示
        print("\n📋 請求列表:")
        for r in related[:20]:
            print(f"  {r.get('method', 'GET')} {r.get('url', '')[:80]}")
        
        # 儲存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(related, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
