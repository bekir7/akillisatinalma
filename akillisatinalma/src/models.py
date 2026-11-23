from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class QuoteLine:
    """Tek bir teklif satırı (normalize edilmiş)."""

    supplier: str
    product_code: str
    product_name: str
    unit_price: float
    currency: str
    delivery_days: int
    payment_days: int
    quantity: float = 1.0
    unit: str = "adet"
    source_file: str = ""
    notes: str = ""

    @property
    def line_total(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class SupplierScore:
    """Bir ürün için tedarikçi skor sonucu."""

    supplier: str
    product_code: str
    product_name: str
    unit_price: float
    delivery_days: int
    payment_days: int
    price_score: float
    delivery_score: float
    payment_score: float
    total_score: float
    quantity: float = 1.0
    currency: str = "TRY"
    source_file: str = ""
    is_recommended: bool = False

    @property
    def line_total(self) -> float:
        return self.unit_price * self.quantity


@dataclass
class ComparisonResult:
    """Karşılaştırma özeti."""

    product_code: str
    product_name: str
    candidates: list[SupplierScore] = field(default_factory=list)
    recommended: Optional[SupplierScore] = None
