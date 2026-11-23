"""Örnek tedarikçi teklif dosyalarını (CSV / Excel / PDF) üretir."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "quotes"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    _write_csv_a()
    _write_excel_b()
    _write_csv_c()
    _write_pdf_d()
    print(f"Örnek teklifler oluşturuldu: {OUT}")


def _write_csv_a() -> None:
    # Klasik TR sütun adları, noktalı virgül
    df = pd.DataFrame(
        [
            {
                "Ürün Kodu": "FAN-220",
                "Ürün Adı": "Kümes Fan Motoru 220V",
                "Birim Fiyat": "4.850,00",
                "Para Birimi": "TRY",
                "Teslim Süresi": "14 gün",
                "Ödeme Vadesi": "30 gün",
                "Miktar": 10,
                "Tedarikçi": "Anadolu Fan A.Ş.",
            },
            {
                "Ürün Kodu": "NIP-01",
                "Ürün Adı": "Nipel Suluk Seti",
                "Birim Fiyat": "18,75",
                "Para Birimi": "TRY",
                "Teslim Süresi": "7 gün",
                "Ödeme Vadesi": "Peşin",
                "Miktar": 500,
                "Tedarikçi": "Anadolu Fan A.Ş.",
            },
            {
                "Ürün Kodu": "SENS-TMP",
                "Ürün Adı": "Sıcaklık Sensörü",
                "Birim Fiyat": "320,00",
                "Para Birimi": "TRY",
                "Teslim Süresi": "10 gün",
                "Ödeme Vadesi": "45 gün",
                "Miktar": 40,
                "Tedarikçi": "Anadolu Fan A.Ş.",
            },
        ]
    )
    df.to_csv(OUT / "anadolu_fan_teklif.csv", index=False, sep=";", encoding="utf-8-sig")


def _write_excel_b() -> None:
    # Farklı İngilizce sütun adları
    wb = Workbook()
    ws = wb.active
    ws.title = "Quote"
    headers = [
        "SKU",
        "Description",
        "Unit Price",
        "Currency",
        "Lead Time",
        "Payment Terms",
        "Qty",
        "Vendor",
    ]
    ws.append(headers)
    rows = [
        ["FAN-220", "Poultry Fan Motor 220V", 145.0, "EUR", "21 days", "Net 60", 10, "EuroAgri GmbH"],
        ["NIP-01", "Nipple Drinker Kit", 0.55, "EUR", "12 days", "Net 30", 500, "EuroAgri GmbH"],
        ["SENS-TMP", "Temperature Sensor", 9.8, "EUR", "5 days", "Net 15", 40, "EuroAgri GmbH"],
        ["BELT-X2", "Conveyor Belt X2", 890.0, "EUR", "30 days", "Net 45", 4, "EuroAgri GmbH"],
    ]
    for row in rows:
        ws.append(row)
    wb.save(OUT / "euroagri_quote.xlsx")


def _write_csv_c() -> None:
    # Daha da farklı TR sütun adları + virgül ayırıcı
    df = pd.DataFrame(
        [
            {
                "Stok Kodu": "FAN-220",
                "Malzeme": "Fan Motoru 220V Endüstriyel",
                "Net Fiyat": "5.100",
                "PB": "TL",
                "Teslimat": "10",
                "Vade": "60 gün",
                "Adet": 10,
                "Firma": "Ege Kanatlı Ekipman",
            },
            {
                "Stok Kodu": "NIP-01",
                "Malzeme": "Nipel Suluk",
                "Net Fiyat": "16,90",
                "PB": "TL",
                "Teslimat": "5 gün",
                "Vade": "30",
                "Adet": 500,
                "Firma": "Ege Kanatlı Ekipman",
            },
            {
                "Stok Kodu": "BELT-X2",
                "Malzeme": "Konveyör Bant X2",
                "Net Fiyat": "38.500,00",
                "PB": "TRY",
                "Teslimat": "20 gün",
                "Vade": "Peşin",
                "Adet": 4,
                "Firma": "Ege Kanatlı Ekipman",
            },
            {
                "Stok Kodu": "SENS-TMP",
                "Malzeme": "Temp Sensör",
                "Net Fiyat": "295",
                "PB": "TRY",
                "Teslimat": "15",
                "Vade": "30 gün",
                "Adet": 40,
                "Firma": "Ege Kanatlı Ekipman",
            },
        ]
    )
    df.to_csv(OUT / "ege_kanatli_fiyat.csv", index=False, encoding="utf-8-sig")


def _write_pdf_d() -> None:
    path = OUT / "delta_otomasyon_teklif.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4)
    styles = getSampleStyleSheet()
    # ReportLab varsayilan fontu Turkce karakterleri bozabilecegi icin ASCII baslik kullanilir.
    story = [
        Paragraph("DELTA OTOMASYON - FIYAT TEKLIFI", styles["Title"]),
        Paragraph("Tarih: 16.11.2026 | Gecerlilik: 30 gun", styles["Normal"]),
        Spacer(1, 16),
    ]
    data = [
        ["Urun Kodu", "Urun Adi", "Birim Fiyat", "Para Birimi", "Teslim Suresi", "Odeme Vadesi", "Miktar", "Tedarikci"],
        ["FAN-220", "Fan Motoru 220V", "4.650,00", "TRY", "18 gun", "45 gun", "10", "Delta Otomasyon"],
        ["NIP-01", "Nipel Suluk Seti", "19,20", "TRY", "3 gun", "15 gun", "500", "Delta Otomasyon"],
        ["SENS-TMP", "Sicaklik Sensoru", "310,00", "TRY", "7 gun", "30 gun", "40", "Delta Otomasyon"],
        ["BELT-X2", "Konveyor Bant X2", "36.900,00", "TRY", "25 gun", "30 gun", "4", "Delta Otomasyon"],
    ]
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F4E79")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.Color(0.93, 0.93, 0.93)]),
                ("ALIGN", (2, 1), (2, -1), "RIGHT"),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "Not: Fiyatlar KDV hariçtir. Teslim yeri: İstanbul (Asya).",
            styles["Italic"],
        )
    )
    doc.build(story)


if __name__ == "__main__":
    main()
