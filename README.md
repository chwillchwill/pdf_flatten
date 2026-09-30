# PDF Flattener

Pick a PDF from a dialog, turn its annotation comments into visible text boxes, and flatten
everything (annotations and form fields) into the page content. The result is saved beside
the original as `<name>_flattened.pdf`. The original file is not modified.

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

The dialog uses tkinter. It comes with Python on Windows and macOS. On Ubuntu/WSL, install it with:

```bash
sudo apt install python3-tk
```

## Usage

```bash
.venv/bin/python pdf_flattener.py              # choose a file in the dialog
.venv/bin/python pdf_flattener.py input.pdf    # or skip the dialog
```

## What happens to annotations

- Any annotation with a comment (sticky notes, highlights, shapes, etc.) gets a yellow text box
  beside it showing `Author: comment`.
- Sticky-note icons are removed, since their text now appears in a box. Highlights, shapes, ink,
  and other markups stay as they look.
- All annotations and form fields are then baked into the page, so the output has no
  annotations left.

## Windows executable

Builds a single `dist\PDFFlattener.exe` (no console window, no Python needed to run it) with
PyInstaller. It must be built on Windows with Python installed (the `py` launcher).

- From a Windows checkout: run `build.bat`.
- From WSL: run `./build_windows.sh`. It builds in `%TEMP%\pdf_flattener_build` using the
  Windows Python and copies the result to `dist/PDFFlattener.exe`.

Double-click the exe to choose a file, or drop a PDF onto it to flatten that file directly.

## Tests

```bash
.venv/bin/pip install pytest
.venv/bin/python -m pytest tests
```
