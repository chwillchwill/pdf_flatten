"""Convert PDF annotations to text boxes and flatten the document.

Run with no arguments to pick a PDF from a file dialog, or pass a path:

    python pdf_flattener.py [input.pdf]

In the Windows .exe, dropping a PDF onto the program flattens it directly.

The result is written next to the input as <name>_flattened.pdf.
"""

import sys
from pathlib import Path

import pymupdf

BOX_WIDTH = 180  # points
FONT_SIZE = 9
FONT_NAME = "helv"
PADDING = 4
GAP = 6  # space between the annotation and its text box

# Annotations that have no comment of their own to convert.
SKIP_TYPES = {
    pymupdf.PDF_ANNOT_FREE_TEXT,  # already a text box
    pymupdf.PDF_ANNOT_POPUP,
    pymupdf.PDF_ANNOT_LINK,
    pymupdf.PDF_ANNOT_WIDGET,
}


def output_path_for(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}_flattened.pdf")


def _wrap_line_count(text: str, width: float) -> int:
    """Estimate how many lines `text` needs when wrapped to `width`."""
    lines = 0
    for paragraph in text.splitlines() or [""]:
        line_len = 0.0
        lines += 1
        for word in paragraph.split(" "):
            w = pymupdf.get_text_length(word + " ", fontname=FONT_NAME, fontsize=FONT_SIZE)
            if line_len and line_len + w > width:
                lines += 1
                line_len = 0.0
            line_len += w
    return lines


def _place_box(
    annot_rect: pymupdf.Rect, page_rect: pymupdf.Rect, height: float, placed: list[pymupdf.Rect]
) -> pymupdf.Rect:
    """Put the box to the right of the annotation, else left, else below; keep it on the page
    and move it down past any box already placed that it would overlap."""
    width = min(BOX_WIDTH, page_rect.width - 2 * GAP)
    height = min(height, page_rect.height - 2 * GAP)
    top = annot_rect.y0

    if annot_rect.x1 + GAP + width <= page_rect.x1:
        x0 = annot_rect.x1 + GAP
    elif annot_rect.x0 - GAP - width >= page_rect.x0:
        x0 = annot_rect.x0 - GAP - width
    else:
        x0 = annot_rect.x0
        top = annot_rect.y1 + GAP

    x0 = max(page_rect.x0 + GAP, min(x0, page_rect.x1 - GAP - width))
    top = max(page_rect.y0 + GAP, min(top, page_rect.y1 - GAP - height))
    rect = pymupdf.Rect(x0, top, x0 + width, top + height)
    moved = True
    while moved:
        moved = False
        for other in placed:
            if rect.intersects(other) and other.y1 + GAP + height <= page_rect.y1 - GAP:
                rect = pymupdf.Rect(x0, other.y1 + GAP, x0 + width, other.y1 + GAP + height)
                moved = True
    return rect


def annotations_to_text_boxes(page: pymupdf.Page) -> int:
    """Add a FreeText box for every annotation comment on the page. Returns the count."""
    # Lay boxes out in visible (rotated) coordinates; annotations use unrotated ones.
    page_rect = page.rect
    to_add = []
    to_delete = []

    for annot in page.annots():
        if annot.type[0] in SKIP_TYPES:
            continue
        content = (annot.info.get("content") or "").strip()
        if content:
            author = (annot.info.get("title") or "").strip()
            text = f"{author}: {content}" if author else content
            to_add.append((annot.rect * page.rotation_matrix, text))
        # Sticky-note icons carry nothing visual once their text is shown.
        if annot.type[0] == pymupdf.PDF_ANNOT_TEXT:
            to_delete.append(annot)

    for annot in to_delete:
        page.delete_annot(annot)

    placed = []
    for annot_rect, text in sorted(to_add, key=lambda item: (item[0].y0, item[0].x0)):
        inner_width = min(BOX_WIDTH, page_rect.width - 2 * GAP) - 2 * PADDING
        lines = _wrap_line_count(text, inner_width)
        height = lines * FONT_SIZE * 1.25 + 2 * PADDING + 2
        visible_rect = _place_box(annot_rect, page_rect, height, placed)
        placed.append(visible_rect)
        rect = visible_rect * page.derotation_matrix
        box = page.add_freetext_annot(
            rect,
            text,
            fontsize=FONT_SIZE,
            fontname=FONT_NAME,
            text_color=(0, 0, 0),
            fill_color=(1, 1, 0.8),
            border_width=0.5,
            rotate=page.rotation,
        )
        box.set_border(width=0.5)
        box.update()

    return len(to_add)


def flatten_pdf(input_path: Path) -> tuple[Path, int]:
    """Convert annotations to text boxes, flatten, and save. Returns (output path, boxes added)."""
    output_path = output_path_for(input_path)
    with pymupdf.open(input_path) as doc:
        if doc.needs_pass:
            raise ValueError("The PDF is password protected.")
        added = sum(annotations_to_text_boxes(page) for page in doc)
        # Burn all annotations and form fields into the page content.
        doc.bake(annots=True, widgets=True)
        doc.save(output_path, garbage=3, deflate=True)
    return output_path, added


def run_gui(input_path: Path | None = None) -> None:
    """Flatten `input_path` with dialog feedback, asking for a file if none is given."""
    import tkinter as tk
    from tkinter import filedialog, messagebox

    root = tk.Tk()
    root.withdraw()
    try:
        _pick_and_flatten(filedialog, messagebox, input_path)
    finally:
        root.destroy()


def _pick_and_flatten(filedialog, messagebox, input_path: Path | None) -> None:
    if input_path is None:
        selected = filedialog.askopenfilename(
            title="Select a PDF to flatten",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
        )
        if not selected:
            return
        input_path = Path(selected)

    output_path = output_path_for(input_path)
    if output_path.exists() and not messagebox.askyesno(
        "Overwrite?", f"{output_path.name} already exists. Overwrite it?"
    ):
        return

    try:
        output_path, added = flatten_pdf(input_path)
    except Exception as exc:
        messagebox.showerror("PDF Flattener", f"Could not flatten {input_path.name}:\n\n{exc}")
        return

    messagebox.showinfo(
        "PDF Flattener",
        f"Converted {added} annotation(s) to text boxes.\n\nSaved:\n{output_path}",
    )


def main() -> None:
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    # A windowed .exe has no console (sys.stdout is None), e.g. when a PDF is
    # dropped onto it, so report through dialogs instead of printing.
    if input_path is not None and sys.stdout is not None:
        output_path, added = flatten_pdf(input_path)
        print(f"Converted {added} annotation(s) to text boxes. Saved {output_path}")
    else:
        run_gui(input_path)


if __name__ == "__main__":
    main()
