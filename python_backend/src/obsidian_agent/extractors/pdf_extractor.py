"""PDF content extraction with text and OCR support."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PDFPage:
    """Extracted content from a PDF page."""
    page_num: int
    text: str
    images: list[bytes] = None
    ocr_text: str | None = None
    metadata: dict[str, Any] = None
    
    def __post_init__(self):
        self.images = self.images or []
        self.metadata = self.metadata or {}


@dataclass  
class PDFContent:
    """Complete extracted PDF content."""
    path: str
    title: str
    pages: list[PDFPage]
    metadata: dict[str, Any]
    total_pages: int
    
    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text or p.ocr_text or "" for p in self.pages)


class PDFExtractor:
    """Extract text and images from PDF files."""
    
    def __init__(self, ocr_enabled: bool = True, ocr_language: str = "eng"):
        self.ocr_enabled = ocr_enabled
        self.ocr_language = ocr_language
        self._pymupdf_available = self._check_pymupdf()
        self._tesseract_available = self._check_tesseract()
    
    def _check_pymupdf(self) -> bool:
        try:
            import fitz
            return True
        except ImportError:
            logger.warning("PyMuPDF not available. Install with: pip install pymupdf")
            return False
    
    def _check_tesseract(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            logger.warning("Tesseract not available for OCR")
            return False
    
    async def extract(self, path: Path) -> PDFContent | None:
        """Extract content from a PDF file."""
        if not self._pymupdf_available:
            logger.error("PyMuPDF required for PDF extraction")
            return None
        
        import fitz
        
        try:
            doc = fitz.open(str(path))
            pages = []
            
            for page_num, page in enumerate(doc):
                text = page.get_text()
                images = []
                ocr_text = None
                
                # Extract images if OCR is enabled
                if self.ocr_enabled and self._tesseract_available:
                    image_list = page.get_images()
                    for img_index, img in enumerate(image_list):
                        xref = img[0]
                        base_image = doc.extract_image(xref)
                        images.append(base_image["image"])
                    
                    # OCR if no text was extracted
                    if not text.strip() and images:
                        ocr_text = await self._ocr_page(page)
                
                pages.append(PDFPage(
                    page_num=page_num + 1,
                    text=text,
                    images=images,
                    ocr_text=ocr_text,
                ))
            
            metadata = doc.metadata or {}
            title = metadata.get("title") or path.stem
            
            doc.close()
            
            return PDFContent(
                path=str(path),
                title=title,
                pages=pages,
                metadata=metadata,
                total_pages=len(pages),
            )
        except Exception as e:
            logger.error(f"Failed to extract PDF {path}: {e}")
            return None
    
    async def _ocr_page(self, page) -> str | None:
        """OCR a PDF page."""
        if not self._tesseract_available:
            return None
        
        import pytesseract
        from PIL import Image
        import io
        
        try:
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return pytesseract.image_to_string(img, lang=self.ocr_language)
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            return None
    
    def get_capabilities(self) -> dict[str, bool]:
        return {
            "text_extraction": self._pymupdf_available,
            "ocr": self._tesseract_available and self.ocr_enabled,
            "image_extraction": self._pymupdf_available,
        }
