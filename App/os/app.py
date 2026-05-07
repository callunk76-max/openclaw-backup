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
import struct
import zipfile
import tempfile
from datetime import datetime
import shapefile

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

@app.route('/api/export-shp', methods=['POST'])
def export_shapefile():
    """Export polygon as Shapefile (.shp + .shx + .dbf + .prj)."""
    data = request.get_json()
    if not data or data.get('type') != 'FeatureCollection':
        return jsonify({'error': 'Need valid FeatureCollection'}), 400

    features = data.get('features', [])
    if not features:
        return jsonify({'error': 'No features'}), 400

    geom = features[0].get('geometry', {})
    props = features[0].get('properties', {})
    if geom.get('type') not in ('Polygon', 'MultiPolygon'):
        return jsonify({'error': 'Must be Polygon or MultiPolygon'}), 400

    keterangan = props.get('keterangan_lokasi', 'Lokasi Usaha')
    luas = props.get('luas_m2', 0)
    nama_usaha = props.get('nama_usaha', '')

    coords = geom['coordinates']
    if geom['type'] == 'Polygon':
        parts = [coords]
    else:
        parts = coords

    # Build shapefile in memory
    with tempfile.NamedTemporaryFile(suffix='.shp', delete=False) as tmp_shp:
        shp_path = tmp_shp.name.replace('.shp', '')

    try:
        w = shapefile.Writer(shp_path, shapeType=shapefile.POLYGON)
        w.field('NAMA_USAHA', 'C', size=100)
        w.field('KETERANGAN', 'C', size=250)
        w.field('LUAS_M2', 'N', size=15, decimal=2)

        for ring_list in parts:
            # ring_list[0] = outer ring (list of [lng, lat])
            pts = [(c[0], c[1]) for c in ring_list[0]]
            w.poly([pts])
            w.record(nama_usaha or '-', keterangan or '-', float(luas))

        w.close()

        # Create .prj file (WGS84)
        prj_content = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'

        # Package all into zip
        base = f"polygon_nib_{''.join(c if c.isalnum() or c in '-_' else '_' for c in keterangan)[:40]}"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for ext in ['shp', 'shx', 'dbf']:
                fpath = f'{shp_path}.{ext}'
                if os.path.exists(fpath):
                    zf.write(fpath, f'{base}_{timestamp}.{ext}')
            zf.writestr(f'{base}_{timestamp}.prj', prj_content)

        buf.seek(0)

        return send_file(
            buf,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f'{base}_{timestamp}.zip'
        )

    finally:
        # Cleanup temp files
        for ext in ['shp', 'shx', 'dbf', 'shp.xml']:
            fpath = f'{shp_path}.{ext}'
            if os.path.exists(fpath):
                try:
                    os.unlink(fpath)
                except:
                    pass


