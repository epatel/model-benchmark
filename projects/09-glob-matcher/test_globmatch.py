import unittest

from globmatch import match


class TestGlobMatch(unittest.TestCase):
    def test_literals(self):
        self.assertTrue(match("hello", "hello"))
        self.assertFalse(match("hello", "hell"))
        self.assertFalse(match("hell", "hello"))
        self.assertTrue(match("", ""))
        self.assertFalse(match("a", ""))
        self.assertFalse(match("", "a"))

    def test_question_mark(self):
        self.assertTrue(match("cat", "c?t"))
        self.assertFalse(match("ct", "c?t"))
        self.assertTrue(match("abc", "???"))
        self.assertFalse(match("abcd", "???"))

    def test_star(self):
        self.assertTrue(match("anything", "*"))
        self.assertTrue(match("", "*"))
        self.assertTrue(match("file.txt", "*.txt"))
        self.assertFalse(match("file.txt", "*.md"))
        self.assertTrue(match("abcde", "a*e"))
        self.assertTrue(match("ae", "a*e"))
        self.assertFalse(match("aed", "a*e"))

    def test_star_combinations(self):
        self.assertTrue(match("abcabc", "*abc"))
        self.assertTrue(match("xyzzy", "x*z*y"))
        self.assertTrue(match("mississippi", "m*iss*ippi"))
        self.assertFalse(match("mississippi", "m*iss*z*"))

    def test_classes(self):
        self.assertTrue(match("cat", "[bc]at"))
        self.assertFalse(match("rat", "[bc]at"))
        self.assertTrue(match("rat", "[!bc]at"))
        self.assertFalse(match("cat", "[!bc]at"))
        self.assertTrue(match("log1", "log[123]"))
        self.assertFalse(match("log4", "log[123]"))

    def test_mixed(self):
        self.assertTrue(match("report-2024.csv", "report-????.[ct]sv"))
        self.assertTrue(match("a1b2c3", "a*[123]"))
        self.assertFalse(match("a1b2c!", "a*[123]"))


if __name__ == "__main__":
    unittest.main()
