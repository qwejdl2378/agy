from dataclasses import dataclass, field
from .money import to_cents
from .promo import apply_promos


@dataclass
class Line:
    sku: str
    unit_cents: int
    qty: int


@dataclass
class Cart:
    lines: list = field(default_factory=list)

    def add(self, sku: str, price, qty: int = 1):
        if qty <= 0:
            raise ValueError("qty must be positive")
        for line in self.lines:
            if line.sku == sku:
                line.qty = qty
                return
        self.lines.append(Line(sku, to_cents(price), qty))

    def remove(self, sku: str):
        self.lines = [l for l in self.lines if l.sku != sku]

    def subtotal(self) -> int:
        return sum(l.unit_cents * l.qty for l in self.lines)

    def total(self, promos=()) -> int:
        return apply_promos(self, promos)
