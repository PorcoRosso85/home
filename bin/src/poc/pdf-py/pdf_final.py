#!/usr/bin/env python3
"""
PDF OCR extraction - Final version
Extracts "限定承認広告" and other Japanese text from PDFs correctly
"""
import requests
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import sys
import re

def download_pdf(url):
    """Download PDF from URL"""
    print(f"Downloading PDF from: {url}")
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    return io.BytesIO(response.content)

def process_text_layer(text):
    """Process extracted text to handle single character splits"""
    if not text.strip():
        return ""
    
    # Split into lines
    lines = text.split('\n')
    processed_lines = []
    char_buffer = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if char_buffer:
                # Flush the buffer when encountering empty line
                processed_lines.append(''.join(char_buffer))
                char_buffer = []
            continue
            
        # If line is a single character (common in vertical text converted to horizontal)
        if len(line) == 1:
            # Check if it's a Japanese character
            if any('\u3040' <= c <= '\u9fff' for c in line):
                char_buffer.append(line)
            else:
                if char_buffer:
                    processed_lines.append(''.join(char_buffer))
                    char_buffer = []
                processed_lines.append(line)
        else:
            if char_buffer:
                processed_lines.append(''.join(char_buffer))
                char_buffer = []
            processed_lines.append(line)
    
    # Don't forget remaining characters
    if char_buffer:
        processed_lines.append(''.join(char_buffer))
    
    # Join and clean up
    result = '\n'.join(processed_lines)
    
    # Fix common patterns where characters get split
    # Note: The actual term is 限定承認公告 (not 広告)
    result = re.sub(r'限\s*定\s*承\s*認\s*公\s*告', '限定承認公告', result)
    result = re.sub(r'限\s*定\s*承\s*認\s*広\s*告', '限定承認広告', result)
    result = re.sub(r'限\s*定\s*承\s*認', '限定承認', result)
    result = re.sub(r'資\s*本\s*金', '資本金', result)
    result = re.sub(r'債\s*権\s*者', '債権者', result)
    result = re.sub(r'相\s*続', '相続', result)
    
    return result

