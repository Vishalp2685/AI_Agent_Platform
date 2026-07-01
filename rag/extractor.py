import pymupdf

def extract_text_from_pdf(file_path):

    doc = pymupdf.open(file_path)
    doc_text = ""
    for page_num, page in enumerate(doc):
        doc_text += f"\n--- Page {page_num + 1} ---\n"
        text = page.get_text()
        doc_text += text
    return doc_text
