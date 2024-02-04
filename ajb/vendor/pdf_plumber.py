import io
import urllib3
import pdfplumber


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
