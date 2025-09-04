#!/usr/bin/env python3
"""
PDF Text Extractor - Refactored Version following SOLID principles
Extracts Japanese text from PDFs including "限定承認公告"
"""
from typing import List, Optional, Tuple, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import sys
import io
import re

import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image


# ===============================
# Configuration (Open/Closed Principle)
# ===============================
@dataclass(frozen=True)
class Config:
    """Immutable configuration - closed for modification, open for extension"""
    TARGET_URL: str = "https://www.kanpo.go.jp/20250903/20250903h01541/20250903h015410032f.html"
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    OUTPUT_FILE: str = "log_extracted.txt"
    PAGE_ZOOM: float = 2.0
    
    # OCR configurations in priority order
    OCR_CONFIGS: Tuple[Tuple[str, str], ...] = (
        ('jpn_vert', '--psm 5'),  # Vertical Japanese text
        ('jpn', '--psm 6'),       # Uniform block of text
    )
    
    # Search terms for validation
    SEARCH_TERMS: Tuple[Tuple[str, str], ...] = (
        ("限定承認公告", "Limited acceptance announcement"),
        ("限定承認広告", "Limited acceptance notice"),
        ("限定承認", "Limited acceptance"),
    )
    
    # Text patterns to fix
    TEXT_PATTERNS: Tuple[Tuple[str, str], ...] = (
        (r'限\s*定\s*承\s*認\s*公\s*告', '限定承認公告'),
        (r'限\s*定\s*承\s*認\s*広\s*告', '限定承認広告'),
        (r'限\s*定\s*承\s*認', '限定承認'),
    )


# ===============================
# Interfaces (Dependency Inversion Principle)
# ===============================
class TextProcessor(Protocol):
    """Protocol for text processing"""
    def process(self, text: str) -> str:
        """Process and clean text"""
        ...


class PDFLoader(Protocol):
    """Protocol for PDF loading"""
    def load(self, url: str) -> io.BytesIO:
        """Load PDF from source"""
        ...


class TextExtractor(Protocol):
    """Protocol for text extraction"""
    def extract(self, source: any) -> str:
        """Extract text from source"""
        ...


# ===============================
# Single Responsibility Classes
# ===============================
class URLConverter:
    """Single responsibility: Convert HTML URL to PDF URL"""
    
    @staticmethod
    def html_to_pdf(html_url: str) -> str:
        """Convert HTML URL to PDF URL"""
        parts = html_url.split('/')
        date_part = parts[-3]
        issue_part = parts[-2]
        filename = parts[-1].replace('f.html', '.pdf')
        return f"https://www.kanpo.go.jp/{date_part}/{issue_part}/pdf/{filename}"


class HTTPPDFLoader:
    """Single responsibility: Download PDF from URL"""
    
    def __init__(self, user_agent: str):
        self.user_agent = user_agent
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def load(self, url: str) -> io.BytesIO:
        """Download PDF from URL"""
        self.logger.info(f"Downloading PDF from: {url}")
        
        try:
            response = requests.get(url, headers={'User-Agent': self.user_agent})
            response.raise_for_status()
            return io.BytesIO(response.content)
        except requests.RequestException as e:
            self.logger.error(f"Failed to download PDF: {e}")
            raise


class JapaneseTextProcessor:
    """Single responsibility: Process Japanese text"""
    
    def __init__(self, patterns: Tuple[Tuple[str, str], ...]):
        self.patterns = patterns
    
    def process(self, text: str) -> str:
        """Process text to fix common OCR issues"""
        if not text:
            return ""
        
        # Apply all pattern replacements
        result = text
        for pattern, replacement in self.patterns:
            result = re.sub(pattern, replacement, result)
        
        return result


class OCRTextExtractor:
    """Single responsibility: Extract text using OCR"""
    
    def __init__(self, configs: Tuple[Tuple[str, str], ...], processor: TextProcessor):
        self.configs = configs
        self.processor = processor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract_from_image(self, image: Image.Image) -> str:
        """Extract text from image using OCR"""
        best_text = ""
        
        for lang, config in self.configs:
            try:
                text = pytesseract.image_to_string(image, lang=lang, config=config)
                processed = self.processor.process(text)
                
                if processed and len(processed) > len(best_text):
                    best_text = processed
                    # Found good text, no need to try other configs
                    if "限定承認公告" in best_text or "限定承認広告" in best_text:
                        break
                        
            except Exception as e:
                self.logger.debug(f"OCR failed with {lang}: {e}")
                continue
        
        return best_text