@app.route('/api/export-zip', methods=['POST'])
def export_zip():
    """Export all formats (GeoJSON + KML + Shapefile) in one ZIP."""
    data = request.get_json()
    if not data or data.get('type') != 'FeatureCollection':
        return jsonify({'error': 'Need valid FeatureCollection'}), 400

    features = data.get('features', [])
    if not features:
        return jsonify({'error': 'No features'}), 400

    geom = features[0].get('geometry', {})
    props = features[0].get('properties', {})
    if geom.get('type') not in ('Polygon', 'MultiPolygon'):
        return jsonify({'error': 'Must be Polygon or MultiPolygon'}), 400

    keterangan = props.get('keterangan_lokasi', 'Lokasi Usaha')
    safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in keterangan)[:40]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    base = f'nib_{safe_name}_{timestamp}'

    buf = io.BytesIO()

    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 1. GeoJSON
        geojson_output = {
            'type': 'FeatureCollection',
            'metadata': {
                'generated_by': 'oss-polygon-editor',
                'generated_at': datetime.utcnow().isoformat() + 'Z',
                'purpose': 'NIB OSS-RBA',
                'crs': 'EPSG:4326'
            },
            'features': features
        }
        zf.writestr(f'{base}.geojson', json.dumps(geojson_output, indent=2, ensure_ascii=False))

        # 2. KML
        kml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<kml xmlns="http://www.opengis.net/kml/2.2">',
            '  <Document>',
            f'    <name>NIB Polygon - {keterangan}</name>',
            f'    <description>Generated {datetime.utcnow().isoformat()}Z</description>'
        ]
        for feat in features:
            g = feat['geometry']
            p = feat.get('properties', {})
            name = p.get('keterangan_lokasi', 'Lokasi Usaha')
            luas_val = p.get('luas_m2', '')
            kml_parts.append('    <Placemark>')
            kml_parts.append(f'      <name>{name}</name>')
            if luas_val:
                kml_parts.append(f'      <description>Luas: {luas_val} m²</description>')
            kml_parts.append('      <Polygon>')
            kml_parts.append('        <outerBoundaryIs>')
            kml_parts.append('          <LinearRing>')
            kml_parts.append('            <coordinates>')
            for coord in g['coordinates'][0]:
                kml_parts.append(f'              {coord[0]},{coord[1]},0')
            kml_parts.append('            </coordinates>')
            kml_parts.append('          </LinearRing>')
            kml_parts.append('        </outerBoundaryIs>')
            kml_parts.append('      </Polygon>')
            kml_parts.append('    </Placemark>')
        kml_parts.append('  </Document>')
        kml_parts.append('</kml>')
        zf.writestr(f'{base}.kml', '\n'.join(kml_parts))

        # 3. Shapefile
        coords = geom['coordinates']
        if geom['type'] == 'Polygon':
            parts = [coords]
        else:
            parts = coords

        with tempfile.NamedTemporaryFile(suffix='.shp', delete=False) as tmp_shp:
            shp_path = tmp_shp.name.replace('.shp', '')

        try:
            w = shapefile.Writer(shp_path, shapeType=shapefile.POLYGON)
            w.field('NAMA_USAHA', 'C', size=100)
            w.field('KETERANGAN', 'C', size=250)
            w.field('LUAS_M2', 'N', size=15, decimal=2)

            for ring_list in parts:
                pts = [(c[0], c[1]) for c in ring_list[0]]
                w.poly([pts])
                w.record(props.get('nama_usaha', '-'), keterangan or '-', float(props.get('luas_m2', 0)))
            w.close()

            prj_content = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'
            for ext in ['shp', 'shx', 'dbf']:
                fpath = f'{shp_path}.{ext}'
                if os.path.exists(fpath):
                    zf.write(fpath, f'{base}.{ext}')
            zf.writestr(f'{base}.prj', prj_content)
        finally:
            for ext in ['shp', 'shx', 'dbf', 'shp.xml']:
                fpath = f'{shp_path}.{ext}'
                if os.path.exists(fpath):
                    try:
                        os.unlink(fpath)
                    except:
                        pass

        # 4. README
        readme = f"""File Polygon NIB - OSS RBA
{'='*40}

Nama Usaha      : {props.get('nama_usaha', '-')}
Keterangan      : {keterangan}
Luas            : {props.get('luas_m2', 0)} m²
Tanggal Export  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Sumber          : oss-polygon-editor (callunk.my.id/os)

Format dalam ZIP:
- {base}.geojson  → GeoJSON (untuk OSS-RBA)
- {base}.kml      → KML (Google Earth)
- {base}.shp      → Shapefile (ArcGIS/QGIS)
- {base}.shx      → Shape index
- {base}.dbf      → Shape attributes
- {base}.prj      → Proyeksi WGS84

Cara upload ke OSS-RBA:
1. Buka https://oss.go.id
2. Pilih menu Permohonan NIB
3. Upload file ZIP atau GeoJSON di bagian lokasi usaha
4. Pastikan polygon tidak tumpang tindih dengan kawasan hutan
"""
        zf.writestr('README.txt', readme)

    buf.seek(0)

    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'nib_{safe_name}_{timestamp}.zip'
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
