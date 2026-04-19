# Runbook: PDF Payslip Merger

## 1. System Overview
**Application Name**: PDF Payslip Merger  
**Framework**: FastAPI (Python)  
**Port**: `8000` (Default)  
**Environment**: Local / Development  

## 2. Operational Procedures

### Starting the Application
Ensure you are in the application root directory (`/pdf-merger-fast-api/`).
```bash
poetry install
poetry run uvicorn main:app --reload
```
The application will be accessible at `http://127.0.0.1:8000`.

### Stopping the Application
Press `Ctrl + C` in the terminal where `uvicorn` is running.

### Cleaning Up Old Outputs
The application writes merged PDFs to the `merged_outputs/` directory locally. Over time, this folder may grow large and consume disk space.
To clean up processed files:
```bash
# Mac / Linux
rm -rf merged_outputs/*.pdf
```

## 3. Troubleshooting

### Issue: Port 8000 is already in use
**Symptom**: `uvicorn` throws an `[Errno 98] Address already in use` error when starting.
**Resolution**: Start the server on a different port:
```bash
poetry run uvicorn main:app --reload --port 8080
```

### Issue: `ModuleNotFoundError`
**Symptom**: Missing packages like `fastapi` or `PyPDF2` when attempting to run the app.
**Resolution**: The virtual environment hasn't been properly set up. Run `poetry install` to ensure the virtual environment has downloaded all dependencies.

### Issue: Merge failing for specific PDFs
**Symptom**: The application logs `Failed to process <filename>: <error>` in the terminal.
**Resolution**: 
1. Ensure the problematic PDF is not password-protected or encrypted. The tool currently does not bypass PDF passwords.
2. Verify the PDF is not corrupted by attempting to open it in a standard system PDF viewer.