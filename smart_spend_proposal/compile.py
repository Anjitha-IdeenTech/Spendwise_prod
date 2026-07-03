#!/usr/bin/env python3
import os
import subprocess
import sys
import re

def main():
    print("=== Smart Spend Proposal Compilation Script ===")
    
    html_file = "proposal.html"
    pdf_file = "proposal.pdf"
    preview_dir = "preview"
    
    if not os.path.exists(html_file):
        print(f"Error: {html_file} not found in the current directory.")
        sys.exit(1)
        
    print(f"1. Compiling {html_file} to {pdf_file} using wkhtmltopdf...")
    
    # Run wkhtmltopdf with margins set to 0 to respect the CSS A4 sizing
    cmd = [
        "wkhtmltopdf",
        "--page-size", "A4",
        "--margin-top", "0",
        "--margin-bottom", "0",
        "--margin-left", "0",
        "--margin-right", "0",
        "--enable-local-file-access",
        html_file,
        pdf_file
    ]
    
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        print("✓ Compilation successful.")
    except subprocess.CalledProcessError as e:
        print("✗ Compilation failed.")
        print("stdout:", e.stdout)
        print("stderr:", e.stderr)
        sys.exit(1)
        
    print("2. Verifying PDF Page Count...")
    try:
        info_result = subprocess.run(["pdfinfo", pdf_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        pages_match = re.search(r"Pages:\s+(\d+)", info_result.stdout)
        if pages_match:
            page_count = int(pages_match.group(1))
            print(f"✓ Detected page count: {page_count}")
            if page_count != 12:
                print(f"⚠️ WARNING: Page count is {page_count}, expected exactly 12!")
            else:
                print("✓ Page count matches the target structure exactly (12 pages).")
        else:
            print("⚠️ WARNING: Could not parse page count from pdfinfo output.")
    except Exception as e:
        print(f"⚠️ WARNING: Failed to get pdfinfo: {e}")
        
    print(f"3. Rendering PDF pages to images in '{preview_dir}/' using pdftoppm...")
    if not os.path.exists(preview_dir):
        os.makedirs(preview_dir)
    else:
        # Clear existing preview files
        for f in os.listdir(preview_dir):
            if f.endswith(".png"):
                os.remove(os.path.join(preview_dir, f))
                
    pdftoppm_cmd = [
        "pdftoppm",
        "-png",
        "-r", "150",
        pdf_file,
        os.path.join(preview_dir, "page")
    ]
    
    try:
        subprocess.run(pdftoppm_cmd, check=True)
        pngs = sorted([f for f in os.listdir(preview_dir) if f.endswith(".png")])
        print(f"✓ Successfully rendered {len(pngs)} preview pages:")
        for png in pngs:
            print(f"  - {os.path.join(preview_dir, png)}")
    except Exception as e:
        print(f"✗ Failed to render preview images: {e}")
        sys.exit(1)
        
    print("=== Done ===")

if __name__ == "__main__":
    main()
