// Center on Yilan Dongshan Basian Section
var map = L.map('map').setView([24.635, 121.785], 17);

// 1. Add Base Layers
var osm = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap'
});

var googleSat = L.tileLayer('http://{s}.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',{
    maxZoom: 22,
    subdomains:['mt0','mt1','mt2','mt3']
});

// 2. Add Taiwan NLSC Layers
// 官方段界 (黃線)
var landSect = L.tileLayer('https://wmts.nlsc.gov.tw/wmts/LANDSECT2/default/GoogleMapsCompatible/{z}/{y}/{x}', {
    opacity: 0.8,
    maxZoom: 20,
    zIndex: 50,
    attribution: '段籍圖'
});

// 591 地籍圖層 (Vercel Serverless Proxy)
var cadastral591 = L.tileLayer('/api/proxy?z={z}&x={x}&y={y}', {
    opacity: 1.0,
    maxZoom: 22,       
    maxNativeZoom: 20, 
    zIndex: 100,
    attribution: '591地籍圖'
});

// 農業部農地圖層 (ALRIS)
var landUse = L.tileLayer('https://wmts.nlsc.gov.tw/wmts/LUIMAP/default/GoogleMapsCompatible/{z}/{y}/{x}', {
    opacity: 0.6,
    maxZoom: 20,
    attribution: '國土利用(農地)'
});

// 3. OSM Data Layer
var osmLayers = new L.FeatureGroup();

// Add layers (預設開啟 白底OSM + 591紅線)
// 這樣紅線會最明顯！
osm.addTo(map); 
landSect.addTo(map); 
cadastral591.addTo(map);
osmLayers.addTo(map);

var baseMaps = {
    "一般地圖 (白底)": osm,
    "衛星地圖": googleSat
};

var overlayMaps = {
    "591 地籍紅線 (最強!)": cadastral591,
    "官方段界 (黃線)": landSect,
    "農地分布": landUse,
    "自動農地框 (OSM)": osmLayers
};

L.control.layers(baseMaps, overlayMaps).addTo(map);

L.control.locate({position: 'topleft', strings: {title: "我的位置"}}).addTo(map);

// Load OSM Button
var osmBtn = L.control({position: 'topright'});
osmBtn.onAdd = function (map) {
    var div = L.DomUtil.create('div', 'leaflet-bar leaflet-control');
    div.innerHTML = '<a href="#" title="自動抓取農地框線" style="background:white; font-size: 24px; width: 40px; height: 40px; line-height: 40px; display:flex; align-items:center; justify-content:center; text-decoration:none;">🌾</a>';
    div.onclick = function(e) {
        e.preventDefault();
        loadOSMData();
    };
    return div;
};
osmBtn.addTo(map);

function loadOSMData() {
    var bounds = map.getBounds();
    // Query for farmland in current view
    var query = `
        [out:json];
        (
          way["landuse"="farmland"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="farm"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="orchard"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
          way["landuse"="grass"](${bounds.getSouth()},${bounds.getWest()},${bounds.getNorth()},${bounds.getEast()});
        );
        out body;
        >;
        out skel qt;
    `;
    
    var btnLink = osmBtn.getContainer().querySelector('a');
    btnLink.innerHTML = '⏳';

    fetch('https://overpass-api.de/api/interpreter?data=' + encodeURIComponent(query))
        .then(res => res.json())
        .then(data => {
            btnLink.innerHTML = '🌾';
            
            if (typeof osmtogeojson === 'undefined') {
                alert("錯誤：核心套件未載入，請重新整理網頁！");
                return;
            }
            
            var geojson = osmtogeojson(data);
            osmLayers.clearLayers();
            
            var layer = L.geoJSON(geojson, {
                style: { color: "#ffff00", weight: 2, opacity: 0.9, fillOpacity: 0.2 },
                onEachFeature: function(feature, layer) {
                    layer.on('click', function() {
                        var areaSqm = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
                        updateDisplay(areaSqm);
                        osmLayers.eachLayer(l => osmLayers.resetStyle(l));
                        layer.setStyle({color: "#ff0000", fillOpacity: 0.5, weight: 4});
                    });
                }
            }).addTo(osmLayers);
            
            if (layer.getLayers().length === 0) {
                alert("這裡在 OSM 上沒有農地資料... 請用手動框選！");
            } else {
                alert(`成功抓到 ${layer.getLayers().length} 塊農地！`);
            }
        })
        .catch(err => {
            alert("連線失敗：" + err);
            btnLink.innerHTML = '❌';
        });
}

// Draw Tools
var drawnItems = new L.FeatureGroup();
map.addLayer(drawnItems);
var drawControl = new L.Control.Draw({
    draw: { polygon: { showArea: true }, polyline: false, circle: false, rectangle: true, marker: false, circlemarker: false },
    edit: { featureGroup: drawnItems }
});
map.addControl(drawControl);

// Area Calc Logic
var pricePerFenInput = document.getElementById('pricePerFen');
var areaDisplay = document.getElementById('areaDisplay');
var areaSubDisplay = document.getElementById('areaSubDisplay');
var priceDisplay = document.getElementById('priceDisplay');
const SQM_TO_FEN = 0.00103102; 
const SQM_TO_PING = 0.3025;    

map.on(L.Draw.Event.CREATED, function (e) {
    drawnItems.clearLayers();
    var layer = e.layer;
    drawnItems.addLayer(layer);
    var areaSqm = L.GeometryUtil.geodesicArea(layer.getLatLngs()[0]);
    updateDisplay(areaSqm);
});

function updateDisplay(sqm) {
    var areaFen = sqm * SQM_TO_FEN;
    var areaPing = sqm * SQM_TO_PING;
    
    areaDisplay.innerText = areaFen.toFixed(2) + " 分";
    areaSubDisplay.innerText = "(" + Math.floor(areaPing) + " 坪)";
    
    var price = Math.ceil(areaFen * parseFloat(pricePerFenInput.value));
    priceDisplay.innerText = "$" + price.toLocaleString();
}

document.getElementById('locateBtn').addEventListener('click', function() {
    map.locate({setView: true, maxZoom: 18});
});