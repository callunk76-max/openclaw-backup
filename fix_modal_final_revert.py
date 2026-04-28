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
                                warningBadges += '<div class="px-2 py-1 mt-2 bg-amber-100 text-amber-800 text-[10px] font-bold rounded border border-amber-200">⚠️ Info: Realisasi dicocokkan berdasarkan Nama Paket (Kode RUP berbeda/kosong).</div>';
                            }
                            
                            let statusBadgeColor = "bg-emerald-100 border-emerald-200 text-emerald-800";
                            let statusText = r['Status Paket'] || r['Status'] || 'ON PROCESS';
                            if(statusText.toUpperCase() === 'SELESAI') statusBadgeColor = "bg-emerald-100 border-emerald-200 text-emerald-800";
                            else if(statusText.toUpperCase().includes('BATAL')) statusBadgeColor = "bg-red-100 border-red-200 text-red-800";
                            
                            const tahun = r['Tahun Anggaran'] || '2026';
                            const sumber = r['Sumber Transaksi'] || 'E-Katalog APBD PDN';
                            
                            html += `
                            <div class="bg-emerald-50/30 border border-emerald-100 p-4 rounded-xl text-sm text-slate-700 space-y-3 relative mb-3 shadow-sm">
                                
                                <div class="mb-1">
                                    <h3 class="text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-1">DATA REALISASI PENYEDIA</h3>
                                    <h4 class="font-extrabold text-slate-800 text-base leading-snug uppercase">${penyedia}</h4>
                                    <div class="text-xl font-black text-emerald-600 mt-1">Rp ${valRp}</div>
                                </div>
                                
                                <div class="flex flex-wrap gap-2 text-[10px] font-bold mt-2">
                                    <span class="px-2 py-1 ${statusBadgeColor} rounded border">Status: ${statusText}</span>
                                    <span class="px-2 py-1 bg-white text-slate-600 rounded border border-slate-200">Tahun ${tahun}</span>
                                    <span class="px-2 py-1 bg-blue-50 text-blue-700 rounded border border-blue-200">${sumber}</span>
                                </div>
                                
                                <div class="grid grid-cols-1 gap-1 mt-3 pt-3 border-t border-emerald-100/70">
                                    <div class="flex flex-col"><span class="text-[10px] uppercase text-slate-400 font-bold">KODE RUP</span> <span class="font-mono text-xs text-slate-600">${r['Kode RUP'] || p.id || '-'}</span></div>
                                    <div class="flex flex-col mt-1"><span class="text-[10px] uppercase text-slate-400 font-bold">KODE PAKET</span> <span class="font-mono text-xs text-slate-600">${r['Kode Paket'] || '-'}</span></div>
                                </div>
                                
                                ${warningBadges}
                            </div>
                            `;
                        });
                        html += '</div>';"""

content = pattern.sub(new_foreach, content)

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed layout correctly this time!")
