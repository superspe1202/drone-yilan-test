#!/usr/bin/env python3
"""
八仙段完整土地邊界偵測
下載衛星圖磚 -> OpenCV 偵測 -> 儲存 GeoJSON
"""

import os
import math
import json
import requests
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 八仙段範圍（從 1126 個中心點計算）
MIN_LAT = 24.6538
MAX_LAT = 24.6660
MIN_LON = 121.7770
MAX_LON = 121.7935

ZOOM = 19
OUTPUT_FILE = "drone-app/baxian_all_boundaries.json"

# 偵測參數
MIN_AREA = 300  # 最小面積
CANNY_LOW = 30
CANNY_HIGH = 80

def lat_lon_to_tile(lat, lon, zoom):
    """經緯度轉圖磚座標"""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def tile_to_lat_lon(x, y, zoom):
    """圖磚座標轉經緯度"""
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def download_tile(x, y, zoom):
    """下載單個圖磚"""
    # 使用 ESRI 衛星圖
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
    
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'OpenClaw/1.0'})
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except Exception as e:
        print(f"下載失敗 ({x},{y}): {e}")
    
    return None

def detect_boundaries_in_image(image):
    """偵測圖片中的土地邊界"""
    if image is None:
        return []
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Canny 邊緣偵測
    edges = cv2.Canny(blurred, CANNY_LOW, CANNY_HIGH)
    
    # 轉 HSV 偵測綠色農地
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([20, 20, 20])
    upper_green = np.array([90, 255, 200])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # 合併邊緣和綠色遮罩
    combined = cv2.bitwise_or(edges, mask)
    
    # 形態學處理
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(combined, kernel, iterations=2)
    eroded = cv2.erode(dilated, kernel, iterations=1)
    
    # 找輪廓
    contours, _ = cv2.findContours(eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 過濾
    valid = [c for c in contours if cv2.contourArea(c) > MIN_AREA]
    
    return valid

def image_to_geojson_contours(contours, img_shape, min_lon, min_lat, max_lon, max_lat):
    """將輪廓轉為 GeoJSON 座標"""
    h, w = img_shape[:2]
    lon_per_px = (max_lon - min_lon) / w
    lat_per_px = (max_lat - min_lat) / h
    
    coords_list = []
    for contour in contours:
        coords = []
        for point in contour:
            px, py = point[0]
            lon = min_lon + px * lon_per_px
            lat = max_lat - py * lat_per_px
            coords.append([lon, lat])
        
        # 閉合
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])
        
        if len(coords) >= 3:
            coords_list.append(coords)
    
    return coords_list

def process_tile(tx, ty, zoom, tile_bounds):
    """處理單個圖磚"""
    print(f"處理圖磚: ({tx}, {ty})")
    tile = download_tile(tx, ty, zoom)
    
    if tile is None:
        return []
    
    contours = detect_boundaries_in_image(tile)
    
    if contours:
        coords = image_to_geojson_contours(contours, tile.shape, 
            tile_bounds['min_lon'], tile_bounds['min_lat'],
            tile_bounds['max_lon'], tile_bounds['max_lat'])
        return coords
    
    return []

def main():
    print("=== 八仙段土地邊界偵測 ===")
    print(f"範圍: lat {MIN_LAT:.4f}~{MAX_LAT:.4f}, lon {MIN_LON:.4f}~{MAX_LON:.4f}")
    
    # 計算需要的圖磚
    min_tx, min_ty = lat_lon_to_tile(MAX_LAT, MIN_LON, ZOOM)
    max_tx, max_ty = lat_lon_to_tile(MIN_LAT, MAX_LON, ZOOM)
    
    print(f"圖磚範圍: x={min_tx}~{max_tx}, y={min_ty}~{max_ty}")
    
    tiles = []
    for y in range(min_ty, max_ty + 1):  # Y 遞增
        for x in range(min_tx, max_tx + 1):
            # 計算這個圖磚的地理邊界
            lat1, lon1 = tile_to_lat_lon(x, y, ZOOM)
            lat2, lon2 = tile_to_lat_lon(x + 1, y + 1, ZOOM)
            bounds = {
                'min_lon': lon1,
                'max_lat': lat1,
                'max_lon': lon2,
                'min_lat': lat2
            }
            tiles.append((x, y, ZOOM, bounds))
    
    print(f"總共 {len(tiles)} 個圖磚")
    
    # 下載並處理所有圖磚
    all_features = []
    
    for i, (tx, ty, zoom, bounds) in enumerate(tiles):
        print(f"[{i+1}/{len(tiles)}] 處理圖磚 ({tx}, {ty})...")
        
        tile = download_tile(tx, ty, zoom)
        if tile is None:
            continue
        
        contours = detect_boundaries_in_image(tile)
        
        if contours:
            coords = image_to_geojson_contours(contours, tile.shape,
                bounds['min_lon'], bounds['min_lat'],
                bounds['max_lon'], bounds['max_lat'])
            
            for j, c in enumerate(coords):
                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [c]
                    },
                    "properties": {
                        "id": f"{tx}_{ty}_{j}",
                        "tile": f"{tx}_{ty}"
                    }
                }
                all_features.append(feature)
            
            print(f"  -> 偵測到 {len(coords)} 塊")
        
        time.sleep(0.1)  # 避免請求太快
    
    # 儲存結果
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }
    
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2, ensure_ascii=False)
    
    print(f"\n完成！")
    print(f"總共偵測到: {len(all_features)} 塊土地")
    print(f"已儲存到: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
