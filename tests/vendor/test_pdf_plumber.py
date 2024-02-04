import unittest
from unittest.mock import patch, MagicMock
from ajb.vendor.pdf_plumber import extract_pdf_text_by_url


class TestExtractPdfTextByUrl(unittest.TestCase):
    @patch("urllib3.PoolManager")
    @patch("pdfplumber.open")
    def test_extract_pdf_text_by_url(self, mock_pdfplumber_open, mock_pool_manager):
        mock_pool_manager.return_value.request.return_value.data = b"PDF data"
        mock_pdf = MagicMock()
        mock_pdf.pages = [MagicMock(), MagicMock()]
        mock_pdf.pages[0].extract_text.return_value = "Page 1 text"
        mock_pdf.pages[1].extract_text.return_value = "Page 2 text"
        mock_pdfplumber_open.return_value.__enter__.return_value = mock_pdf
        result = extract_pdf_text_by_url("https://example.com/test.pdf")
        self.assertEqual(result, "\nPage 1 text\nPage 2 text")
