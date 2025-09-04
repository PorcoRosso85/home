#!/usr/bin/env python3
"""
Simple OCR Detection for PDFs
Detects whether OCR is needed based on text layer density and image overlap
"""
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import logging


@dataclass
class TextBlock:
    """Represents a text block with position"""
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    
    @property
    def area(self) -> float:
        """Calculate area of text block"""
        return (self.x1 - self.x0) * (self.y1 - self.y0)
    
    def overlaps(self, other: 'TextBlock') -> bool:
        """Check if this block overlaps with another"""
        return not (self.x1 < other.x0 or self.x0 > other.x1 or
                   self.y1 < other.y0 or self.y0 > other.y1)


@dataclass
class ImageRegion:
    """Represents an image region"""
    x0: float
    y0: float
    x1: float
    y1: float
    
    @property
    def area(self) -> float:
        """Calculate area of image region"""
        return (self.x1 - self.x0) * (self.y1 - self.y0)


class SimpleOCRDetector:
    """Simple OCR necessity detector"""
    
    def __init__(self, density_threshold: float = 0.7):
        """
        Initialize detector
        
        Args:
            density_threshold: Minimum text density (text area / page area)
                              Below this threshold, OCR is needed
        """
        self.density_threshold = density_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def analyze_page(self, page) -> Dict:
        """
        Analyze a single page for OCR necessity
        
        Returns:
            Dict with analysis results
        """
        page_rect = page.rect
        page_area = page_rect.width * page_rect.height
        
        # Get text blocks with positions
        text_blocks = self._get_text_blocks(page)
        
        # Get image regions
        image_regions = self._get_image_regions(page)
        
        # Calculate text density
        text_area = sum(block.area for block in text_blocks)
        text_density = text_area / page_area if page_area > 0 else 0
        
        # Check for text-image overlap
        has_text_over_images = self._check_text_image_overlap(text_blocks, image_regions)
        
        # Determine if OCR is needed
        needs_ocr = (
            text_density < self.density_threshold or  # Low text density
            (len(image_regions) > 0 and not has_text_over_images)  # Images without text
        )
        
        return {
            'page_area': page_area,
            'text_blocks': len(text_blocks),
            'text_area': text_area,
            'text_density': text_density,
            'image_regions': len(image_regions),
            'has_text_over_images': has_text_over_images,
            'needs_ocr': needs_ocr,
            'raw_text': page.get_text("text")
        }
    
    def _get_text_blocks(self, page) -> List[TextBlock]:
        """Extract text blocks with coordinates"""
        blocks = []
        for block in page.get_text("blocks"):
            if block[6] == 0:  # Text block (not image)
                blocks.append(TextBlock(
                    x0=block[0],
                    y0=block[1],
                    x1=block[2],
                    y1=block[3],
                    text=block[4]
                ))
        return blocks
    
    def _get_image_regions(self, page) -> List[ImageRegion]:
        """Extract image regions"""
        regions = []
        for img in page.get_images():
            # Get image position
            xref = img[0]
            rects = page.get_image_rects(xref)
            for rect in rects:
                regions.append(ImageRegion(
                    x0=rect.x0,
                    y0=rect.y0,
                    x1=rect.x1,
                    y1=rect.y1
                ))
        return regions
    
    def _check_text_image_overlap(self, text_blocks: List[TextBlock], 
                                  image_regions: List[ImageRegion]) -> bool:
        """Check if text blocks overlap with image regions"""
        for text in text_blocks:
            for img in image_regions:
                # Simple overlap check
                if not (text.x1 < img.x0 or text.x0 > img.x1 or
                       text.y1 < img.y0 or text.y0 > img.y1):
                    return True
        return False
    
    def process_pdf(self, pdf_path: str, target_text: str = "千葉県佐倉市海隣寺町") -> Dict:
        """
        Process entire PDF and search for target text
        
        Args:
            pdf_path: Path to PDF file
            target_text: Text to search for
            
        Returns:
            Dict with processing results
        """
        doc = fitz.open(pdf_path)
        results = {
            'total_pages': doc.page_count,
            'pages_needing_ocr': [],
            'target_found_text_layer': False,
            'target_found_ocr': False,
            'extracted_text': []
        }
        
        try:
            for page_num in range(doc.page_count):
                page = doc[page_num]
                
                # Analyze page
                analysis = self.analyze_page(page)
                
                # Check if target is in text layer
                if target_text in analysis['raw_text']:
                    results['target_found_text_layer'] = True
                    self.logger.info(f"✓ Found '{target_text}' in text layer on page {page_num + 1}")
                
                # If OCR is needed, perform it
                if analysis['needs_ocr']:
                    results['pages_needing_ocr'].append(page_num + 1)
                    
                    # Perform OCR
                    ocr_text = self._perform_page_ocr(page)
                    if ocr_text:
                        results['extracted_text'].append(f"Page {page_num + 1} (OCR):\n{ocr_text}")
                        
                        if target_text in ocr_text:
                            results['target_found_ocr'] = True
                            self.logger.info(f"✓ Found '{target_text}' via OCR on page {page_num + 1}")
                else:
                    # Just use text layer
                    results['extracted_text'].append(f"Page {page_num + 1} (Text Layer):\n{analysis['raw_text']}")
                
                # Log analysis
                self.logger.info(f"Page {page_num + 1}: Density={analysis['text_density']:.2%}, "
                               f"Text blocks={analysis['text_blocks']}, "
                               f"Images={analysis['image_regions']}, "
                               f"Needs OCR={analysis['needs_ocr']}")
        
        finally:
            doc.close()
        
        return results
    
    def _perform_page_ocr(self, page) -> str:
        """Perform OCR on a page"""
        try:
            # Render page as image
            mat = fitz.Matrix(2, 2)  # 2x zoom
            pix = page.get_pixmap(matrix=mat)
            img_data = pix.pil_tobytes(format="PNG")
            pix = None
            
            # OCR with Japanese
            image = Image.open(io.BytesIO(img_data))
            text = pytesseract.image_to_string(image, lang='jpn')
            
            return text
        except Exception as e:
            self.logger.error(f"OCR failed: {e}")
            return ""


