#!/usr/bin/env python3
"""
build_template.py — writes the default manual template (template/manual-template.docx).

Usage:
    python3 build_template.py [output.docx] [--primary 1F3A5F] [--accent 2563EB] [--letter]

The template is plain WordprocessingML written from scratch, so it carries no logos and
no third-party branding. --primary is the table header color (theme accent1), --accent
the line under section titles and the bar of notes (theme accent2). --letter uses US
Letter instead of A4. You can also open the generated file in Word or LibreOffice and
restyle it by hand: build_manual.py only needs the {{...}} markers, the built-in
heading/list/TOC styles, one bulleted list and one a), b), c) list.
"""
import argparse
import os
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_OUT = os.path.join(HERE, '..', 'template', 'manual-template.docx')

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" ' \
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
DARK = '1F2937'
GRAY = '4B5563'


def content_types():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Default Extension="png" ContentType="image/png"/>'
            '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
            '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
            '<Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>'
            '<Override PartName="/word/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
            '<Override PartName="/word/header1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.header+xml"/>'
            '<Override PartName="/word/footer1.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>'
            '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
            '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
            '</Types>')


def root_rels():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            '</Relationships>')


def document_rels():
    t = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f'<Relationship Id="rId1" Type="{t}styles" Target="styles.xml"/>'
            f'<Relationship Id="rId2" Type="{t}numbering" Target="numbering.xml"/>'
            f'<Relationship Id="rId3" Type="{t}settings" Target="settings.xml"/>'
            f'<Relationship Id="rId4" Type="{t}theme" Target="theme/theme1.xml"/>'
            f'<Relationship Id="rId5" Type="{t}header" Target="header1.xml"/>'
            f'<Relationship Id="rId6" Type="{t}footer" Target="footer1.xml"/>'
            '</Relationships>')


def core():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>User manual</dc:title><dc:creator>webapp-docs-kit</dc:creator></cp:coreProperties>')


def app():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
            '<Application>webapp-docs-kit</Application></Properties>')


def settings():
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:settings {W}><w:defaultTabStop w:val="720"/><w:characterSpacingControl w:val="doNotCompress"/>'
            '<w:compat><w:compatSetting w:name="compatibilityMode" w:uri="http://schemas.microsoft.com/office/word" w:val="15"/></w:compat>'
            '</w:settings>')


def theme(primary, accent):
    fills = ('<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>' * 3)
    lines = ''.join(f'<a:ln w="{w}"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>' for w in (6350, 12700, 19050))
    effects = '<a:effectStyle><a:effectLst/></a:effectStyle>' * 3
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="webapp-docs-kit"><a:themeElements>'
            '<a:clrScheme name="webapp-docs-kit">'
            '<a:dk1><a:srgbClr val="000000"/></a:dk1><a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>'
            f'<a:dk2><a:srgbClr val="{DARK}"/></a:dk2><a:lt2><a:srgbClr val="F3F4F6"/></a:lt2>'
            f'<a:accent1><a:srgbClr val="{primary}"/></a:accent1><a:accent2><a:srgbClr val="{accent}"/></a:accent2>'
            '<a:accent3><a:srgbClr val="10B981"/></a:accent3><a:accent4><a:srgbClr val="F59E0B"/></a:accent4>'
            '<a:accent5><a:srgbClr val="8B5CF6"/></a:accent5><a:accent6><a:srgbClr val="EF4444"/></a:accent6>'
            '<a:hlink><a:srgbClr val="2563EB"/></a:hlink><a:folHlink><a:srgbClr val="7C3AED"/></a:folHlink></a:clrScheme>'
            '<a:fontScheme name="webapp-docs-kit">'
            '<a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
            '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
            '<a:fmtScheme name="webapp-docs-kit">'
            f'<a:fillStyleLst>{fills}</a:fillStyleLst><a:lnStyleLst>{lines}</a:lnStyleLst>'
            f'<a:effectStyleLst>{effects}</a:effectStyleLst><a:bgFillStyleLst>{fills}</a:bgFillStyleLst>'
            '</a:fmtScheme></a:themeElements><a:objectDefaults/><a:extraClrSchemeLst/></a:theme>')


