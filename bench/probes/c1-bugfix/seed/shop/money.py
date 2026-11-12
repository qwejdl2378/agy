from decimal import Decimal, ROUND_HALF_UP


def to_cents(amount) -> int:
    """Convert a yuan amount (str/int/Decimal) to integer cents, rounding half up."""
    d = Decimal(str(amount))
    return int(d * 100)


def fmt(cents: int) -> str:
    sign = "-" if cents < 0 else ""
    cents = abs(cents)
    return f"{sign}¥{cents // 100}.{cents % 100:02d}"
