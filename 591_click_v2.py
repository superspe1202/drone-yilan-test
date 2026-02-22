#!/usr/bin/env python3
"""
591 土地資料擷取 - 從 URL 進入後點擊每個土地
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_full.json"

async def click_land_get_details(page, item, index: int):
    """點擊土地取得詳細資料和座標"""
    
    try:
        # 點擊
        await item.click()
        await asyncio.sleep(1.5)
        
        # 取得整個彈出內容
        popup_text = await page.inner_text("body")
        
        # 找座標
        coords = re.findall(r'(\d+\.\d{5,})[,\s]+(\d+\.\d{5,})', popup_text)
        
        # 找土地編號
        land_match = re.search(r'([^\s]+段[^地號]+地號[^\s]*)', popup_text)
        
        # 找面積
        area_match = re.search(r'(\d+\.?\d*)\s*坪', popup_text)
        
        # 找價格
        price_match = re.search(r'(\d+\.?\d*)\s*(萬/坪|元/坪)', popup_text)
        
        result = {
            "index": index,
            "land_number": land_match.group(1) if land_match else None,
            "area": area_match.group(1) + "坪" if area_match else None,
            "price": price_match.group(0) if price_match else None,
        }
        
        # 如果找到座標
        if coords:
            # 找看起來像 lat/lng 的座標 (宜蘭約 24.6xxx, 121.7xxx)
            for c in coords:
                lat, lng = float(c[0]), float(c[1])
                if 24.5 < lat < 25 and 121.5 < lng < 122:
                    result["lat"] = lat
                    result["lng"] = lng
                    break
        
        # 點擊關閉
        try:
            close_btn = page.locator("button:has-text('×'), [class*='close'], .icon-close").first
            await close_btn.click(timeout=1000)
        except:
            await page.click("body", offset=(50, 50))
        
        await asyncio.sleep(0.5)
        
        return result
        
    except Exception as e:
        return {"index": index, "error": str(e)[:100]}

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        # 直接用包含 keyword 的 URL
        url = "https://land.591.com.tw/map?region_id=21&mode=tenor&keyword=%E6%AD%A6%E6%B7%B5%E4%BA%8C%E6%AE%B5"
        
        print(f"\n🌐 前往 {url}")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(8000)
        
        print("\n📋 等待載入...")
        
        # 檢查是否成功載入武淵二段
        page_text = await page.inner_text("body")
        if "武淵二段" in page_text:
            print("  ✅ 成功載入武淵二段")
        else:
            print("  ⚠️ 未檢測到武淵二段，請手動操作")
        
        print("\n📍 點擊每個土地取得座標...")
        
        # 找到所有土地項目
        land_items = await page.query_selector_all(
            "[class*='land-item'], [class*='list-item'], "
            ".item, [class*='card'], .land-card"
        )
        
        print(f"  找到 {len(land_items)} 個土地項目")
        
        results = []
        
        # 點擊每個
        for i, item in enumerate(land_items[:30]):  # 先做30個
            result = await click_land_get_details(page, item, i+1)
            results.append(result)
            
            if (i+1) % 5 == 0:
                print(f"    已處理 {i+1} 筆")
        
        # 統計
        with_coords = sum(1 for r in results if r.get("lat"))
        
        print(f"\n📋 結果:")
        print(f"   總處理: {len(results)}")
        print(f"   有座標: {with_coords}")
        
        # 顯示有座標的
        for r in results:
            if r.get("lat"):
                print(f"   - {r.get('land_number')}: lat={r.get('lat')}, lng={r.get('lng')}")
        
        # 儲存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "section": "武淵二段",
                "total": len(results),
                "with_coords": with_coords,
                "lands": results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        # 保持開啟
        print("\n🔔 瀏覽器保持開啟...")
        await asyncio.sleep(60)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
