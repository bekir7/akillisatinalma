"""
Akıllı Satın Alma / Tedarikçi Teklif Karşılaştırma

Kullanım:
  python main.py
  python main.py --input data/quotes --output output/rapor.xlsx
  python main.py --price-weight 0.6 --delivery-weight 0.25 --payment-weight 0.15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.pipeline import run_comparison
from src.scoring import DEFAULT_WEIGHTS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Farklı formatlardaki tedarikçi tekliflerini karşılaştırır ve yönetici raporu üretir."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/quotes"),
        help="Teklif dosyalarının bulunduğu klasör (CSV/Excel/PDF)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/tedarikci_karsilastirma_raporu.xlsx"),
        help="Excel rapor çıktı yolu",
    )
    parser.add_argument("--price-weight", type=float, default=DEFAULT_WEIGHTS["price"])
    parser.add_argument("--delivery-weight", type=float, default=DEFAULT_WEIGHTS["delivery"])
    parser.add_argument("--payment-weight", type=float, default=DEFAULT_WEIGHTS["payment"])
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    weights = {
        "price": args.price_weight,
        "delivery": args.delivery_weight,
        "payment": args.payment_weight,
    }
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        print(f"Uyarı: ağırlık toplamı {total:.3f}. 1.0 olacak şekilde normalize ediliyor.")
        weights = {k: v / total for k, v in weights.items()}

    try:
        _lines, _results, report_path, console_text = run_comparison(
            input_dir=args.input,
            output_path=args.output,
            weights=weights,
        )
    except Exception as exc:
        print(f"Hata: {exc}", file=sys.stderr)
        return 1

    print(console_text)
    print(f"\nRapor kaydedildi: {report_path.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
