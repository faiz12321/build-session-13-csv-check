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
    folder.mkdir(exist_ok=True)
    for name, data in FILES.items():
        (folder / name).write_bytes(data)
    return folder


if __name__ == "__main__":
    make(Path(__file__).resolve().parent / "sample")
    print("Made sample/good.csv, ragged.csv, quoted.csv, bom.csv and semicolon.csv")
    sys.exit(0)
