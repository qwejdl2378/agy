"""Promotions. Rules (from product spec):
- PercentOff(pct, min_subtotal): pct% off the whole cart when subtotal >= min_subtotal.
- BuyNGetOne(sku, n): for every n+1 units of sku, one is free.
- Promotions apply in order: item-level (BuyNGetOne) first, then cart-level (PercentOff)
  computed on the already-discounted amount. Discount amounts round half up to the cent.
- Total never goes below 0.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


@dataclass
class PercentOff:
    pct: int
    min_subtotal: int = 0


@dataclass
class BuyNGetOne:
    sku: str
    n: int


def _item_discount(cart, p: BuyNGetOne) -> int:
    for l in cart.lines:
        if l.sku == p.sku:
            free = l.qty // p.n
            return free * l.unit_cents
    return 0


def apply_promos(cart, promos) -> int:
    amount = cart.subtotal()
    for p in promos:
        if isinstance(p, BuyNGetOne):
            amount -= _item_discount(cart, p)
    for p in promos:
        if isinstance(p, PercentOff) and cart.subtotal() >= p.min_subtotal:
            off = Decimal(amount) * p.pct / 100
            amount -= int(off)
    return amount
