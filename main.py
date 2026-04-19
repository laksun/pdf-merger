import os
import time
import re
from pathlib import Path
from typing import List, Set
from fastapi import FastAPI, HTTPException, Form, File, UploadFile
from fastapi.responses import HTMLResponse
from PyPDF2 import PdfWriter, PdfReader

app = FastAPI(title="PDF Payslip Merger")

def get_html_header(title: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 40px; background-color: #f9f9f9; color: #333; }}
            .container {{ max-width: 800px; margin: auto; background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
            h1 {{ color: #2c3e50; }}
            input[type="text"] {{ width: 100%; padding: 10px; margin: 10px 0 20px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }}
            button {{ background-color: #007aff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }}
            button:hover {{ background-color: #005bb5; }}
            .success {{ color: #28a745; font-weight: bold; }}
            .file-list {{ background: #f1f1f1; padding: 15px; border-radius: 4px; font-family: monospace; overflow-x: auto; }}
            a.back-link {{ display: inline-block; margin-top: 20px; color: #007aff; text-decoration: none; }}
        </style>
    </head>
    <body>
        <div class="container">
    """

def get_html_footer() -> str:
    return """
        </div>
    </body>
    </html>
    """

@app.get("/", response_class=HTMLResponse)
async def serve_form():
    """Serves the input form to the user."""
    html_content = get_html_header("PDF Payslip Merger") + """
        <h1>Merge Your Payslips</h1>
        <p>Select the folder containing your PDF files and specify the maximum file size. The app will automatically read the files, sort them by date, ignore duplicates, and split outputs at your specified limit.</p>
        <form action="/merge/" method="post" enctype="multipart/form-data">
            <label for="max_size_mb">Max File Size (MB):</label>
            <input type="number" id="max_size_mb" name="max_size_mb" value="5.0" min="0.5" step="0.1" required>
            <label for="folder_picker">Select Folder:</label>
            <input type="file" id="folder_picker" name="files" webkitdirectory directory multiple required>
            <button type="submit">Merge PDFs</button>
        </form>
    """ + get_html_footer()
    return html_content

@app.post("/merge/", response_class=HTMLResponse)
async def merge_pdfs(files: List[UploadFile] = File(...), max_size_mb: float = Form(5.0)):
    """Processes the PDFs and generates the report."""

    # 1. Fetch, Deduplicate, and Filter Files
    unique_names: Set[str] = set()
    pdf_files: List[UploadFile] = []
    
    for f in files:
        filename = Path(f.filename).name
        
        if not filename.lower().endswith(".pdf"):
            continue
            
        # Ignore already merged files from previous runs to prevent loops
        if filename.startswith("merged_payslips_"):
            continue
        
        # Deduplicate files based on file name
        if filename not in unique_names:
            unique_names.add(filename)
            pdf_files.append(f)

    if not pdf_files:
        return HTMLResponse(content=get_html_header("No Files") + """
            <h1>No valid PDFs found</h1>
            <p>No new PDF files were found in the selected directory.</p>
            <a href="/" class="back-link">← Back</a>
        """ + get_html_footer())

    # 2. Sort by Date Segment in Descending Order
    def extract_sort_key(upload_file: UploadFile):
        name = Path(upload_file.filename).name
        
        # Check for YYYY-MM-DD format (e.g., 2025-09-10_Statement)
        match_dashed = re.search(r'(\d{4})-(\d{2})-(\d{2})', name)
        if match_dashed:
            return "".join(match_dashed.groups())  # normalizes to 'YYYYMMDD' for uniform sorting
            
        # Check for YYYYMMDD format
        match_solid = re.search(r'(\d{8})', name)
        if match_solid:
            return match_solid.group(1)
            
        # Fallback to the original splitting logic
        if '_' in name:
            parts = name.split('_')
            if len(parts) > 1:
                return parts[1] # e.g., '20250411'
        return name
        
    pdf_files.sort(key=extract_sort_key, reverse=True)

    # 3. Merge and enforce user-defined size limit
    max_size_bytes = (max_size_mb * 0.95) * 1024 * 1024  # 95% threshold to prevent breaching absolute limit
    run_timestamp = int(time.time())
    output_files_created = []
    files_merged_count = 0
    
    writer = PdfWriter()
    batch_number = 1
    
    # Create a dedicated local output directory since we don't know the absolute source path anymore
    output_dir = Path("merged_outputs")
    output_dir.mkdir(exist_ok=True)
    
    current_output_name = f"merged_payslips_{run_timestamp}_part_{batch_number}.pdf"
    current_output_path = output_dir / current_output_name
    
    for pdf in pdf_files:
        try:
            reader = PdfReader(pdf.file)
            for page in reader.pages:
                writer.add_page(page)
            files_merged_count += 1
            
            # Save current progress
            with open(current_output_path, "wb") as f:
                writer.write(f)
            
            # Check size after adding this file. 
            # If it exceeds the safe threshold, set up a new file for the *next* iterations.
            if os.path.getsize(current_output_path) > max_size_bytes:
                output_files_created.append(current_output_path)
                batch_number += 1
                writer = PdfWriter()
                current_output_name = f"merged_payslips_{run_timestamp}_part_{batch_number}.pdf"
                current_output_path = output_dir / current_output_name
                
        except Exception as e:
            print(f"Failed to process {pdf.filename}: {e}")

    # Capture the final batch if it wasn't already appended
    if current_output_path.exists() and current_output_path not in output_files_created:
        output_files_created.append(current_output_path)

    # 4. Generate Output Report HTML
    file_list_html = "".join([f"<li>{file.resolve()}</li>" for file in output_files_created])
    
    html_content = get_html_header("Merge Complete") + f"""
        <h1>Merge Completed Successfully</h1>
        <p class="success">Successfully processed and merged {files_merged_count} PDF files!</p>
        
        <h3>Output Details:</h3>
        <p>Because of the {max_size_mb}MB size limit, your output was split into <strong>{len(output_files_created)}</strong> file(s).</p>
        
        <div class="file-list">
            <ul>
                {file_list_html}
            </ul>
        </div>
        
        <a href="/" class="back-link">← Merge More Files</a>
    """ + get_html_footer()
    
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    # Starts the web server on port 8000
    print("Starting server... Open http://127.0.0.1:8000 in your web browser.")
    uvicorn.run(app, host="127.0.0.1", port=8000)