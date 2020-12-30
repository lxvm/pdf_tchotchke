# Redaction

Redaction is removing text in a document.

## Summary

- `whiteout.py`: a tool that removes or replaces text in any document type. 
It also has some tools for pdfs, some requiring 
- `redact.py`: a tool to search for and remove particular pdf objects.
- `prepare.py` : a shell script to automate redaction

To use these scripts, install the dependencies of [`pdftotext`](https://github.com/jalan/pdftotext).

There are other similar python tools: [`pdf-redactor`](https://github.com/JoshData/pdf-redactor).

There are plenty of people who want [this ability](https://stackoverflow.com/questions/52346942/how-to-replace-delete-text-from-a-pdf-using-python/57483809) but the efficiency of various implementations is questionable.
