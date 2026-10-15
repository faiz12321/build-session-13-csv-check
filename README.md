# Check a CSV file for mistakes

A small read-only Python tool built step by step. Give it a CSV file (comma-separated values, the plain text format spreadsheets export) and it reports rows with a different number of fields than the header, blank lines, empty or repeated column names, a byte order mark, text that is not UTF-8, and quoting that stops the parser. It only reads the file.

## Run it

    python make_sample.py                  # makes made-up CSV files in sample/
    python csvcheck.py sample/ragged.csv   # report on one file
    python -m unittest -v                  # nineteen automated tests

On Windows, if `python` is not found, use `py`.

## Files

- `csvcheck.py` - the tool
- `make_sample.py` - makes five made-up files: good, rows of the wrong length, quoted fields with a comma and a line break, byte order mark, semicolon-separated
- `test_csvcheck.py` - tests

## Notes

- It reads commas only. It does not guess other separators. If the header is one column but contains a semicolon, a tab or a pipe, it reports a possible problem.
- Python's csv module can spread one record over several lines when a quoted field holds a line break, so a line count and a row count can differ (https://docs.python.org/3/library/csv.html). The tool reports line numbers where each record starts.
- The tool counts every problem but shows only the first five examples of each kind.
- Unclosed quotes and text after a closing quote stop the parser. The tool reports the first such error only and stops there, so fix it and run again.
- "No problems found by these checks" only means those checks passed. It does not check what the values mean, data types, or whether another program will accept the file.
- Tested only on small made-up files, not on large or real-world files or other encodings. Python 3.10 (Linux) and, by GitHub Actions, Python 3.12 on Windows and Ubuntu. Not tested on a Windows 10 or 11 desktop.
- Educational example, no warranty. Use at your own risk.
- Code is MIT licensed (see LICENSE). Python is a separate project with its own license; this repository does not include it.
