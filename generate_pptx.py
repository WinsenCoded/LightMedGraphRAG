"""
LightMedGraphRAG - PowerPoint Presentation Generator (.pptx)
============================================================
Menghasilkan berkas presentasi profesional 16:9 (Widescreen)
untuk presentasi seminar / sidang magang riset di BRIN.
"""

import sys
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_PPTX = Path(r"c:\Magang BRIN\Belajar_RAG\LightRAG_medis\LightMedGraphRAG_Presentation.pptx")

# ==============================================================================
# PALET WARNA PROFESIONAL MEDIS & AKADEMIK
# ==============================================================================
COLOR_PRIMARY_NAVY  = RGBColor(30, 58, 138)    # #1E3A8A (Navy Utama)
COLOR_SECONDARY_TEAL= RGBColor(13, 148, 136)   # #0D9488 (Teal Medis)
COLOR_DARK_SLATE    = RGBColor(15, 23, 42)     # #0F172A (Latar Gelap)
COLOR_TEXT_DARK     = RGBColor(30, 41, 59)     # #1E293B (Teks Utama)
COLOR_TEXT_MUTED    = RGBColor(100, 116, 139)  # #64748B (Teks Sekunder)
COLOR_CARD_BG       = RGBColor(241, 245, 249)  # #F1F5F9 (Background Card)
COLOR_ALERT_RED     = RGBColor(225, 29, 72)    # #E11D48 (Peringatan DDI)
COLOR_ALERT_BG      = RGBColor(255, 241, 242)  # #FFF1F2 (Red Tint)
COLOR_SUCCESS_GREEN = RGBColor(16, 185, 129)   # #10B981 (Hijau Sukses)
COLOR_WHITE         = RGBColor(255, 255, 255)
COLOR_BORDER_LIGHT  = RGBColor(226, 232, 240)