def download_test_pdfs():
    """Download test PDFs from kanpo"""
    import requests
    
    test_urls = {
        'test1.pdf': 'https://www.kanpo.go.jp/20250903/20250903h01541/pdf/20250903h015410001.pdf',
        'test2.pdf': 'https://www.kanpo.go.jp/20250903/20250903h01541/pdf/20250903h015410002.pdf',
    }
    
    for filename, url in test_urls.items():
        print(f"Downloading {filename} from {url}")
        try:
            response = requests.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()
            
            with open(filename, 'wb') as f:
                f.write(response.content)
            print(f"✓ Saved {filename}")
        except Exception as e:
            print(f"✗ Failed to download {filename}: {e}")


def main():
    """Main entry point"""
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    
    print("="*60)
    print("Simple OCR Detection Demo")
    print("="*60)
    
    # Download test PDFs
    download_test_pdfs()
    
    # Initialize detector (force OCR with high threshold)
    detector = SimpleOCRDetector(density_threshold=0.7)
    
    # Process test PDFs
    for pdf_file in ['test1.pdf', 'test2.pdf']:
        print(f"\n--- Processing {pdf_file} ---")
        
        try:
            results = detector.process_pdf(pdf_file, target_text="千葉県佐倉市海隣寺町")
            
            print(f"Total pages: {results['total_pages']}")
            print(f"Pages needing OCR: {results['pages_needing_ocr']}")
            print(f"Target found in text layer: {results['target_found_text_layer']}")
            print(f"Target found via OCR: {results['target_found_ocr']}")
            
            # Save extracted text
            output_file = pdf_file.replace('.pdf', '_extracted.txt')
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(results['extracted_text']))
            print(f"✓ Extracted text saved to {output_file}")
            
            # Search for target in saved file
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "千葉県佐倉市海隣寺町" in content:
                    print(f"✓✓✓ SUCCESS: Found '千葉県佐倉市海隣寺町' in {pdf_file}!")
                else:
                    print(f"⚠ Warning: '千葉県佐倉市海隣寺町' not found in {pdf_file}")
                    
        except Exception as e:
            print(f"✗ Error processing {pdf_file}: {e}")
    
    print("\n" + "="*60)
    print("OCR Detection Complete")
    print("="*60)


if __name__ == "__main__":
    main()