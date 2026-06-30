import unittest

from pricing import process_order


class TestProcessOrder(unittest.TestCase):
    def test_regular_no_coupon(self):
        r = process_order([{"price": 50, "qty": 1}], "regular", None)
        self.assertEqual(
            r,
            {"subtotal": 50, "discount": 0, "tax": 4.0, "shipping": 10, "total": 64.0},
        )

    def test_vip_free_shipping_threshold(self):
        r = process_order([{"price": 100, "qty": 2}], "vip", None)
        self.assertEqual(
            r,
            {"subtotal": 200, "discount": 20.0, "tax": 14.4, "shipping": 0, "total": 194.4},
        )

    def test_member_save5(self):
        r = process_order([{"price": 100, "qty": 1}], "member", "SAVE5")
        self.assertEqual(
            r,
            {"subtotal": 100, "discount": 10.0, "tax": 7.2, "shipping": 10, "total": 107.2},
        )

    def test_freeship_coupon(self):
        r = process_order([{"price": 50, "qty": 1}], "regular", "FREESHIP")
        self.assertEqual(
            r,
            {"subtotal": 50, "discount": 0, "tax": 4.0, "shipping": 0, "total": 54.0},
        )


if __name__ == "__main__":
    unittest.main()
