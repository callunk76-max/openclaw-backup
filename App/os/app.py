#!/usr/bin/env python3
"""
OSS-RBA Polygon Editor
Generate GeoJSON polygon files for NIB (Nomor Induk Berusaha) submissions.
Compliant with OSS-RBA spatial data format specifications.
"""

from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import io
import time
import hashlib
from datetime import datetime

app = Flask(__name__)

APP_DIR = os.path.dirname(os.path.abspath(__file__))
HEALTH_FILE = os.path.join(APP_DIR, 'health.txt')
# Rate limiting simple in-memory
_request_times = {}

# ============================================================
# Routes
# ============================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    status = {
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'oss-polygon-editor',
        'version': '1.0.0'
    }
    # Write health proof file
    with open(HEALTH_FILE, 'w') as f:
        f.write(json.dumps(status))
    return jsonify(status), 200

@app.route('/api/export', methods=['POST'])
def export_polygon():
    """Receive GeoJSON FeatureCollection, validate and return download."""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    # Validate structure
    if data.get('type') != 'FeatureCollection':
        return jsonify({'error': 'Must be a FeatureCollection'}), 400
    
    features = data.get('features', [])
    if not features:
        return jsonify({'error': 'No features (polygons) found'}), 400
    
    # Validate each feature
    for i, feat in enumerate(features):
        geom = feat.get('geometry', {})
        if geom.get('type') not in ('Polygon', 'MultiPolygon'):
            return jsonify({'error': f'Feature {i+1}: geometry must be Polygon or MultiPolygon'}), 400
        
        coords = geom.get('coordinates', [])
        if not coords:
            return jsonify({'error': f'Feature {i+1}: no coordinates'}), 400
        
        # Ensure ring closure for Polygon
        if geom['type'] == 'Polygon':
            ring = coords[0]
            if len(ring) < 4:
                return jsonify({'error': f'Feature {i+1}: Polygon needs at least 4 points (ring closure)'}), 400
            if ring[0] != ring[-1]:
                ring.append(ring[0])  # Auto-close ring
    
    # Generate filename
    keterangan = features[0].get('properties', {}).get('keterangan_lokasi', 'lokasi_usaha')
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in keterangan)[:50]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"polygon_nib_{safe_name}_{timestamp}.geojson"
    
    # Prepare GeoJSON for OSS-RBA
    output = {
        'type': 'FeatureCollection',
        'metadata': {
            'generated_by': 'oss-polygon-editor',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'purpose': 'NIB OSS-RBA',
            'crs': 'EPSG:4326'
        },
        'features': features
    }
    
    json_bytes = json.dumps(output, indent=2, ensure_ascii=False).encode('utf-8')
    
    return send_file(
        io.BytesIO(json_bytes),
        mimetype='application/geo+json',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/export-kml', methods=['POST'])
def export_kml():
    """Export polygon as KML format (alternative for some OSS workflows)."""
    data = request.get_json()
    
    if not data or data.get('type') != 'FeatureCollection':
        return jsonify({'error': 'Need valid FeatureCollection'}), 400
    
    features = data.get('features', [])
    if not features:
        return jsonify({'error': 'No features'}), 400
    
    keterangan = features[0].get('properties', {}).get('keterangan_lokasi', 'Lokasi Usaha')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"polygon_nib_{timestamp}.kml"
    
    # Build KML
    kml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<kml xmlns="http://www.opengis.net/kml/2.2">',
        '  <Document>',
        f'    <name>NIB Polygon - {keterangan}</name>',
        f'    <description>Generated {datetime.utcnow().isoformat()}Z</description>'
    ]
    
    for feat in features:
        geom = feat['geometry']
        props = feat.get('properties', {})
        name = props.get('keterangan_lokasi', 'Lokasi Usaha')
        luas = props.get('luas_m2', '')
        
        kml_parts.append('    <Placemark>')
        kml_parts.append(f'      <name>{name}</name>')
        if luas:
            kml_parts.append(f'      <description>Luas: {luas} m²</description>')
        kml_parts.append('      <Polygon>')
        kml_parts.append('        <outerBoundaryIs>')
        kml_parts.append('          <LinearRing>')
        kml_parts.append('            <coordinates>')
        
        # Polygon coordinates: lng,lat (KML order!)
        ring = geom['coordinates'][0]
        for coord in ring:
            lng, lat = coord[0], coord[1]
            kml_parts.append(f'              {lng},{lat},0')
        
        kml_parts.append('            </coordinates>')
        kml_parts.append('          </LinearRing>')
        kml_parts.append('        </outerBoundaryIs>')
        kml_parts.append('      </Polygon>')
        kml_parts.append('    </Placemark>')
    
    kml_parts.append('  </Document>')
    kml_parts.append('</kml>')
    
    kml_bytes = '\n'.join(kml_parts).encode('utf-8')
    
    return send_file(
        io.BytesIO(kml_bytes),
        mimetype='application/vnd.google-earth.kml+xml',
        as_attachment=True,
        download_name=filename
    )

