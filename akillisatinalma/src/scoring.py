from __future__ import annotations

from collections import defaultdict

from .models import ComparisonResult, QuoteLine, SupplierScore


DEFAULT_WEIGHTS = {
    "price": 0.50,
    "delivery": 0.30,
    "payment": 0.20,
}


def compare_quotes(
    lines: list[QuoteLine],
    weights: dict[str, float] | None = None,
) -> list[ComparisonResult]:
    """Ürün bazında tedarikçileri skorlar ve en uygununu önerir."""
    weights = weights or DEFAULT_WEIGHTS
    by_product: dict[str, list[QuoteLine]] = defaultdict(list)

    for line in lines:
        by_product[line.product_code].append(line)

    results: list[ComparisonResult] = []
    for product_code, group in sorted(by_product.items()):
        scored = _score_group(group, weights)
        recommended = max(scored, key=lambda s: s.total_score)
        recommended.is_recommended = True
        results.append(
            ComparisonResult(
                product_code=product_code,
                product_name=group[0].product_name,
                candidates=sorted(scored, key=lambda s: s.total_score, reverse=True),
                recommended=recommended,
            )
        )
    return results


def _score_group(group: list[QuoteLine], weights: dict[str, float]) -> list[SupplierScore]:
    prices = [g.unit_price for g in group]
    deliveries = [g.delivery_days for g in group]
    payments = [g.payment_days for g in group]

    min_price, max_price = min(prices), max(prices)
    min_delivery, max_delivery = min(deliveries), max(deliveries)
    min_payment, max_payment = min(payments), max(payments)

    scored: list[SupplierScore] = []
    for line in group:
        price_score = _invert_normalize(line.unit_price, min_price, max_price)
        delivery_score = _invert_normalize(line.delivery_days, min_delivery, max_delivery)
        payment_score = _normalize(line.payment_days, min_payment, max_payment)

        total = (
            price_score * weights["price"]
            + delivery_score * weights["delivery"]
            + payment_score * weights["payment"]
        )

        scored.append(
            SupplierScore(
                supplier=line.supplier,
                product_code=line.product_code,
                product_name=line.product_name,
                unit_price=line.unit_price,
                delivery_days=line.delivery_days,
                payment_days=line.payment_days,
                price_score=round(price_score, 3),
                delivery_score=round(delivery_score, 3),
                payment_score=round(payment_score, 3),
                total_score=round(total, 3),
                quantity=line.quantity,
                currency=line.currency,
                source_file=line.source_file,
            )
        )
    return scored


def _normalize(value: float, min_v: float, max_v: float) -> float:
    if max_v == min_v:
        return 1.0
    return (value - min_v) / (max_v - min_v)


def _invert_normalize(value: float, min_v: float, max_v: float) -> float:
    """Düşük değer = yüksek skor (fiyat, teslim süresi)."""
    return 1.0 - _normalize(value, min_v, max_v)
