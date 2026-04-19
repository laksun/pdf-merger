# PDF Payslip Merger

A fast, lightweight web application built with FastAPI to easily merge multiple PDF payslips into consolidated files.

## Features
- **Smart Sorting**: Automatically extracts dates from filenames (e.g., `YYYY-MM-DD` or `YYYYMMDD`) and merges them in descending order (newest first).
- **Deduplication**: Ignores already merged output files to prevent infinite loops and deduplicates identical filenames.
- **Size Management**: Allows users to specify a maximum file size limit (in MB). The application will automatically split the output into multiple parts if the merged file exceeds the limit.
- **Folder Upload**: Native web folder selection to safely parse multiple PDFs at once.

## Prerequisites
- Python 3.9+
- Poetry (Recommended for dependency management)

## Installation

1. Clone the repository and navigate to the project folder.
2. Install dependencies using Poetry:
   ```bash
   poetry install
   ```
   *(Alternatively, if you are not using Poetry, you can use pip: `pip install fastapi uvicorn PyPDF2 python-multipart`)*

## Usage

1. Start the FastAPI development server:
   ```bash
   poetry run uvicorn main:app --reload
   ```
2. Open your web browser and navigate to: http://127.0.0.1:8000
3. Enter your desired **Max File Size (MB)**.
4. Click **Choose Files** (or Select Folder) and pick the directory containing your PDFs.
5. Click **Merge PDFs**.

## Outputs
The merged files will be securely generated and saved in the `merged_outputs/` directory located in the root of the project.