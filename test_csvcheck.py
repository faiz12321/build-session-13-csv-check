from unittest import mock
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


class TestScope(Base):
    def test_blank_first_line_means_no_header(self):
        r = self.run_on(b"\na,b\n1,2\n")
        self.assertIn("no header", r["fatal"])
        self.assertTrue(csvcheck.problems(r))

    def test_line_of_spaces_is_a_row_not_a_blank_line(self):
        r = self.run_on(b"a,b\n  \n1,2\n")
        self.assertEqual(r["blank_lines"], [])
        self.assertEqual(r["wrong_length"], [(2, 1)])

    def test_repeated_names_must_match_exactly(self):
        r = self.run_on(b"a,A,a \n1,2,3\n")
        self.assertEqual(r["repeated_names"], [])

    def test_quote_error_reports_no_counts(self):
        r = self.run_on(b'a,b\n1,2\n3,"x"y\n')
        text = csvcheck.report(r)
        self.assertIn("Line 3", text)
        self.assertNotIn("Data rows", text)
        self.assertNotIn("No problems found", text)


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


class SetupSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.sample = self.root / 'sample'

    def test_existing_folder_preserves_nested_bytes_and_metadata(self):
        (self.sample / 'nested').mkdir(parents=True)
        keep = self.sample / 'nested' / 'keep.bin'
        keep.write_bytes(b'KEEP')
        before = (keep.read_bytes(), keep.stat().st_mtime_ns)
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (keep.read_bytes(), keep.stat().st_mtime_ns))
        self.assertEqual(sorted(p.relative_to(self.sample).as_posix() for p in self.sample.rglob('*')), ['nested','nested/keep.bin'])

    def test_existing_file_preserved(self):
        self.sample.write_bytes(b'KEEP')
        before = (self.sample.read_bytes(), self.sample.stat().st_mtime_ns)
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, (self.sample.read_bytes(), self.sample.stat().st_mtime_ns))

    def test_repeat_setup_preserves_generated_bytes_and_metadata(self):
        make_sample.make(self.sample)
        before = {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.iterdir()}
        with self.assertRaises(FileExistsError):
            make_sample.make(self.sample)
        self.assertEqual(before, {p.name:(p.read_bytes(),p.stat().st_mtime_ns) for p in self.sample.iterdir()})

    def test_cli_refuses_without_replacing(self):
        import shutil, subprocess, sys
        script = self.root / 'make_sample.py'
        shutil.copyfile(Path(__file__).resolve().parent / 'make_sample.py', script)
        self.sample.mkdir()
        keep = self.sample / 'keep'
        keep.write_bytes(b'KEEP')
        result = subprocess.run([sys.executable,str(script)],capture_output=True,text=True)
        self.assertEqual(result.returncode,1)
        self.assertIn('Nothing was replaced or deleted',result.stderr)
        self.assertEqual(keep.read_bytes(),b'KEEP')




class PathSafety(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name);self.root=self.base/'sample'
        make_sample.make(self.root);self.file=self.root/'good.csv'
    def link(self,path,target,directory=False):
        try:path.symlink_to(target,target_is_directory=directory)
        except OSError:self.skipTest('Symlink creation unavailable')
    def code(self,path):
        with contextlib.redirect_stdout(io.StringIO()) as out:code=csvcheck.main(['csvcheck.py',str(path)])
        return code,out.getvalue()
    def test_file_link_refuses(self):
        p=self.base/'linked';self.link(p,self.file)
        with self.assertRaises(OSError):csvcheck.safe_input(p)
        self.assertEqual(self.code(p)[0],2)
    def test_linked_ancestor_refuses(self):
        p=self.base/'linked';self.link(p,self.root,True)
        self.assertEqual(self.code(p/'good.csv')[0],2)
    def test_dangling_link_refuses(self):
        p=self.base/'linked';self.link(p,self.base/'missing')
        self.assertEqual(self.code(p)[0],2)
    def test_self_loop_refuses(self):
        p=self.base/'linked';self.link(p,p)
        self.assertEqual(self.code(p)[0],2)
    def test_hardlink_refuses(self):
        p=self.base/'hard';os.link(self.file,p)
        self.assertEqual(self.code(p)[0],2)
    def test_pipe_refuses_without_blocking(self):
        if not hasattr(os,'mkfifo'):self.skipTest('Unix pipe unavailable')
        p=self.base/'pipe';os.mkfifo(p)
        self.assertEqual(self.code(p)[0],2)
    def test_directory_refuses(self):self.assertEqual(self.code(self.root)[0],2)
    def test_traversal_refuses(self):self.assertEqual(self.code(self.root/'..'/'sample'/'good.csv')[0],2)
    def test_reparse_attribute_refuses(self):
        real=Path.lstat;target=self.file
        def fake(path,*args,**kwargs):
            value=real(path,*args,**kwargs)
            if path==target:return type('Reparse',(),{'st_mode':value.st_mode,'st_file_attributes':0x400})()
            return value
        with mock.patch.object(Path,'lstat',fake):self.assertEqual(self.code(self.file)[0],2)
    def test_metadata_failure_nonzero(self):
        with mock.patch.object(Path,'lstat',side_effect=OSError('forced metadata error')):
            code,text=self.code(self.file);self.assertEqual(code,2);self.assertIn('forced metadata error',text)
    def test_setup_linked_parent_refuses(self):
        p=self.base/'linked';self.link(p,self.root,True)
        with self.assertRaises(OSError):make_sample.make(p/'new')
        self.assertFalse((self.root/'new').exists())
    def test_setup_traversal_refuses(self):
        with self.assertRaises(OSError):make_sample.make(self.root/'..'/'new')



if __name__ == "__main__":
    unittest.main()
