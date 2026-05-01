from flask import Flask, render_template, jsonify, request
import requests
import json
import time
from functools import lru_cache

app = Flask(__name__)

GEONODE_URL = "https://geoportal.bulukumbakab.go.id"
API_URL = f"{GEONODE_URL}/api/v2"
GEOSERVER_URL = f"{GEONODE_URL}/geoserver"

CACHE_TTL = 300  # 5 minutes
_cache = {}

def cached_get(url, params=None, ttl=CACHE_TTL):
    key = f"{url}:{json.dumps(params or {}, sort_keys=True)}"
    now = time.time()
    if key in _cache and now - _cache[key]['time'] < ttl:
        return _cache[key]['data']
    try:
        resp = requests.get(url, params=params, timeout=15, verify=False)
        data = resp.json() if resp.status_code == 200 else None
        _cache[key] = {'data': data, 'time': now}
        return data
    except:
        return None

def get_dataset_title(ds):
    return ds.get('title') or ds.get('name', 'Unknown')

def get_dataset_owner(ds):
    owner = ds.get('owner', {})
    return owner.get('username', 'Unknown') if owner else 'Unknown'

def get_dataset_abstract(ds):
    abstract = ds.get('abstract') or ds.get('raw_abstract') or 'Tidak ada deskripsi'
    return abstract[:200] + '...' if len(abstract) > 200 else abstract

@app.route('/')
def index():
    return render_template('index.html',
        geonode_url=GEONODE_URL,
        geoserver_url=GEOSERVER_URL
    )

