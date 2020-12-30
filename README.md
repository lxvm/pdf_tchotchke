# misc

A script is worth a thousand functions

## PDF Tchotchke

Baubles for pdfs

### Installation

```
$ git pull https://github.com/lord-zo/misc.git
$ cd misc/pdf_tchotchke
$ python3 -m pip install --user .
```

`pip` installs the scripts from this package in `$HOME/.local/bin`.
Alternatively, use a [`venv`](https://docs.python.org/3/library/venv.html).
Either way, check that the `bin` folder installation directory is on your `PATH`.
This will make the scripts available to run from the command line.

Some of the functions rely on an installation of `pdftotext`.
This is a package from `poppler-utils`, available through most package managers.

This package has only been tested on Debian.

### Summary

The main contents of this package are the following command-line scripts:
- `bkmk`: a script that formats bookmarks for pdfs
- `interleave`: a helper script for `bkmk`
- `whiteout`: a script that whites-out specific text objects in a pdf
- `redact`: a script that deletes objects from pdfs
- `prepare`: a script to automate redaction

For more details, see the README's herein.
