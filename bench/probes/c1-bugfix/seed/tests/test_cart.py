from shop.cart import Cart
from shop.money import to_cents, fmt
from shop.promo import PercentOff, BuyNGetOne


def test_to_cents_rounding():
    assert to_cents("19.99") == 1999
    assert to_cents("0.125") == 13


def test_add_same_sku_accumulates():
    c = Cart()
    c.add("A", "10", 1)
    c.add("A", "10", 2)
    assert c.subtotal() == 3000


def test_buy_two_get_one():
    c = Cart()
    c.add("tea", "5", 3)
    assert c.total([BuyNGetOne("tea", 2)]) == 1000


def test_percent_after_item():
    c = Cart()
    c.add("tea", "5", 3)
    c.add("cup", "33.33", 1)
    # 15 + 33.33 = 48.33; minus one free tea = 43.33; 10% off = 4.333 -> 4.33 => 39.00
    assert c.total([PercentOff(10), BuyNGetOne("tea", 2)]) == 3900


def test_fmt():
    assert fmt(-5) == "-¥0.05"
