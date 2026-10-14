#!/usr/bin/env python3
"""
build_manual.py — builds a user manual .docx on top of a Word template.

Usage:
    python3 build_manual.py manual.md output.docx [--template template.docx]

Without --template it uses the neutral template from build_template.py, generated
once into ~/.cache/webapp-docs-kit/manual-template-v2.docx.

The Markdown follows references/markdown-format.md: front matter with the cover data,
the preface text before the first "#", then the sections. The template keeps the cover,
header, footer and table of contents; only its {{...}} markers are replaced: cover data,
{{PREFACE}} and, from {{CONTENT}} to the end, the body. The table of contents stays stale
until the .docx goes through to_pdf.py (LibreOffice or Word recompute it).

Styles are looked up by their built-in names ("heading 1", "List Paragraph", "toc 1"),
which Word keeps in English whatever the UI language, so a template saved from a Word
in any language works. Table header and accent colors come from the template theme
(accent1 and accent2).
"""
import argparse
import datetime
import os
import re
import struct
import sys
import zipfile
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
# The default template is not shipped as a binary: build_template.py writes it to the
# user cache the first time it is needed.
DEFAULT_TEMPLATE = os.path.join(os.environ.get('XDG_CACHE_HOME') or os.path.join(os.path.expanduser('~'), '.cache'),
                                'webapp-docs-kit', 'manual-template-v2.docx')

EMU_PER_TWIP = 635
EMU_MAX_WIDTH = 5580000               # ~15.5 cm
EMU_MAX_HEIGHT = 4300000              # ~11.9 cm: a tall screenshot does not eat the whole page
DEFAULT_PRIMARY = '1F3A5F'
DEFAULT_ACCENT = '2563EB'

MARKERS = ['{{TITLE}}', '{{APP}}', '{{SUBTITLE}}', '{{ORGANIZATION}}', '{{DATE}}',
           '{{PREFACE_TITLE}}', '{{PREFACE}}', '{{CONTENTS_TITLE}}', '{{CONTENT}}']
STYLES = {'h1': 'heading 1', 'h2': 'heading 2', 'h3': 'heading 3', 'list': 'list paragraph'}


def fail(msg):
    sys.exit('Error: ' + msg)


# ── Markdown ────────────────────────────────────────────────────────────────

def read_markdown(path):
    text = open(path, encoding='utf-8').read().replace('\r\n', '\n')
    meta = {}
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                meta[k.strip()] = v.strip().strip('"\'')
        text = text[m.end():]
    if not meta.get('app'):
        fail(f'missing "app" in the front matter of {path}')
    return meta, text


STEP = r'^\s*([a-z]|\d+)[).]\s+'


def blocks(text):
    """Groups lines into blocks: (kind, data)."""
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.strip() == '\\newpage':
            yield ('pagebreak', None); i += 1; continue
        m = re.match(r'^(#{1,3})\s+(.*)$', line)
        if m:
            yield ('h%d' % len(m.group(1)), m.group(2).strip()); i += 1; continue
        m = re.match(r'^!\[(.*?)\]\((.*?)\)\s*$', line)
        if m:
            yield ('figure', (m.group(1), m.group(2))); i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells):
                    rows.append(cells)
                i += 1
            yield ('table', rows); continue
        if line.startswith('>'):
            parts = []
            while i < len(lines) and lines[i].startswith('>'):
                parts.append(lines[i][1:].strip()); i += 1
            yield ('note', ' '.join(parts)); continue
        if re.match(r'^\s*[-*]\s+', line):
            items = []
            while i < len(lines) and re.match(r'^\s*[-*]\s+', lines[i]):
                items.append(re.sub(r'^\s*[-*]\s+', '', lines[i]).strip()); i += 1
            yield ('bullets', items); continue
        if re.match(STEP, line):
            items = []
            while i < len(lines) and re.match(STEP, lines[i]):
                items.append(re.sub(STEP, '', lines[i]).strip()); i += 1
            yield ('steps', items); continue
        parts = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#|!\[|\||>|\s*[-*]\s|\s*([a-z]|\d+)[).]\s|\\newpage)', lines[i]):
            parts.append(lines[i].strip()); i += 1
        yield ('paragraph', ' '.join(parts))


