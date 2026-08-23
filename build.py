#!/usr/bin/env python3
import os

b64_data = {}
for fn in os.listdir('b64_cache'):
    if fn.endswith('.b64'):
        key = fn.replace('.b64', '')
        with open(f'b64_cache/{fn}', 'r') as f:
            b64_data[key] = f.read().strip()

with open('index_template.html', 'r', encoding='utf-8') as f:
    html = f.read()

pharma_jpgs = sorted([k for k in b64_data if k.startswith('pharma_') and k.endswith('_batch')])
fomed_jpgs = sorted([k for k in b64_data if k.startswith('fomed_') and k.endswith('_batch')])

# JS variables
js_vars = []
for key in sorted(pharma_jpgs + fomed_jpgs):
    js_vars.append(f'        const {key} = "data:image/jpeg;base64,{b64_data[key]}";')
for key in ['pharma_tana', 'fomed_tana', 'pharma_arranged', 'fomed_arranged']:
    if key in b64_data:
        js_vars.append(f'        const {key}_pdf = "data:application/pdf;base64,{b64_data[key]}";')
js_block = '\n'.join(js_vars)

image_map_entries = []
for key in sorted(pharma_jpgs + fomed_jpgs):
    image_map_entries.append(f"            '{key}': {key},")
image_map_block = '\n'.join(image_map_entries)

# Pharma
pharma_cards = []
for key in pharma_jpgs:
    batch = key.replace('pharma_', '').replace('_', ' ')
    pharma_cards.append(f'<div class="batch-card" data-img="{key}"><div class="batch-card-inner"><span class="batch-icon">📄</span><span class="batch-name">{batch.title()}</span></div></div>')

pharma_batchwise = f'''
        <section id="pharma-batchwise" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Pharmacology › Previous 2nd Assessment Questions</span> › Batchwise</div>
            <h2>🔬 Pharmacology - Batchwise Questions</h2>
            <p style="color:#666;margin-bottom:20px;">Select a batch to view the question paper</p>
            <div class="batch-grid">{"".join(pharma_cards)}</div>
        </section>'''

pharma_sections = []
for key in pharma_jpgs:
    batch = key.replace('pharma_', '').replace('_', ' ')
    dl = f'Pharmacology_{batch.replace(" ", "_")}.jpg'
    pharma_sections.append(f'''
        <section id="{key}" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="pharma-batchwise">pdf › Pharmacology › Previous 2nd Assessment › Batchwise</span> › {batch.title()}</div>
            <h2>Pharmacology - {batch.title()}</h2>
            <div class="image-viewer">
                <img id="{key}_img" src="" alt="Pharmacology {batch}">
                <p>Uploaded by Admin</p>
                <div class="download-row">
                    <button class="btn-download" data-imgkey="{key}" data-dlname="{dl}">⬇️ Download</button>
                    <button class="btn-back" data-section="pharma-batchwise">← Back to list</button>
                </div>
            </div>
        </section>''')

pharma_arranged = '''
        <section id="pharma-arranged" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Pharmacology › Previous 2nd Assessment Questions</span> › Arranged</div>
            <h2>Pharmacology - Arranged Questions</h2>
            <div class="image-viewer">
                <p style="margin-bottom:15px;color:#333;font-size:15px;">📄 MBBS Pharmacology Topicwise Questions</p>
                <div class="download-row">
                    <button class="btn-download" data-pdfkey="pharma_arranged" data-dlname="MBBS_Pharmacology_Topicwise_Questions.pdf">⬇️ Download PDF</button>
                </div>
            </div>
        </section>'''

pharma_tana = '''
        <section id="pharma-tana" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Pharmacology</span> › Tana Question</div>
            <h2>Pharmacology - Tana Question</h2>
            <div class="image-viewer">
                <p style="margin-bottom:15px;color:#333;font-size:15px;">📄 Pharmacology Tana Questions</p>
                <div class="download-row">
                    <button class="btn-download" data-pdfkey="pharma_tana" data-dlname="Pharmacology_Tana_Questions.pdf">⬇️ Download PDF</button>
                </div>
            </div>
        </section>'''

pharma_slides = '''
        <section id="pharma-slides" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Pharmacology</span> › Class slides, curriculum and others</div>
            <h2>Pharmacology - Class Slides, Curriculum & Others</h2>
            <div class="drive-section">
                <p>Access Pharmacology class slides, curriculum materials and other resources on Google Drive.</p>
                <a href="https://drive.google.com/drive/folders/1uzN0IG65yVPiEcH8XKppxvy0HQs0aWqn" target="_blank" class="btn-drive">📁 Open in Google Drive</a>
            </div>
        </section>'''

