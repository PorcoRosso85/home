#!/usr/bin/env python3
import requests
import PyPDF2
import io
import sys

def download_pdf(url):
    """Download PDF from URL"""
    print(f"Downloading PDF from: {url}")
    response = requests.get(url, headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    response.raise_for_status()
    return io.BytesIO(response.content)

def extract_text_from_pdf(pdf_data):
    """Extract text from PDF using pypdf2"""
    reader = PyPDF2.PdfReader(pdf_data)
    text_parts = []
    
    print(f"Total pages: {len(reader.pages)}")
    
    for page_num, page in enumerate(reader.pages, 1):
        print(f"Processing page {page_num}...")
        page_text = page.extract_text()
        if page_text:
            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
    
    return "\n\n".join(text_parts)

def save_to_log(text, filename="log.txt"):
    """Save extracted text to log file"""
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Text saved to {filename}")
    
    # Show first 500 characters as preview
    preview = text[:500] if len(text) > 500 else text
    print(f"\nPreview of extracted text:\n{preview}...")
    print(f"\nTotal characters extracted: {len(text)}")

def main():
    # Target PDF URL (官報のPDF)
    # The HTML URL format: /20250903/20250903h01541/20250903h015410032f.html
    # The PDF URL format:  /20250903/20250903h01541/pdf/20250903h015410032.pdf
    html_url = "https://www.kanpo.go.jp/20250903/20250903h01541/20250903h015410032f.html"
    
    # Convert HTML URL to PDF URL based on 官報's pattern
    # Remove the 'f' from the end of the filename and add pdf/ prefix
    parts = html_url.split('/')
    date_part = parts[-3]  # 20250903
    issue_part = parts[-2]  # 20250903h01541
    filename = parts[-1].replace('f.html', '.pdf')  # 20250903h015410032f.html -> 20250903h015410032.pdf
    
    pdf_url = f"https://www.kanpo.go.jp/{date_part}/{issue_part}/pdf/{filename}"
    print(f"Using PDF URL: {pdf_url}")
    
    try:
        # Download PDF
        pdf_data = download_pdf(pdf_url)
        
        # Extract text
        text = extract_text_from_pdf(pdf_data)
        
        # Save to log
        save_to_log(text)
        
        print("\nPOC completed successfully!")
        return 0
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading PDF: {e}")
        return 1
    except PyPDF2.errors.PdfReadError as e:
        print(f"Error reading PDF: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())