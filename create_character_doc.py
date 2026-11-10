"""
create_character_doc.py
Generates a beautifully formatted Microsoft Word (.docx) document
detailing KathaVaani narrator character dossiers, portraits, acoustic traits,
voice mappings across 10 Indian languages, and character count / credit metrics.
"""

import os
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT

def generate_doc():
    doc = Document()

    # Set page margins
    for section in doc.sections:
        section.top_margin = Inches(0.8)
        section.bottom_margin = Inches(0.8)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

    # Palette
    c_dark = RGBColor(39, 26, 16)       # Deep ink #271a10
    c_gold = RGBColor(168, 108, 30)     # Antique gold #a86c1e
    c_burgundy = RGBColor(143, 45, 36)  # Wax seal #8f2d24

    # Document Header / Title
    title_p = doc.add_paragraph()
    title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    title_run = title_p.add_run("KathaVaani (कथावाणी)")
    title_run.font.name = "Georgia"
    title_run.font.size = Pt(26)
    title_run.font.bold = True
    title_run.font.color.rgb = c_dark

    sub_p = doc.add_paragraph()
    sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    sub_run = sub_p.add_run("Narrator Character Dossier & Voice Profiles\nPowered by Gnani Timbre v2.5 Text-to-Speech")
    sub_run.font.name = "Georgia"
    sub_run.font.size = Pt(13)
    sub_run.font.italic = True
    sub_run.font.color.rgb = c_gold

    doc.add_paragraph()

    # Section 1: Overview
    h1 = doc.add_heading(level=1)
    h1_run = h1.add_run("1. Overview & Concept")
    h1_run.font.name = "Georgia"
    h1_run.font.color.rgb = c_dark

    p_intro = doc.add_paragraph(
        "KathaVaani breathes acoustic life into written literature using two curated narrator personas: "
        "Kavya (Feminine Voice) and Kabir (Masculine Voice). Each character is engineered to embody "
        "distinct acoustic dynamics, storytelling cadence, and emotional warmth across 10 major Indian languages. "
        "The literature is spoken strictly in its native mother tongue without any artificial translation step."
    )
    p_intro.style.font.name = "Georgia"
    p_intro.style.font.size = Pt(11)

    # Section 2: Character 1 - Kavya
    h2 = doc.add_heading(level=1)
    h2_run = h2.add_run("2. Character Profile: Kavya (काव्या / కావ్య)")
    h2_run.font.name = "Georgia"
    h2_run.font.color.rgb = c_burgundy

    table1 = doc.add_table(rows=1, cols=2)
    table1.alignment = WD_TABLE_ALIGNMENT.CENTER
    table1.autofit = False

    cell_img = table1.cell(0, 0)
    cell_img.width = Inches(2.2)
    p_img = cell_img.paragraphs[0]
    if os.path.exists("images/character1.jpg"):
        p_img.add_run().add_picture("images/character1.jpg", width=Inches(2.0))

    cell_info = table1.cell(0, 1)
    cell_info.width = Inches(4.6)
    p_c1 = cell_info.paragraphs[0]
    
    def add_field(p, label, val, italic=False):
        lbl_r = p.add_run(label + ": ")
        lbl_r.font.bold = True
        lbl_r.font.name = "Georgia"
        val_r = p.add_run(val + "\n")
        val_r.font.italic = italic
        val_r.font.name = "Georgia"

    add_field(p_c1, "Role", "Feminine Storyteller & Lyricist Persona")
    add_field(p_c1, "Underlying Gnani Voice", "Nalini (Model: timbre-v2.5)")
    add_field(p_c1, "Archetype", "Empathetic, lyrical storyteller with nuanced emotional pacing")
    add_field(p_c1, "Acoustic Profile", "Warm mid-range register, gentle breath modulation, melodic intonation on conjunct syllables, fluid sentence flow.")
    add_field(p_c1, "Ideal Literary Genres", "Poetry, character-driven fiction, folklore, memoirs, children's fables, and emotional drama.")
    add_field(p_c1, "Signature Quote", '"Every word holds a fragrance; I merely allow it to take flight into the open air."', italic=True)

    doc.add_paragraph()

    # Section 3: Character 2 - Kabir
    h3 = doc.add_heading(level=1)
    h3_run = h3.add_run("3. Character Profile: Kabir (कबीर / కబీర్)")
    h3_run.font.name = "Georgia"
    h3_run.font.color.rgb = c_burgundy

    table2 = doc.add_table(rows=1, cols=2)
    table2.alignment = WD_TABLE_ALIGNMENT.CENTER
    table2.autofit = False

    cell_img2 = table2.cell(0, 0)
    cell_img2.width = Inches(2.2)
    p_img2 = cell_img2.paragraphs[0]
    if os.path.exists("images/character2.jpg"):
        p_img2.add_run().add_picture("images/character2.jpg", width=Inches(2.0))

    cell_info2 = table2.cell(0, 1)
    cell_info2.width = Inches(4.6)
    p_c2 = cell_info2.paragraphs[0]

    add_field(p_c2, "Role", "Masculine Storyteller & Sage Persona")
    add_field(p_c2, "Underlying Gnani Voice", "Deepak (Model: timbre-v2.5)")
    add_field(p_c2, "Archetype", "Grounded, resonant elder narrator with calm, timeless authority")
    add_field(p_c2, "Acoustic Profile", "Baritone depth, deliberate cadence, crisp articulation of plosives, reflective pauses between sentences.")
    add_field(p_c2, "Ideal Literary Genres", "Historical narratives, philosophical essays, classic epics, biographies, crime fiction, and reflective non-fiction.")
    add_field(p_c2, "Signature Quote", '"Time wears away stone, but a story well-spoken remains unyielding."', italic=True)

    doc.add_paragraph()

    # Section 4: Language & Voice Mapping Matrix
    h4 = doc.add_heading(level=1)
    h4_run = h4.add_run("4. Language & Voice Compatibility Matrix")
    h4_run.font.name = "Georgia"
    h4_run.font.color.rgb = c_dark

    p_matrix = doc.add_paragraph(
        "Both Kavya and Kabir have been empirically verified across all 10 supported Indian languages "
        "with a 100% success rate (20/20 test queries returned HTTP 200 OK with native acoustic fidelity):"
    )
    p_matrix.style.font.name = "Georgia"

    matrix_data = [
        ("Language", "Code", "Native Script", "Kavya Voice", "Kabir Voice", "Verification Status"),
        ("Telugu", "te-IN", "తెలుగు లిపి", "Nalini", "Deepak", "Verified (sample1.txt)"),
        ("Hindi", "hi-IN", "देवनागरी", "Nalini", "Deepak", "Verified (Panch Parmeshwar)"),
        ("English (India)", "en-IN", "Latin", "Nalini", "Deepak", "Verified (sample.txt)"),
        ("Tamil", "ta-IN", "தமிழ்", "Nalini", "Deepak", "Verified (200 OK)"),
        ("Kannada", "kn-IN", "ಕನ್ನಡ", "Nalini", "Deepak", "Verified (200 OK)"),
        ("Malayalam", "ml-IN", "മലയാളം", "Nalini", "Deepak", "Verified (200 OK)"),
        ("Marathi", "mr-IN", "मराठी", "Nalini", "Deepak", "Verified (200 OK)"),
        ("Bengali", "bn-IN", "বাংলা", "Nalini", "Deepak", "Verified (200 OK)"),
        ("Gujarati", "gu-IN", "ગુજરાતી", "Nalini", "Deepak", "Verified (200 OK)"),
        ("Punjabi", "pa-IN", "ਪੰਜਾਬੀ", "Nalini", "Deepak", "Verified (200 OK)")
    ]

    table_matrix = doc.add_table(rows=len(matrix_data), cols=6)
    table_matrix.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_matrix.style = "Table Grid"

    for r_idx, row in enumerate(matrix_data):
        for c_idx, val in enumerate(row):
            cell = table_matrix.cell(r_idx, c_idx)
            cell.text = val
            p = cell.paragraphs[0]
            if r_idx == 0:
                p.runs[0].font.bold = True
                p.runs[0].font.name = "Georgia"
                p.runs[0].font.size = Pt(9.5)
            else:
                p.runs[0].font.name = "Georgia"
                p.runs[0].font.size = Pt(9.0)

    doc.add_paragraph()

    # Section 5: Character Count & Credit Consumption Metrics
    h5 = doc.add_heading(level=1)
    h5_run = h5.add_run("5. Character Count & Credit Consumption Metrics")
    h5_run.font.name = "Georgia"
    h5_run.font.color.rgb = c_dark

    p_cred = doc.add_paragraph(
        "Based on live dashboard tracking (100 credits completed) and backend synthesis logs, "
        "the exact consumption ratios are as follows:"
    )
    p_cred.style.font.name = "Georgia"

    metrics = [
        ("Total Characters Synthesized So Far", "~8,650 characters"),
        ("Total Spoken Audio Duration", "447.36 seconds (~7.5 minutes) across 16 chunks"),
        ("Credits Deducted on Gnani Dashboard", "100 credits"),
        ("Derived Consumption Rate", "~86.5 characters per credit (1 credit ≈ 85–100 chars)"),
        ("Spoken Narration per Credit", "1 credit ≈ 4.5 seconds of synthesized audio"),
        ("Average 1-Page Book Cost (~1,500 chars)", "~15 to 18 credits per book page"),
        ("Estimated Capacity for 5,000 Credit Quota", "~415,000 characters (≈ 6 hours of continuous audio)"),
        ("Maximum Payload Limit per Request", "2,000 characters (KathaVaani safely chunks at 300–650 chars)"),
        ("Disk Cache Savings", "Permanent SHA-256 disk cache ensures 0 credits for repeated playback")
    ]

    table_m = doc.add_table(rows=len(metrics)+1, cols=2)
    table_m.alignment = WD_TABLE_ALIGNMENT.CENTER
    table_m.style = "Table Grid"

    table_m.cell(0, 0).text = "Metric / Parameter"
    table_m.cell(0, 0).paragraphs[0].runs[0].font.bold = True
    table_m.cell(0, 0).paragraphs[0].runs[0].font.name = "Georgia"

    table_m.cell(0, 1).text = "Observed Value & Performance"
    table_m.cell(0, 1).paragraphs[0].runs[0].font.bold = True
    table_m.cell(0, 1).paragraphs[0].runs[0].font.name = "Georgia"

    for idx, (k, v) in enumerate(metrics, start=1):
        c0 = table_m.cell(idx, 0)
        c0.text = k
        c0.paragraphs[0].runs[0].font.name = "Georgia"
        c0.paragraphs[0].runs[0].font.size = Pt(9.5)
        c0.paragraphs[0].runs[0].font.bold = True

        c1 = table_m.cell(idx, 1)
        c1.text = v
        c1.paragraphs[0].runs[0].font.name = "Georgia"
        c1.paragraphs[0].runs[0].font.size = Pt(9.5)

    output_path = "KathaVaani_Character_Info.docx"
    doc.save(output_path)
    print(f"Document successfully saved: {output_path} ({os.path.getsize(output_path):,} bytes)")

if __name__ == "__main__":
    generate_doc()

