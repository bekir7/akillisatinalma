from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".pdf"}


def list_quote_files(folder: Path) -> list[Path]:
    files = [
        p
        for p in sorted(folder.iterdir())
        if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    if not files:
        raise FileNotFoundError(f"Teklif dosyası bulunamadı: {folder}")
    return files


def read_quote_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return _read_csv(path)
    if suffix in {".xlsx", ".xls"}:
        return _read_excel(path)
    if suffix == ".pdf":
        return _read_pdf(path)
    raise ValueError(f"Desteklenmeyen dosya türü: {path.name}")


def _read_csv(path: Path) -> pd.DataFrame:
    for sep in (";", ",", "\t"):
        try:
            df = pd.read_csv(path, sep=sep, encoding="utf-8-sig")
            if df.shape[1] >= 3:
                return _attach_meta(df, path)
        except Exception:
            continue
    df = pd.read_csv(path, encoding="latin-1", sep=None, engine="python")
    return _attach_meta(df, path)


def _read_excel(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, engine="openpyxl")
    return _attach_meta(df, path)


def _read_pdf(path: Path) -> pd.DataFrame:
    """PDF içindeki tabloyu veya 'Alan: Değer' satırlarını okur."""
    rows: list[dict[str, Any]] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables() or []
            for table in tables:
                if not table or len(table) < 2:
                    continue
                header = [_clean_cell(c) for c in table[0]]
                for raw in table[1:]:
                    if not raw or all(c is None or str(c).strip() == "" for c in raw):
                        continue
                    row = {
                        header[i]: _clean_cell(raw[i]) if i < len(raw) else ""
                        for i in range(len(header))
                    }
                    rows.append(row)

            if not rows:
                text = page.extract_text() or ""
                parsed = _parse_key_value_pdf(text)
                if parsed:
                    rows.append(parsed)

    if not rows:
        raise ValueError(f"PDF'den tablo/veri çıkarılamadı: {path.name}")

    df = pd.DataFrame(rows)
    return _attach_meta(df, path)


def _parse_key_value_pdf(text: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    patterns = {
        "ürün kodu": r"(?:ürün\s*kodu|product\s*code|sku)\s*[:\-]\s*(.+)",
        "ürün adı": r"(?:ürün\s*adı|ürün|product)\s*[:\-]\s*(.+)",
        "birim fiyat": r"(?:birim\s*fiyat|unit\s*price|fiyat)\s*[:\-]\s*(.+)",
        "para birimi": r"(?:para\s*birimi|currency)\s*[:\-]\s*(.+)",
        "teslim süresi": r"(?:teslim\s*süresi|delivery)\s*[:\-]\s*(.+)",
        "ödeme vadesi": r"(?:ödeme\s*vadesi|payment)\s*[:\-]\s*(.+)",
        "miktar": r"(?:miktar|quantity|adet)\s*[:\-]\s*(.+)",
        "tedarikçi": r"(?:tedarikçi|firma|supplier)\s*[:\-]\s*(.+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            mapping[key] = match.group(1).strip()
    return mapping


def _clean_cell(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().replace("\n", " ")


def _attach_meta(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    out["_source_file"] = path.name
    out["_supplier_guess"] = _guess_supplier_from_filename(path)
    return out


def _guess_supplier_from_filename(path: Path) -> str:
    stem = path.stem
    stem = re.sub(r"(?i)(teklif|quote|fiyat|offer|_|\-)+", " ", stem)
    stem = re.sub(r"\s+", " ", stem).strip()
    return stem.title() if stem else path.stem
