#!/usr/bin/env python3
"""
591 土地資料擷取 - 嘗試不同模式
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

async def get_all_modes():
    """測試不同模式的資料"""
    
    modes = [
        ("tenor", "地籍查詢/謄本"),
        ("in-sale", "在售土地"),
        ("real-price", "實價登錄"),
    ]
    
    results = {}
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        for mode_id, mode_name in modes:
            print(f"\n🔄 測試模式: {mode_name}")
            
            context = await browser.new_context(viewport={"width": 1400, "height": 900})
            page = await context.new_page()
            
            try:
                # 前往該模式
                await page.goto(f"https://land.591.com.tw/map?region_id=21&mode={mode_id}")
                await page.wait_for_timeout(5000)
                
                # 選擇武淵二段
                try:
                    dropdown = page.locator("p:has-text('鄉鎮/地段/捷運'), div:has-text('鄉鎮/地段/捷運')").first
                    await dropdown.click(timeout=3000)
                    await asyncio.sleep(1)
                    
                    section_tab = page.locator("div:has-text('地段')").first
                    await section_tab.click(timeout=3000)
                    await asyncio.sleep(1)
                    
                    search = page.locator("input[type='text']").first
                    await search.fill("武淵二段")
                    await search.press("Enter")
                    await asyncio.sleep(2)
                    
                    result = page.locator("text=武淵二段").first
                    await result.click(timeout=3000)
                    await asyncio.sleep(1)
                    
                    confirm = page.locator("button:has-text('確定')").first
                    await confirm.click(timeout=3000)
                    await asyncio.sleep(5000)
                except Exception as e:
                    print(f"  ⚠️ 選擇地段失敗: {e}")
                
                # 取得頁面文字
                page_text = await page.inner_text("body")
                
                # 找總筆數
                import re
                count_match = re.search(r'共\s*(\d+)\s*筆', page_text)
                total_count = int(count_match.group(1)) if count_match else 0
                
                # 找土地筆數
                land_matches = re.findall(r'武淵二段\d+[-+]?\d*地號', page_text)
                land_count = len(set(land_matches))
                
                results[mode_name] = {
                    "total_shown": total_count,
                    "lands_found": land_count,
                    "url": page.url
                }
                
                print(f"  📊 顯示: {total_count} 筆, 找到: {land_count} 筆")
                
            except Exception as e:
                print(f"  ❌ 錯誤: {e}")
            
            await context.close()
        
        await browser.close()
    
    return results

async def main():
    results = await get_all_modes()
    
    print("\n" + "="*50)
    print("📊 各模式結果:")
    for mode, data in results.items():
        print(f"  {mode}: {data}")
    
    # 儲存
    with open("/Users/superspe/.openclaw/workspace/591_modes.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
