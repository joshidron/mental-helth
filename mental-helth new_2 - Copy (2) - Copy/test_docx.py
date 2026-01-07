from docx import Document
import os
import sys

# Set UTF-8 encoding for console output
sys.stdout.reconfigure(encoding='utf-8')

files = [f for f in os.listdir('uploads') if f.endswith('.docx')]
latest = max([os.path.join('uploads', f) for f in files], key=os.path.getctime)
print(f"Reading: {latest}")

doc = Document(latest)
count = 0
for i, p in enumerate(doc.paragraphs):
    if p.text.strip() and count < 40:
        print(f"{i}: {p.text[:200]}")
        count += 1
