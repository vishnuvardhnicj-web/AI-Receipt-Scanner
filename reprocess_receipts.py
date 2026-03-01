from pathlib import Path
import os
from app import app, Receipt, db, extract_fields, EASYOCR_OK
from PIL import Image, ImageOps, ImageFilter
import easyocr


SEARCH_DIRS = [Path(app.config['UPLOAD_FOLDER']), Path.home() / 'Downloads', Path.home() / 'Desktop', Path.home() / 'Documents', Path.home() / 'Pictures']


def find_file(filename):
    for d in SEARCH_DIRS:
        p = d / filename
        if p.exists():
            return p
    # last resort: walk user's home (may be slow)
    home = Path.home()
    for dirpath, dirnames, filenames in os.walk(str(home)):
        if filename in filenames:
            return Path(dirpath) / filename
    return None


def ocr_file(p: Path):
    if not p or not p.exists():
        return ''
    suffix = p.suffix.lower()
    if suffix == '.pdf':
        return ''
    try:
        img = Image.open(p)
    except Exception:
        return ''

    # Only use EasyOCR here
    if not EASYOCR_OK:
        return ''
    try:
        reader = easyocr.Reader(['en'], gpu=False)
        results = reader.readtext(str(p))
        text = '\n'.join([r[1] for r in results if r and len(r) > 1])
        return text
    except Exception:
        return ''


def main():
    with app.app_context():
        receipts = Receipt.query.order_by(Receipt.id).all()
        updated = 0
        for r in receipts:
            use_text = ''
            raw = (r.raw_text or '').strip()
            if raw and not raw.startswith('['):
                use_text = raw
            else:
                # try to locate file and OCR it
                p = find_file(r.filename)
                if p:
                    use_text = ocr_file(p)
            if not use_text:
                # nothing to extract
                continue
            fields = extract_fields(use_text)
            changed = False
            # always update raw_text if different
            if r.raw_text != fields.get('raw_text'):
                r.raw_text = fields.get('raw_text')
                changed = True

            # vendor: prefer extracted, fallback to first OCR line
            vendor_val = fields.get('vendor') or ''
            if not vendor_val:
                first_line = ''
                for ln in use_text.splitlines():
                    ln = ln.strip()
                    if ln:
                        first_line = ln
                        break
                vendor_val = first_line
            if (r.vendor or '') != (vendor_val or ''):
                r.vendor = vendor_val
                changed = True

            # date: prefer extracted, fallback to more patterns
            date_val = fields.get('date') or ''
            if not date_val:
                m = None
                m = re.search(r"Date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", use_text, flags=re.IGNORECASE)
                if m:
                    date_val = m.group(1)
            if (r.date or '') != (date_val or ''):
                r.date = date_val
                changed = True

            # total: prefer extracted, fallback to 'amount' or last decimal number
            total_val = fields.get('total') or ''
            if not total_val:
                m = re.search(r"(?:total|amount due|amount|grand total)[:\s]*([0-9]{1,3}(?:,[0-9]{3})*[.,][0-9]{2})", use_text, flags=re.IGNORECASE)
                if m:
                    total_val = m.group(1)
                else:
                    m2 = re.findall(r"([0-9]{1,3}(?:,[0-9]{3})*[.,][0-9]{2})", use_text)
                    if m2:
                        total_val = max(m2, key=lambda s: len(s.replace(",", "")))
            # normalize before saving
            if total_val:
                total_val = total_val.replace(",", "")
            if (r.total or '') != (total_val or ''):
                r.total = total_val
                changed = True

            # currency and receipt number
            currency_val = fields.get('currency') or ''
            if (r.currency or '') != (currency_val or ''):
                r.currency = currency_val
                changed = True
            receipt_val = fields.get('receipt_number') or ''
            if (r.receipt_number or '') != (receipt_val or ''):
                r.receipt_number = receipt_val
                changed = True
            if changed:
                updated += 1
        if updated:
            db.session.commit()
        print('Reprocessed', updated, 'receipts')


if __name__ == '__main__':
    main()
