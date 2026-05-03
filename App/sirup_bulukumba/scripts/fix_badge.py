import re

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'const tahun = r\[\'Tahun Anggaran\'\] \|\| \'2026\';\s*const sumber = r\[\'Sumber Transaksi\'\] \|\| \'E-Katalog APBD PDN\';', re.DOTALL)

new_vars = """const tahun = r['Tahun Anggaran'] || '2026';
                            const sumber = r['Sumber Dana'] || r['Sumber Transaksi'] || 'APBD';
                            const isPDN = (valRp !== '0') ? '<span class="px-2 py-1 bg-green-50 text-green-700 rounded border border-green-200">PDN: Ya</span>' : '';"""

content = pattern.sub(new_vars, content)

pattern2 = re.compile(r'<span class="px-2 py-1 bg-blue-50 text-blue-700 rounded border border-blue-200">\${sumber}</span>', re.DOTALL)
new_badges = """<span class="px-2 py-1 bg-blue-50 text-blue-700 rounded border border-blue-200">${sumber}</span>
                                    ${isPDN}"""

content = pattern2.sub(new_badges, content)

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print("Done fixing badges")
