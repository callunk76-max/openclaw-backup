import re

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("let html = '<div class=\"space-y-4\">';", "let html = '<h3 class=\"text-xs font-bold text-slate-500 uppercase tracking-wider mb-3\">DATA REALISASI PENYEDIA</h3><div class=\"space-y-4\">';")

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
