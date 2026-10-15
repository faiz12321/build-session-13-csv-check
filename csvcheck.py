"""Checks a comma-separated (CSV) file for common mistakes. Read-only.

Run: python csvcheck.py FILE.csv
It reads commas only. It does not guess other separators.
"""
import csv
import io
import sys

SHOW = 5          # examples shown per kind of problem
BOM = b"\xef\xbb\xbf"


def check(path):
    """Return a dict describing what was found. Never writes anything."""
    result = {"path": path, "fatal": None, "bom": False, "rows": 0, "columns": 0,
              "multiline_records": 0, "blank_lines": [], "wrong_length": [],
              "empty_names": [], "repeated_names": [], "hint": None}
    with open(path, "rb") as handle:
        data = handle.read()
    if data.startswith(BOM):
        result["bom"] = True
        data = data[len(BOM):]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        result["fatal"] = "The file is not UTF-8 text (first bad byte at position %d)." % error.start
        return result
    if not text.strip():
        result["fatal"] = "The file is empty."
        return result
    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = next(reader)
        if not header:
            result["fatal"] = "Line 1 is blank, so the file has no header row."
            return result
        result["columns"] = len(header)
        seen = {}
        for position, name in enumerate(header, 1):
            if not name.strip():
                result["empty_names"].append(position)
            seen.setdefault(name, []).append(position)
        result["repeated_names"] = [(name, places) for name, places in seen.items()
                                    if len(places) > 1 and name.strip()]
        if len(header) == 1 and any(mark in header[0] for mark in (";", "\t", "|")):
            result["hint"] = "the header is one column but contains ; or a tab or |. The file may use another separator, which this tool does not read."
        while True:
            start = reader.line_num + 1
            row = next(reader)
            if reader.line_num - start > 0:
                result["multiline_records"] += 1
            if not row:
                result["blank_lines"].append(start)
                continue
            result["rows"] += 1
            if len(row) != len(header):
                result["wrong_length"].append((start, len(row)))
    except StopIteration:
        pass
    except csv.Error as error:
        result["fatal"] = "Line %d: %s. The tool stops here, so counts and the other checks are not shown." % (reader.line_num, error)
    return result


def lines_for(label, items, fmt):
    out = ["%s: %d" % (label, len(items))]
    out.extend("  " + fmt(item) for item in items[:SHOW])
    if len(items) > SHOW:
        out.append("  ... and %d more not shown" % (len(items) - SHOW))
    return out


def problems(result):
    return bool(result["fatal"] or result["bom"] or result["blank_lines"] or result["wrong_length"]
                or result["empty_names"] or result["repeated_names"] or result["hint"])


def report(result):
    lines = ["File: " + result["path"]]
    if result["bom"]:
        lines.append("Flagged: the file starts with a UTF-8 byte order mark (the bytes EF BB BF). The tool skips it and checks the rest.")
    if result["fatal"]:
        lines.append("Problem: " + result["fatal"])
    else:
        lines.append("Columns in the header: %d. Data rows: %d. Records that span more than one line: %d."
                     % (result["columns"], result["rows"], result["multiline_records"]))
        if result["hint"]:
            lines.append("Possible problem: " + result["hint"])
        if result["empty_names"]:
            lines += lines_for("Empty column names", result["empty_names"], lambda p: "column %d" % p)
        if result["repeated_names"]:
            lines += lines_for("Repeated column names (exact match)", result["repeated_names"],
                               lambda item: "'%s' in columns %s" % (item[0], ", ".join(map(str, item[1]))))
        if result["wrong_length"]:
            lines += lines_for("Rows with a different number of fields than the header", result["wrong_length"],
                               lambda item: "line %d has %d fields" % item)
        if result["blank_lines"]:
            lines += lines_for("Blank lines", result["blank_lines"], lambda n: "line %d" % n)
    if not problems(result):
        lines.append("No problems found by these checks. This does not check what the values mean.")
    return "\n".join(lines)


def main(argv):
    if len(argv) != 2:
        print("Usage: python csvcheck.py FILE.csv")
        return 2
    try:
        result = check(argv[1])
    except OSError as error:
        print("Could not read the file: %s" % error.strerror)
        return 2
    print(report(result))
    return 1 if problems(result) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
