#!/usr/bin/env python3
"""
591 土地資料擷取 - 點擊載入更多
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_data.json"

async def select_and_scroll(page, section_name: str):
    """選擇地段並滾動載入"""
    
    # 選擇地段
    try:
        dropdown = page.locator("p:has-text('鄉鎮/地段/捷運'), div:has-text('鄉鎮/地段/捷運')").first
        await dropdown.click(timeout=3000)
        await asyncio.sleep(1)
        
        section_tab = page.locator("div:has-text('地段')").first
        await section_tab.click(timeout=3000)
        await asyncio.sleep(1)
        
        search = page.locator("input[type='text']").first
        await search.fill(section_name)
        await search.press("Enter")
        await asyncio.sleep(2)
        
        result = page.locator(f"text={section_name}").first
        await result.click(timeout=3000)
        await asyncio.sleep(1)
        
        confirm = page.locator("button:has-text('確定')").first
        await confirm.click(timeout=3000)
        await asyncio.sleep(5000)
    except Exception as e:
        print(f"  ⚠️ 選擇失敗: {e}")
    
    # 取得頁面顯示的總筆數
    page_text = await page.inner_text("body")
    count_match = re.search(r'共\s*(\d+)\s*筆', page_text)
    total_shown = int(count_match.group(1)) if count_match else 0
    print(f"  📊 頁面顯示: {total_shown} 筆")
    
    lands = []
    
    # 嘗試點擊載入更多
    for i in range(50):  # 最多50次
        try:
            # 找 "載入更多" 或 "看更多" 按鈕
            load_more = page.locator("text=載入更多, text=看更多, text=更多").first
            await load_more.click(timeout=2000)
            print(f"    點擊載入更多 ({i+1})")
            await asyncio.sleep(1)
        except:
            pass
        
        # 滾動
        await page.evaluate("window.scrollBy(0, 300)")
        await asyncio.sleep(0.5)
        
        # 提取當前可見的土地
        try:
            items = await page.query_selector_all("[class*='land'], [class*='item'], .list-item, .land-item")
            
            for item in items:
                try:
                    text = await item.inner_text()
                    if "地號" in text and "段" in text:
                        lines = [l.strip() for l in text.split("\n") if l.strip()]
                        
                        land_num = area = price = land_type = None
                        
                        for line in lines:
                            if "地號" in line and not land_num:
                                land_num = line
                            elif "坪" in line and not area:
                                area = line
                            elif ("萬/坪" in line or "元/坪" in line) and not price:
                                price = line
                            elif "都市" in line or "非都市" in line:
                                land_type = line
                        
                        if land_num:
                            exists = any(l.get("land_number") == land_num for l in lands)
                            if not exists:
                                lands.append({
                                    "land_number": land_num,
                                    "area": area,
                                    "price": price,
                                    "land_type": land_type
                                })
                except:
                    pass
        except:
            pass
        
        # 檢查數量
        if len(lands) >= total_shown and total_shown > 0:
            print(f"    已達到顯示上限: {len(lands)}")
            break
        
        if i % 10 == 0:
            print(f"    目前進度: {len(lands)} 筆")
    
    return lands, total_shown

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        print("\n🌐 前往 591...")
        await page.goto("https://land.591.com.tw/map?region_id=21&mode=tenor")
        await page.wait_for_timeout(5000)
        
        print("\n🎯 選擇武淵二段...")
        lands, total = await select_and_scroll(page, "武淵二段")
        
        print(f"\n📋 結果:")
        print(f"   顯示上限: {total}")
        print(f"   擷取筆數: {len(lands)}")
        
        # 顯示前10筆
        for i, land in enumerate(lands[:10]):
            print(f"   {i+1}. {land}")
        
        # 儲存
        result = {
            "section": "武淵二段",
            "region": "宜蘭縣冬山鄉",
            "total_displayed": total,
            "lands_count": len(lands),
            "lands": lands
        }
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
