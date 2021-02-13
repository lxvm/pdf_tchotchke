# Redaction

Redaction is removing text in a document.

## Summary

- `whiteout.py`: a tool that replaces text in any document type with spaces (for pdfs, for sure, otherwise maybe). 
- `whiteout_re.py`: a tool that replaces text in pdfs with spaces (for sure)
- `redact.py`: a tool to search for and remove particular pdf objects. (Unfinished)
- `editor.py`: classes to parse pdfs into their parts. (in progress)
- `prepare.py` : a shell script to automate redaction

To use these scripts, install the dependencies of [`pdftotext`](https://github.com/jalan/pdftotext).

There are other similar python tools: [`pdf-redactor`](https://github.com/JoshData/pdf-redactor).

There are plenty of people who want [this ability](https://stackoverflow.com/questions/52346942/how-to-replace-delete-text-from-a-pdf-using-python/57483809) but the efficiency of various implementations is questionable.
