import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path

import csvcheck
import make_sample


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def run_on(self, data):
        path = self.dir / "t.csv"
        path.write_bytes(data)
        return csvcheck.check(str(path))


class TestCheck(Base):
    def test_good_file(self):
        r = self.run_on(b"a,b\n1,2\n3,4\n")
        self.assertEqual((r["columns"], r["rows"]), (2, 2))
        self.assertFalse(csvcheck.problems(r))

    def test_wrong_length_rows_have_line_numbers(self):
        r = self.run_on(b"a,b,c\n1,2,3\n4,5\n6,7,8,9\n")
        self.assertEqual(r["wrong_length"], [(3, 2), (4, 4)])

    def test_total_is_counted_but_only_first_examples_shown(self):
        rows = b"".join(b"%d\n" % n for n in range(10))
        r = self.run_on(b"a,b\n" + rows)
        self.assertEqual(len(r["wrong_length"]), 10)
        text = csvcheck.report(r)
        self.assertIn("different number of fields than the header: 10", text)
        self.assertIn("and 5 more not shown", text)
        self.assertEqual(text.count("has 1 fields"), 5)

    def test_quoted_comma_and_newline_are_fine(self):
        r = self.run_on(b'a,b\n1,"x, y"\n2,"two\nlines"\n')
        self.assertEqual(r["rows"], 2)
        self.assertEqual(r["multiline_records"], 1)
        self.assertFalse(csvcheck.problems(r))

    def test_line_number_after_a_multiline_record(self):
        r = self.run_on(b'a,b\n1,"two\nlines"\n3\n')
        self.assertEqual(r["wrong_length"], [(4, 1)])

    def test_byte_order_mark(self):
        r = self.run_on(b"\xef\xbb\xbfa,b\n1,2\n")
        self.assertTrue(r["bom"])
        self.assertEqual(r["columns"], 2)
        self.assertTrue(csvcheck.problems(r))

    def test_not_utf8(self):
        r = self.run_on(b"a,b\n\xff,2\n")
        self.assertIn("not UTF-8", r["fatal"])

    def test_empty_file_and_spaces_only(self):
        self.assertIn("empty", self.run_on(b"")["fatal"])
        self.assertIn("empty", self.run_on(b"  \n\n")["fatal"])

    def test_header_only_is_not_a_problem(self):
        r = self.run_on(b"a,b\n")
        self.assertEqual(r["rows"], 0)
        self.assertFalse(csvcheck.problems(r))

    def test_repeated_and_empty_column_names(self):
        r = self.run_on(b"a,b,a,\n1,2,3,4\n")
        self.assertEqual(r["repeated_names"], [("a", [1, 3])])
        self.assertEqual(r["empty_names"], [4])

    def test_blank_line_in_the_middle(self):
        r = self.run_on(b"a,b\n1,2\n\n3,4\n")
        self.assertEqual(r["blank_lines"], [3])
        self.assertEqual(r["rows"], 2)

    def test_single_trailing_newline_is_not_a_blank_line(self):
        self.assertEqual(self.run_on(b"a,b\n1,2\n")["blank_lines"], [])
        self.assertEqual(self.run_on(b"a,b\n1,2")["blank_lines"], [])

    def test_windows_line_endings(self):
        r = self.run_on(b"a,b\r\n1,2\r\n3,4\r\n")
        self.assertEqual(r["rows"], 2)
        self.assertFalse(csvcheck.problems(r))

    def test_semicolon_file_is_flagged_as_possible_problem(self):
        r = self.run_on(b"a;b;c\n1;2;3\n")
        self.assertTrue(r["hint"])
        self.assertTrue(csvcheck.problems(r))
        self.assertNotIn("No problems found", csvcheck.report(r))

    def test_unterminated_quote_stops_with_an_error(self):
        r = self.run_on(b'a,b\n1,"never closed\n')
        self.assertIn("Line", r["fatal"])

    def test_text_after_a_closing_quote_stops_with_an_error(self):
        r = self.run_on(b'a,b\n1,"x"y\n')
        self.assertIn("Line", r["fatal"])


class TestMain(Base):
    def call(self, args):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            code = csvcheck.main(["p"] + args)
        return code, out.getvalue()

    def test_exit_codes(self):
        good = self.dir / "g.csv"
        good.write_bytes(b"a\n1\n")
        bad = self.dir / "b.csv"
        bad.write_bytes(b"a,b\n1\n")
        self.assertEqual(self.call([str(good)])[0], 0)
        self.assertEqual(self.call([str(bad)])[0], 1)
        self.assertEqual(self.call([])[0], 2)
        self.assertEqual(self.call([str(self.dir / "missing.csv")])[0], 2)

    def test_sample_files(self):
        make_sample.make(self.dir / "s")
        expect = {"good.csv": 0, "ragged.csv": 1, "quoted.csv": 0, "bom.csv": 1, "semicolon.csv": 1}
        for name, code in expect.items():
            self.assertEqual(self.call([str(self.dir / "s" / name)])[0], code, name)

    def test_file_is_not_changed(self):
        path = self.dir / "t.csv"
        path.write_bytes(b"a,b\n1\n")
        os.utime(path, (1700000000, 1700000000))
        before = (path.read_bytes(), path.stat().st_mtime)
        self.call([str(path)])
        self.assertEqual(before, (path.read_bytes(), path.stat().st_mtime))
        self.assertEqual(os.listdir(self.dir), ["t.csv"])


if __name__ == "__main__":
    unittest.main()
