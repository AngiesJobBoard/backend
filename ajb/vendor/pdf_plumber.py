import io
import urllib3
import pdfplumber
from docx import Document


class BadFileTypeException(Exception):
    pass


def extract_pdf_text_by_url(url: str):
    """
    Extracts text from a PDF by URL.
    """
    http = urllib3.PoolManager()
    temp = io.BytesIO()
    temp.write(http.request("GET", url).data)
    all_text = ""
    with pdfplumber.open(temp) as pdf:
        for pdf_page in pdf.pages:
            single_page_text = pdf_page.extract_text()
            all_text = all_text + "\n" + single_page_text
    return all_text


def extract_docx_text_by_url(url: str):
    """
    Extracts text from a DOCX by URL.
    """
    http = urllib3.PoolManager()
    temp = io.BytesIO()
    temp.write(http.request("GET", url).data)
    doc = Document(temp)
    all_text = ""
    for paragraph in doc.paragraphs:
        all_text = all_text + "\n" + paragraph.text
    return all_text


def extract_pdf_text_by_file(content: bytes):
    """
    Extracts text from a PDF file.
    """
    temp = io.BytesIO(content)
    all_text = ""
    with pdfplumber.open(temp) as pdf:
        for pdf_page in pdf.pages:
            single_page_text = pdf_page.extract_text()
            all_text = all_text + "\n" + single_page_text
    return all_text


def extract_docx_text_by_file(content: bytes):
    """
    Extracts text from a DOCX file.
    """
    temp = io.BytesIO(content)
    doc = Document(temp)
    all_text = ""
    for paragraph in doc.paragraphs:
        all_text = all_text + "\n" + paragraph.text
    return all_text


def extract_text_file(contents: bytes):
    """
    Extracts text from a text file.
    """
    text = contents.decode("utf-8")
    return text


def extract_text(file_bytes: bytes):
    """
    Extracts text from a file based on its type.
    """
    try:
        return extract_pdf_text_by_file(file_bytes)
    # pylint: disable=broad-except
    except Exception:
        try:
            return extract_text_file(file_bytes)
        # pylint: disable=broad-except
        except Exception:
            return extract_docx_text_by_file(file_bytes)
