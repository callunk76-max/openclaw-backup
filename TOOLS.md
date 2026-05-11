# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## Web Scraping Protocol (per Callunk)

When asked to scrape/extract data from any website, ALWAYS use the **stealth-browser + Tavily search combo**:
1. **Tavily Search** first — to find relevant pages, URLs, and summary info
2. **Stealth Browser** (puppeteer-extra + stealth plugin) — to access blocked/protected sites and extract detailed data
3. Cross-reference results from both for completeness

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

Add whatever helps you do your job. This is your cheat sheet.

## Logging: Image Beacon (most reliable)

For client-side logging that must work in ALL browsers (including WebViews):

```javascript
// Client-side (JS):
new Image().src = '/api/log?' + encodeURIComponent(JSON.stringify({msg: 'hello'}));
```

```python
# Server-side (Flask):
@app.route('/api/log', methods=['GET'])
def log():
    data = json.loads(request.args.get('d', '{}'))
    with open('/tmp/debug.log', 'a') as f:
        f.write(json.dumps(data) + '\n')
    # Return 1x1 transparent GIF
    return app.response_class(b'GIF89a\x01\x00...', mimetype='image/gif')
```

**Why**: `fetch()`, `XMLHttpRequest`, `sendBeacon`, and `Blob` all fail in some WebViews. Image beacon works everywhere since it was added in 1996.

## Flask Dev Server vs Gunicorn

- **Flask dev server** (`python3 app.py`, `debug=True`): single-threaded, will hang on file uploads. Never use in production.
- **Gunicorn** (`gunicorn -w 2 -b 127.0.0.1:5007 app:app`): multi-worker, handles concurrent requests.
- Always check for systemd services before killing processes: `systemctl status <name>`
