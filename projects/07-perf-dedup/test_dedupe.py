import unittest

from dedupe import dedupe


class TestDedupe(unittest.TestCase):
    def test_removes_duplicates_preserving_order(self):
        self.assertEqual(dedupe([3, 1, 3, 2, 1]), [3, 1, 2])

    def test_strings(self):
        self.assertEqual(dedupe(["a", "b", "a", "c", "b"]), ["a", "b", "c"])

    def test_empty(self):
        self.assertEqual(dedupe([]), [])

    def test_no_duplicates(self):
        self.assertEqual(dedupe([1, 2, 3]), [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
