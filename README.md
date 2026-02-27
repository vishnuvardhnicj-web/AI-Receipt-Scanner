# AI Receipt Scanner

Simple Flask app to upload receipts, run OCR, extract key fields, store in SQLite, and export CSVs.

Setup

1. Create a Python virtual environment and activate it.

```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate # macOS / Linux
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Install EasyOCR (only supported OCR engine)

- Activate your virtualenv then install dependencies:

```powershell
venv\Scripts\activate
pip install -r requirements.txt
```

This project uses EasyOCR for all OCR extraction. PDF-to-image conversion is not included; upload images (PNG, JPG) for OCR. If you need PDF support, convert PDFs to images before uploading.

Run

```bash
python app.py
```

Open http://127.0.0.1:5000 in your browser. Register a user, then upload receipt images.

Export

Use the export form on the home page or visit `/export?start=2023-01-01&end=2023-12-31` to download a CSV for a date range.

Upload

When uploading a receipt you can optionally provide the date manually; OCR extraction will still run but any date you enter will be stored instead of the guessed value.

Notes

- This is a minimal demo. For production, secure sessions, add file validation, and harden OCR handling.
- The SQLite DB is `receipts.db` in the project root.
