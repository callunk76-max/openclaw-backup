import os
from docx import Document
import pandas as pd

workspace = '/root/.openclaw/workspace'
target_folder = os.path.join(workspace, 'LPSE')

# Convert TXT to DOCX
for file in os.listdir(workspace):
    if file.endswith('.txt'):
        txt_path = os.path.join(workspace, file)
        docx_name = file.replace('.txt', '.docx')
        docx_path = os.path.join(target_folder, docx_name)
        
        doc = Document()
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            doc.add_paragraph(content)
        doc.save(docx_path)
        print(f"Converted {file} to {docx_name}")

# Convert CSV to XLSX
for file in os.listdir(workspace):
    if file.endswith('.csv'):
        csv_path = os.path.join(workspace, file)
        xlsx_name = file.replace('.csv', '.xlsx')
        xlsx_path = os.path.join(target_folder, xlsx_name)
        
        df = pd.read_csv(csv_path)
        df.to_excel(xlsx_path, index=False)
        print(f"Converted {file} to {xlsx_name}")
