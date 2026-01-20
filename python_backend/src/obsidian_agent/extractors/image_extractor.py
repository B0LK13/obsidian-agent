"""Image content extraction with OCR support."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ImageContent:
    """Extracted content from an image."""
    path: str
    text: str
    width: int
    height: int
    format: str
    metadata: dict[str, Any]
    confidence: float = 0.0


class ImageExtractor:
    """Extract text from images using OCR."""
    
    SUPPORTED_FORMATS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"}
    
    def __init__(self, language: str = "eng", confidence_threshold: float = 0.5):
        self.language = language
        self.confidence_threshold = confidence_threshold
        self._tesseract_available = self._check_tesseract()
        self._pillow_available = self._check_pillow()
    
    def _check_tesseract(self) -> bool:
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except Exception:
            logger.warning("Tesseract not available")
            return False
    
    def _check_pillow(self) -> bool:
        try:
            from PIL import Image
            return True
        except ImportError:
            logger.warning("Pillow not available")
            return False
    
    def is_supported(self, path: Path) -> bool:
        return path.suffix.lower() in self.SUPPORTED_FORMATS
    
    async def extract(self, path: Path) -> ImageContent | None:
        """Extract text from an image using OCR."""
        if not self._tesseract_available or not self._pillow_available:
            logger.error("Tesseract and Pillow required for image extraction")
            return None
        
        if not self.is_supported(path):
            logger.warning(f"Unsupported image format: {path.suffix}")
            return None
        
        import pytesseract
        from PIL import Image
        from PIL.ExifTags import TAGS
        
        try:
            img = Image.open(path)
            
            # Get image info
            width, height = img.size
            fmt = img.format or path.suffix[1:].upper()
            
            # Extract EXIF metadata
            metadata = {}
            if hasattr(img, "_getexif") and img._getexif():
                for tag_id, value in img._getexif().items():
                    tag = TAGS.get(tag_id, tag_id)
                    if isinstance(value, (str, int, float)):
                        metadata[tag] = value
            
            # Perform OCR
            ocr_data = pytesseract.image_to_data(img, lang=self.language, output_type=pytesseract.Output.DICT)
            
            # Filter by confidence and extract text
            texts = []
            confidences = []
            for i, conf in enumerate(ocr_data["conf"]):
                if conf > self.confidence_threshold * 100:
                    text = ocr_data["text"][i].strip()
                    if text:
                        texts.append(text)
                        confidences.append(conf)
            
            full_text = " ".join(texts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            img.close()
            
            return ImageContent(
                path=str(path),
                text=full_text,
                width=width,
                height=height,
                format=fmt,
                metadata=metadata,
                confidence=avg_confidence / 100,
            )
        except Exception as e:
            logger.error(f"Failed to extract image {path}: {e}")
            return None
    
    async def batch_extract(self, paths: list[Path]) -> list[ImageContent]:
        """Extract text from multiple images."""
        results = []
        for path in paths:
            content = await self.extract(path)
            if content:
                results.append(content)
        return results
    
    def get_capabilities(self) -> dict[str, bool]:
        return {
            "ocr": self._tesseract_available and self._pillow_available,
            "metadata_extraction": self._pillow_available,
        }
