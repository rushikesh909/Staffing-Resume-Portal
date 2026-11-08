import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os

def md_to_docx(md_path, docx_path):
    with open(md_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    doc = docx.Document()

    # Page margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    in_code_block = False
    code_lines = []

    for line in lines:
        raw = line.rstrip("\r\n")

        # Code block toggle
        if raw.startswith("```"):
            if in_code_block:
                # Flush code block
                p = doc.add_paragraph()
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.left_indent = Inches(0.2)
                run = p.add_run("\n".join(code_lines))
                run.font.name = "Consolas"
                run.font.size = Pt(8.5)
                run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
                code_lines = []
                in_code_block = False
            else:
                in_code_block = True
                code_lines = []
            continue

        if in_code_block:
            code_lines.append(raw)
            continue

        # Header 1
        if raw.startswith("# "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(raw[2:])
            run.bold = True
            run.font.size = Pt(20)
            run.font.color.rgb = RGBColor(0x99, 0x1B, 0x1B) # Crimson
            continue

        # Header 2
        if raw.startswith("## "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(12)
            p.paragraph_format.space_after = Pt(4)
            run = p.add_run(raw[3:])
            run.bold = True
            run.font.size = Pt(15)
            run.font.color.rgb = RGBColor(0x1E, 0x29, 0x3B)
            continue

        # Header 3
        if raw.startswith("### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(raw[4:])
            run.bold = True
            run.font.size = Pt(12)
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            continue

        # Header 4
        if raw.startswith("#### "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(raw[5:])
            run.bold = True
            run.font.size = Pt(10.5)
            run.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
            continue

        # Bullet list
        if raw.startswith("- ") or raw.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            run = p.add_run(raw[2:])
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            continue

        # Numbered list
        if len(raw) > 2 and raw[0].isdigit() and raw[1:3] in (". ", ") "):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.left_indent = Inches(0.2)
            run = p.add_run(raw)
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)
            continue

        # Horizontal rule
        if raw.strip() == "---":
            continue

        # Normal text
        if raw.strip():
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(3)
            run = p.add_run(raw)
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

    doc.save(docx_path)
    print(f"Generated {docx_path} ({os.path.getsize(docx_path)} bytes)")

if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    md = os.path.join(root, "Technical-Design-Document.md")
    docx_file = os.path.join(root, "Technical-Design-Document.docx")
    md_to_docx(md, docx_file)