def create_deck():
    prs = Presentation()
    # 16:9 Widescreen Layout
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]  # Blank slide

    def add_header(slide, title_text, category_text="LIGHTMEDGRAPHRAG • BRIN RESEARCH PRESENTATION"):
        """Header standar halaman konten."""
        # Top accent bar
        bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(0.5), Inches(0.12), Inches(0.85))
        bar.fill.solid()
        bar.fill.fore_color.rgb = COLOR_SECONDARY_TEAL
        bar.line.fill.background()

        # Category / Overline text
        tx_box = slide.shapes.add_textbox(Inches(1.05), Inches(0.42), Inches(11.4), Inches(0.3))
        tf = tx_box.text_frame
        tf.word_wrap = True
        p0 = tf.paragraphs[0]
        p0.text = category_text.upper()
        p0.font.size = Pt(11)
        p0.font.bold = True
        p0.font.color.rgb = COLOR_SECONDARY_TEAL
        p0.font.name = "Calibri"

        # Main Title text
        tx_title = slide.shapes.add_textbox(Inches(1.05), Inches(0.72), Inches(11.4), Inches(0.65))
        tf_t = tx_title.text_frame
        tf_t.word_wrap = True
        p1 = tf_t.paragraphs[0]
        p1.text = title_text
        p1.font.size = Pt(24)
        p1.font.bold = True
        p1.font.color.rgb = COLOR_PRIMARY_NAVY
        p1.font.name = "Arial"

    # ==========================================================================
    # SLIDE 1: TITLE SLIDE (Dark Executive Navy Theme)
    # ==========================================================================
    slide1 = prs.slides.add_slide(blank_layout)
    bg1 = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg1.fill.solid()
    bg1.fill.fore_color.rgb = COLOR_DARK_SLATE
    bg1.line.fill.background()

    # Subtitle badge
    badge = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.4), Inches(5.8), Inches(0.45))
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_SECONDARY_TEAL
    badge.line.fill.background()
    p_badge = badge.text_frame.paragraphs[0]
    p_badge.text = "BADAN RISET DAN INOVASI NASIONAL (BRIN) • 2026"
    p_badge.font.size = Pt(12)
    p_badge.font.bold = True
    p_badge.font.color.rgb = COLOR_WHITE
    p_badge.alignment = PP_ALIGN.CENTER

    # Main Title
    tbox1 = slide1.shapes.add_textbox(Inches(1.2), Inches(2.1), Inches(11.0), Inches(2.2))
    tf1 = tbox1.text_frame
    tf1.word_wrap = True
    p_t1 = tf1.paragraphs[0]
    p_t1.text = "LightMedGraphRAG"
    p_t1.font.size = Pt(46)
    p_t1.font.bold = True
    p_t1.font.color.rgb = COLOR_WHITE
    p_t1.font.name = "Arial"

    p_t2 = tf1.add_paragraph()
    p_t2.text = "Arsitektur Hibrida RAG Medis: Efisiensi Token LightRAG & Grounding Ontologi Farmakologi MedGraphRAG"
    p_t2.font.size = Pt(20)
    p_t2.font.color.rgb = RGBColor(148, 163, 184)
    p_t2.font.name = "Calibri"

    # Presenter Card Box
    pbox = slide1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(4.7), Inches(10.9), Inches(1.6))
    pbox.fill.solid()
    pbox.fill.fore_color.rgb = RGBColor(30, 41, 59)
    pbox.line.color.rgb = COLOR_SECONDARY_TEAL
    pbox.line.width = Pt(1.5)
    tf_p = pbox.text_frame
    tf_p.word_wrap = True
    
    pp0 = tf_p.paragraphs[0]
    pp0.text = "Presenter: Tim Peneliti Magang BRIN (Pusat Riset Informatika & Pusat Riset Biomedis)"
    pp0.font.size = Pt(15)
    pp0.font.bold = True
    pp0.font.color.rgb = COLOR_WHITE

    pp1 = tf_p.add_paragraph()
    pp1.text = "Topik Riset: Clinical Decision Support Systems (CDSS), Knowledge Graphs, & Token-Efficient LLMs"
    pp1.font.size = Pt(13)
    pp1.font.color.rgb = RGBColor(203, 213, 225)

    pp2 = tf_p.add_paragraph()
    pp2.text = "Repositori Terbuka GitHub: https://github.com/WinsenCoded/LightMedGraphRAG"
    pp2.font.size = Pt(12)
    pp2.font.color.rgb = COLOR_SECONDARY_TEAL
    pp2.font.bold = True

    # ==========================================================================
    # SLIDE 2: DILEMA KLINIS (Problem Statement)
    # ==========================================================================
    slide2 = prs.slides.add_slide(blank_layout)
    add_header(slide2, "Latar Belakang & Dilema Klinis AI Medis Saat Ini")

    # Card 1: Dilema Fatalitas Klinis (Kiri)
    c1 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(4.2))
    c1.fill.solid()
    c1.fill.fore_color.rgb = COLOR_ALERT_BG
    c1.line.color.rgb = COLOR_ALERT_RED
    c1.line.width = Pt(1.5)
    tf_c1 = c1.text_frame
    tf_c1.word_wrap = True
    
    p = tf_c1.paragraphs[0]
    p.text = "🚨 DILEMA 1: RISIKO FATALITAS KLINIS"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = COLOR_ALERT_RED

    points1 = [
        "Naive RAG hanya mengandalkan kemiripan teks kosinus (text cosine similarity).",
        "Rawan halusinasi obat fatal: Sering merekomendasikan Beta-bloker non-selektif pada pasien PPOK/Asma.",
        "Ketiadaan verifikasi ontologi: Jawaban LLM tidak terikat ke standar farmakope resmi (UMLS / RxNorm / SNOMED CT).",
        "Tingkat halusinasi & kelalaian interaksi obat pada LLM umum mencapai 30% - 40%."
    ]
    for pt in points1:
        p_pt = tf_c1.add_paragraph()
        p_pt.text = "• " + pt
        p_pt.font.size = Pt(13)
        p_pt.font.color.rgb = COLOR_TEXT_DARK

    # Card 2: Dilema Inefisiensi GraphRAG (Kanan)
    c2 = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(4.2))
    c2.fill.solid()
    c2.fill.fore_color.rgb = COLOR_CARD_BG
    c2.line.color.rgb = COLOR_PRIMARY_NAVY
    c2.line.width = Pt(1.5)
    tf_c2 = c2.text_frame
    tf_c2.word_wrap = True

    p = tf_c2.paragraphs[0]
    p.text = "📉 DILEMA 2: TOKEN EXPLOSION & BIAYA"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_NAVY

    points2 = [
        "Standard GraphRAG melakukan clustering hierarkis komunitas dan multi-hop extraction masif.",
        "Konsumsi token membengkak drastis: Menghabiskan >12.000 token per satu kueri klinis.",
        "Latensi inferensi sangat tinggi (>15 - 30 detik), tidak aplikatif untuk penanganan gawat darurat.",
        "Re-indexing pedoman baru sangat mahal dan menuntut komputasi ulang seluruh graf."
    ]
    for pt in points2:
        p_pt = tf_c2.add_paragraph()
        p_pt.text = "• " + pt
        p_pt.font.size = Pt(13)
        p_pt.font.color.rgb = COLOR_TEXT_DARK

    # Pertanyaan Riset Banner di Bawah
    q_banner = slide2.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.05), Inches(11.7), Inches(0.95))
    q_banner.fill.solid()
    q_banner.fill.fore_color.rgb = COLOR_PRIMARY_NAVY
    q_banner.line.fill.background()
    p_q = q_banner.text_frame.paragraphs[0]
    p_q.text = "PERTANYAAN RISET: Dapatkah kita membangun sistem yang sehemat token LightRAG (<600 token/kueri) namun memiliki ketepatan ontologi dan garansi keamanan farmakologi 100% seperti MedGraphRAG?"
    p_q.font.size = Pt(13)
    p_q.font.bold = True
    p_q.font.color.rgb = COLOR_WHITE
    p_q.alignment = PP_ALIGN.CENTER

    # ==========================================================================
    # SLIDE 3: RESEARCH GAP & KONTRIBUSI UTAMA
    # ==========================================================================
    slide3 = prs.slides.add_slide(blank_layout)
    add_header(slide3, "Tiga Kontribusi Utama Arsitektur LightMedGraphRAG")

    contributions = [
        {
            "num": "01",
            "title": "Dual-Level Hybrid Retrieval & RRF",
            "desc": "Memisahkan pencarian entitas spesifik (kˡ) dan tema patofisiologi (kᵍ) dengan fusi Reciprocal Rank Fusion (RRF) antara TF-IDF sparse dan LSA dense vector. Menghemat token hingga >95% dibanding GraphRAG standar."
        },
        {
            "num": "02",
            "title": "Deterministic Safety Gate (0 Token LLM)",
            "desc": "Pengecekan Drug-Drug Interaction (DDI) dan Drug-Disease Contraindication (DDC) dilakukan 100% deterministik berbasis database resmi RxNorm NLM dan FDA Black Box Warnings tanpa membebani LLM (Biaya: 0 Token, Latensi <2ms)."
        },
        {
            "num": "03",
            "title": "Zero-Loss Evidence Grounding (CUI/RxCUI)",
            "desc": "Agregasi subgraf terekspansi 1-hop yang menyertakan alternatif terapi aman secara otomatis. Setiap klaim medis dan rekomendasi obat wajib mengutip kode ontologi resmi (UMLS CUI dan RxNorm RxCUI) demi integritas ilmiah."
        }
    ]

    for i, c in enumerate(contributions):
        left_pos = Inches(0.8 + (i * 4.0))
        box = slide3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left_pos, Inches(1.8), Inches(3.7), Inches(4.8))
        box.fill.solid()
        box.fill.fore_color.rgb = COLOR_CARD_BG
        box.line.color.rgb = COLOR_SECONDARY_TEAL
        box.line.width = Pt(1.5)
        tf = box.text_frame
        tf.word_wrap = True

        p_num = tf.paragraphs[0]
        p_num.text = c["num"]
        p_num.font.size = Pt(36)
        p_num.font.bold = True
        p_num.font.color.rgb = COLOR_SECONDARY_TEAL

        p_title = tf.add_paragraph()
        p_title.text = c["title"]
        p_title.font.size = Pt(16)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_PRIMARY_NAVY

        p_desc = tf.add_paragraph()
        p_desc.text = "\n" + c["desc"]
        p_desc.font.size = Pt(13)
        p_desc.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 4: ARSITEKTUR SISTEM HULU-KE-HILIR (Flowchart Stages)
    # ==========================================================================
    slide4 = prs.slides.add_slide(blank_layout)
    add_header(slide4, "Arsitektur Sistem & Alur Pemrosesan Hulu-ke-Hilir")

    stages = [
        ("TAHAP 1: INKREMENTAL INDEXING", [
            "Pedoman Klinis dibagi ke chunk 1.200 token.",
            "LLM mengekstrak entitas medis taksonomi T1-T5 & relasi.",
            "Grounding resmi NLM UMLS (CUI) & RxNorm (RxCUI).",
            "Simpan ke Graf NetworkX & Key-Value Vector Store."
        ], COLOR_PRIMARY_NAVY),
        ("TAHAP 2: DUAL-LEVEL RETRIEVAL", [
            "LLM mikro mengekstrak kˡ (low-level) & kᵍ (high-level).",
            "Hybrid RRF Search mencocokkan kˡ ke Nodes & kᵍ ke Edges.",
            "1-Hop Subgraph Expansion menarik entitas tetangga.",
            "Tarik alternatif terapi aman otomatis dari graf."
        ], COLOR_SECONDARY_TEAL),
        ("TAHAP 3: DETERMINISTIC SAFETY GATE", [
            "Kumpulkan seluruh RxCUI zat aktif dari subgraf.",
            "Evaluasi matriks aturan FDA & RxNorm deterministik.",
            "Deteksi DDI (antar-obat) & DDC (obat vs komorbiditas).",
            "Eksekusi dalam memori: BIAYA 0 TOKEN LLM!"
        ], COLOR_ALERT_RED),
        ("TAHAP 4: ZERO-LOSS SINTESIS", [
            "Zero-Loss Context merangkum bukti tanpa distorsi.",
            "Multi-backend LLM mensintesis rekomendasi klinis.",
            "Real-time token streaming (TTFT < 1 detik di Web UI).",
            "Catat stempel waktu, token, & latensi ke audit log .jsonl."
        ], COLOR_DARK_SLATE)
    ]

    for i, (title, items, col) in enumerate(stages):
        top_pos = Inches(1.6 + (i * 1.35))
        # Stage bar left
        s_bar = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(3.2), Inches(1.15))
        s_bar.fill.solid()
        s_bar.fill.fore_color.rgb = col
        s_bar.line.fill.background()
        p_sb = s_bar.text_frame.paragraphs[0]
        p_sb.text = title
        p_sb.font.size = Pt(12)
        p_sb.font.bold = True
        p_sb.font.color.rgb = COLOR_WHITE
        p_sb.alignment = PP_ALIGN.CENTER

        # Stage detail box
        d_box = slide4.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(4.1), top_pos, Inches(8.4), Inches(1.15))
        d_box.fill.solid()
        d_box.fill.fore_color.rgb = COLOR_CARD_BG
        d_box.line.color.rgb = COLOR_BORDER_LIGHT
        tf_d = d_box.text_frame
        tf_d.word_wrap = True
        p_first = tf_d.paragraphs[0]
        p_first.text = "• " + items[0] + "   • " + items[1]
        p_first.font.size = Pt(12)
        p_first.font.color.rgb = COLOR_TEXT_DARK
        p_second = tf_d.add_paragraph()
        p_second.text = "• " + items[2] + "   • " + items[3]
        p_second.font.size = Pt(12)
        p_second.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 5: INOVASI 1 - DUAL-LEVEL RETRIEVAL & RRF
    # ==========================================================================
    slide5 = prs.slides.add_slide(blank_layout)
    add_header(slide5, "Inovasi 1: Dual-Level Retrieval & Reciprocal Rank Fusion (RRF)")

    # Left box: Konsep Dual-Level
    b_left = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    b_left.fill.solid()
    b_left.fill.fore_color.rgb = COLOR_CARD_BG
    b_left.line.color.rgb = COLOR_PRIMARY_NAVY
    tf_bl = b_left.text_frame
    tf_bl.word_wrap = True
    
    p = tf_bl.paragraphs[0]
    p.text = "🔍 PARADIGMA DUAL-LEVEL (LIGHTRAG)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_NAVY

    b_pts = [
        "Satu panggilan LLM mikro (<100 token) memecah kueri klinis menjadi dua tingkat abstraksi.",
        "kˡ (Low-Level Keywords): Nama obat spesifik, keluhan langsung (cth: 'Metoprolol', 'Salbutamol', 'Sesak Napas'). Dicocokkan ke simpul Nodes.",
        "kᵍ (High-Level Keywords): Tema sindrom, patofisiologi, & pedoman (cth: 'Komorbiditas Kardiopulmonal', 'Terapi Bronkodilator'). Dicocokkan ke sisi Edges.",
        "Menghilangkan overhead community summary GraphRAG yang boros token."
    ]
    for pt in b_pts:
        p_pt = tf_bl.add_paragraph()
        p_pt.text = "\n• " + pt
        p_pt.font.size = Pt(13)
        p_pt.font.color.rgb = COLOR_TEXT_DARK

    # Right box: Formula Matematika RRF
    b_right = slide5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    b_right.fill.solid()
    b_right.fill.fore_color.rgb = COLOR_CARD_BG
    b_right.line.color.rgb = COLOR_SECONDARY_TEAL
    tf_br = b_right.text_frame
    tf_br.word_wrap = True

    p = tf_br.paragraphs[0]
    p.text = "📐 RECIPROCAL RANK FUSION (RRF)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_SECONDARY_TEAL

    p_f = tf_br.add_paragraph()
    p_f.text = "\nFormula Penggabungan Sparse + Dense Rank:\n\nRRF(d) = 1 / (60 + rank_sparse(d)) + 1 / (60 + rank_dense(d)) + Boost"
    p_f.font.size = Pt(13)
    p_f.font.bold = True
    p_f.font.color.rgb = COLOR_PRIMARY_NAVY

    r_pts = [
        "Jalur Sparse: TF-IDF Sublinear N-gram menangkap istilah leksikal eksak (nama obat & CUI) tanpa meleset.",
        "Jalur Dense: Latent Semantic Analysis (TruncatedSVD) memproyeksikan konsep sinonim ke ruang vektor kontinu.",
        "Konstanta Penghalusan k = 60 mencegah dominasi salah satu jalur pencarian.",
        "Latensi retrieval ultra-cepat (< 0.04 detik) dengan akurasi pencarian konsep sinonim yang tinggi."
    ]
    for pt in r_pts:
        p_pt = tf_br.add_paragraph()
        p_pt.text = "• " + pt
        p_pt.font.size = Pt(13)
        p_pt.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 6: INOVASI 2 - TAKSONOMI T1-T5 & GROUNDING NLM
    # ==========================================================================
    slide6 = prs.slides.add_slide(blank_layout)
    add_header(slide6, "Inovasi 2: Taksonomi Entitas T1-T5 & Grounding Ontologi NLM")

    # Tabel Taksonomi
    rows = 6
    cols = 4
    table_shape = slide6.shapes.add_table(rows, cols, Inches(0.8), Inches(1.6), Inches(11.7), Inches(4.2))
    tbl = table_shape.table
    tbl.columns[0].width = Inches(1.5)
    tbl.columns[1].width = Inches(3.2)
    tbl.columns[2].width = Inches(4.2)
    tbl.columns[3].width = Inches(2.8)

    headers = ["Taksonomi", "Kategori Entitas Klinis", "Contoh di Pengetahuan Sistem", "Kode Grounding Resmi"]
    for c_idx, h in enumerate(headers):
        cell = tbl.cell(0, c_idx)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = COLOR_PRIMARY_NAVY
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    taxonomy_data = [
        ("T1", "Symptom / Sign (Gejala)", "Dyspnea / Sesak Napas Akut", "UMLS CUI: C0013404"),
        ("T2", "Disease / Syndrome (Penyakit)", "PPOK Berat & Gagal Jantung Kongestif", "UMLS CUI: C0028268, C0018801"),
        ("T3", "Anatomy / Organ (Struktur Tubuh)", "Saluran Napas / Bronkus, Miokardium", "UMLS CUI: C0006255, C0027061"),
        ("T4", "Medication / Substance (Obat)", "Metoprolol, Tiotropium, Salbutamol", "RxNorm RxCUI: 6918, 69120, 435"),
        ("T5", "Procedure / Test Lab (Pemeriksaan)", "Spirometri (FEV1), Elektrokardiogram", "UMLS CUI: C0037936, C0013798")
    ]

    for r_idx, row in enumerate(taxonomy_data, 1):
        for c_idx, val in enumerate(row):
            cell = tbl.cell(r_idx, c_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = COLOR_CARD_BG if r_idx % 2 == 1 else COLOR_WHITE
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(12)
            p.font.color.rgb = COLOR_TEXT_DARK
            if c_idx == 0:
                p.font.bold = True
                p.font.color.rgb = COLOR_SECONDARY_TEAL

    # Banner Manfaat di Bawah
    b_foot = slide6.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(6.1), Inches(11.7), Inches(0.9))
    b_foot.fill.solid()
    b_foot.fill.fore_color.rgb = COLOR_SECONDARY_TEAL
    b_foot.line.fill.background()
    p_bf = b_foot.text_frame.paragraphs[0]
    p_bf.text = "MANFAAT ILMIAH: Standarisasi UMLS CUI & RxNorm RxCUI mencegah kebingungan sinonim (ambiguitas leksikal) dan menjamin jawaban sistem dapat diverifikasi silang dengan rekam medis rumah sakit."
    p_bf.font.size = Pt(12)
    p_bf.font.bold = True
    p_bf.font.color.rgb = COLOR_WHITE
    p_bf.alignment = PP_ALIGN.CENTER

    # ==========================================================================
    # SLIDE 7: INOVASI 3 - DETERMINISTIC SAFETY GATE (0 TOKEN)
    # ==========================================================================
    slide7 = prs.slides.add_slide(blank_layout)
    add_header(slide7, "Inovasi 3: Deterministic Pharmacology Safety Gate (0 Token LLM)")

    # Box Kiri: Mengapa Deterministik?
    b_why = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.6), Inches(5.6), Inches(5.2))
    b_why.fill.solid()
    b_why.fill.fore_color.rgb = COLOR_CARD_BG
    b_why.line.color.rgb = COLOR_PRIMARY_NAVY
    tf_w = b_why.text_frame
    tf_w.word_wrap = True

    p = tf_w.paragraphs[0]
    p.text = "⚠️ MENGAPA TIDAK MENYERAHKAN KE LLM?"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY_NAVY

    w_pts = [
        "LLM generatif bersifat probabilistik, bukan deterministik.",
        "Studi klinis membuktikan LLM memiliki tingkat false negative hingga 40% pada polifarmasi kompleks (melewatkan kontraindikasi fatal).",
        "Menanyakan interaksi obat berulang-ulang ke LLM memboroskan ribuan token dan menambah latensi.",
        "Solusi Kami: Pisahkan verifikasi keselamatan obat dari LLM. Serahkan keselamatan ke mesin deterministik farmakope!"
    ]
    for pt in w_pts:
        p_pt = tf_w.add_paragraph()
        p_pt.text = "\n• " + pt
        p_pt.font.size = Pt(13)
        p_pt.font.color.rgb = COLOR_TEXT_DARK

    # Box Kanan: Cara Kerja Deterministik
    b_how = slide7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.2))
    b_how.fill.solid()
    b_how.fill.fore_color.rgb = COLOR_ALERT_BG
    b_how.line.color.rgb = COLOR_ALERT_RED
    tf_h = b_how.text_frame
    tf_h.word_wrap = True

    p = tf_h.paragraphs[0]
    p.text = "🛡️ CARA KERJA SAFETY GATE KAMI"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_ALERT_RED

    h_pts = [
        "Ekstraksi RxCUI: Seluruh obat di subgraf aktif dikonversi ke kode unik RxNorm.",
        "Evaluasi Aturan Ganda: Memeriksa DDI (Antar-Obat) dan DDC (Obat vs Komorbiditas Penyakit Pasien).",
        "Biaya Komputasi: 0 TOKEN LLM (Eksekusi aturan dalam memori).",
        "Latensi: < 2 milidetik.",
        "Contoh Riil: Pasien PPOK diberi Metoprolol + Salbutamol -> Sistem langsung memicu peringatan merah & menarik Tiotropium sebagai alternatif aman!"
    ]
    for pt in h_pts:
        p_pt = tf_h.add_paragraph()
        p_pt.text = "\n• " + pt
        p_pt.font.size = Pt(13)
        p_pt.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 8: HASIL EVALUASI & KOMPARASI EMPIRIS
    # ==========================================================================
    slide8 = prs.slides.add_slide(blank_layout)
    add_header(slide8, "Hasil Evaluasi & Komparasi Empiris (Benchmark Report)")

    # Table Hasil Evaluasi
    r8 = 4
    c8 = 5
    t8_shape = slide8.shapes.add_table(r8, c8, Inches(0.8), Inches(1.6), Inches(11.7), Inches(2.8))
    tbl8 = t8_shape.table
    tbl8.columns[0].width = Inches(3.2)
    tbl8.columns[1].width = Inches(2.1)
    tbl8.columns[2].width = Inches(2.1)
    tbl8.columns[3].width = Inches(2.1)
    tbl8.columns[4].width = Inches(2.2)

    h8 = ["Arsitektur RAG", "Konsumsi Token", "Token Reduction", "DDI/DDC Recall", "Latensi Retrieval"]
    for idx, h in enumerate(h8):
        c = tbl8.cell(0, idx)
        c.text = h
        c.fill.solid()
        c.fill.fore_color.rgb = COLOR_PRIMARY_NAVY
        p = c.text_frame.paragraphs[0]
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE

    bench_data = [
        ("Standard GraphRAG", "~12.500 token", "0.0% (Baseline)", "74.2% (Rawan Lolos)", "> 15.00 detik"),
        ("Naive RAG (Vector-Only)", "~1.500 token", "+88.0%", "41.5% (Halusinasi)", "~ 0.50 detik"),
        ("LightMedGraphRAG (Ours)", "531 token", "+95.75% (Terhemat)", "100.0% (Deterministik)", "< 0.04 detik")
    ]

    for r_i, r_data in enumerate(bench_data, 1):
        for c_i, val in enumerate(r_data):
            cell = tbl8.cell(r_i, c_i)
            cell.text = val
            cell.fill.solid()
            if r_i == 3:
                cell.fill.fore_color.rgb = RGBColor(236, 253, 245) # Light green highlight
            else:
                cell.fill.fore_color.rgb = COLOR_CARD_BG if r_i % 2 == 1 else COLOR_WHITE
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(13)
            p.font.color.rgb = COLOR_TEXT_DARK
            if r_i == 3:
                p.font.bold = True
                p.font.color.rgb = COLOR_PRIMARY_NAVY if c_i == 0 else COLOR_SECONDARY_TEAL

    # Summary 3 Highlight Cards di Bawah
    hl = [
        ("95.75%", "Penghematan Token", "Memangkas biaya token dari >12.500 menjadi hanya 531 token."),
        ("100.0%", "Safety Gate Recall", "Nol kelalaian pada deteksi kontraindikasi fatal obat & komorbiditas."),
        ("< 1 Detik", "Time-to-First-Token", "Streaming token real-time memberikan UX tanpa jeda tunggu.")
    ]
    for i, (stat, title, sub) in enumerate(hl):
        l_pos = Inches(0.8 + (i * 4.0))
        b = slide8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l_pos, Inches(4.7), Inches(3.7), Inches(2.2))
        b.fill.solid()
        b.fill.fore_color.rgb = COLOR_CARD_BG
        b.line.color.rgb = COLOR_SECONDARY_TEAL
        tf = b.text_frame
        tf.word_wrap = True

        p_s = tf.paragraphs[0]
        p_s.text = stat
        p_s.font.size = Pt(30)
        p_s.font.bold = True
        p_s.font.color.rgb = COLOR_SECONDARY_TEAL

        p_t = tf.add_paragraph()
        p_t.text = title
        p_t.font.size = Pt(14)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_PRIMARY_NAVY

        p_sub = tf.add_paragraph()
        p_sub.text = sub
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = COLOR_TEXT_MUTED

    # ==========================================================================
    # SLIDE 9: SKENARIO LIVE DEMO INTERAKTIF
    # ==========================================================================
    slide9 = prs.slides.add_slide(blank_layout)
    add_header(slide9, "Skenario Live Demo Interaktif (Gradio Web UI)")

    demo_steps = [
        ("Langkah 1: Masukkan Kasus Pasien", "Pasien laki-laki 68 tahun dengan PPOK berat dan gagal jantung mengeluh sesak napas akut. Diberikan metoprolol dan salbutamol. Apakah kombinasi ini aman dan apa alternatifnya?"),
        ("Langkah 2: Streaming Respons Real-Time", "Dalam waktu <1 detik, teks jawaban klinis mulai terketik secara progresif di layar tanpa pengguna menunggu layar kosong."),
        ("Langkah 3: Peringatan Merah DDI Muncul", "Sistem menampilkan kotak peringatan: Metoprolol mengantagonis efek bronkodilasi Salbutamol, memicu risiko fatal bronkospasme akut."),
        ("Langkah 4: Rekomendasi Subgraf Cerdas", "Sistem otomatis menarik alternatif obat aman dari graf: Tiotropium (RxCUI: 69120) & Bisoprolol (RxCUI: 19484)."),
        ("Langkah 5: Audit Log & Transparansi Token", "Tabel profiler membuktikan latensi respons riil, konsumsi token (~500 token), dan sitasi kode UMLS/RxNorm.")
    ]

    for i, (title, desc) in enumerate(demo_steps):
        top_pos = Inches(1.6 + (i * 1.05))
        # Step number circle
        num_box = slide9.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.8), top_pos, Inches(0.8), Inches(0.8))
        num_box.fill.solid()
        num_box.fill.fore_color.rgb = COLOR_PRIMARY_NAVY
        num_box.line.fill.background()
        p_n = num_box.text_frame.paragraphs[0]
        p_n.text = str(i + 1)
        p_n.font.size = Pt(18)
        p_n.font.bold = True
        p_n.font.color.rgb = COLOR_WHITE
        p_n.alignment = PP_ALIGN.CENTER

        # Step card
        s_card = slide9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.8), top_pos, Inches(10.7), Inches(0.85))
        s_card.fill.solid()
        s_card.fill.fore_color.rgb = COLOR_CARD_BG
        s_card.line.color.rgb = COLOR_BORDER_LIGHT
        tf_sc = s_card.text_frame
        tf_sc.word_wrap = True
        p_t = tf_sc.paragraphs[0]
        p_t.text = title + ": "
        p_t.font.bold = True
        p_t.font.size = Pt(13)
        p_t.font.color.rgb = COLOR_PRIMARY_NAVY
        
        p_d = p_t
        run = p_d.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 10: LIMITASI & ROADMAP PENGEMBANGAN KE DEPAN (Future Works)
    # ==========================================================================
    slide10 = prs.slides.add_slide(blank_layout)
    add_header(slide10, "Limitasi Saat Ini & Roadmap Pengembangan Masa Depan")

    roadmap = [
        ("01", "Canonical Node Merging via UMLS CUI", "Penyatuan otomatis variasi sinonim istilah medis (misal: 'PPOK', 'COPD', 'Chronic Obstructive Lung Disease') ke dalam satu simpul kanonikal CUI tunggal agar tidak terjadi fragmentasi simpul di graf."),
        ("02", "Cross-Lingual Medical Mapping (ID -> EN)", "Modul normalisasi istilah keluhan bahasa Indonesia ke konsep kedokteran UMLS internasional (contoh: 'sesak napas saat berbaring' secara otomatis dipetakan ke konsep baku 'Orthopnea / C0029269')."),
        ("03", "Lab-Adjusted CDSS (Penyesuaian Organ Ginjal/Hati)", "Integrasi parameter laboratorium pasien (eGFR, serum kreatinin, kalium) sehingga peringatan kontraindikasi obat dapat disesuaikan dengan stadium disfungsi organ secara presisi."),
        ("04", "Pengujian Skala Penuh Benchmark MedQA (1.000+ Soal)", "Evaluasi komprehensif pada ribuan soal ujian USMLE dan PubMedQA untuk mengukur akurasi diagnostik formal dan skor ROUGE-L / BERTScore demi naskah publikasi jurnal Q1 bereputasi."),
        ("05", "Interoperabilitas Rekam Medis Elektronik (HL7 / FHIR)", "Integrasi pipeline LightMedGraphRAG langsung ke dalam sistem Rumah Sakit menggunakan standar protokol medis internasional Fast Healthcare Interoperability Resources (FHIR).")
    ]

    for i, (num, title, desc) in enumerate(roadmap):
        top_pos = Inches(1.6 + (i * 1.05))
        # Badge
        b_num = slide10.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), top_pos, Inches(0.7), Inches(0.85))
        b_num.fill.solid()
        b_num.fill.fore_color.rgb = COLOR_SECONDARY_TEAL
        b_num.line.fill.background()
        p = b_num.text_frame.paragraphs[0]
        p.text = num
        p.font.size = Pt(16)
        p.font.bold = True
        p.font.color.rgb = COLOR_WHITE
        p.alignment = PP_ALIGN.CENTER

        # Content box
        c_box = slide10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.65), top_pos, Inches(10.85), Inches(0.85))
        c_box.fill.solid()
        c_box.fill.fore_color.rgb = COLOR_CARD_BG
        c_box.line.color.rgb = COLOR_BORDER_LIGHT
        tf = c_box.text_frame
        tf.word_wrap = True
        p_t = tf.paragraphs[0]
        p_t.text = title + " — "
        p_t.font.bold = True
        p_t.font.size = Pt(13)
        p_t.font.color.rgb = COLOR_PRIMARY_NAVY
        run = p_t.add_run()
        run.text = desc
        run.font.bold = False
        run.font.size = Pt(12)
        run.font.color.rgb = COLOR_TEXT_DARK

    # ==========================================================================
    # SLIDE 11: KESIMPULAN & SESI TANYA JAWAB (Q&A)
    # ==========================================================================
    slide11 = prs.slides.add_slide(blank_layout)
    bg11 = slide11.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg11.fill.solid()
    bg11.fill.fore_color.rgb = COLOR_DARK_SLATE
    bg11.line.fill.background()

    # Center card
    card11 = slide11.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(1.2), Inches(10.3), Inches(5.1))
    card11.fill.solid()
    card11.fill.fore_color.rgb = RGBColor(30, 41, 59)
    card11.line.color.rgb = COLOR_SECONDARY_TEAL
    card11.line.width = Pt(2.0)
    tf11 = card11.text_frame
    tf11.word_wrap = True

    p0 = tf11.paragraphs[0]
    p0.text = "KESIMPULAN PENELITIAN"
    p0.font.size = Pt(24)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_SECONDARY_TEAL
    p0.alignment = PP_ALIGN.CENTER

    c_points = [
        "LightMedGraphRAG berhasil membuktikan bahwa efisiensi ekstrem LightRAG (>95% penghematan token) dapat dikawinkan dengan ketegasan ontologi MedGraphRAG.",
        "Penerapan Deterministic Safety Gate memecahkan masalah fatalitas halusinasi obat dengan biaya 0 TOKEN LLM dan tingkat recall kontraindikasi 100%.",
        "Pipeline dilengkapi kemampuan Real-Time Token Streaming (TTFT < 1s) dan Multi-Backend LLM (Lokal/Cloud) yang siap saji untuk evaluasi klinis.",
        "Seluruh kode sumber, dataset graf terindeks, dan skrip evaluasi telah dipublikasikan terbuka di GitHub: https://github.com/WinsenCoded/LightMedGraphRAG"
    ]
    for pt in c_points:
        p_pt = tf11.add_paragraph()
        p_pt.text = "✓ " + pt
        p_pt.font.size = Pt(14)
        p_pt.font.color.rgb = COLOR_WHITE

    p_qa = tf11.add_paragraph()
    p_qa.text = "\nTERIMA KASIH ATAS PERHATIAN BAPAK / IBU\nSesi Diskusi & Tanya Jawab (Q&A) Dipersilakan"
    p_qa.font.size = Pt(18)
    p_qa.font.bold = True
    p_qa.font.color.rgb = RGBColor(56, 189, 248) # Sky blue
    p_qa.alignment = PP_ALIGN.CENTER

    # Simpan berkas PPTX
    prs.save(OUTPUT_PPTX)
    print(f"[SUCCESS] Berkas presentasi PPTX berhasil dibuat: {OUTPUT_PPTX}")


if __name__ == "__main__":
    create_deck()