def styles(primary):
    def heading(n, size, before, after, color):
        return (f'<w:style w:type="paragraph" w:styleId="Heading{n}"><w:name w:val="heading {n}"/>'
                f'<w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:uiPriority w:val="9"/><w:qFormat/>'
                f'<w:pPr><w:keepNext/><w:keepLines/><w:spacing w:before="{before}" w:after="{after}"/><w:outlineLvl w:val="{n - 1}"/></w:pPr>'
                f'<w:rPr><w:b/><w:bCs/><w:color w:val="{color}"/><w:sz w:val="{size}"/><w:szCs w:val="{size}"/></w:rPr></w:style>')

    def toc(n, indent):
        return (f'<w:style w:type="paragraph" w:styleId="TOC{n}"><w:name w:val="toc {n}"/><w:basedOn w:val="Normal"/>'
                f'<w:next w:val="Normal"/><w:uiPriority w:val="39"/><w:pPr><w:tabs><w:tab w:val="right" w:leader="dot" w:pos="9060"/></w:tabs>'
                f'<w:spacing w:after="80"/><w:ind w:left="{indent}"/></w:pPr>{"<w:rPr><w:b/></w:rPr>" if n == 1 else ""}</w:style>')

    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:styles {W}>'
            '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Calibri" w:cs="Calibri"/>'
            f'<w:color w:val="{DARK}"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
            '<w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
            '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
            '<w:style w:type="character" w:default="1" w:styleId="DefaultParagraphFont"><w:name w:val="Default Paragraph Font"/><w:uiPriority w:val="1"/><w:semiHidden/></w:style>'
            '<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:semiHidden/>'
            '<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/>'
            '<w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>'
            '<w:style w:type="numbering" w:default="1" w:styleId="NoList"><w:name w:val="No List"/><w:semiHidden/></w:style>'
            + heading(1, 32, 240, 240, DARK) + heading(2, 26, 200, 160, primary) + heading(3, 23, 160, 120, DARK) +
            '<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/>'
            '<w:pPr><w:spacing w:after="120"/></w:pPr><w:rPr><w:b/><w:sz w:val="72"/><w:szCs w:val="72"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="ListParagraph"><w:name w:val="List Paragraph"/><w:basedOn w:val="Normal"/>'
            '<w:uiPriority w:val="34"/><w:qFormat/><w:pPr><w:ind w:left="720"/><w:contextualSpacing/></w:pPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="TOCHeading"><w:name w:val="TOC Heading"/><w:basedOn w:val="Heading1"/>'
            '<w:next w:val="Normal"/><w:uiPriority w:val="39"/><w:pPr><w:outlineLvl w:val="9"/></w:pPr></w:style>'
            + toc(1, 0) + toc(2, 220) + toc(3, 440) +
            '<w:style w:type="paragraph" w:styleId="Header"><w:name w:val="header"/><w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:spacing w:after="0"/></w:pPr><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="18"/></w:rPr></w:style>'
            '<w:style w:type="paragraph" w:styleId="Footer"><w:name w:val="footer"/><w:basedOn w:val="Normal"/>'
            f'<w:pPr><w:spacing w:after="0"/></w:pPr><w:rPr><w:color w:val="{GRAY}"/><w:sz w:val="18"/></w:rPr></w:style>'
            '<w:style w:type="character" w:styleId="Hyperlink"><w:name w:val="Hyperlink"/><w:uiPriority w:val="99"/>'
            '<w:rPr><w:color w:val="2563EB"/><w:u w:val="single"/></w:rPr></w:style>'
            '</w:styles>')


def numbering():
    bullet = ('<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="hybridMultilevel"/>'
              '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
              '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri"/></w:rPr></w:lvl>'
              '</w:abstractNum>')
    letters = ('<w:abstractNum w:abstractNumId="1"><w:multiLevelType w:val="hybridMultilevel"/>'
               '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="lowerLetter"/><w:lvlText w:val="%1)"/><w:lvlJc w:val="left"/>'
               '<w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:numbering {W}>{bullet}{letters}'
            '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num><w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>'
            '</w:numbering>')


def p(text, ppr='', rpr=''):
    run = f'<w:r>{"<w:rPr>" + rpr + "</w:rPr>" if rpr else ""}<w:t xml:space="preserve">{text}</w:t></w:r>' if text else ''
    return f'<w:p>{"<w:pPr>" + ppr + "</w:pPr>" if ppr else ""}{run}</w:p>'


PAGE_BREAK = '<w:p><w:r><w:br w:type="page"/></w:r></w:p>'


def header(text_width):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:hdr {W}><w:p><w:pPr><w:pStyle w:val="Header"/>'
            '<w:pBdr><w:bottom w:val="single" w:sz="4" w:space="4" w:color="D1D5DB"/></w:pBdr><w:jc w:val="right"/></w:pPr>'
            '<w:r><w:t xml:space="preserve">{{APP}} · {{ROLE}}</w:t></w:r></w:p></w:hdr>')


def footer(text_width):
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:ftr {W}><w:p><w:pPr><w:pStyle w:val="Footer"/><w:tabs><w:tab w:val="right" w:pos="{text_width}"/></w:tabs></w:pPr>'
            '<w:r><w:t xml:space="preserve">{{ORGANIZATION}}</w:t></w:r><w:r><w:tab/></w:r>'
            '<w:fldSimple w:instr=" PAGE "><w:r><w:t>2</w:t></w:r></w:fldSimple></w:p></w:ftr>')


