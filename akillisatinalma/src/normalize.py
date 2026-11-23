from __future__ import annotations

import re
from typing import Any, Optional

import pandas as pd

from .models import QuoteLine


# Demo için sabit kurlar (TRY bazlı karşılaştırma).
# Gerçek kullanımda ERP / TCMB kur servisine bağlanabilir.
FX_TO_TRY: dict[str, float] = {
    "TRY": 1.0,
    "TL": 1.0,
    "EUR": 38.5,
    "USD": 35.0,
    "GBP": 44.0,
}


# Farklı tedarikçi şablonlarındaki sütun adları → standart alan
COLUMN_ALIASES: dict[str, list[str]] = {
    "supplier": [
        "tedarikçi",
        "tedarikci",
        "firma",
        "şirket",
        "sirket",
        "supplier",
        "vendor",
        "company",
    ],
    "product_code": [
        "ürün kodu",
        "urun kodu",
        "stok kodu",
        "malzeme kodu",
        "kod",
        "sku",
        "item code",
        "product code",
        "part no",
        "part_no",
    ],
    "product_name": [
        "ürün adı",
        "urun adi",
        "urun adn",  # PDF OCR/encoding bozulması
        "ürün",
        "urun",
        "malzeme",
        "açıklama",
        "aciklama",
        "kalem",
        "product",
        "product name",
        "description",
        "item",
    ],
    "unit_price": [
        "birim fiyat",
        "birim_fiyat",
        "fiyat",
        "unit price",
        "price",
        "unit_price",
        "net fiyat",
        "birim fiyat (tl)",
        "birim fiyat try",
    ],
    "currency": [
        "para birimi",
        "currency",
        "pb",
        "döviz",
        "doviz",
    ],
    "delivery_days": [
        "teslim süresi",
        "teslim suresi",
        "teslimat",
        "teslim gün",
        "teslim gun",
        "delivery",
        "delivery days",
        "lead time",
        "lead_time",
    ],
    "payment_days": [
        "ödeme vadesi",
        "odeme vadesi",
        "vade",
        "ödeme",
        "odeme",
        "payment",
        "payment terms",
        "payment_days",
    ],
    "quantity": [
        "miktar",
        "adet",
        "quantity",
        "qty",
        "miktar (adet)",
    ],
    "unit": [
        "birim",
        "unit",
        "ölçü birimi",
        "olcu birimi",
        "uom",
    ],
    "notes": [
        "not",
        "notes",
        "açıklama notu",
        "aciklama notu",
        "remark",
    ],
}


def normalize_dataframe(df: pd.DataFrame) -> list[QuoteLine]:
    mapping = _map_columns(df.columns.tolist())
    lines: list[QuoteLine] = []

    for _, row in df.iterrows():
        try:
            line = _row_to_quote(row, mapping)
        except ValueError:
            continue
        if line is not None:
            lines.append(line)
    return lines


def _map_columns(columns: list[str]) -> dict[str, str]:
    normalized = {c: _slug(c) for c in columns}
    mapping: dict[str, str] = {}

    for field, aliases in COLUMN_ALIASES.items():
        alias_slugs = {_slug(a) for a in aliases}
        for original, slug in normalized.items():
            if original.startswith("_"):
                continue
            if slug in alias_slugs and field not in mapping:
                mapping[field] = original
                break
    return mapping


def _slug(text: str) -> str:
    text = str(text).strip().lower()
    text = (
        text.replace("ı", "i")
        .replace("ğ", "g")
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ö", "o")
        .replace("ç", "c")
    )
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _row_to_quote(row: pd.Series, mapping: dict[str, str]) -> Optional[QuoteLine]:
    source_file = str(row.get("_source_file", ""))
    supplier_guess = str(row.get("_supplier_guess", ""))

    supplier = _get(row, mapping, "supplier") or supplier_guess
    product_code = _get(row, mapping, "product_code")
    product_name = _get(row, mapping, "product_name") or product_code
    unit_price_raw = _get(row, mapping, "unit_price")
    delivery_raw = _get(row, mapping, "delivery_days")
    payment_raw = _get(row, mapping, "payment_days")

    if not supplier or not product_code or unit_price_raw is None:
        raise ValueError("Zorunlu alanlar eksik")

    unit_price = _parse_price(unit_price_raw)
    delivery_days = _parse_days(delivery_raw, default=30)
    payment_days = _parse_payment_days(payment_raw, default=0)
    quantity = _parse_float(_get(row, mapping, "quantity"), default=1.0)
    currency = (_get(row, mapping, "currency") or "TRY").upper()
    unit = _get(row, mapping, "unit") or "adet"
    notes = _get(row, mapping, "notes") or ""

    if currency in {"TL", "TRY", "₺"}:
        currency = "TRY"

    # Karşılaştırma için fiyatı TRY'ye çevir; orijinal kur notlarda kalsın
    fx = FX_TO_TRY.get(currency, 1.0)
    price_try = unit_price * fx
    if currency != "TRY":
        note_fx = f"Orijinal: {unit_price} {currency} (kur {fx})"
        notes = f"{notes} | {note_fx}".strip(" |")

    return QuoteLine(
        supplier=str(supplier).strip(),
        product_code=str(product_code).strip().upper(),
        product_name=str(product_name).strip(),
        unit_price=price_try,
        currency="TRY",
        delivery_days=delivery_days,
        payment_days=payment_days,
        quantity=quantity,
        unit=unit,
        source_file=source_file,
        notes=notes,
    )


def _get(row: pd.Series, mapping: dict[str, str], field: str) -> Any:
    col = mapping.get(field)
    if not col:
        return None
    value = row.get(col)
    if pd.isna(value):
        return None
    return value


def _parse_price(value: Any) -> float:
    text = str(value).strip()
    text = text.replace("TL", "").replace("TRY", "").replace("₺", "").replace("€", "").replace("$", "")
    text = text.replace(" ", "")
    # 1.250,50 → 1250.50 | 1,250.50 → 1250.50 | 5.100 → 5100 | 16,90 → 16.90
    if "," in text and "." in text:
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        text = text.replace(",", ".")
    elif "." in text:
        # Sadece nokta varsa: 1.250 / 5.100 (binlik) vs 145.0 (ondalık)
        if re.fullmatch(r"\d{1,3}(\.\d{3})+", text):
            text = text.replace(".", "")
    return float(text)


def _parse_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(str(value).replace(",", ".").strip())
    except ValueError:
        return default


def _parse_days(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).lower().strip()
    match = re.search(r"(\d+)", text)
    if not match:
        return default
    return int(match.group(1))


def _parse_payment_days(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    text = str(value).lower().strip()
    if any(k in text for k in ("peşin", "pesin", "cash", "immediate")):
        return 0
    match = re.search(r"(\d+)", text)
    if not match:
        return default
    return int(match.group(1))
