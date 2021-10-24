# PDF Bookmarking
Why? To make navigating pdf textbooks as easy as real ones.

## Summary
- `interleaving.py`: A python script for interleaving/alternating lines matching certain TOC patterns. It will run if on `PATH`.
- `bkmk.py`: A python script for converting a TOC into a bookmarks file for one of several command-line utilities. It will run if on `PATH`.

Though the code is documented with docstrings, this README is the main documentation.
See the examples directory for some examples of how the output of these modules.

## Basic Usage

```
$ bkmk -h
usage: bkmk [-h] [-o OUTPUT] {convert,create,import} ... {cpdf,gs,pdftk} input

a script to produce pdf bookmarks

positional arguments:
  {convert,create,import}
                        action!
    convert             change a bookmark file syntax or renumber the pages
    create              create bookmarks from a raw TOC file
    import              read in a pdf to get a rough TOC that will need
                        inspection
  {cpdf,gs,pdftk}       choose bookmark output format
  input                 input file name

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT             output file name
```

## Depends

The outputs of this program would be useless without a pdf editing utility that takes the bookmarks this produces and incorporates them into a pdf document.
The author recommends any of `cpdf`, `Ghostscript`, and `PDFtk` (more details below).
In addition, in order to not have to type many bookmark entries yourself, the author recommends the `pdftotext` tool in [`poppler-utils`](https://poppler.freedesktop.org/) to do some of the hard work.
Writing this code also depended on an effort of several days.
I hope that the code is easy to read, use, and is as stable as a rock.
And feel free to let me know what you think about it or if you'd like to change it

## Supports

`bkmk.py` supports the cpdf, Ghostscript/pdfmarks, and PDFtk bookmark formats.
These have all been tested and reproduce the same bookmark tree in any pdf reader (sample outputs included in the repository).
In addition you can correctly convert one syntax to any other (due to the magic of the `bkmk.repairIndex()` function).
If you should run into format issues, have a go at fixing their defining regular expressions in the `BKMK_SYNTAX` dictionary in `bkmk.py`.

Where to obtain any of the pdf utilities:
- [`cpdf`](https://github.com/coherentgraphics/cpdf-binaries) has binaries available on Github and documentation [here](https://www.coherentpdf.com/cpdfmanual/cpdfmanual.html). I use this utility because of it is easy to learn, convenient to use, and well-documented.
- [`Ghostscript`](https://www.ghostscript.com/), which uses [pdfmark](https://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/pdfmarkreference.pdf), a pdf markup language, is capable of very high quality pdf work and tries to conform closely to Adobe's pdf standards.
- [`PDFtk`](https://www.pdflabs.com/tools/pdftk-server/) has a command line version which can be built from source on the preceeding link. It may also be available (and more or less guaranteed to work, unlike trying to build from source) from your package manager. For instance, in Debian this utility is available as the `pdftk-java` package.

Note these libraries are capable of many more things than bookmarks. 
I only have a need for quickly converting tables of contents to pdf bookmarks but have a look at those libraries to get an idea of what they can do because they might be useful to you.
It must also be said that these scripts aren't useful beyond generating bookmarks -- the maker of the pdf still has to load the bookmarks into the pdf file as described in the [commands](#commands). 
Also, these utilities are all free software for personal uses, though generally not commerical ones.

## Long Description

When creating bookmarks for a pdf text book, it is nice not to have to type everything yourself.
Hopefully this manual outlines the process effectively.

The most manual and straightforward option is to simply type up the TOC yourself, though `bkmk.py` automates the formatting and adds regular expression capabilities.
Using the [`cpdf`](https://github.com/coherentgraphics/cpdf-binaries) utility the bookmark file format is quite straight forwards.
The cpdf syntax for each line is
```
<index> "<text>" <page number> "[<page number></view command>]"
```
Where each line represents a bookmark entry (and the syntax varies for the other formats).

The `<index>` should be an integer representing the depth of the bookmark entry in the index.
The value of this integer depends on the format which encodes the depth of each entry in the TOC.
For example, in `cpdf` all the beginnings of chapters may have index 0, their sections index 1, subsections index 2.
If the index goes beyond 2 you are probably dealing with a very large and detailed document!
It is best to reproduce the original structure of the TOC though, so if index larger than 2 is required then use it.

The `"<text>"` entry contains the text describing the bookmark entry.
It is often the title of the chapter or the name of the section.
For `cpdf`, quotations surrounding the text are required.

The `<page number>` is the page number in the pdf at which the entry appears.
This is typically offset by a certain integer from the page numbers appearing in the TOC.
For example, if page 1 in the TOC is page 15 in the pdf, then 14 must be added to each page number from the TOC.
It is often most convenient to automate this step.

The `"[<page number></view command>]"` is optional and it lets you specify at what position on the page the entry in various ways.
A description of the anatomy of this command is [here](https://thechriskent.com/2017/04/12/adding-bookmarks-to-pdf-documents-with-pdfmark/).

The automation of pdf bookmark generation from a TOC is made easy by this script as soon as you have the text of the TOC.
How you get that depends on the following cases:
- The document was scanned, but without text identification, so the pdf is just a series of images
- The document was scanned with text identification
- The document was generated as a pdf (such as with LaTeX) and this is the best case scenario

In the first case you could just type the table of contents, but people have made optical-character recognition software (OCR) to do this.
Applying programs such as [`tesseract`](https://github.com/tesseract-ocr/tesseract), or derived utilities such as [`pdfsandwich`](https://sourceforge.net/projects/pdfsandwich/), will take you from the first to the second case.

If the document was scanned with text identification, you can copy and paste the text into a file you will process.
Additionally, libraries such as `poppler-utils` have tools such as `pdftotext` which could get the text for you.
However, the logical structure of the TOC is may be scrambled in the output of these programs, which is what `interleave.py` was created for.
For instance it may read the TOC by columns instead of by rows, which `interleave.py` corrects.

If the document was generated as a pdf you can always copy and paste or use `pdftotext`.

The next stage is to prepare that text for a script that will rewrite it into the syntax described above.
One should run spellcheck on the copied text because text identification software often makes mistakes even if the quality of the scanned pdf is good.
Often, in the case of Mathematical textbooks there will be misread mathematical symbols (e.g. Infinity appears as "00") that you can fix.
However you group your entries for the bookmarks, make sure that you can identify the text and page number using a regular expression.
`bkmk.py` uses a flag `-p, --pattern` that reads in the entries using this regexp to make this process as flexible as possible.
See the module documentation and source code for details.

Now we can run that file through bkmk.py and use the output.
Some elements of the output will have to be reviewed by hand such as entries with roman numerals (e.g. preface) or covers that weren't in the original TOC to begin with.

## Commands

### Getting bookmark data from a pdf

- `cpdf -list-bookmarks in.pdf > bkmk.txt`
- `pdftk in.pdf dump_data output bkmk.txt`
- With `gs` I don't know how to extract pdfmarks. For ideas see [this](https://github.com/trueroad/extractpdfmark)
- `mutool show in.pdf outline > bkmk.txt`

### Writing bookmark data to a pdf

- `cpdf -add-bookmarks bkmk.txt in.pdf -o out.pdf`
- `pdftk in.pdf update_info bkmk.txt output out.pdf`
- `gs -dBATCH -dNOPAUSE -sDEVICE=pdfwrite -sOutputFile=out.pdf in*.pdf bkmk.txt`
- pretty sure this can be done with `mutool run ...` by invoking `Document#set_toc`.
See [issue with example in PyMuPDF](https://github.com/pymupdf/PyMuPDF/issues/213).

## Tips

It is nice not to type a table of contents for every textbook, yet it is still an arduous process to get all the facts right about the document.
I have been thrown off by unique quirks of several books, including:

- The main TOC of the book only lists the chapters, but then a separate TOC for items in each chapter is printed at the start of each chapter.
- The publisher of the pdf kindly removes all the blank pages from the pdf, causing the TOC page numbers in the front of the book to be offset from their actual locations in the text.

Usually these quirks have to be corrected by hand before passing the TOC to `bkmk.py` where it can be parsed using regular expressions.
This processing, though by hand, is systematic and benefits from regular expressions, search and replace, and some basic arithmetic.
A text editor can help you with these tasks, and a capable one is Vim.
Here are some commonly used tips that are a helpful step for automating repetitive tasks

- When getting the TOC from the pdf using `pdftotext`, use the `-layout` flag to save time by retaining the visual structure of the TOC
- In Vim, marking the page numbers at the ends of lines (for parsing with `bkmk.py`) and offsetting their numbers at the same time can be done with `:%s/\(\d\+\)$/\='@'.(submatch(1)+20)/g`.
- In Vim, one can create subsection numberings, or continue them (since sometimes the textbook's lessons are numbered but the exercises aren't), and here is an example: `:%s/^\(\d\+\.\)\(\d\+\)\(.\+\n\)\(Exercises.\+\n\)/\=submatch(1).submatch(2).submatch(3).submatch(1).(str2nr(submatch(2))+1).' '.submatch(4)/g`

## Extra

For completeness, some other open source command line pdf tools include [`mupdf`](https://www.mupdf.com/) and [`qpdf`](http://qpdf.sourceforge.net/).
They may be useful for additional tasks.

For a general discussion of pdf bookmarks, see [this](https://superuser.com/questions/276311/how-to-import-export-and-edit-bookmarks-of-a-pdf-file).

Others have done [similar work](https://github.com/goerz/bmconverter.py) that is a different implementation using classes.
In addition, see [`booky`](https://github.com/SiddharthPant/booky/blob/master/booky.py).

Text extraction from pdfs is a difficult task which others have done already.
[PDFBox](https://pdfbox.apache.org/index.html), written in Java, can do all of these [things](https://www.tutorialkart.com/apache-pdfbox-tutorial/).
The [Text Extraction Toolkit (TET)](https://www.pdflib.com/products/tet/) is an expensive software, but is apparently very good at its task.