def extract_text_from_pdf(pdf_data):
    """Extract text from PDF including OCR on images"""
    doc = fitz.open(stream=pdf_data, filetype="pdf")
    all_text_parts = []
    
    print(f"Total pages: {doc.page_count}")
    
    for page_num in range(doc.page_count):
        print(f"\n=== Processing page {page_num + 1} ===")
        page = doc[page_num]
        page_texts = []
        
        # 1. Extract and process regular text layer
        regular_text = page.get_text("text")
        if regular_text.strip():
            processed_text = process_text_layer(regular_text)
            
            if processed_text:
                page_texts.append("--- Text Layer (Processed) ---")
                page_texts.append(processed_text)
                print(f"  Text layer: {len(processed_text)} characters extracted")
                
                # Check for key content
                if "限定承認公告" in processed_text:
                    print(f"  ✓✓✓ Found '限定承認公告' in text layer!")
                elif "限定承認広告" in processed_text:
                    print(f"  ✓✓✓ Found '限定承認広告' in text layer!")
                elif "限定承認" in processed_text:
                    print(f"  ✓ Found '限定承認' in text layer")
        
        # 2. Also try extracting raw blocks for better structure
        blocks = page.get_text("blocks")
        if blocks:
            block_texts = []
            for block in blocks:
                if block[6] == 0:  # text block (not image)
                    block_text = block[4].strip()
                    if block_text:
                        # Process each block
                        processed_block = process_text_layer(block_text)
                        if processed_block:
                            block_texts.append(processed_block)
            
            if block_texts:
                combined_blocks = '\n'.join(block_texts)
                page_texts.append("\n--- Text Blocks (Combined) ---")
                page_texts.append(combined_blocks)
                
                if "限定承認公告" in combined_blocks:
                    print(f"  ✓✓✓ Found '限定承認公告' in text blocks!")
                elif "限定承認広告" in combined_blocks:
                    print(f"  ✓✓✓ Found '限定承認広告' in text blocks!")
        
        # 3. Extract images and perform OCR
        image_list = page.get_images()
        if image_list:
            print(f"  Found {len(image_list)} image(s), performing OCR...")
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # Convert to PIL Image for OCR
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.pil_tobytes(format="PNG")
                else:  # CMYK
                    pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    img_data = pix1.pil_tobytes(format="PNG")
                    pix1 = None
                
                # Open with PIL
                pil_image = Image.open(io.BytesIO(img_data))
                
                # Perform OCR with Japanese language
                try:
                    # Try multiple OCR configurations
                    configs = [
                        ('jpn_vert', '--psm 5'),  # Vertical text (best for Japanese official documents)
                        ('jpn', '--psm 6'),  # Uniform block of text
                        ('jpn', '--psm 3'),  # Fully automatic page segmentation
                        ('jpn', '--psm 11'), # Sparse text
                        ('jpn', '--psm 4'),  # Single column of text
                    ]
                    
                    best_text = ""
                    for lang, config in configs:
                        try:
                            ocr_text = pytesseract.image_to_string(pil_image, lang=lang, config=config)
                            if ocr_text.strip():
                                # Process the OCR text
                                processed_ocr = process_text_layer(ocr_text)
                                if "限定承認広告" in processed_ocr or len(processed_ocr) > len(best_text):
                                    best_text = processed_ocr
                                    if "限定承認公告" in processed_ocr or "限定承認広告" in processed_ocr:
                                        break  # Found what we're looking for
                        except:
                            pass
                    
                    if best_text:
                        page_texts.append(f"\n--- OCR from Image {img_index + 1} ---")
                        page_texts.append(best_text)
                        print(f"    Image {img_index + 1}: {len(best_text)} characters extracted via OCR")
                        
                        if "限定承認公告" in best_text:
                            print(f"    ✓✓✓ Found '限定承認公告' in image {img_index + 1}!")
                        elif "限定承認広告" in best_text:
                            print(f"    ✓✓✓ Found '限定承認広告' in image {img_index + 1}!")
                        elif "限定承認" in best_text:
                            print(f"    ✓ Found '限定承認' in image {img_index + 1}")
                            
                except Exception as e:
                    print(f"    OCR error: {e}")
                
                pix = None
        
        # 4. Try rendering page as image for full-page OCR
        if page_num == 0:  # Focus on first page where the text likely is
            print("  Rendering full page as image for OCR...")
            try:
                # Render page at high resolution
                mat = fitz.Matrix(2, 2)  # 2x zoom for better OCR
                pix = page.get_pixmap(matrix=mat)
                img_data = pix.pil_tobytes(format="PNG")
                
                # Save for debugging
                with open(f"page_{page_num + 1}_rendered.png", "wb") as f:
                    f.write(img_data)
                
                pil_image = Image.open(io.BytesIO(img_data))
                
                # OCR the full page - try vertical text first
                try:
                    # Try vertical text mode first (better for Japanese official documents)
                    full_page_text = pytesseract.image_to_string(pil_image, lang='jpn_vert', config='--psm 5')
                    if not full_page_text.strip():
                        # Fallback to regular mode
                        full_page_text = pytesseract.image_to_string(pil_image, lang='jpn', config='--psm 6')
                    
                    if full_page_text.strip():
                        processed_full = process_text_layer(full_page_text)
                        page_texts.append("\n--- Full Page OCR ---")
                        page_texts.append(processed_full)
                        print(f"  Full page OCR: {len(processed_full)} characters")
                        
                        if "限定承認公告" in processed_full:
                            print(f"  ✓✓✓ Found '限定承認公告' in full page OCR!")
                        elif "限定承認広告" in processed_full:
                            print(f"  ✓✓✓ Found '限定承認広告' in full page OCR!")
                except Exception as e:
                    print(f"  Full page OCR error: {e}")
                
                pix = None
            except Exception as e:
                print(f"  Page rendering error: {e}")
        
        # Combine all text from this page
        if page_texts:
            all_text_parts.append(f"=== Page {page_num + 1} ===\n" + "\n".join(page_texts))
    
    doc.close()
    return "\n\n".join(all_text_parts)

