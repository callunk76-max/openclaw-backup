import re

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix table font size
content = content.replace('<table class="w-full text-left border-collapse">', '<table class="w-full text-left border-collapse text-xs">')
content = content.replace('<th class="p-4 text-xs', '<th class="p-3 text-[10px]')
content = content.replace('<td class="p-4', '<td class="p-3')
content = content.replace('text-sm text-slate-500 font-medium', 'text-xs text-slate-500 font-medium')
content = content.replace('text-sm text-slate-600', 'text-xs text-slate-600')
content = content.replace('text-sm font-bold text-slate-700', 'text-xs font-bold text-slate-700')

# Fix modal popup structure
old_modal = """                            html += `
                            <div class="bg-emerald-50 border border-emerald-100 p-4 rounded-xl text-sm text-slate-700 space-y-3 relative">
                                <div class="flex flex-wrap gap-2 text-xs font-bold">
                                    <span class="px-2 py-1 bg-emerald-200 text-emerald-800 rounded-lg">Status: ${r['Status Paket'] || '-'}</span>
                                    <span class="px-2 py-1 bg-white border border-slate-200 rounded-lg text-slate-600">Tahun ${r['Tahun Anggaran'] || '-'}</span>
                                    <span class="px-2 py-1 bg-white border border-slate-200 rounded-lg text-slate-600">${r['Sumber Transaksi'] || '-'}</span>
                                </div>
                                <div class="grid grid-cols-1 gap-1 mt-2">
                                    <div class="flex flex-col"><span class="text-[10px] uppercase text-slate-400 font-bold">Kode RUP</span> <span class="font-mono">${r['Kode RUP'] || '-'}</span></div>
                                    <div class="flex flex-col"><span class="text-[10px] uppercase text-slate-400 font-bold">Kode Paket</span> <span class="font-mono">${r['Kode Paket'] || '-'}</span></div>
                                </div>
                                ${warningBadges}
                                <div class="pt-2 border-t border-emerald-200/50 mt-2">
                                    <p class="text-[10px] uppercase text-emerald-600 font-bold mb-1">Data Realisasi / Penyedia</p>
                                    <p class="font-bold text-slate-800 text-base">${r['Nama Penyedia'] || 'Belum Ada / Swakelola'}</p>
                                    <p class="font-bold text-emerald-700 text-lg mt-1">Rp ${valRp}</p>
                                </div>
                            </div>
                            `;"""

new_modal = """                            const penyedia = r['Nama Penyedia'] || 'Penyedia Tidak Diketahui';
                            const status = r['Status Paket'] || 'Selesai';
                            const tahun = r['Tahun Anggaran'] || '2026';
                            const sumber = r['Sumber Transaksi'] || 'E-Katalog APBD PDN';

                            html += `
                            <div class="bg-emerald-50/50 border border-emerald-100 p-4 rounded-xl text-sm text-slate-700 space-y-3 relative">
                                <div class="flex justify-between items-start gap-2">
                                    <h4 class="font-bold text-slate-800 text-base flex-1 leading-snug uppercase">${penyedia}</h4>
                                </div>
                                <div class="text-xl font-black text-emerald-600">Rp ${valRp}</div>
                                <div class="flex flex-wrap gap-2 text-[10px] font-bold mt-1">
                                    <span class="px-2 py-0.5 bg-slate-200 text-slate-600 rounded">Status: ${status}</span>
                                    <span class="px-2 py-0.5 bg-slate-200 text-slate-600 rounded">Tahun ${tahun}</span>
                                    <span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded border border-blue-200">${sumber}</span>
                                </div>
                                <div class="grid grid-cols-1 gap-1 mt-2 pt-2 border-t border-emerald-200/50">
                                    <div class="flex flex-col"><span class="text-[10px] uppercase text-slate-400 font-bold">Kode RUP</span> <span class="font-mono text-xs">${r['Kode RUP'] || '-'}</span></div>
                                    <div class="flex flex-col"><span class="text-[10px] uppercase text-slate-400 font-bold">Kode Paket</span> <span class="font-mono text-xs">${r['Kode Paket'] || '-'}</span></div>
                                </div>
                                ${warningBadges}
                            </div>
                            `;"""

content = content.replace(old_modal, new_modal)

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done fixing HTML")
