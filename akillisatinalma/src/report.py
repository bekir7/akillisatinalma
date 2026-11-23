from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from .models import ComparisonResult, QuoteLine


def build_detail_dataframe(results: list[ComparisonResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        for c in result.candidates:
            rows.append(
                {
                    "Ürün Kodu": c.product_code,
                    "Ürün Adı": c.product_name,
                    "Tedarikçi": c.supplier,
                    "Birim Fiyat": c.unit_price,
                    "Para Birimi": c.currency,
                    "Miktar": c.quantity,
                    "Satır Tutarı": round(c.line_total, 2),
                    "Teslim (gün)": c.delivery_days,
                    "Ödeme Vadesi (gün)": c.payment_days,
                    "Fiyat Skoru": c.price_score,
                    "Teslim Skoru": c.delivery_score,
                    "Vade Skoru": c.payment_score,
                    "Toplam Skor": c.total_score,
                    "Öneri": "EVET" if c.is_recommended else "",
                    "Kaynak Dosya": c.source_file,
                }
            )
    return pd.DataFrame(rows)


def build_summary_dataframe(results: list[ComparisonResult]) -> pd.DataFrame:
    rows = []
    for result in results:
        rec = result.recommended
        if rec is None:
            continue
        alternatives = [c.supplier for c in result.candidates if not c.is_recommended]
        rows.append(
            {
                "Ürün Kodu": rec.product_code,
                "Ürün Adı": rec.product_name,
                "Önerilen Tedarikçi": rec.supplier,
                "Birim Fiyat": rec.unit_price,
                "Para Birimi": rec.currency,
                "Teslim (gün)": rec.delivery_days,
                "Ödeme Vadesi (gün)": rec.payment_days,
                "Toplam Skor": rec.total_score,
                "Karşılaştırılan Tedarikçi Sayısı": len(result.candidates),
                "Diğer Alternatifler": ", ".join(alternatives) if alternatives else "-",
            }
        )
    return pd.DataFrame(rows)


def write_excel_report(
    results: list[ComparisonResult],
    lines: list[QuoteLine],
    output_path: Path,
    weights: dict[str, float],
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_summary_dataframe(results)
    detail = build_detail_dataframe(results)
    raw = pd.DataFrame(
        [
            {
                "Tedarikçi": x.supplier,
                "Ürün Kodu": x.product_code,
                "Ürün Adı": x.product_name,
                "Birim Fiyat": x.unit_price,
                "Para Birimi": x.currency,
                "Teslim (gün)": x.delivery_days,
                "Ödeme Vadesi (gün)": x.payment_days,
                "Miktar": x.quantity,
                "Kaynak": x.source_file,
            }
            for x in lines
        ]
    )

    meta = pd.DataFrame(
        [
            {"Alan": "Rapor Tarihi", "Değer": datetime.now().strftime("%Y-%m-%d %H:%M")},
            {"Alan": "Toplam Teklif Satırı", "Değer": len(lines)},
            {"Alan": "Karşılaştırılan Ürün", "Değer": len(results)},
            {"Alan": "Fiyat Ağırlığı", "Değer": weights.get("price", 0.5)},
            {"Alan": "Teslim Ağırlığı", "Değer": weights.get("delivery", 0.3)},
            {"Alan": "Vade Ağırlığı", "Değer": weights.get("payment", 0.2)},
            {
                "Alan": "Tahmini Tasarruf (satır toplamı farkı)*",
                "Değer": round(_estimate_savings(results), 2),
            },
        ]
    )

    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        meta.to_excel(writer, sheet_name="Yonetici_Ozet", index=False)
        summary.to_excel(writer, sheet_name="Oneriler", index=False, startrow=0)
        detail.to_excel(writer, sheet_name="Detayli_Karsilastirma", index=False)
        raw.to_excel(writer, sheet_name="Ham_Veri", index=False)

        # Yönetici özet sayfasına önerileri de ekle
        summary.to_excel(writer, sheet_name="Yonetici_Ozet", index=False, startrow=len(meta) + 2)

    return output_path


def format_console_report(results: list[ComparisonResult], output_path: Path) -> str:
    lines = [
        "=" * 64,
        "  AKILLI SATIN ALMA — TEDARİKÇİ TEKLİF KARŞILAŞTIRMA RAPORU",
        "=" * 64,
        f"Rapor zamanı : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Excel çıktı  : {output_path}",
        "",
        "ÜRÜN BAZLI ÖNERİLER",
        "-" * 64,
    ]

    for result in results:
        rec = result.recommended
        if rec is None:
            continue
        lines.append(f"[{rec.product_code}] {rec.product_name}")
        lines.append(
            f"  → Öneri : {rec.supplier} | "
            f"{rec.unit_price:,.2f} {rec.currency} | "
            f"Teslim {rec.delivery_days}g | Vade {rec.payment_days}g | "
            f"Skor {rec.total_score:.3f}"
        )
        for c in result.candidates:
            mark = "★" if c.is_recommended else "·"
            lines.append(
                f"    {mark} {c.supplier:<22} "
                f"{c.unit_price:>10,.2f} | {c.delivery_days:>3}g | "
                f"{c.payment_days:>3}g vade | skor {c.total_score:.3f}"
            )
        lines.append("")

    savings = _estimate_savings(results)
    lines.extend(
        [
            "-" * 64,
            f"Tahmini satır tutarı tasarrufu (en pahalıya göre)* : {savings:,.2f}",
            "* Basit fark hesabı; nihai karar için kalite/risk de değerlendirilmelidir.",
            "=" * 64,
        ]
    )
    return "\n".join(lines)


def _estimate_savings(results: list[ComparisonResult]) -> float:
    total = 0.0
    for result in results:
        if not result.candidates or result.recommended is None:
            continue
        worst = max(result.candidates, key=lambda c: c.line_total)
        total += worst.line_total - result.recommended.line_total
    return total
