import re

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

pattern = re.compile(r'result\.data\.forEach\(r => \{.*?\n\s*\}\);\s*html \+= \'</div>\';', re.DOTALL)

new_foreach = """result.data.forEach(r => {
                            const valRp = r['Total Nilai (Rp)'] ? Number(r['Total Nilai (Rp)']).toLocaleString('id-ID') : '0';
                            const penyedia = r['Nama Penyedia'] || r['Penyedia'] || 'Penyedia Tidak Diketahui';
                            
                            // Check if this realisasi is a strict match or a fallback match
                            const isStrictMatch = (p.id && r['Kode RUP'] && String(p.id) === String(r['Kode RUP']));
                            
                            let warningBadges = '';
                            if (!isStrictMatch) {
                                warningBadges += '<div class="px-2 py-1 mt-2 bg-amber-100 text-amber-800 text-[10px] font-bold rounded border border-amber-200">⚠️ Info: Realisasi ini dicocokkan berdasarkan Nama Paket, bukan Kode RUP (Kode RUP berbeda/kosong).</div>';
                            }
                            
                            let statusBadgeColor = "bg-emerald-200 text-emerald-800";
                            let statusText = r['Status Paket'] || r['Status'] || 'ON PROCESS';
                            if(statusText.toUpperCase() === 'SELESAI') statusBadgeColor = "bg-emerald-200 text-emerald-800";
                            else if(statusText.toUpperCase().includes('BATAL')) statusBadgeColor = "bg-red-200 text-red-800";
                            
                            const tahun = r['Tahun Anggaran'] || '2026';
                            const sumber = r['Sumber Transaksi'] || 'E-Katalog 6.0';
                            
                            html += `
                            <div class="bg-[#f0fdf4] border border-[#d1fae5] p-4 rounded-xl text-sm text-slate-700 space-y-3 relative mb-3">
                                
                                <div class="flex flex-wrap gap-2 text-xs font-bold mb-3">
                                    <span class="px-3 py-1 ${statusBadgeColor} rounded-md">Status: ${statusText}</span>
                                    <span class="px-3 py-1 bg-white border border-slate-200 rounded-md text-slate-600">Tahun ${tahun}</span>
                                    <span class="px-3 py-1 bg-white border border-slate-200 rounded-md text-slate-600">${sumber}</span>
                                </div>
                                
                                <div class="grid grid-cols-1 gap-1 mb-4">
                                    <div class="flex flex-col"><span class="text-[10px] uppercase text-slate-400 font-bold">KODE RUP</span> <span class="font-mono text-xs text-slate-700">${r['Kode RUP'] || p.id || '-'}</span></div>
                                    <div class="flex flex-col mt-2"><span class="text-[10px] uppercase text-slate-400 font-bold">KODE PAKET</span> <span class="font-mono text-xs text-slate-700">${r['Kode Paket'] || '-'}</span></div>
                                </div>
                                
                                <div class="pt-3 border-t border-emerald-100">
                                    <p class="text-[10px] uppercase text-emerald-700 font-bold mb-1">DATA REALISASI / PENYEDIA</p>
                                    <h4 class="font-extrabold text-slate-800 text-base leading-snug uppercase mb-1">${penyedia}</h4>
                                    <div class="text-lg font-black text-emerald-700">Rp ${valRp}</div>
                                </div>
                                
                                ${warningBadges}
                            </div>
                            `;
                        });
                        html += '</div>';"""

content = content.replace("let html = '<h3 class=\"text-xs font-bold text-slate-500 uppercase tracking-wider mb-3\">DATA REALISASI PENYEDIA</h3><div class=\"space-y-4\">';", "let html = '<div>';")
content = pattern.sub(new_foreach, content)

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Modal content replaced to match screenshot.")
