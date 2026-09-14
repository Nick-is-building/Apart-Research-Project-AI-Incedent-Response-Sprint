"""Place output/paper.md into the official submission template.

The template supplies the page setup, the fonts and the named styles; this
module supplies the content. It rebuilds `word/document.xml` from the paper's
markdown and leaves `styles.xml`, `numbering.xml`, the theme and the section
properties exactly as the template defines them, so the result carries the
template's typography rather than an imitation of it.

Writes output/paper.docx. Convert and count pages with --pdf.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = REPO_ROOT / "Digital Minds Research Sprint submission template.docx"
PAPER_MD = REPO_ROOT / "output" / "paper.md"
OUTPUT_DOCX = REPO_ROOT / "output" / "paper.docx"

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"
WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"

EMU_PER_INCH = 914400
CONTENT_WIDTH_EMU = int(6.5 * EMU_PER_INCH)  # Letter minus 1in margins
BULLET_NUM_ID = "3"  # abstractNum 3 is the bullet list in the template


def esc(text: str) -> str:
    return (text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def runs(text: str) -> str:
    """Inline markdown -> WordprocessingML runs. Bold, italic, code."""
    out: list[str] = []
    token = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)")
    for part in token.split(text):
        if not part:
            continue
        props = ""
        if part.startswith("**") and part.endswith("**"):
            part, props = part[2:-2], "<w:b/>"
        elif part.startswith("*") and part.endswith("*"):
            part, props = part[1:-1], "<w:i/>"
        elif part.startswith("`") and part.endswith("`"):
            part, props = part[1:-1], '<w:rFonts w:ascii="Courier New" w:hAnsi="Courier New"/>'
        rpr = f"<w:rPr>{props}</w:rPr>" if props else ""
        out.append(f'<w:r>{rpr}<w:t xml:space="preserve">{esc(part)}</w:t></w:r>')
    return "".join(out)


def para(text: str = "", style: str | None = None, extra: str = "") -> str:
    ppr = ""
    if style or extra:
        style_xml = '<w:pStyle w:val="%s"/>' % style if style else ""
        ppr = "<w:pPr>%s%s</w:pPr>" % (style_xml, extra)
    return f"<w:p>{ppr}{runs(text)}</w:p>"


def bullet(text: str) -> str:
    extra = (f'<w:numPr><w:ilvl w:val="0"/><w:numId w:val="{BULLET_NUM_ID}"/></w:numPr>'
             '<w:spacing w:before="0" w:after="40"/>')
    return para(text, extra=extra)


def quote(text: str) -> str:
    # pPr child order is schema-enforced: spacing precedes ind.
    extra = '<w:spacing w:before="60" w:after="60"/><w:ind w:left="567"/>' 
    return f'<w:p><w:pPr>{extra}</w:pPr>{runs("*" + text + "*")}</w:p>'


def column_weights(rows: list[list[str]], columns: int) -> list[float]:
    """Share the table width by how much text each column actually carries.

    Equal columns waste most of a page when one column holds a sentence and
    another holds "yes". Weights are clamped so no column collapses.
    """
    longest = [max((len(r[c]) for r in rows if c < len(r)), default=1) for c in range(columns)]
    clamped = [max(4.0, min(float(v), 90.0)) for v in longest]
    total = sum(clamped)
    return [v / total for v in clamped]


def table(rows: list[list[str]]) -> str:
    if not rows:
        return ""
    columns = max(len(r) for r in rows)
    width = 9360  # 6.5in in DXA
    weights = column_weights(rows, columns)
    widths = [max(500, int(width * w)) for w in weights]
    borders = ("<w:tblBorders>"
               + "".join(f'<w:{e} w:val="single" w:sz="4" w:color="BFBFBF"/>'
                         for e in ("top", "left", "bottom", "right", "insideH", "insideV"))
               + "</w:tblBorders>")
    grid = "".join(f'<w:gridCol w:w="{w}"/>' for w in widths)
    out = [f'<w:tbl><w:tblPr><w:tblW w:w="{width}" w:type="dxa"/>{borders}</w:tblPr>'
           f'<w:tblGrid>{grid}</w:tblGrid>']
    for index, row in enumerate(rows):
        cells = []
        for column in range(columns):
            text = row[column] if column < len(row) else ""
            body = para(f"**{text}**" if index == 0 else text,
                        extra='<w:spacing w:before="20" w:after="20"/>')
            shade = '<w:shd w:val="clear" w:fill="F2F2F2"/>' if index == 0 else ""
            cells.append(f'<w:tc><w:tcPr><w:tcW w:w="{widths[column]}" w:type="dxa"/>{shade}'
                         f'</w:tcPr>{body}</w:tc>')
        out.append(f"<w:tr>{''.join(cells)}</w:tr>")
    out.append("</w:tbl>")
    return "".join(out) + para()


def image(rel_id: str, width_emu: int, height_emu: int, name: str) -> str:
    return (
        f'<w:p><w:pPr><w:spacing w:before="120" w:after="60"/><w:jc w:val="center"/></w:pPr>'
        f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0" '
        f'xmlns:wp="{WP}">'
        f'<wp:extent cx="{width_emu}" cy="{height_emu}"/>'
        f'<wp:docPr id="{abs(hash(name)) % 100000}" name="{esc(name)}"/>'
        f'<a:graphic xmlns:a="{A}"><a:graphicData '
        f'uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:pic xmlns:pic="{PIC}"><pic:nvPicPr>'
        f'<pic:cNvPr id="0" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip xmlns:r="{R}" r:embed="{rel_id}"/>'
        f'<a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        f'<pic:spPr><a:xfrm><a:off x="0" y="0"/>'
        f'<a:ext cx="{width_emu}" cy="{height_emu}"/></a:xfrm>'
        f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        f'</pic:pic></a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
    )


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"not a PNG: {path}")
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


class Converter:
    """Markdown -> WordprocessingML body, using the template's named styles."""

    def __init__(self) -> None:
        self.images: list[tuple[str, Path]] = []
        self.body: list[str] = []

    def add_image(self, path: Path) -> str:
        rel_id = f"rIdImg{len(self.images) + 1}"
        self.images.append((rel_id, path))
        pixels_w, pixels_h = png_size(path)
        width = CONTENT_WIDTH_EMU
        height = int(width * pixels_h / pixels_w)
        self.body.append(image(rel_id, width, height, path.name))
        return rel_id

    def convert(self, markdown: str) -> str:
        lines = markdown.splitlines()
        index = 0
        pending_table: list[list[str]] = []

        def flush_table() -> None:
            nonlocal pending_table
            if pending_table:
                self.body.append(table(pending_table))
                pending_table = []

        while index < len(lines):
            line = lines[index].rstrip()
            stripped = line.strip()

            if stripped.startswith("|"):
                cells = [c.strip() for c in stripped.strip("|").split("|")]
                if not all(set(c) <= set("-: ") for c in cells):
                    pending_table.append(cells)
                index += 1
                continue
            flush_table()

            if not stripped:
                index += 1
                continue
            if stripped == "---":
                index += 1
                continue

            picture = re.match(r"!\[[^\]]*\]\(([^)]+)\)", stripped)
            if picture:
                path = REPO_ROOT / "output" / picture.group(1)
                if path.exists():
                    self.add_image(path)
                index += 1
                continue

            if stripped.startswith("# "):
                self.body.append(para(stripped[2:], style="Title"))
            elif stripped.startswith("### "):
                self.body.append(para(stripped[4:], style="Heading3"))
            elif stripped.startswith("## "):
                self.body.append(para(stripped[3:], style="Heading2"))
            elif stripped.startswith("#### "):
                self.body.append(para(stripped[5:], style="Heading4"))
            elif stripped.startswith("> "):
                self.body.append(quote(stripped[2:]))
            elif stripped.startswith("- "):
                self.body.append(bullet(stripped[2:]))
            else:
                self.body.append(para(stripped))
            index += 1

        flush_table()
        return "".join(self.body)


