#!/usr/bin/env python3
"""
591 土地資料擷取 - 自動點擊每個土地取得座標
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_full.json"

async def select_section(page, section_name: str):
    """選擇地段"""
    try:
        # 點擊下拉選單
        dropdown = page.locator("p:has-text('鄉鎮/地段/捷運'), div:has-text('鄉鎮/地段/捷運')").first
        await dropdown.click(timeout=3000)
        await asyncio.sleep(1)
        
        # 點擊地段標籤
        section_tab = page.locator("div:has-text('地段')").first
        await section_tab.click(timeout=3000)
        await asyncio.sleep(1)
        
        # 輸入搜尋
        search = page.locator("input[type='text'], input.search-input").first
        await search.fill(section_name)
        await search.press("Enter")
        await asyncio.sleep(2)
        
        # 點擊結果
        result = page.locator(f"text={section_name}").first
        await result.click(timeout=3000)
        await asyncio.sleep(1)
        
        # 點擊確定
        confirm = page.locator("button:has-text('確定')").first
        await confirm.click(timeout=3000)
        await asyncio.sleep(5000)
        
        return True
    except Exception as e:
        print(f"  選擇失敗: {e}")
        return False

async def click_each_land_and_get_coords(page, max_clicks: int = 100):
    """點擊每個土地取得座標"""
    
    lands = []
    
    # 取得土地列表元素
    land_items = await page.query_selector_all("[class*='land'], [class*='item'], .list-item, .land-item")
    
    print(f"  找到 {len(land_items)} 個土地項目")
    
    clicked_count = 0
    
    for i, item in enumerate(land_items[:max_clicks]):
        try:
            # 點擊土地項目
            await item.click()
            await asyncio.sleep(1)
            
            # 嘗試取得彈出視窗的座標
            # 可能在 DOM 中找到 lat/lng
            
            # 方法1: 從 URL 取得
            current_url = page.url
            
            # 方法2: 從頁面元素取得座標
            coord_text = await page.evaluate("""
                () => {
                    // 嘗試從各種元素取得座標
                    const els = document.querySelectorAll('[class*="coord"], [class*="lat"], [class*="lng"], [class*="position"]');
                    for (let el of els) {
                        if (el.innerText.match(/\\d+\\.\\d+/)) {
                            return el.innerText;
                        }
                    }
                    return null;
                }
            """)
            
            # 方法3: 從地圖取得中心點
            map_center = await page.evaluate("""
                () => {
                    const mapEl = document.querySelector('[class*="map"]');
                    if (mapEl && mapEl.__data__) {
                        return JSON.stringify(mapEl.__data__);
                    }
                    return null;
                }
            """)
            
            # 取得土地詳細資訊
            detail_text = await page.inner_text("body")
            
            # 嘗試解析座標
            import re
            coords = re.findall(r'(\d+\.\d{4,})[,\s]+(\d+\.\d{4,})', detail_text)
            
            land_info = {
                "index": i + 1,
                "url": current_url,
                "coords_found": len(coords) > 0,
                "detail_preview": detail_text[:500]
            }
            
            if coords:
                land_info["lat"] = float(coords[0][0])
                land_info["lng"] = float(coords[0][1])
            
            lands.append(land_info)
            clicked_count += 1
            
            if clicked_count % 10 == 0:
                print(f"    已點擊 {clicked_count} 筆")
            
            # 點擊其他地方關閉彈窗
            await page.click("body", offset=(10, 10))
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"    點擊失敗: {e}")
    
    return lands

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(5000)
        
        print("\n🎯 選擇武淵二段...")
        success = await select_section(page, "武淵二段")
        
        if not success:
            print("選擇失敗，請手動操作後按 Enter...")
            input()
        
        # 等待載入
        await page.wait_for_timeout(5000)
        
        print("\n📍 開始點擊每個土地取得座標...")
        lands = await click_each_land_and_get_coords(page, max_clicks=50)
        
        # 統計
        has_coords = sum(1 for l in lands if l.get("lat"))
        
        print(f"\n📋 結果:")
        print(f"   總點擊: {len(lands)}")
        print(f"   有座標: {has_coords}")
        
        # 顯示有座標的
        for l in lands[:10]:
            if l.get("lat"):
                print(f"   - lat: {l.get('lat')}, lng: {l.get('lng')}")
        
        # 儲存
        result = {
            "section": "武淵二段",
            "total_clicked": len(lands),
            "with_coords": has_coords,
            "lands": lands
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
