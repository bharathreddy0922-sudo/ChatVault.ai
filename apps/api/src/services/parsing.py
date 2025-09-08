import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import fitz  # PyMuPDF
from ..config import settings

logger = logging.getLogger(__name__)


class DocumentParser:
    def __init__(self):
        self.ocr = None
        self._init_ocr()
    
    def _init_ocr(self):
        """Initialize OCR if available (optional)"""
        if not settings.enable_ocr:
            logger.info("OCR disabled by configuration")
            return
            
        try:
            import pytesseract
            from PIL import Image
            self.ocr = pytesseract
            logger.info("OCR (pytesseract) initialized successfully")
        except ImportError:
            logger.warning("pytesseract not available - OCR disabled")
            self.ocr = None
        except Exception as e:
            logger.warning(f"OCR initialization failed: {e}")
            self.ocr = None
    
    def parse_document(self, file_path: str, filetype: str, force_ocr: bool = False) -> Dict[str, Any]:
        """Parse a document and extract text with metadata"""
        try:
            # Check file size limit
            file_size = os.path.getsize(file_path)
            if file_size > settings.max_file_size:
                raise ValueError(f"File size {file_size} exceeds limit {settings.max_file_size}")
            
            if filetype.lower() == '.pdf':
                return self._parse_pdf(file_path, force_ocr)
            elif filetype.lower() in ['.docx', '.doc']:
                return self._parse_docx(file_path)
            elif filetype.lower() in ['.txt']:
                return self._parse_txt(file_path)
            elif filetype.lower() in ['.csv']:
                return self._parse_csv(file_path)
            elif filetype.lower() in ['.xlsx', '.xls']:
                return self._parse_excel(file_path)
            else:
                return self._parse_generic(file_path)
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {e}")
            raise
    
    def _parse_pdf(self, file_path: str, force_ocr: bool = False) -> Dict[str, Any]:
        """Parse PDF with page numbers and optional OCR"""
        try:
            doc = fitz.open(file_path)
            
            # Check page limit
            if len(doc) > settings.max_pages_per_document:
                logger.warning(f"PDF has {len(doc)} pages, limiting to {settings.max_pages_per_document}")
                doc = fitz.open(file_path)
                doc.select(range(settings.max_pages_per_document))
            
            pages = []
            total_text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                
                # Extract text first
                text = page.get_text()
                
                # If no text and OCR is enabled, try OCR
                if (not text.strip() or force_ocr) and self.ocr:
                    try:
                        from PIL import Image
                        pix = page.get_pixmap()
                        img_data = pix.tobytes("png")
                        img = Image.open(io.BytesIO(img_data))
                        
                        # OCR the image
                        text = self.ocr.image_to_string(img, lang=settings.ocr_language)
                    except Exception as ocr_error:
                        logger.warning(f"OCR failed for page {page_num + 1}: {ocr_error}")
                
                if text.strip():
                    pages.append({
                        'page': page_num + 1,
                        'text': text,
                        'type': 'ocr' if force_ocr and not page.get_text().strip() else 'text'
                    })
                    total_text += text + "\n"
            
            doc.close()
            
            return {
                'text': total_text,
                'pages': len(pages),
                'page_content': pages,
                'metadata': {
                    'parsing_method': 'pymupdf',
                    'total_pages': len(pages),
                    'ocr_used': force_ocr
                }
            }
            
        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise
    

    
    def _parse_docx(self, file_path: str) -> Dict[str, Any]:
        """Parse DOCX document"""
        try:
            from docx import Document
            doc = Document(file_path)
            
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text)
            
            text = '\n'.join(paragraphs)
            
            return {
                'text': text,
                'pages': 1,  # DOCX doesn't have explicit pages
                'page_content': [{'page': 1, 'text': text, 'type': 'text'}],
                'metadata': {
                    'parsing_method': 'python-docx',
                    'total_pages': 1,
                    'paragraphs': len(paragraphs)
                }
            }
        except Exception as e:
            logger.error(f"Error parsing DOCX: {e}")
            raise
    
    def _parse_txt(self, file_path: str) -> Dict[str, Any]:
        """Parse text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return {
                'text': text,
                'pages': 1,
                'page_content': [{'page': 1, 'text': text, 'type': 'text'}],
                'metadata': {
                    'parsing_method': 'text',
                    'total_pages': 1
                }
            }
        except Exception as e:
            logger.error(f"Error parsing TXT: {e}")
            raise
    
    def _parse_csv(self, file_path: str) -> Dict[str, Any]:
        """Parse CSV file"""
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            
            # Convert to text representation
            text = df.to_string(index=False)
            
            return {
                'text': text,
                'pages': 1,
                'page_content': [{'page': 1, 'text': text, 'type': 'table'}],
                'metadata': {
                    'parsing_method': 'pandas',
                    'total_pages': 1,
                    'rows': len(df),
                    'columns': len(df.columns)
                }
            }
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            raise
    
    def _parse_excel(self, file_path: str) -> Dict[str, Any]:
        """Parse Excel file"""
        try:
            import pandas as pd
            excel_file = pd.ExcelFile(file_path)
            
            all_text = []
            page_content = []
            page_num = 1
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(file_path, sheet_name=sheet_name)
                sheet_text = f"Sheet: {sheet_name}\n{df.to_string(index=False)}"
                all_text.append(sheet_text)
                
                page_content.append({
                    'page': page_num,
                    'text': sheet_text,
                    'type': 'table',
                    'sheet': sheet_name
                })
                page_num += 1
            
            return {
                'text': '\n\n'.join(all_text),
                'pages': len(excel_file.sheet_names),
                'page_content': page_content,
                'metadata': {
                    'parsing_method': 'pandas',
                    'total_pages': len(excel_file.sheet_names),
                    'sheets': excel_file.sheet_names
                }
            }
        except Exception as e:
            logger.error(f"Error parsing Excel: {e}")
            raise
    
    def _parse_generic(self, file_path: str) -> Dict[str, Any]:
        """Parse generic file as text"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            return {
                'text': text,
                'pages': 1,
                'page_content': [{'page': 1, 'text': text, 'type': 'text'}],
                'metadata': {
                    'parsing_method': 'text',
                    'total_pages': 1
                }
            }
        except Exception as e:
            logger.error(f"Error parsing generic file: {e}")
            raise
