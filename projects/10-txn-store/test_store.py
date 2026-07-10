import unittest

from store import Store, Conflict, TxnClosed


class TestBasics(unittest.TestCase):
    def setUp(self):
        self.store = Store()

    def seed(self, **kv):
        t = self.store.begin()
        for k, v in kv.items():
            t.put(k, v)
        t.commit()

    def test_put_get_commit(self):
        t = self.store.begin()
        t.put("a", 1)
        t.commit()
        t2 = self.store.begin()
        self.assertEqual(t2.get("a"), 1)

    def test_read_your_writes_and_deletes(self):
        self.seed(a=1)
        t = self.store.begin()
        t.put("a", 2)
        self.assertEqual(t.get("a"), 2)
        t.delete("a")
        self.assertIsNone(t.get("a"))

    def test_snapshot_read_ignores_later_commits(self):
        self.seed(a=1)
        t1 = self.store.begin()
        self.assertEqual(t1.get("a"), 1)
        t2 = self.store.begin()
        t2.put("a", 2)
        t2.commit()
        self.assertEqual(t1.get("a"), 1)

    def test_write_write_conflict(self):
        self.seed(a=1)
        t1 = self.store.begin()
        t2 = self.store.begin()
        t1.put("a", 10)
        t2.put("a", 20)
        t2.commit()
        with self.assertRaises(Conflict):
            t1.commit()

    def test_abort_discards_writes(self):
        self.seed(a=1)
        t = self.store.begin()
        t.put("a", 99)
        t.abort()
        self.assertEqual(self.store.begin().get("a"), 1)

    def test_closed_txn_raises(self):
        t = self.store.begin()
        t.put("a", 1)
        t.commit()
        with self.assertRaises(TxnClosed):
            t.get("a")
        with self.assertRaises(TxnClosed):
            t.put("a", 2)

    def test_read_only_txn_commits(self):
        self.seed(a=1)
        t = self.store.begin()
        self.assertEqual(t.get("a"), 1)
        t.commit()

    def test_delete_commits(self):
        self.seed(a=1)
        t = self.store.begin()
        t.delete("a")
        t.commit()
        self.assertIsNone(self.store.begin().get("a"))


if __name__ == "__main__":
    unittest.main()
