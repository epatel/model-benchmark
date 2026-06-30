import unittest

from lru import LRUCache


class TestLRUCache(unittest.TestCase):
    def test_keeps_only_capacity(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.put("c", 3)  # should evict "a"
        self.assertEqual(len(c), 2)
        self.assertIsNone(c.get("a"))
        self.assertEqual(c.get("b"), 2)
        self.assertEqual(c.get("c"), 3)

    def test_lru_eviction_order(self):
        c = LRUCache(2)
        c.put("a", 1)
        c.put("b", 2)
        c.get("a")     # "a" is now most-recently used
        c.put("c", 3)  # should evict "b", not "a"
        self.assertIsNone(c.get("b"))
        self.assertEqual(c.get("a"), 1)
        self.assertEqual(c.get("c"), 3)


if __name__ == "__main__":
    unittest.main()
