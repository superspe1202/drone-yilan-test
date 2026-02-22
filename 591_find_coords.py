#!/usr/bin/env python3
"""
591 土地資料擷取 - 深入查找座標
"""

import asyncio
import json
import re
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_FILE = Path(__file__).parent / "591_wuyuan2_coords.json"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(viewport={"width": 1400, "height": 900})
        page = await context.new_page()
        
        url = "https://land.591.com.tw/map?region_id=21&mode=tenor&keyword=%E6%AD%A6%E6%B7%B5%E4%BA%8C%E6%AE%B5"
        
        print(f"\n🌐 前往...")
        await page.goto(url, wait_until="networkidle")
        await page.wait_for_timeout(8000)
        
        print("\n📋 點擊第一個土地...")
        
        # 點擊第一個土地
        try:
            first_item = page.locator("[class*='land-item'], .item, .list-item").first
            await first_item.click()
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  點擊失敗: {e}")
        
        # 嘗試各種方式取得座標
        print("\n🔍 搜尋座標...")
        
        # 方法1: 從 page.evaluate 取得
        coords_data = await page.evaluate("""
            () => {
                const results = {};
                
                // 1. 從 window 物件
                for (let key in window) {
                    if (key.includes('lat') || key.includes('lng') || key.includes('coord')) {
                        results[key] = typeof window[key] === 'object' ? JSON.stringify(window[key]) : window[key];
                    }
                }
                
                // 2. 從地圖元素
                const mapEl = document.querySelector('[class*="map"]');
                if (mapEl) {
                    results.mapEl = mapEl.className;
                    // 嘗試取得 data
                    for (let attr of mapEl.attributes) {
                        if (attr.name.includes('data') || attr.name.includes('prop')) {
                            results[attr.name] = attr.value;
                        }
                    }
                }
                
                // 3. 從彈出視窗
                const popup = document.querySelector('[class*="popup"], [class*="detail"], [class*="info"]');
                if (popup) {
                    results.popup = popup.innerText.substring(0, 500);
                }
                
                // 4. 從 URL 參數
                results.url = window.location.href;
                
                return results;
            }
        """)
        
        print("  方法1結果:")
        for k, v in list(coords_data.items())[:10]:
            print(f"    {k}: {str(v)[:100]}")
        
        # 方法2: 取得頁面所有文字中的座標格式
        page_text = await page.inner_text("body")
        coords = re.findall(r'(24\.\d{4,7})[,\s]+(121\.\d{4,7})', page_text)
        
        print(f"\n  方法2 - 找到 {len(coords)} 組座標:")
        for c in coords[:5]:
            print(f"    lat={c[0]}, lng={c[1]}")
        
        # 方法3: 從 DOM 元素取得
        all_coords = await page.evaluate("""
            () => {
                const coords = [];
                const allText = document.body.innerText;
                const matches = allText.matchAll(/24\\.\\d{4,7}[,\\s]+121\\.\\d{4,7}/g);
                for (let m of matches) {
                    const parts = m[0].split(/[,\\s]+/);
                    if (parts.length >= 2) {
                        coords.push({raw: m[0], lat: parts[0], lng: parts[1]});
                    }
                }
                return coords;
            }
        """)
        
        print(f"\n  方法3 - DOM 座標: {all_coords}")
        
        # 儲存
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "methods": {
                    "window_data": coords_data,
                    "regex_coords": coords,
                    "dom_coords": all_coords
                }
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 儲存至 {OUTPUT_FILE}")
        
        # 保持開啟讓使用者查看
        print("\n🔔 瀏覽器保持開啟 60 秒...")
        await asyncio.sleep(60)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
