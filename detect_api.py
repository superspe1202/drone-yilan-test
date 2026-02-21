#!/usr/bin/env python3
"""
八仙段土地邊界偵測 API
接收參數 -> 下載圖磚 -> OpenCV 偵測 -> 回傳 GeoJSON
"""

import os
import math
import json
import requests
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor
import time

app = Flask(__name__)

# 八仙段範圍
MIN_LAT = 24.6538
MAX_LAT = 24.6660
MIN_LON = 121.7770
MAX_LON = 121.7935
ZOOM = 19

def lat_lon_to_tile(lat, lon, zoom):
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return x, y

def tile_to_lat_lon(x, y, zoom):
    n = 2.0 ** zoom
    lon = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat = math.degrees(lat_rad)
    return lat, lon

def download_tile(x, y, zoom):
    url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{y}/{x}"
    try:
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'OpenClaw/1.0'})
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    except:
        pass
    return None

def detect_boundaries(image, canny_low, canny_high, min_area):
    if image is None:
        return []
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    
    # Canny 邊緣偵測（參數可調）
    edges = cv2.Canny(blurred, canny_low, canny_high)
    
    # 轉 HSV 偵測綠色農地
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    lower_green = np.array([20, 20, 20])
    upper_green = np.array([90, 255, 200])
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # 合併
    combined = cv2.bitwise_or(edges, mask)
    
    # 形態學處理
    kernel = np.ones((3, 3), np.uint8)
    dilated = cv2.dilate(combined, kernel, iterations=2)
    
    # 找輪廓
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 過濾
    valid = [c for c in contours if cv2.contourArea(c) > min_area]
    
    return valid

def to_geojson(contours, img_shape, min_lon, min_lat, max_lon, max_lat):
    h, w = img_shape[:2]
    lon_per = (max_lon - min_lon) / w
    lat_per = (max_lat - min_lat) / h
    
    features = []
    for i, c in enumerate(contours):
        coords = []
        for pt in c:
            px, py = pt[0]
            lon = min_lon + px * lon_per
            lat = max_lat - py * lat_per
            coords.append([lon, lat])
        
        if coords and coords[0] != coords[-1]:
            coords.append(coords[0])
        
        if len(coords) >= 3:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                },
                "properties": {
                    "id": i,
                    "area": cv2.contourArea(c)
                }
            })
    
    return {"type": "FeatureCollection", "features": features}

@app.route('/detect', methods=['GET', 'POST'])
def detect():
    # 取得參數
    canny_low = request.args.get('canny_low', 30, type=int)
    canny_high = request.args.get('canny_high', 80, type=int)
    min_area = request.args.get('min_area', 40, type=int)
    
    print(f"偵測參數: canny_low={canny_low}, canny_high={canny_high}, min_area={min_area}")
    
    # 計算圖磚範圍
    min_tx, min_ty = lat_lon_to_tile(MAX_LAT, MIN_LON, ZOOM)
    max_tx, max_ty = lat_lon_to_tile(MIN_LAT, MAX_LON, ZOOM)
    
    all_features = []
    
    for y in range(min_ty, max_ty + 1):
        for x in range(min_tx, max_tx + 1):
            lat1, lon1 = tile_to_lat_lon(x, y, ZOOM)
            lat2, lon2 = tile_to_lat_lon(x + 1, y + 1, ZOOM)
            
            tile = download_tile(x, y, ZOOM)
            if tile:
                contours = detect_boundaries(tile, canny_low, canny_high, min_area)
                
                if contours:
                    coords = to_geojson(contours, tile.shape, lon1, lat2, lon2, lat1)
                    for c in coords['features']:
                        c['properties']['tile'] = f"{x}_{y}"
                        all_features.append(c)
            
            time.sleep(0.02)  # 避免請求太快
    
    result = {"type": "FeatureCollection", "features": all_features}
    
    return jsonify({
        "count": len(all_features),
        "params": {
            "canny_low": canny_low,
            "canny_high": canny_high,
            "min_area": min_area
        },
        "data": result
    })

@app.route('/')
def index():
    return '''
    <h1>八仙段邊界偵測 API</h1>
    <p>使用方法：</p>
    <ul>
        <li>/detect?canny_low=30&canny_high=80&min_area=40</li>
    </ul>
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
