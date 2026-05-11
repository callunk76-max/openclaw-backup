# Errors

Command failures and integration errors.

---

## [ERR-20250511-001] Flask dev server vs gunicorn

**Logged**: 2026-05-11T14:50:00Z
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
FileBox app was running Flask dev server (`python3 app.py` with `debug=True`) instead of gunicorn. Single-threaded dev server caused uploads to hang.

### Error
```
# ps aux showed:
/usr/bin/python3 /root/.openclaw/workspace/App/filebox/app.py
# Not:
gunicorn -w 2 ... app:app
```

### Context
- App: FileBox Flask app on port 5007
- Started via systemd service (`/etc/systemd/system/filebox.service`)
- Original config: `ExecStart=/usr/bin/python3 app.py`
- Flask dev server is single-threaded, not suitable for file uploads

### Suggested Fix
Updated to:
```
ExecStart=/usr/local/bin/gunicorn -w 2 -b 127.0.0.1:5007 ... app:app
WorkingDirectory=/root/.openclaw/workspace/App/filebox
```

### Resolution
- **Resolved**: 2026-05-11T13:10:00Z
- **Notes**: Changed systemd service to use gunicorn with 2 workers

### Metadata
- Reproducible: yes
- Related Files: /etc/systemd/system/filebox.service, App/filebox/app.py

---

## [ERR-20250511-002] JS temporal dead zone

**Logged**: 2026-05-11T14:50:00Z
**Priority**: high
**Status**: resolved
**Area**: frontend

### Summary
`const fileInput` used before declaration line, causing ReferenceError. File upload form never submitted.

### Error
```
fileInput.addEventListener('change', function() {
  // ...
});

const fileInput = document.getElementById('fileInput');  // TOO LATE!
```

### Context
- Introduced when fixing drag-drop in filebox template
- Moved `const fileInput` below its usage
- `const` has temporal dead zone — accessing before initialization throws ReferenceError

### Suggested Fix
Move `const` declarations above their first usage:
```
const fileInput = document.getElementById('fileInput');
fileInput.addEventListener('change', function() { ... });
```

### Resolution
- **Resolved**: 2026-05-11T13:37:00Z
- **Notes**: Moved const declarations above event listener registrations

### Metadata
- Reproducible: yes
- Related Files: App/filebox/templates/index.html

---

## [ERR-20250511-003] Unbalanced braces

**Logged**: 2026-05-11T14:50:00Z
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
`if (dropZone) {` block missing closing `}` — 17 opens vs 16 closes.

### Error
```
if (dropZone) {
  // ... lots of code ...
  // Missing closing brace!
  
  // Toast helper
  function showToast(msg) { ... }
```

### Context
- Introduced when splitting the drag-drop code into an `if (dropZone)` guard
- Forgot to add the closing `}` before the `// Toast helper` comment

### Suggested Fix
Always count braces after editing JS blocks: `opens=$(grep -o '{' file.js | wc -l)` vs `closes=$(grep -o '}' file.js | wc -l)`

### Resolution
- **Resolved**: 2026-05-11T13:43:00Z
- **Notes**: Added missing closing brace

### Metadata
- Reproducible: yes
- Related Files: App/filebox/templates/index.html