@app.route('/api/search', methods=['GET'])
def search_location():
    """Proxy Nominatim geocoding search (avoid CORS issues client-side)."""
    q = request.args.get('q', '')
    if not q or len(q) < 3:
        return jsonify({'error': 'Query too short'}), 400
    
    # Rate limit ourselves
    now = time.time()
    ip = request.remote_addr or 'unknown'
    last = _request_times.get(ip, 0)
    if now - last < 0.5:
        return jsonify({'error': 'Terlalu cepat. Tunggu sebentar.'}), 429
    _request_times[ip] = now
    
    try:
        import urllib.request
        import urllib.parse
        
        url = ('https://nominatim.openstreetmap.org/search?'
               f'q={urllib.parse.quote(q)}&format=json&limit=8&countrycodes=id'
               '&accept-language=id')
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'OSSPolygonEditor/1.0 (callunk.my.id)'
        })
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode('utf-8'))
        
        formatted = [{
            'display_name': r['display_name'],
            'lat': float(r['lat']),
            'lon': float(r['lon']),
            'type': r.get('type', ''),
            'class': r.get('class', '')
        } for r in results]
        
        return jsonify(formatted)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-id', methods=['GET'])
def search_location_id():
    """Search with stronger Indonesia bias."""
    q = request.args.get('q', '')
    if not q or len(q) < 3:
        return jsonify({'error': 'Query too short'}), 400
    
    now = time.time()
    ip = request.remote_addr or 'unknown'
    last = _request_times.get(ip, 0)
    if now - last < 0.5:
        return jsonify({'error': 'Terlalu cepat.'}), 429
    _request_times[ip] = now
    
    try:
        import urllib.request
        import urllib.parse
        
        url = ('https://nominatim.openstreetmap.org/search?'
               f'q={urllib.parse.quote(q + ", Indonesia")}&format=json&limit=10'
               '&accept-language=id')
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'OSSPolygonEditor/1.0 (callunk.my.id)'
        })
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode('utf-8'))
        
        formatted = [{
            'display_name': r['display_name'],
            'lat': float(r['lat']),
            'lon': float(r['lon']),
            'type': r.get('type', ''),
            'class': r.get('class', '')
        } for r in results]
        
        return jsonify(formatted)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reverse', methods=['GET'])
def reverse_geocode():
    """Get address from lat/lng."""
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    if not lat or not lon:
        return jsonify({'error': 'Need lat & lon'}), 400
    
    try:
        import urllib.request
        import urllib.parse
        
        url = (f'https://nominatim.openstreetmap.org/reverse?'
               f'lat={lat}&lon={lon}&format=json&accept-language=id')
        
        req = urllib.request.Request(url, headers={
            'User-Agent': 'OSSPolygonEditor/1.0 (callunk.my.id)'
        })
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        
        display = result.get('display_name', '')
        address = result.get('address', {})
        
        return jsonify({
            'display_name': display,
            'road': address.get('road', ''),
            'village': address.get('village', '') or address.get('town', '') or address.get('city', ''),
            'city': address.get('city', '') or address.get('county', ''),
            'state': address.get('state', ''),
            'postcode': address.get('postcode', '')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    # For dev/testing only. Production uses gunicorn.
    app.run(host='127.0.0.1', port=5008, debug=False)