class PDFTextExtractor:
    """Single responsibility: Extract all text from PDF"""
    
    def __init__(self, ocr_extractor: OCRTextExtractor, processor: TextProcessor):
        self.ocr_extractor = ocr_extractor
        self.processor = processor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def extract(self, pdf_data: io.BytesIO) -> str:
        """Extract text from PDF"""
        doc = fitz.open(stream=pdf_data, filetype="pdf")
        all_texts = []
        
        try:
            for page_num in range(doc.page_count):
                page_text = self._extract_page(doc[page_num], page_num)
                if page_text:
                    all_texts.append(page_text)
        finally:
            doc.close()
        
        return "\n\n".join(all_texts)
    
    def _extract_page(self, page, page_num: int) -> str:
        """Extract text from a single page"""
        texts = []
        
        # 1. Try text layer
        text_layer = page.get_text("text")
        if text_layer.strip():
            processed = self.processor.process(text_layer)
            if processed:
                texts.append(f"=== Page {page_num + 1} Text Layer ===\n{processed}")
        
        # 2. Try OCR on embedded images
        for img_index, img in enumerate(page.get_images()):
            img_text = self._extract_from_embedded_image(page.parent, img[0])
            if img_text:
                texts.append(f"\n=== Page {page_num + 1} Image {img_index + 1} ===\n{img_text}")
        
        # 3. Try full page OCR (only for first page to save time)
        if page_num == 0:
            page_text = self._extract_from_page_render(page)
            if page_text:
                texts.append(f"\n=== Page {page_num + 1} Full OCR ===\n{page_text}")
        
        return "\n".join(texts)
    
    def _extract_from_embedded_image(self, doc, xref: int) -> str:
        """Extract text from embedded image"""
        try:
            pix = fitz.Pixmap(doc, xref)
            img_data = pix.pil_tobytes(format="PNG")
            pix = None
            
            image = Image.open(io.BytesIO(img_data))
            return self.ocr_extractor.extract_from_image(image)
        except Exception as e:
            self.logger.debug(f"Failed to extract from embedded image: {e}")
            return ""
    
    def _extract_from_page_render(self, page) -> str:
        """Render page and extract text"""
        try:
            mat = fitz.Matrix(Config.PAGE_ZOOM, Config.PAGE_ZOOM)
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.pil_tobytes(format="PNG")
            pix = None
            
            image = Image.open(io.BytesIO(img_data))
            return self.ocr_extractor.extract_from_image(image)
        except Exception as e:
            self.logger.debug(f"Failed to extract from page render: {e}")
            return ""


class TextAnalyzer:
    """Single responsibility: Analyze extracted text"""
    
    def __init__(self, search_terms: Tuple[Tuple[str, str], ...]):
        self.search_terms = search_terms
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze(self, text: str) -> bool:
        """Analyze text and return whether target was found"""
        target_found = False
        
        self.logger.info("\n=== Analysis Results ===")
        for term, description in self.search_terms:
            count = text.count(term)
            if count > 0:
                self.logger.info(f"✓ '{term}' ({description}): {count} occurrences")
                if term in ["限定承認公告", "限定承認広告"]:
                    target_found = True
                    self._show_context(text, term)
            else:
                self.logger.info(f"✗ '{term}' ({description}): 0 occurrences")
        
        self.logger.info(f"Total characters: {len(text)}")
        return target_found
    
    def _show_context(self, text: str, term: str):
        """Show context around found term"""
        index = text.find(term)
        if index >= 0:
            start = max(0, index - 30)
            end = min(len(text), index + len(term) + 30)
            context = text[start:end].replace('\n', ' ')
            self.logger.info(f"  Context: ...{context}...")


class FileWriter:
    """Single responsibility: Write text to file"""
    
    def __init__(self, filename: str):
        self.filename = filename
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def write(self, text: str):
        """Write text to file"""
        try:
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write(text)
            self.logger.info(f"✓ Text saved to {self.filename}")
        except IOError as e:
            self.logger.error(f"Failed to write file: {e}")
            raise


# ===============================
# Application Facade (Single Entry Point)
# ===============================
class PDFExtractorApplication:
    """Main application coordinating all components"""
    
    def __init__(self, config: Config):
        self.config = config
        self._setup_logging()
        self._setup_components()
    
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s'
        )
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def _setup_components(self):
        """Initialize all components (Dependency Injection)"""
        self.url_converter = URLConverter()
        self.pdf_loader = HTTPPDFLoader(self.config.USER_AGENT)
        self.text_processor = JapaneseTextProcessor(self.config.TEXT_PATTERNS)
        self.ocr_extractor = OCRTextExtractor(self.config.OCR_CONFIGS, self.text_processor)
        self.pdf_extractor = PDFTextExtractor(self.ocr_extractor, self.text_processor)
        self.analyzer = TextAnalyzer(self.config.SEARCH_TERMS)
        self.writer = FileWriter(self.config.OUTPUT_FILE)
    
    def run(self) -> int:
        """Run the application"""
        try:
            self.logger.info("="*60)
            self.logger.info("PDF Text Extractor - SOLID Principles Version")
            self.logger.info("="*60)
            
            # Convert URL
            pdf_url = self.url_converter.html_to_pdf(self.config.TARGET_URL)
            self.logger.info(f"PDF URL: {pdf_url}")
            
            # Download PDF
            pdf_data = self.pdf_loader.load(pdf_url)
            
            # Extract text
            self.logger.info("\nExtracting text...")
            text = self.pdf_extractor.extract(pdf_data)
            
            # Save to file
            self.writer.write(text)
            
            # Analyze results
            target_found = self.analyzer.analyze(text)
            
            if target_found:
                self.logger.info("\n✓✓✓ SUCCESS: Target text successfully extracted!")
                return 0
            else:
                self.logger.info("\n⚠ Warning: Target text not found")
                return 1
                
        except Exception as e:
            self.logger.error(f"\n✗ Error: {e}")
            return 1


# ===============================
# Entry Point
# ===============================
def main():
    """Main entry point"""
    config = Config()
    app = PDFExtractorApplication(config)
    return app.run()


if __name__ == "__main__":
    sys.exit(main())