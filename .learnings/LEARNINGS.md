# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20250511-001] best_practice

**Logged**: 2026-05-11T14:50:00Z
**Priority**: high
**Status**: promoted
**Area**: debug

### Summary
Always add server-side logging FIRST before guessing what's wrong client-side.

### Details
Debugged filebox upload issue for hours without logs. Added Flask debug logging later and immediately found the JS temporal dead zone bug. The user specifically said "debug dari log dulu, baru fix" — wasted many tokens on speculation instead of instrumentation.

### Suggested Action
When debugging any issue: add a server-side logging endpoint FIRST, then reproduce the issue, then check logs. Don't guess.

### Metadata
- Source: user_feedback
- Tags: debugging, logging, efficiency

---

## [LRN-20250511-002] correction

**Logged**: 2026-05-11T14:50:00Z
**Priority**: high
**Status**: promoted
**Area**: frontend

### Summary
JavaScript `const` declarations used before their declaration line cause ReferenceError (temporal dead zone), silently breaking all subsequent code.

### Details
In filebox `templates/index.html`, `const fileInput` and `const uploadForm` were used in event listener registration BEFORE being declared. This caused the entire script to crash silently at parse time, preventing ALL event handlers (upload, drag-drop, toast) from being attached. Upload worked via curl (no JS) but not via browser.

### Suggested Action
Always declare `const`/`let` variables at the TOP of their scope before any usage. Better yet, use `document.getElementById()` inline instead of cached const refs if order isn't guaranteed.

### Metadata
- Source: error
- Related Files: App/filebox/templates/index.html
- Tags: javascript, temporal-dead-zone, const

---

## [LRN-20250511-003] correction

**Logged**: 2026-05-11T14:50:00Z
**Priority**: high
**Status**: promoted
**Area**: frontend

### Summary
Unbalanced braces (`{` without `}`) in if blocks cause JavaScript to fail silently. Always validate brace balance.

### Details
The `if (dropZone) {` block was opened but never closed with `}`. This caused all code after it (showToast function, urlParams, etc.) to be inside an unclosed block. While `new Function()` test passed, browser behavior was unpredictable.

### Suggested Action
After editing JS, count brace balance (`grep -o '{' | wc -l` vs `grep -o '}' | wc -l`). Zero diff means balanced.

### Metadata
- Source: error
- Tags: javascript, syntax, braces

---

## [LRN-20250511-004] best_practice

**Logged**: 2026-05-11T14:50:00Z
**Priority**: medium
**Status**: pending
**Area**: debug

### Summary
For client-side logging that must work in all browsers (including WebViews), use `new Image().src = url` instead of fetch/XHR/sendBeacon.

### Details
Tried `console.log`, `XMLHttpRequest`, `fetch`, `sendBeacon`, and `Blob` — none sent data from the user's browser. Only `new Image().src = url` with GET parameters worked reliably across all browsers and WebViews because it's the oldest, most compatible technique.

### Suggested Action
Default to Image beacon (`new Image().src = '/log?data=' + encodeURIComponent(json)`) for any cross-browser logging. The server endpoint must accept GET and return a 1x1 GIF.

### Metadata
- Source: user_feedback
- Tags: logging, cross-browser, image-beacon

---

## [LRN-20250511-005] best_practice

**Logged**: 2026-05-11T14:50:00Z
**Priority**: medium
**Status**: pending
**Area**: debug

### Summary
Make ONE small change at a time and test before making the next change. Don't rewrite entire files or make batch changes.

### Details
Made many simultaneous changes to the fishing app (sonar, themes, GPS logging, zoom) which introduced multiple bugs that were hard to isolate. Each change should have been tested independently. Reverting to backup and re-applying changes one-by-one would have saved time.

### Suggested Action
For any multi-feature update: make one change → test → commit/memoize → next change.

### Metadata
- Source: user_feedback
- Tags: workflow, incremental-changes

---

## [LRN-20250511-006] knowledge_gap

**Logged**: 2026-05-11T14:50:00Z
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
When a process keeps restarting after being killed, check for systemd services (`systemctl list-units | grep <name>`).

### Details
Killed filebox Flask processes with `kill -9` but they kept reappearing. Found `filebox.service` in systemd with `Restart=always`. The service was running Flask dev server (`python3 app.py`) instead of gunicorn. Had to update the service file to use gunicorn.

### Suggested Action
Before killing a process: `systemctl status <service_name>` to check if it's managed by systemd. If modifying a systemd service: `systemctl daemon-reload` after changing the file.

### Metadata
- Source: error
- Tags: systemd, flask, gunicorn, process-management
