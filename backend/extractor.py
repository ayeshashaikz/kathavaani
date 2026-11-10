"""
Text extraction module for KathaVaani.
Extracts text per page from PDF (using PyMuPDF) and TXT manuscripts,
with automatic scanned-document detection and text cleaning.
"""

import re
from typing import Dict, Any, List
import fitz  # PyMuPDF


def clean_text(text: str) -> str:
    """
    Cleans extracted text:
    - Removes hyphenated line breaks (e.g., 'trans-\nport' -> 'transport')
    - Replaces odd control characters while keeping unicode/Indic scripts
    - Normalizes multiple spaces and newlines
    """
    if not text:
        return ""
    
    # Reconnect words split across lines with hyphens
    text = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', text)
    
    # Normalize multiple newlines into paragraph breaks
    text = re.sub(r'\r\n', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace non-breaking spaces and irregular tabs
    text = text.replace('\xa0', ' ').replace('\t', ' ')
    
    # Strip trailing and leading whitespace
    return text.strip()


def extract_from_pdf(pdf_bytes: bytes, filename: str = "document.pdf") -> Dict[str, Any]:
    """
    Extracts text per page from a PDF file using PyMuPDF.
    Detects if the PDF is scanned / lacks selectable text layer.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)
    
    pages: List[Dict[str, Any]] = []
    total_chars = 0
    
    for page_idx in range(total_pages):
        page = doc[page_idx]
        raw_text = page.get_text("text")
        cleaned = clean_text(raw_text)
        
        char_count = len(cleaned)
        word_count = len(cleaned.split()) if cleaned else 0
        total_chars += char_count
        
        pages.append({
            "page_number": page_idx + 1,
            "text": cleaned,
            "char_count": char_count,
            "word_count": word_count
        })
        
    doc.close()
    
    # Check if document has practically no extractable text layer
    is_scanned = (total_chars < 25 * max(1, total_pages))
    
    message = (
        "This PDF appears to be a scanned document without a selectable text layer. "
        "Scanned books are not supported yet."
        if is_scanned and total_pages > 0
        else "Text extracted successfully."
    )
    
    return {
        "filename": filename,
        "file_type": "pdf",
        "total_pages": total_pages,
        "is_scanned": is_scanned,
        "message": message,
        "pages": pages
    }


def extract_from_txt(txt_bytes: bytes, filename: str = "document.txt", chars_per_page: int = 1400) -> Dict[str, Any]:
    """
    Extracts text from a plain text file, splitting content into
    virtual pages (~1400 chars each) breaking cleanly at paragraphs/sentences.
    """
    try:
        content = txt_bytes.decode("utf-8")
    except UnicodeDecodeError:
        content = txt_bytes.decode("latin-1", errors="replace")
        
    cleaned = clean_text(content)
    
    if not cleaned:
        return {
            "filename": filename,
            "file_type": "txt",
            "total_pages": 0,
            "is_scanned": False,
            "message": "The uploaded text file is empty.",
            "pages": []
        }
        
    # Split by paragraphs
    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [line.strip() for line in cleaned.splitlines() if line.strip()]
        
    pages: List[Dict[str, Any]] = []
    current_page_text: List[str] = []
    current_length = 0
    page_num = 1
    
    for para in paragraphs:
        if current_length + len(para) > chars_per_page and current_page_text:
            page_text = "\n\n".join(current_page_text).strip()
            pages.append({
                "page_number": page_num,
                "text": page_text,
                "char_count": len(page_text),
                "word_count": len(page_text.split())
            })
            page_num += 1
            current_page_text = [para]
            current_length = len(para)
        else:
            current_page_text.append(para)
            current_length += len(para)
            
    if current_page_text:
        page_text = "\n\n".join(current_page_text).strip()
        pages.append({
            "page_number": page_num,
            "text": page_text,
            "char_count": len(page_text),
            "word_count": len(page_text.split())
        })
        
    return {
        "filename": filename,
        "file_type": "txt",
        "total_pages": len(pages),
        "is_scanned": False,
        "message": "Text extracted successfully.",
        "pages": pages
    }


def extract_text_from_file(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Router to extract text based on file extension."""
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return extract_from_pdf(pdf_bytes=file_bytes, filename=filename)
    elif ext in ("txt", "text"):
        return extract_from_txt(txt_bytes=file_bytes, filename=filename)
    else:
        raise ValueError(f"Unsupported file format: '.{ext}'. Please upload a PDF or TXT file.")