def save_to_log(text, filename="log_final.txt"):
    """Save extracted text to log file and analyze content"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"\n✓ Text saved to {filename}")
    
    # Show preview focusing on key terms
    print("\n=== 検索結果 ===")
    search_terms = [
        ("限定承認公告", "Limited acceptance announcement"),
        ("限定承認広告", "Limited acceptance notice"),
        ("限定承認", "Limited acceptance"),
        ("資本金の額の減少公告", "Capital reduction notice"),
        ("相続", "Inheritance"),
        ("債権者", "Creditor"),
    ]
    
    found_key_term = False
    for term, description in search_terms:
        if term in text:
            count = text.count(term)
            print(f"✓ '{term}' ({description}): {count} 件")
            if term == "限定承認公告" or term == "限定承認広告":
                found_key_term = True
                # Show context around the term
                index = text.find(term)
                start = max(0, index - 50)
                end = min(len(text), index + len(term) + 50)
                context = text[start:end].replace('\n', ' ')
                print(f"  Context: ...{context}...")
        else:
            print(f"✗ '{term}' ({description}): 0 件")
    
    print(f"\nTotal characters extracted: {len(text)}")
    
    if not found_key_term:
        # Try alternative search with spaces
        if "限" in text and "定" in text and "承" in text and "認" in text and "広" in text and "告" in text:
            print("\n⚠ Individual characters found but not as continuous string")
            print("  Attempting to locate separated characters...")
            
            # Find positions of each character
            positions = {
                "限": [i for i, c in enumerate(text) if c == "限"],
                "定": [i for i, c in enumerate(text) if c == "定"],
                "承": [i for i, c in enumerate(text) if c == "承"],
                "認": [i for i, c in enumerate(text) if c == "認"],
                "広": [i for i, c in enumerate(text) if c == "広"],
                "告": [i for i, c in enumerate(text) if c == "告"],
            }
            
            # Check if they appear in sequence within reasonable distance
            for p1 in positions["限"]:
                for p2 in positions["定"]:
                    if 0 < p2 - p1 < 10:  # Within 10 characters
                        for p3 in positions["承"]:
                            if 0 < p3 - p2 < 10:
                                for p4 in positions["認"]:
                                    if 0 < p4 - p3 < 10:
                                        for p5 in positions["広"]:
                                            if 0 < p5 - p4 < 10:
                                                for p6 in positions["告"]:
                                                    if 0 < p6 - p5 < 10:
                                                        print(f"  Found sequence at positions: {p1},{p2},{p3},{p4},{p5},{p6}")
                                                        context = text[p1:p6+1]
                                                        print(f"  Raw text: {repr(context)}")
    
    return found_key_term

def main():
    print("="*60)
    print("PDF Text Extraction - Final Version")
    print("Target: Extract '限定承認広告' from official gazette PDF")
    print("="*60)
    
    # Target PDF URL
    html_url = "https://www.kanpo.go.jp/20250903/20250903h01541/20250903h015410032f.html"
    
    # Convert HTML URL to PDF URL
    parts = html_url.split('/')
    date_part = parts[-3]
    issue_part = parts[-2]
    filename = parts[-1].replace('f.html', '.pdf')
    
    pdf_url = f"https://www.kanpo.go.jp/{date_part}/{issue_part}/pdf/{filename}"
    print(f"PDF URL: {pdf_url}")
    
    try:
        # Download PDF
        pdf_data = download_pdf(pdf_url)
        
        # Extract text with enhanced processing
        print("\nExtracting text with enhanced processing...")
        text = extract_text_from_pdf(pdf_data)
        
        # Save to log and analyze
        found = save_to_log(text)
        
        if found:
            print("\n✓✓✓ SUCCESS: '限定承認広告' was successfully extracted!")
        else:
            print("\n⚠ Warning: '限定承認広告' not found as exact string")
            print("  The characters may be present but separated")
        
        return 0 if found else 1
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Error downloading PDF: {e}")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())