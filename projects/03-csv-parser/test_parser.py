import unittest

from parser import parse_csv


class TestParseCSV(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(parse_csv("a,b,c"), [["a", "b", "c"]])

    def test_multiple_rows(self):
        self.assertEqual(parse_csv("a,b\nc,d"), [["a", "b"], ["c", "d"]])

    def test_blank_lines_skipped(self):
        self.assertEqual(parse_csv("a,b\n\nc,d"), [["a", "b"], ["c", "d"]])

    def test_quoted_comma(self):
        self.assertEqual(parse_csv('"a,b",c'), [["a,b", "c"]])


if __name__ == "__main__":
    unittest.main()
