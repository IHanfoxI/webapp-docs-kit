#!/usr/bin/env python3
"""
to_pdf.py — refreshes the .docx table of contents and exports the PDF.

Usage:
    python3 to_pdf.py manual.docx [--title "..."] [--author "..."] [--engine auto|libreoffice|word]

Leaves manual.docx (with the table of contents recomputed) and manual.pdf next to it.
`soffice --convert-to pdf` is not enough: it does not refresh the table of contents, so
the PDF would show the template's page numbers.

Engines:
- libreoffice (default when installed): drives LibreOffice through UNO. Needs the `uno`
  module, which only some Pythons ship: on Linux the system one (/usr/bin/python3 +
  python3-uno), on Windows and macOS the one bundled with LibreOffice. If this script
  runs under another Python it relaunches itself with that one.
- word (Windows only): drives Microsoft Word through COM via PowerShell. Used when
  LibreOffice is not installed.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile

WINDOWS = os.name == 'nt'
MAC = sys.platform == 'darwin'
LO_DIRS_WINDOWS = [os.path.join(os.environ.get(v, ''), 'LibreOffice', 'program')
                   for v in ('ProgramFiles', 'ProgramFiles(x86)') if os.environ.get(v)]
LO_MAC = '/Applications/LibreOffice.app/Contents'


def python_with_uno():
    if WINDOWS:
        candidates = [os.path.join(d, 'python.exe') for d in LO_DIRS_WINDOWS]
    elif MAC:
        candidates = [os.path.join(LO_MAC, 'Resources', 'python')]
    else:
        candidates = ['/usr/bin/python3', *glob.glob('/opt/libreoffice*/program/python')]
    return next((c for c in candidates if os.path.exists(c)), None)


def soffice():
    found = shutil.which('soffice')
    if found:
        return found
    candidates = [os.path.join(d, 'soffice.exe') for d in LO_DIRS_WINDOWS] + [os.path.join(LO_MAC, 'MacOS', 'soffice')]
    return next((c for c in candidates if os.path.exists(c)), None)


def with_word(docx, pdf, title, author):
    """Updates fields and the TOC in Microsoft Word and exports the PDF (Windows)."""
    ps = r'''
$ErrorActionPreference = 'Stop'
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
try {
    $doc = $word.Documents.Open($env:WDK_DOCX, $false, $false)
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    $doc.Fields.Update() | Out-Null
    foreach ($t in $doc.TablesOfContents) { $t.Update() }
    # Document properties are late-bound COM objects: PowerShell needs InvokeMember.
    $props = $doc.BuiltInDocumentProperties
    foreach ($kv in @(@('Title', $env:WDK_TITLE), @('Author', $env:WDK_AUTHOR))) {
        if ($kv[1]) {
            $p = [System.__ComObject].InvokeMember('Item', 'GetProperty', $null, $props, @($kv[0]))
            [System.__ComObject].InvokeMember('Value', 'SetProperty', $null, $p, @($kv[1])) | Out-Null
        }
    }
    $doc.Save()
    # SaveAs2 as wdFormatPDF (17) keeps the document properties; ExportAsFixedFormat drops them.
    $doc.SaveAs2([ref]$env:WDK_PDF, [ref]17)
} finally {
    # wdDoNotSaveChanges. Never leave a hidden Word holding the file.
    try { $word.Quit([ref]0) } catch { }
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
'''
    env = {**os.environ, 'WDK_DOCX': docx, 'WDK_PDF': pdf, 'WDK_TITLE': title, 'WDK_AUTHOR': author}
    code = subprocess.call(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps], env=env)
    if code:
        sys.exit('Error: Microsoft Word could not export the PDF.')


def with_libreoffice(docx, pdf, title, author):
    try:
        import uno
        from com.sun.star.beans import PropertyValue
    except ImportError:
        other = python_with_uno()
        if other and not os.environ.get('WDK_RELAUNCHED'):   # only once: no loops
            sys.exit(subprocess.call([other, os.path.abspath(__file__), docx, '--title', title, '--author', author,
                                      '--engine', 'libreoffice'], env={**os.environ, 'WDK_RELAUNCHED': '1'}))
        sys.exit('Error: the uno module is missing. Linux: sudo apt install python3-uno. Windows/macOS: install LibreOffice.')

    def prop(name, value):
        p = PropertyValue()
        p.Name, p.Value = name, value
        return p

    profile = tempfile.mkdtemp(prefix='lo-manual-')
    port = 2002 + os.getpid() % 1000
    # Own profile: does not clash with a LibreOffice the user already has open.
    proc = subprocess.Popen([soffice(), '--headless', '--invisible', '--nologo', '--norestore',
                             '-env:UserInstallation=' + uno.systemPathToFileUrl(profile),
                             f'--accept=socket,host=127.0.0.1,port={port};urp;'],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    desktop = None
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
        ctx = None
        for _ in range(60):
            try:
                ctx = resolver.resolve(f'uno:socket,host=127.0.0.1,port={port};urp;StarOffice.ComponentContext')
                break
            except Exception:
                time.sleep(0.5)
        if ctx is None:
            sys.exit('Error: LibreOffice did not respond')
        desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
        doc = desktop.loadComponentFromURL(uno.systemPathToFileUrl(docx), '_blank', 0, (prop('Hidden', True),))
        indexes = doc.getDocumentIndexes()
        for i in range(indexes.getCount()):
            indexes.getByIndex(i).update()
        doc.refresh()
        props = doc.getDocumentProperties()
        if title:
            props.Title = title
        if author:
            props.Author = author
        doc.storeToURL(uno.systemPathToFileUrl(docx), (prop('FilterName', 'MS Word 2007 XML'),))
        doc.storeToURL(uno.systemPathToFileUrl(pdf), (prop('FilterName', 'writer_pdf_Export'),))
        doc.close(True)
    finally:
        try:
            desktop.terminate()
        except Exception:
            pass
        try:
            proc.wait(timeout=20)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


def scrub(docx):
    """Removes "last modified by": Word and LibreOffice fill it with the local user's name."""
    with zipfile.ZipFile(docx) as z:
        files = {n: z.read(n) for n in z.namelist()}
    core = files.get('docProps/core.xml', b'').decode('utf-8')
    clean = re.sub(r'<cp:lastModifiedBy>.*?</cp:lastModifiedBy>|<cp:lastModifiedBy/>', '', core, flags=re.S)
    if clean == core:
        return
    files['docProps/core.xml'] = clean.encode('utf-8')
    with zipfile.ZipFile(docx, 'w', zipfile.ZIP_DEFLATED) as z:
        for n, data in files.items():
            z.writestr(n, data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('docx')
    ap.add_argument('--title', default='')
    ap.add_argument('--author', default='')
    ap.add_argument('--engine', choices=['auto', 'libreoffice', 'word'], default='auto')
    a = ap.parse_args()

    docx = os.path.abspath(a.docx)
    pdf = os.path.splitext(docx)[0] + '.pdf'
    engine = a.engine
    if engine == 'auto':
        engine = 'libreoffice' if soffice() else 'word' if WINDOWS else None
    if engine is None:
        sys.exit('Error: LibreOffice (soffice) was not found.')
    if engine == 'libreoffice':
        if not soffice():
            sys.exit('Error: LibreOffice (soffice) was not found.')
        with_libreoffice(docx, pdf, a.title, a.author)
    else:
        with_word(docx, pdf, a.title, a.author)
    scrub(docx)
    print('pdf: ' + pdf)


if __name__ == '__main__':
    main()
