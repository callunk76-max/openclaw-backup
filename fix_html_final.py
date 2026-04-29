import re

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Make sure realisasi modal is exactly as requested
old_modal_start = "result.data.forEach(r => {"
old_modal_end = "html += '</div>';"

# We will use regex to replace the entire foreach block inside the fetch
import re
pattern = re.compile(r'result\.data\.forEach\(r => \{.*?\n\s*\}\);\s*html \+= \'</div>\';', re.DOTALL)

new_foreach = """result.data.forEach(r => {
                            const valRp = r['Total Nilai (Rp)'] ? Number(r['Total Nilai (Rp)']).toLocaleString('id-ID') : '0';
                            const penyedia = r['Nama Penyedia'] || r['Penyedia'] || 'Penyedia Tidak Diketahui';
                            const status = r['Status Paket'] || r['Status'] || 'Selesai';
                            const tahun = r['Tahun Anggaran'] || '2026';
                            const sumber = r['Sumber Transaksi'] || 'E-Katalog APBD PDN';
                            
                            html += `
                            <div class="bg-emerald-50/50 border border-emerald-100 p-4 rounded-xl text-sm text-slate-700 space-y-3 relative">
                                <div class="flex justify-between items-start gap-2 mb-1">
                                    <h4 class="font-bold text-slate-800 text-base leading-snug uppercase">${penyedia}</h4>
                                </div>
                                <div class="text-xl font-black text-emerald-600 mb-2">Rp ${valRp}</div>
                                <div class="flex flex-wrap gap-2 text-[10px] font-bold mt-2">
                                    <span class="px-2 py-0.5 bg-slate-200 text-slate-600 rounded">Status: ${status}</span>
                                    <span class="px-2 py-0.5 bg-slate-200 text-slate-600 rounded">Tahun ${tahun}</span>
                                    <span class="px-2 py-0.5 bg-blue-100 text-blue-700 rounded border border-blue-200">${sumber}</span>
                                </div>
                            </div>
                            `;
                        });
                        html += '</div>';"""

content = pattern.sub(new_foreach, content)

with open('/root/.openclaw/workspace/App/sirup_bulukumba/templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Modal content replaced.")