# ── WordprocessingML ────────────────────────────────────────────────────────

class Writer:
    def __init__(self, ids, primary, accent, text_width, figure_label):
        self.ids, self.primary, self.accent = ids, primary, accent
        self.text_width, self.figure_label = text_width, figure_label

    @staticmethod
    def runs(text, rpr=''):
        """Inline **bold**, *italic* and `code`."""
        out = []
        for piece in re.split(r'(\*\*.+?\*\*|`.+?`|\*.+?\*)', text):
            if not piece:
                continue
            extra = ''
            if piece.startswith('**'):
                piece, extra = piece[2:-2], '<w:b/><w:bCs/>'
            elif piece.startswith('`'):
                piece, extra = piece[1:-1], '<w:rFonts w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/><w:sz w:val="20"/>'
            elif piece.startswith('*'):
                piece, extra = piece[1:-1], '<w:i/><w:iCs/>'
            props = extra + rpr
            out.append(f'<w:r>{"<w:rPr>" + props + "</w:rPr>" if props else ""}'
                       f'<w:t xml:space="preserve">{escape(piece)}</w:t></w:r>')
        return ''.join(out)

    def paragraph(self, text, ppr='<w:spacing w:after="160"/>', rpr=''):
        return f'<w:p><w:pPr>{ppr}</w:pPr>{self.runs(text, rpr)}</w:p>'

    EMPTY = '<w:p/>'

    def heading1(self, text):
        # Bordered paragraph rather than a table: LibreOffice ignores "keep with next" on
        # tables and the title could end up alone at the bottom of a page.
        return (self.EMPTY +
                f'<w:p><w:pPr><w:pStyle w:val="{self.ids["h1"]}"/><w:keepNext/><w:keepLines/>'
                f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="1" w:color="{self.accent}"/></w:pBdr>'
                f'<w:spacing w:before="240" w:after="240"/></w:pPr>'
                f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')

    def heading(self, text, level):
        return (f'<w:p><w:pPr><w:pStyle w:val="{self.ids[level]}"/><w:keepNext/><w:spacing w:before="200" w:after="160"/></w:pPr>'
                f'<w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>')

    def listing(self, items, num_id):
        return ''.join(
            f'<w:p><w:pPr><w:pStyle w:val="{self.ids["list"]}"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num_id}"/></w:numPr>'
            f'<w:spacing w:after="60"/></w:pPr>{self.runs(t)}</w:p>' for t in items) + self.EMPTY

    def note(self, text):
        return (f'<w:p><w:pPr><w:pBdr><w:left w:val="single" w:sz="24" w:space="8" w:color="{self.accent}"/></w:pBdr>'
                f'<w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/><w:spacing w:before="120" w:after="200"/><w:ind w:left="170" w:right="170"/></w:pPr>'
                f'{self.runs(text)}</w:p>')

    def table(self, rows):
        ncol = max(len(r) for r in rows)
        rows = [r + [''] * (ncol - len(r)) for r in rows]
        # Width proportional to each column's longest text, capped so no column becomes unreadable.
        weights = [min(max(len(re.sub(r'[*`]', '', r[c])) for r in rows), 60) + 8 for c in range(ncol)]
        widths = [int((self.text_width - 120) * w / sum(weights)) for w in weights]

        def cell(text, width, head):
            shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{self.primary}"/>' if head else ''
            rpr = '<w:sz w:val="21"/><w:szCs w:val="21"/>' + ('<w:b/><w:color w:val="FFFFFF"/>' if head else '')
            jc = 'center' if head else 'left'
            return (f'<w:tc><w:tcPr><w:tcW w:w="{width}" w:type="dxa"/>{shd}</w:tcPr>'
                    f'<w:p><w:pPr><w:spacing w:before="40" w:after="40"/><w:jc w:val="{jc}"/></w:pPr>{self.runs(text, rpr)}</w:p></w:tc>')
        xml = ('<w:tbl><w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblInd w:w="60" w:type="dxa"/><w:tblBorders>'
               + ''.join(f'<w:{b} w:val="single" w:sz="4" w:space="0" w:color="BFC5CD"/>' for b in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'))
               + '</w:tblBorders><w:tblCellMar><w:left w:w="90" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar></w:tblPr><w:tblGrid>'
               + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>')
        for n, r in enumerate(rows):
            xml += ('<w:tr><w:trPr><w:cantSplit/>' + ('<w:tblHeader/>' if n == 0 else '') + '</w:trPr>'
                    + ''.join(cell(t, w, n == 0) for t, w in zip(r, widths)) + '</w:tr>')
        return xml + '</w:tbl>' + self.EMPTY

    def figure(self, rid, n, width_px, height_px, caption):
        cx = min(EMU_MAX_WIDTH, self.text_width * EMU_PER_TWIP)
        cy = int(cx * height_px / width_px)
        if cy > EMU_MAX_HEIGHT:
            cy = EMU_MAX_HEIGHT
            cx = int(cy * width_px / height_px)
        caption = f'{self.figure_label} {n}. {caption}'
        return (
            '<w:p><w:pPr><w:keepNext/><w:jc w:val="center"/><w:spacing w:before="120" w:after="60"/></w:pPr><w:r><w:drawing>'
            f'<wp:inline xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{1000 + n}" name="Figure {n}" descr="{escape(caption, {chr(34): "&quot;"})}"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"><pic:nvPicPr><pic:cNvPr id="{1000 + n}" name="figure{n}.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '<a:ln w="9525"><a:solidFill><a:srgbClr val="BFC5CD"/></a:solidFill></a:ln></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'
            + self.paragraph(caption, '<w:jc w:val="center"/><w:spacing w:after="240"/>', '<w:i/><w:color w:val="595959"/><w:sz w:val="18"/>')
        )


def png_size(path):
    with open(path, 'rb') as f:
        head = f.read(24)
    if head[:8] != b'\x89PNG\r\n\x1a\n':
        fail(f'{path} is not a PNG (screenshots must be PNG)')
    return struct.unpack('>II', head[16:24])


# ── Template ────────────────────────────────────────────────────────────────

def find_paragraph(xml, text):
    """Paragraph whose whole text is `text`, even if Word split it into several runs."""
    for m in re.finditer(r'<w:p[ >](?:(?!<w:p[ >]).)*?</w:p>', xml, re.S):
        if ''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', m.group(0))).strip() == text:
            return m
    fail(f'the template does not have the marker {text} alone in a paragraph')


def replace_paragraph_text(xml, old, new):
    m = find_paragraph(xml, old)
    first = [True]

    def sub(_):
        if first[0]:
            first[0] = False
            return f'<w:t xml:space="preserve">{escape(new)}</w:t>'
        return '<w:t></w:t>'
    return xml[:m.start()] + re.sub(r'<w:t[^>]*>[^<]*</w:t>', sub, m.group(0)) + xml[m.end():]


def style_ids(styles_xml):
    ids = {}
    for sid, name in re.findall(r'<w:style [^>]*w:styleId="([^"]+)"[^>]*>\s*<w:name w:val="([^"]+)"', styles_xml):
        for key, wanted in STYLES.items():
            if name.lower() == wanted:
                ids[key] = sid
    missing = [STYLES[k] for k in STYLES if k not in ids]
    if missing:
        fail('the template lacks the built-in styles: ' + ', '.join(missing))
    return ids


def theme_colors(files):
    theme = files.get('word/theme/theme1.xml', b'').decode('utf-8', 'ignore')

    def accent(n, default):
        m = re.search(rf'<a:accent{n}>\s*<a:srgbClr val="([0-9A-Fa-f]{{6}})"', theme)
        return m.group(1).upper() if m else default
    return accent(1, DEFAULT_PRIMARY), accent(2, DEFAULT_ACCENT)


def text_width(doc):
    """Usable width (twips) from the template's last section."""
    sect = doc[doc.rfind('<w:sectPr'):]
    w = re.search(r'<w:pgSz [^>]*w:w="(\d+)"', sect)
    left = re.search(r'<w:pgMar [^>]*w:left="(\d+)"', sect)
    right = re.search(r'<w:pgMar [^>]*w:right="(\d+)"', sect)
    if not (w and left and right):
        return 9070
    return int(w.group(1)) - int(left.group(1)) - int(right.group(1))


def check_template(doc, numbering):
    """Fails with a clear message if the template is unusable. Returns (bullet numId, letters abstractNumId)."""
    for k in MARKERS:
        if doc.count(k) != 1:
            fail(f'the template must contain the marker {k} exactly once (found {doc.count(k)})')
    formats = {}
    for a in re.findall(r'<w:abstractNum .*?</w:abstractNum>', numbering, re.S):
        level0 = re.search(r'<w:lvl w:ilvl="0".*?</w:lvl>', a, re.S)
        fmt = re.search(r'w:numFmt w:val="(\w+)"', level0.group(0)) if level0 else None
        if fmt:
            formats[re.search(r'w:abstractNumId="(\d+)"', a).group(1)] = fmt.group(1)
    bullet = next((n for n, a in re.findall(r'<w:num w:numId="(\d+)"[^>]*>\s*<w:abstractNumId w:val="(\d+)"', numbering)
                   if formats.get(a) == 'bullet'), None)
    letters = next((a for a, f in formats.items() if f == 'lowerLetter'), None)
    if not bullet or not letters:
        fail('the template must define one bulleted list and one a), b), c) list')
    return bullet, letters


# ── Assembly ────────────────────────────────────────────────────────────────

def build(md, out, template):
    meta, text = read_markdown(md)
    md_dir = os.path.dirname(os.path.abspath(md))
    if template is None:
        template = DEFAULT_TEMPLATE
        if not os.path.exists(template):
            sys.path.insert(0, HERE)
            import build_template
            build_template.build(template, build_template.PRIMARY, build_template.ACCENT, False)
    elif not os.path.exists(template):
        fail(f'template not found: {template}')

    with zipfile.ZipFile(template) as z:
        files = {n: z.read(n) for n in z.namelist()}
    doc = files['word/document.xml'].decode('utf-8')
    rels = files['word/_rels/document.xml.rels'].decode('utf-8')
    numbering = files['word/numbering.xml'].decode('utf-8')
    types = files['[Content_Types].xml'].decode('utf-8')

    # Bullets reuse an existing w:num of the template. Each a), b) list gets a new one so it restarts at "a".
    bullet_num, letters_abs = check_template(doc, numbering)
    ids = style_ids(files['word/styles.xml'].decode('utf-8'))
    primary, accent = theme_colors(files)
    w = Writer(ids, primary, accent, text_width(doc), meta.get('figure_label', 'Figure'))
    next_num = max(int(x) for x in re.findall(r'<w:num w:numId="(\d+)"', numbering)) + 1
    new_nums = []

    preface, body = [], []
    target = preface
    h1 = h2 = nfig = 0
    for kind, data in blocks(text):
        if kind == 'h1':
            target = body
            h1 += 1; h2 = 0
            body.append(w.heading1(f'{h1}. {data}'))
        elif kind == 'h2':
            h2 += 1
            target.append(w.heading(f'{h1}.{h2} {data}', 'h2'))
        elif kind == 'h3':
            target.append(w.heading(data, 'h3'))
        elif kind == 'paragraph':
            target.append(w.paragraph(data))
        elif kind == 'bullets':
            target.append(w.listing(data, bullet_num))
        elif kind == 'steps':
            new_nums.append(f'<w:num w:numId="{next_num}"><w:abstractNumId w:val="{letters_abs}"/>'
                            '<w:lvlOverride w:ilvl="0"><w:startOverride w:val="1"/></w:lvlOverride></w:num>')
            target.append(w.listing(data, next_num))
            next_num += 1
        elif kind == 'table':
            target.append(w.table(data))
        elif kind == 'note':
            target.append(w.note(data))
        elif kind == 'pagebreak':
            target.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')
        elif kind == 'figure':
            caption, path = data
            path = path if os.path.isabs(path) else os.path.join(md_dir, path)
            if not os.path.exists(path):
                fail(f'image not found: {path}')
            nfig += 1
            name = f'media/manual{nfig}.png'
            rid = f'rIdManual{nfig}'
            files['word/' + name] = open(path, 'rb').read()
            rels = rels.replace('</Relationships>',
                                f'<Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="{name}"/></Relationships>')
            target.append(w.figure(rid, nfig, *png_size(path), caption))
    if not preface:
        fail('missing the preface text (it goes before the first "#")')

    # Cover, titles, header and footer.
    values = {
        '{{TITLE}}': meta.get('title', 'User manual'),
        '{{APP}}': meta['app'],
        '{{SUBTITLE}}': meta.get('subtitle', ''),
        '{{HEADER}}': meta['app'] + (' · ' + meta['subtitle'] if meta.get('subtitle') else ''),
        '{{ORGANIZATION}}': meta.get('organization', ''),
        '{{DATE}}': meta.get('date', datetime.date.today().strftime('%B %Y')),
        '{{PREFACE_TITLE}}': meta.get('preface_title', 'About this manual'),
        '{{CONTENTS_TITLE}}': meta.get('contents_title', 'Contents'),
    }
    for marker, value in values.items():
        if marker in MARKERS:
            doc = replace_paragraph_text(doc, marker, value)
    for name in list(files):
        if re.fullmatch(r'word/(header|footer)\d*\.xml', name):
            part = files[name].decode('utf-8')
            for marker, value in values.items():
                part = part.replace(marker, escape(value))
            files[name] = part.encode('utf-8')

    # Preface: the marker paragraph becomes the manual's paragraphs.
    m = find_paragraph(doc, '{{PREFACE}}')
    doc = doc[:m.start()] + ''.join(preface) + doc[m.end():]

    # Body: from the {{CONTENT}} paragraph (and the sample after it) to the final sectPr.
    m = re.search(r'<w:p[ >](?:(?!<w:p[ >]).)*?\{\{CONTENT\}\}', doc, re.S)
    doc = doc[:m.start()] + ''.join(body) + doc[doc.rfind('<w:sectPr'):]

    # Images of the sample that are no longer referenced.
    for rid, img in re.findall(r'<Relationship Id="([^"]+)" Type="[^"]*/image" Target="([^"]+)"/>', rels):
        if f'r:embed="{rid}"' not in doc:
            rels = re.sub(rf'<Relationship Id="{rid}"[^>]*/>', '', rels)
            files.pop('word/' + img, None)

    if new_nums:
        # w:num elements go after every w:abstractNum.
        numbering = numbering.replace('</w:numbering>', ''.join(new_nums) + '</w:numbering>')
    if 'Extension="png"' not in types:
        types = types.replace('</Types>', '<Default Extension="png" ContentType="image/png"/></Types>')

    files['word/document.xml'] = doc.encode('utf-8')
    files['word/_rels/document.xml.rels'] = rels.encode('utf-8')
    files['word/numbering.xml'] = numbering.encode('utf-8')
    files['[Content_Types].xml'] = types.encode('utf-8')

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(name, data)
    print(f'docx: {out} ({h1} sections, {nfig} figures)')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('markdown')
    ap.add_argument('output')
    ap.add_argument('--template', help='custom .docx template (default: generated by build_template.py)')
    a = ap.parse_args()
    build(a.markdown, a.output, a.template)
