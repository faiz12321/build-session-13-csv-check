# Check a fictional CSV file

Save three source files in a NEW empty lesson folder.

    python make_sample.py
    python csvcheck.py sample/ragged.csv
    python -m unittest -v

Two Windows and two Ubuntu full replays run exact visible source versions. Final 39 small fixture tests pass (Unix pipe skips on Windows); symlink creation can skip where unavailable. Displayed stdout is first Windows output, not normalized or mixed. Pair differences are unittest time.
Only link/error changes: final reader refuses input/ancestor symbolic links/reparse points, hardlinks, special files and traversal before opening. Metadata/open errors remain exit 2 with readable fallback text. Setup refuses linked parents/traversal and existing sample paths, without reset or deletion. The naive first version remains fictional-sample-only and must be replaced.
Original comma-only CSV parsing, UTF-8/BOM, quoting, multiline/count, blank-line, header and length rules remain unchanged. Exits remain 0 no reported problems, 1 reported problems, 2 usage/read errors. Passing these checks is not schema, value-meaning, formula/spreadsheet safety or acceptance by another program. No separator guessing.
The final checker has no write/move/delete/network code but reads the whole file into memory. No file-size/time/resource limit, atomic snapshot or hostile-race defense. Stop editors/sync. Paths and header names can be private. Small fictional fixtures are not proof on all filesystems. No desktop Windows/macOS recording. Recorder removes only its own temporary fixture folder. Decisions and feedback are teaching text, not recorded output.

MIT code. Python separately licensed/not included.

Reference: https://docs.python.org/3/library/os.html

Windows pair: https://github.com/faiz12321/lesson-lab/actions/runs/38972246221
Ubuntu pair: https://github.com/faiz12321/lesson-lab/actions/runs/38972330611
