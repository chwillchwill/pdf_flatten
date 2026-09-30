from pathlib import Path

import pymupdf

from pdf_flattener import flatten_pdf, output_path_for


def make_sample(path: Path) -> None:
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 100), "Some body text to highlight here.")
    note = page.add_text_annot((500, 90), "Sticky note comment")
    note.set_info(title="Alice")
    note.update()
    hl = page.add_highlight_annot(page.search_for("body text")[0])
    hl.set_info(content="Highlight comment that is long enough to wrap onto several lines of the box.")
    hl.update()
    page.add_rect_annot(pymupdf.Rect(72, 300, 200, 400))  # no comment

    w = pymupdf.Widget()
    w.field_name, w.field_type = "name", pymupdf.PDF_WIDGET_TYPE_TEXT
    w.rect, w.field_value = pymupdf.Rect(72, 500, 300, 520), "Form value"
    page.add_widget(w)

    rotated = doc.new_page()
    rotated.set_rotation(90)
    rotated.add_text_annot((50, 50), "Rotated page note")
    doc.save(path)


def test_flatten(tmp_path):
    src = tmp_path / "sample.pdf"
    make_sample(src)

    out, added = flatten_pdf(src)

    assert out == tmp_path / "sample_flattened.pdf" == output_path_for(src)
    assert added == 3
    with pymupdf.open(out) as doc:
        assert all(not list(p.annots()) and not list(p.widgets()) for p in doc)
        text = "\n".join(p.get_text() for p in doc)
    assert "Alice: Sticky note comment" in text
    assert "several lines" in text
    assert "Form value" in text
    assert "Rotated page note" in text
    assert src.exists()  # original untouched