def build(template: Path = TEMPLATE, paper: Path = PAPER_MD,
          out: Path = OUTPUT_DOCX) -> Path:
    if not template.exists():
        raise SystemExit(f"template not found: {template}")

    work = REPO_ROOT / "output" / "_docx_build"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    with zipfile.ZipFile(template) as archive:
        archive.extractall(work)
    for path in work.rglob("*"):
        if path.is_symlink():
            path.unlink()

    document = work / "word" / "document.xml"
    # Without this, ElementTree re-serialises the section properties with an
    # ns0: prefix instead of w:, which some readers reject.
    ET.register_namespace("w", W)
    tree = ET.parse(document)
    root = tree.getroot()
    body = root.find(f"{{{W}}}body")
    sect_pr = body.find(f"{{{W}}}sectPr")
    sect_xml = ET.tostring(sect_pr, encoding="unicode") if sect_pr is not None else ""

    converter = Converter()
    content = converter.convert(paper.read_text(encoding="utf-8"))

    header = document.read_text(encoding="utf-8").split("<w:body>")[0]
    document.write_text(f"{header}<w:body>{content}{sect_xml}</w:body></w:document>",
                        encoding="utf-8")

    # images: media files, relationships, content-type override
    media = work / "word" / "media"
    media.mkdir(exist_ok=True)
    rels_path = work / "word" / "_rels" / "document.xml.rels"
    rels = rels_path.read_text(encoding="utf-8")
    added = []
    for rel_id, source in converter.images:
        target = media / source.name
        shutil.copy(source, target)
        added.append(
            f'<Relationship Id="{rel_id}" Type="http://schemas.openxmlformats.org/'
            f'officeDocument/2006/relationships/image" Target="media/{source.name}"/>'
        )
    rels_path.write_text(rels.replace("</Relationships>", "".join(added) + "</Relationships>"),
                         encoding="utf-8")

    types_path = work / "[Content_Types].xml"
    types = types_path.read_text(encoding="utf-8")
    if 'Extension="png"' not in types:
        types = types.replace(
            "<Default", '<Default Extension="png" ContentType="image/png"/><Default', 1)
        types_path.write_text(types, encoding="utf-8")

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    # [Content_Types].xml must be the first entry in the archive; some readers
    # refuse the package otherwise even though the XML itself validates.
    files = [p for p in sorted(work.rglob("*")) if p.is_file()]
    first = work / "[Content_Types].xml"
    ordered = ([first] if first in files else []) + [p for p in files if p != first]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in ordered:
            archive.write(path, path.relative_to(work).as_posix())
    shutil.rmtree(work)
    return out


def to_pdf(docx: Path) -> tuple[Path | None, int | None]:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None, None
    subprocess.run([soffice, "--headless", "--convert-to", "pdf",
                    "--outdir", str(docx.parent), str(docx)],
                   check=True, capture_output=True, timeout=300)
    pdf = docx.with_suffix(".pdf")
    if not pdf.exists():
        return None, None
    pages = pdf.read_bytes().count(b"/Type /Page") or pdf.read_bytes().count(b"/Type/Page")
    return pdf, pages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", action="store_true", help="also convert and count pages")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args(argv)

    docx = build()
    if not args.quiet:
        print(f"Written: {docx.relative_to(REPO_ROOT)}")
    if args.pdf:
        pdf, pages = to_pdf(docx)
        if pdf is None:
            print("LibreOffice not available; page count not determined")
        elif not args.quiet:
            print(f"Written: {pdf.relative_to(REPO_ROOT)}   pages: {pages}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
