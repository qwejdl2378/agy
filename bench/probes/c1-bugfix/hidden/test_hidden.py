from shop.cart import Cart
from shop.money import to_cents
from shop.promo import PercentOff, BuyNGetOne


def test_round_half_up_variants():
    assert to_cents("2.675") == 268
    assert to_cents(1) == 100
    assert to_cents("-0.005") == -1


def test_bngo_counts_groups():
    c = Cart(); c.add("tea", "5", 7)          # groups of 3 -> 2 free
    assert c.total([BuyNGetOne("tea", 2)]) == 2500
    c2 = Cart(); c2.add("tea", "5", 2)
    assert c2.total([BuyNGetOne("tea", 2)]) == 1000


def test_threshold_uses_subtotal_and_half_up():
    c = Cart(); c.add("x", "0.15", 1)
    # 50% of 15 = 7.5 -> 8 discount -> 7
    assert c.total([PercentOff(50)]) == 7
    c2 = Cart(); c2.add("x", "99", 1)
    assert c2.total([PercentOff(10, min_subtotal=10000)]) == 9900


def test_never_negative():
    c = Cart(); c.add("x", "1", 1)
    assert c.total([PercentOff(150)]) == 0


def test_add_accumulates_keeps_price():
    c = Cart(); c.add("A", "1", 1); c.add("A", "1", 4)
    assert c.lines[0].qty == 5 and len(c.lines) == 1
