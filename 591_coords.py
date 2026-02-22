#!/usr/bin/env python3
"""
591 土地 - 從點擊請求中提取座標
"""

import asyncio
import json
import re
from playwright.async_api import async_playwright

OUTPUT_FILE = "/Users/superspe/.openclaw/workspace/wuyuan2_coords.json"
lands = []

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 攔截請求並提取座標
        async def handle_request(request):
            if "land-transcript/map/s" in request.url:
                try:
                    # 取得 POST 資料
                    post_data = await request.post_data
                    if post_data:
                        data_str = post_data.decode('utf-8')
                        data = json.loads(data_str)
                        
                        center = data.get("center", [])
                        target_id = data.get("target_id")
                        section_id = data.get("section_id")
                        
                        if center and len(center) >= 2:
                            lat, lng = center[0], center[1]
                            
                            # 避免重複
                            exists = any(l.get("target_id") == target_id for l in lands)
                            if not exists:
                                lands.append({
                                    "target_id": target_id,
                                    "lat": lat,
                                    "lng": lng,
                                    "section_id": section_id,
                                    "point": data.get("point", [])
                                })
                                print(f"📍 target_id={target_id}, lat={lat}, lng={lng}")
                except Exception as e:
                    pass
        
        page.on("request", handle_request)
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await asyncio.sleep(3)
        
        print("\n" + "="*50)
        print("請選擇武淵二段，然後盡情點擊土地")
        print("我會從請求中提取座標")
        print("="*50)
        
        # 持續監聽
        for i in range(300):  # 5分鐘
            await asyncio.sleep(1)
            if i % 30 == 0 and i > 0:
                print(f"⏰ {i}秒, 已收集 {len(lands)} 筆")
        
        # 儲存
        print(f"\n💾 儲存 {len(lands)} 筆座標...")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(lands, f, ensure_ascii=False, indent=2)
        
        print(f"✅ -> {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