def document(accent, page_w, page_h, margin):
    text_width = page_w - 2 * margin
    cover = (
        p('', '<w:spacing w:before="3400" w:after="0"/>') +
        p('{{TITLE}}', '<w:spacing w:after="120"/>',
          f'<w:b/><w:caps/><w:color w:val="{accent}"/><w:spacing w:val="20"/><w:sz w:val="28"/>') +
        p('{{APP}}', '<w:pStyle w:val="Title"/>') +
        p('', f'<w:pBdr><w:bottom w:val="single" w:sz="24" w:space="1" w:color="{accent}"/></w:pBdr><w:spacing w:after="360"/>') +
        p('{{ROLE}}', '<w:spacing w:after="2600"/>', f'<w:color w:val="{GRAY}"/><w:sz w:val="36"/>') +
        p('{{ORGANIZATION}}', '<w:spacing w:after="60"/>', '<w:b/><w:sz w:val="24"/>') +
        p('{{DATE}}', '', f'<w:color w:val="{GRAY}"/><w:sz w:val="24"/>') +
        PAGE_BREAK)
    h1_line = f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="1" w:color="{accent}"/></w:pBdr>'
    preface = (p('{{PREFACE_TITLE}}', f'<w:pStyle w:val="Heading1"/>{h1_line}') +
               p('{{PREFACE}}') + PAGE_BREAK)
    toc = (p('{{CONTENTS_TITLE}}', f'<w:pStyle w:val="TOCHeading"/>{h1_line}') +
           '<w:sdt><w:sdtPr><w:docPartObj><w:docPartGallery w:val="Table of Contents"/><w:docPartUnique/></w:docPartObj></w:sdtPr>'
           '<w:sdtContent><w:p><w:pPr><w:pStyle w:val="TOC1"/></w:pPr>'
           '<w:r><w:fldChar w:fldCharType="begin" w:dirty="true"/></w:r>'
           '<w:r><w:instrText xml:space="preserve"> TOC \\o "1-2" \\h \\z \\u </w:instrText></w:r>'
           '<w:r><w:fldChar w:fldCharType="separate"/></w:r>'
           '<w:r><w:t>Right-click here and choose Update Field to build the table of contents.</w:t></w:r>'
           '<w:r><w:fldChar w:fldCharType="end"/></w:r></w:p></w:sdtContent></w:sdt>' + PAGE_BREAK)

    def note(text):
        return p(text, f'<w:pBdr><w:left w:val="single" w:sz="24" w:space="8" w:color="{accent}"/></w:pBdr>'
                       '<w:shd w:val="clear" w:color="auto" w:fill="F3F4F6"/><w:ind w:left="170" w:right="170"/>')

    def item(text, num):
        return p(text, f'<w:pStyle w:val="ListParagraph"/><w:numPr><w:ilvl w:val="0"/><w:numId w:val="{num}"/></w:numPr>')

    sample = (
        p('{{CONTENT}}', '', '<w:b/><w:color w:val="DC2626"/>') +
        note('Everything from the red marker above to the end of the document is replaced by the generated manual. '
             'What follows only shows the format. Keep the {{...}} markers and the built-in style names.') +
        p('1. Section title (Heading 1)', f'<w:pStyle w:val="Heading1"/>{h1_line}') +
        p('1.1 Subsection (Heading 2)', '<w:pStyle w:val="Heading2"/>') +
        p('Body text. Button and menu names are written in bold, exactly as they appear on screen.') +
        item('A bullet with something this role can do.', 1) + item('Another bullet.', 1) +
        item('Click New.', 2) + item('Fill in the form.', 2) + item('Click Save.', 2) +
        note('Important: a highlighted note for restrictions and warnings.'))
    sect = (f'<w:sectPr><w:headerReference w:type="default" r:id="rId5"/><w:footerReference w:type="default" r:id="rId6"/>'
            f'<w:pgSz w:w="{page_w}" w:h="{page_h}"/>'
            f'<w:pgMar w:top="{margin}" w:right="{margin}" w:bottom="{margin}" w:left="{margin}" w:header="708" w:footer="708" w:gutter="0"/>'
            '<w:titlePg/></w:sectPr>')
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            f'<w:document {W}><w:body>{cover}{preface}{toc}{sample}{sect}</w:body></w:document>'), text_width


def build(out, primary, accent, letter):
    page_w, page_h = (12240, 15840) if letter else (11906, 16838)
    margin = 1418                                  # 2.5 cm
    doc, text_width = document(accent, page_w, page_h, margin)
    parts = {
        '[Content_Types].xml': content_types(),
        '_rels/.rels': root_rels(),
        'docProps/core.xml': core(),
        'docProps/app.xml': app(),
        'word/document.xml': doc,
        'word/_rels/document.xml.rels': document_rels(),
        'word/styles.xml': styles(primary).replace('w:pos="9060"', f'w:pos="{text_width}"'),
        'word/numbering.xml': numbering(),
        'word/settings.xml': settings(),
        'word/theme/theme1.xml': theme(primary, accent),
        'word/header1.xml': header(text_width),
        'word/footer1.xml': footer(text_width),
    }
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, data in parts.items():
            z.writestr(name, data.encode('utf-8'))
    print('template: ' + os.path.abspath(out))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('output', nargs='?', default=DEFAULT_OUT)
    ap.add_argument('--primary', default='1F3A5F', help='table headers (hex, no #)')
    ap.add_argument('--accent', default='2563EB', help='title lines and note bars (hex, no #)')
    ap.add_argument('--letter', action='store_true', help='US Letter instead of A4')
    a = ap.parse_args()
    build(a.output, a.primary.lstrip('#').upper(), a.accent.lstrip('#').upper(), a.letter)
