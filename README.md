# PDF Tchotchke

Baubles for pdfs

## Installation

Some of the functions rely on an installation of `pdftotext`, a python package
based on the poppler library.
Though the package will be installed along with this one, `pdftotext` has some
system requirements that you must install with it.
Instructions [here](https://github.com/jalan/pdftotext).

```
# I recommend working in a [venv](https://docs.python.org/3/library/venv.html)
$ git pull https://github.com/lord-zo/pdf_tchotchke.git
$ python3 -m pip install [-e] pdf_tchotchke
```

## Summary

The main contents of this package are the following command-line scripts:
- `bkmk`: a script that formats bookmarks for pdfs
- `interleave`: a helper script for `bkmk`
- `whiteout`: a script that whites-out specific text objects
- `whiteout_re`: a refactoring of `whiteout`, but specific to pdfs
- `redact`: a script that deletes objects from pdfs
- `prepare`: a script to automate redaction
These should be available on `$PATH` as soon as you do the install.

The package also contains `editor.py`, a set of classes to parse a pdf.
The [pdfminer](https://github.com/pdfminer/pdfminer.six) package probably does 
this much better.
Or [pikepdf](https://github.com/pikepdf/pikepdf), another pdf editing library.

However, the [PyMuPDF](https://github.com/pymupdf/PyMuPDF) project will
outperform everything else because `MuPDF` is written in C and
is capable of doing any common pdf task.

As you can probably tell, these packages served the purpose of teaching me 
about programming and there are more developed and professional tools elsewhere.

For more details, see the README's herein.