@app.route('/datasets')
def datasets():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')

    params = {'page': page, 'page_size': 20}
    if search:
        params['q'] = search
    if category:
        params['category__identifier'] = category

    data = cached_get(f"{API_URL}/datasets/", params)
    if not data:
        return jsonify({'error': 'Gagal mengambil data'}), 500

    return render_template('datasets.html',
        datasets=data.get('datasets', []),
        total=data.get('total', 0),
        page=page,
        search=search,
        category=category,
        total_pages=max(1, -(-data.get('total', 0) // 20)),
        geonode_url=GEONODE_URL,
        geoserver_url=GEOSERVER_URL
    )

@app.route('/dataset/<pk>')
def dataset_detail(pk):
    data = cached_get(f"{API_URL}/datasets/{pk}")
    if not data:
        return render_template('dataset_detail.html',
            dataset=None,
            error="Dataset tidak ditemukan",
            geonode_url=GEONODE_URL,
            geoserver_url=GEOSERVER_URL
        )
    # GeoNode wraps single dataset response in 'dataset' key
    ds = data.get('dataset', data)
    return render_template('dataset_detail.html',
        dataset=ds,
        geonode_url=GEONODE_URL,
        geoserver_url=GEOSERVER_URL
    )

@app.route('/api/datasets')
def api_datasets():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    params = {'page': page, 'page_size': 12}
    if search: params['q'] = search
    if category: params['category__identifier'] = category
    data = cached_get(f"{API_URL}/datasets/", params)
    if not data:
        return jsonify({'error': 'Gagal mengambil data'}), 500
    datasets = data.get('datasets', [])
    results = []
    for ds in datasets:
        owner = ds.get('owner', {}) or {}
        cat = ds.get('category', {}) or {}
        extent = ds.get('extent', {}) or {}
        coords = extent.get('coords', [])
        results.append({
            'pk': ds.get('pk'),
            'title': get_dataset_title(ds),
            'name': ds.get('name'),
            'abstract': get_dataset_abstract(ds),
            'owner': owner.get('username', 'Unknown'),
            'category': cat.get('gn_description', 'General'),
            'thumbnail': ds.get('thumbnail_url', ''),
            'created': ds.get('created', ''),
            'extent': coords,
            'download_url': f"{GEONODE_URL}{ds.get('download_urls', [{}])[0].get('url', '')}" if ds.get('download_urls') else '',
            'wms_url': f"{GEOSERVER_URL}/ows?service=WMS&version=1.3.0&request=GetMap&layers=geonode:{ds.get('name', '')}&format=image/png&transparent=true"
        })
    return jsonify({
        'datasets': results,
        'total': data.get('total', 0),
        'page': page,
        'total_pages': max(1, -(-data.get('total', 0) // 12))
    })

@app.route('/api/dataset/<pk>')
def api_dataset_detail(pk):
    data = cached_get(f"{API_URL}/datasets/{pk}")
    if not data:
        return jsonify({'error': 'Not found'}), 404
    # GeoNode wraps single dataset in 'dataset' key
    ds = data.get('dataset', data)
    extent = ds.get('extent', {}) or {}
    coords = extent.get('coords', [])
    cat = ds.get('category', {}) or {}
    owner_meta = ds.get('owner', {}) or {}
    links = ds.get('download_urls', [])
    keywords_list = ds.get('keywords', [])
    return jsonify({
        'pk': ds.get('pk'),
        'title': get_dataset_title(ds),
        'name': ds.get('name'),
        'abstract': ds.get('abstract', ''),
        'owner': owner_meta.get('username', 'Unknown'),
        'category': cat.get('gn_description', 'General'),
        'thumbnail': ds.get('thumbnail_url', ''),
        'created': ds.get('created', ''),
        'extent': coords,
        'subtype': ds.get('subtype', ''),
        'keywords': [k.get('name', '') for k in keywords_list],
        'regions': [r.get('name', '') for r in (ds.get('regions') or [])],
        'download_url': f"{GEONODE_URL}{links[0].get('url', '')}" if links else '',
        'embed_url': f"{GEONODE_URL}{ds.get('embed_url', '')}",
        'wms_url': f"{GEOSERVER_URL}/ows?service=WMS&version=1.3.0&request=GetMap&layers=geonode:{ds.get('name', '')}&format=image/png&transparent=true",
        'geojson_url': f"{GEOSERVER_URL}/ows?service=WFS&version=1.0.0&request=GetFeature&typename=geonode:{ds.get('name', '')}&outputFormat=json&srsName=EPSG:4326",
        'shapefile_url': f"{GEOSERVER_URL}/ows?service=WFS&version=1.0.0&request=GetFeature&typename=geonode:{ds.get('name', '')}&outputFormat=SHAPE-ZIP",
        'detail_url': ds.get('detail_url', '')
    })

@app.route('/api/categories')
def api_categories():
    data = cached_get(f"{API_URL}/categories/", {'page_size': 50})
    if not data:
        return jsonify({'categories': []})
    cats = []
    for c in data.get('categories', []):
        if c.get('count', 0) > 0:
            cats.append({
                'id': c.get('identifier'),
                'name': c.get('gn_description', c.get('identifier')),
                'count': c.get('count', 0)
            })
    return jsonify({'categories': cats})

@app.route('/api/owners')
def api_owners():
    data = cached_get(f"{API_URL}/owners/", {'page_size': 100})
    if not data:
        return jsonify({'owners': []})
    owners = []
    for o in data.get('owners', []):
        owners.append({
            'username': o.get('username'),
            'email': o.get('email', '')
        })
    return jsonify({'owners': owners})

@app.route('/api/stats')
def api_stats():
    data = cached_get(f"{API_URL}/datasets/", {'page_size': 1})
    total = data.get('total', 0) if data else 0
    cat_data = cached_get(f"{API_URL}/categories/", {'page_size': 50})
    categories = []
    if cat_data:
        for c in cat_data.get('categories', []):
            if c.get('count', 0) > 0:
                categories.append({
                    'name': c.get('gn_description', c.get('identifier')),
                    'count': c.get('count', 0)
                })
    map_data = cached_get(f"{API_URL}/maps/")
    total_maps = 0
    if map_data:
        total_maps = map_data.get('total', 0)
    return jsonify({
        'total_datasets': total,
        'total_maps': total_maps,
        'categories': categories
    })

@app.route('/flood')
def flood_view():
    return render_template('flood.html',
        geonode_url=GEONODE_URL,
        geoserver_url=GEOSERVER_URL
    )

@app.route('/flood3d')
def flood3d_view():
    return render_template('flood3d.html',
        geonode_url=GEONODE_URL,
        geoserver_url=GEOSERVER_URL
    )

@app.route('/maps')
def maps_view():
    return render_template('maps.html',
        geonode_url=GEONODE_URL,
        geoserver_url=GEOSERVER_URL
    )

@app.context_processor
def inject_prefix():
    return dict(prefix='/geo')

if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # Prefix handled by nginx rewrite, no middleware needed
    app.run(host="127.0.0.1", port=5006)