# FoMed
fomed_cards = []
for key in fomed_jpgs:
    batch = key.replace('fomed_', '').replace('_', ' ')
    fomed_cards.append(f'<div class="batch-card" data-img="{key}"><div class="batch-card-inner"><span class="batch-icon">📄</span><span class="batch-name">{batch.title()}</span></div></div>')

fomed_batchwise = f'''
        <section id="fomed-batchwise" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Forensic Medicine › Previous 2nd Assessment Questions</span> › Batchwise</div>
            <h2>⚖️ Forensic Medicine - Batchwise Questions</h2>
            <p style="color:#666;margin-bottom:20px;">Select a batch to view the question paper</p>
            <div class="batch-grid">{"".join(fomed_cards)}</div>
        </section>'''

fomed_sections = []
for key in fomed_jpgs:
    batch = key.replace('fomed_', '').replace('_', ' ')
    dl = f'Forensic_Medicine_{batch.replace(" ", "_")}.jpg'
    fomed_sections.append(f'''
        <section id="{key}" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="fomed-batchwise">pdf › Forensic Medicine › Previous 2nd Assessment › Batchwise</span> › {batch.title()}</div>
            <h2>Forensic Medicine - {batch.title()}</h2>
            <div class="image-viewer">
                <img id="{key}_img" src="" alt="Forensic Medicine {batch}">
                <p>Uploaded by Admin</p>
                <div class="download-row">
                    <button class="btn-download" data-imgkey="{key}" data-dlname="{dl}">⬇️ Download</button>
                    <button class="btn-back" data-section="fomed-batchwise">← Back to list</button>
                </div>
            </div>
        </section>''')

fomed_arranged = '''
        <section id="fomed-arranged" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Forensic Medicine › Previous 2nd Assessment Questions</span> › Arranged</div>
            <h2>Forensic Medicine - Arranged Questions</h2>
            <div class="image-viewer">
                <p style="margin-bottom:15px;color:#333;font-size:15px;">📄 Forensic Medicine Categorized Questions</p>
                <div class="download-row">
                    <button class="btn-download" data-pdfkey="fomed_arranged" data-dlname="Forensic_Medicine_Categorized_Questions.pdf">⬇️ Download PDF</button>
                </div>
            </div>
        </section>'''

fomed_tana = '''
        <section id="fomed-tana" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Forensic Medicine</span> › Tana Question</div>
            <h2>Forensic Medicine - Tana Question</h2>
            <div class="image-viewer">
                <p style="margin-bottom:15px;color:#333;font-size:15px;">📄 Forensic Medicine Tana Question</p>
                <div class="download-row">
                    <button class="btn-download" data-pdfkey="fomed_tana" data-dlname="Forensic_Medicine_Tana_Question.pdf">⬇️ Download PDF</button>
                </div>
            </div>
        </section>'''

fomed_slides = '''
        <section id="fomed-slides" class="section">
            <div class="breadcrumb"><span class="crumb-link" data-section="none">pdf › Forensic Medicine</span> › Class slides, curriculum and others</div>
            <h2>Forensic Medicine - Class Slides, Curriculum & Others</h2>
            <div class="drive-section">
                <p>Access Forensic Medicine class slides, curriculum materials and other resources on Google Drive.</p>
                <a href="https://drive.google.com/drive/folders/1ZVeP6xFhg_Of-XpuBjGn0gw9iaATdO7g" target="_blank" class="btn-drive">📁 Open in Google Drive</a>
            </div>
        </section>'''

# Replace
html = html.replace('/*__JS_IMAGE_VARS__*/', js_block)
html = html.replace('/*__IMAGE_MAP__*/', image_map_block)
html = html.replace('/*__PHARMA_LIST__*/', pharma_batchwise)
html = html.replace('/*__PHARMA_SECTIONS__*/', '\n'.join(pharma_sections) + '\n' + pharma_arranged + '\n' + pharma_tana + '\n' + pharma_slides)
html = html.replace('/*__FOMED_LIST__*/', fomed_batchwise)
html = html.replace('/*__FOMED_SECTIONS__*/', '\n'.join(fomed_sections) + '\n' + fomed_arranged + '\n' + fomed_tana + '\n' + fomed_slides)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)
print(f"Done: {len(html)} bytes")
