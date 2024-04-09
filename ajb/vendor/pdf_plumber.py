import io
import urllib3
import pdfplumber
from fastapi import UploadFile
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


async def extract_pdf_text_by_file(file: UploadFile):
    """
    Extracts text from a PDF file.
    """
    temp = io.BytesIO(await file.read())
    all_text = ""
    with pdfplumber.open(temp) as pdf:
        for pdf_page in pdf.pages:
            single_page_text = pdf_page.extract_text()
            all_text = all_text + "\n" + single_page_text
    return all_text


async def extract_docx_text_by_file(file: UploadFile):
    """
    Extracts text from a DOCX file.
    """
    temp = io.BytesIO(await file.read())
    doc = Document(temp)
    all_text = ""
    for paragraph in doc.paragraphs:
        all_text = all_text + "\n" + paragraph.text
    return all_text


async def extract_text_file(file: UploadFile):
    """
    Extracts text from a text file.
    """
    contents = await file.read()
    text = contents.decode("utf-8")
    return text


async def extract_text(file: UploadFile):
    """
    Extracts text from a file based on its type.
    """
    file_extension = str(file.filename).split(".")[-1]

    if file_extension == "pdf":
        return await extract_pdf_text_by_file(file)
    elif file_extension == "txt":
        return await extract_text_file(file)
    else:
        try:
            return await extract_docx_text_by_file(file)
        except Exception:
            raise BadFileTypeException
