"""Makes made-up CSV files in a folder called sample.

Run: python make_sample.py
"""
import sys
from pathlib import Path

FILES = {
    "good.csv": b"name,city,age\nAmal,Riyadh,31\nBen,Leeds,28\n",
    "ragged.csv": b"name,city,age\nAmal,Riyadh,31\nBen,Leeds\nCara,Oslo,40,extra\n",
    "quoted.csv": b'name,note\nAmal,"likes tea, no sugar"\nBen,"two\nlines"\nCara,fine\n',
    "bom.csv": b"\xef\xbb\xbfname,age\nAmal,31\n",
    "semicolon.csv": b"name;city;age\nAmal;Riyadh;31\nBen;Leeds;28\n",
}


def make(folder):
    folder = Path(folder)
    folder.mkdir()
    for name, data in FILES.items():
        with (folder / name).open("xb") as handle:
            handle.write(data)
    return folder


if __name__ == "__main__":
    try:
        make(Path(__file__).resolve().parent / "sample")
    except FileExistsError:
        raise SystemExit("Stopped: sample already exists. Nothing was replaced or deleted.")
    print("Made sample/good.csv, ragged.csv, quoted.csv, bom.csv and semicolon.csv")
    sys.exit(0)
