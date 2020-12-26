#!/usr/bin/env python3

# redact.py
# Author: Lorenzo Van Muñoz
# Last Updated Dec 26, 2020

'''
This script redacts pdfs via removing objects one at a time.
I see that all the other python pdf parsing libraries are 
using the object-oriented approach and I dislike it for my
intended purpose, which is simply to remove objects from the
pdf canvas. The approach in this script is to execute code
to modify the pdf file directly by 1, deleting an object, 2 
deleting all references to that (indirect) object, 3 update 
all other object numbers and corresponding reference, and 4
reconstruct the xref table for the new pdf. An attempt will
also be made to remove watermarks with the tools herein.

---- PDF BASICS ---- 
# From the PDF 1.7 reference
In a compressed or uncompressed pdf, you may notice this:
The highest level constructions in pdf files are indirect
objects and xref tables. Indirect objects contain direct 
objects (with relevant information about how to draw the
page) and a label to that indirect object. Xref tables
collect the information about the labels of each object
and their locations in the file to reference the contents 
of the document. A label to an object looks like 'N M obj'
where N is the number of the object and M is a number 
(typically 0) representing which version of the file that 
object was added in (0 is for original).

You may notice the following in an uncompressed pdf:
Within indirect objects are direct objects which can be
- Boolean Values
- Integer and real numbers
- Strings (literal characters or hexadecimal)
- Names
- Arrays
- Dictionaries
- Streams
- The null object
For example, each page in a page object is represented by
a dictionary. A general property of objects is that they 
are allowed to make references to other objects (these 
look like 'N M R') to include data from other indirect 
objects. For example, each page has a dictionary with an
array of references to other indirect objects, whose
contents are what is actually drawn on the canvas.

If we want to delete an object from a pdf, it is enough to
make that object and all references to it disappears, and 
then to update all other labels and references by renumbering 
them and the xref table.
'''

import re , argparse , filenames , logging , subprocess
# Global variables defined above 'if __name__ = '__main__''
# start with error handling
def assert_conditions_pdf(pdf_file_obj):
    '''
    Makes a variety of assertions about the pdf file
    before allowing it to be read.
    It accepts a file object and reads through it line
    by line, making assertions for each line
    '''

    for line in pdf_file_obj:
        assert_uncompressed_pdf(line)
        # add more assertion statements here
    return

def assert_uncompressed_pdf(pdf_line):
    '''
    Asserts that a byte-string contains no /<some>Decode
    flags. Presumably this would indicate that the pdf 
    has no compression filters and that the file is 
    uncompressed.
    '''
    try:
        # list of standard pdf compression filters from
        # the pdf 1.7 reference, table 3.5
        filters = [ b'FlateDecode', b'ASCIIHexDecode', 
                    b'ASCII85Decode',b'LZWDecode', 
                    b'RunLengthDecode', b'CCITTFaxDecode',
                    b'JBIG2Decode', b'DCTDecode',
                    b'JPXDecode', b'Crypt'
                    ]

        for filter in filters:
            p = re.compile(filter)
            assert not bool(p.search(pdf_line))
    except AssertionError as e:
        raise AssertionError(f'{e}: this script requires an uncompressed pdf')

    return

# start the pdf parsing functions


def delete_pdf_indirect_objects_and_refs(labels,depth=0):
    '''
    this removes the indirect pdf objects in a list by their label.
    This function can optionally recurse and delete objects referenced
    by those in the initial list or those objects which reference those in the list
    '''
    pass

# Command-line interface with shell and parsers
def cli_delete_pdf_indirect_objects(args):
    '''
    deletes a specific 
    '''
    pass


def cli_delete_pdf_search(args):
    '''
    searches through a pdf 
    '''
    pass


def cli():
    '''
    This creates the command-line interface for redact.py. Use
    $ redact.py -h
    for more help.
    '''

    parser = argparse.ArgumentParser(   \
        description='''A script to remove objects in a pdf''')
  
    subparsers = parser.add_subparsers(help = 'removal method')
   
    # Setup the delete object command
    parser_object = subparsers.add_parser(  \
            'objects',   \
            help = 'delete an indirect object from pdf by their reference number.   \
                    This is useful for debugging.')
    parser_object.set_defaults( \
            func=cli_delete_pdf_indirect_objects)
    parser_object.add_argument( \
            '-o','--object', \
            type=int,action='append',   \
            help = 'a list of numbers corresponding to objects to delete')

    # Setup the delete search command
    parser_search = subparsers.add_parser(  \
            'search', \
            help = 'delete all objects containing a particular search pattern')
    parser_search.set_defaults(func=cli_delete_pdf_search)
    # search args
    parser_search.add_argument( \
            'patterns', \
            type=argparse.FileType('rb'), \
            help = 'path to a text file with lines to search and remove')
    parser_search.add_argument( \
            '-f','--formats', \
            choices=list(PDF_STR_ENCODINGS.keys()),default=['c'], \
            help = 'try deleting objects containing pattern as literal string (\'c\') or hexadecimal(\'x\',\'X\')')
    parser_search.add_argument( \
            '-F','--all-formats',    \
            dest='formats',action='store_const', \
            const=list(PDF_STR_ENCODINGS.keys()),\
            help = 'tries all string encodings, overriding --format')
    parser_search.add_argument( \
            '-t','--types',   \
            choices=list(PDF_OBJ_TYPES.keys()), default=['stream'],    \
            action='extend',nargs='+',    \
            help = 'if the search patterns appears as text on the pdf canvas, \
                    try deleting the specified types of objects and testing if  \
                    they delete the desired text using an external module.\n\
                    Requires: (?pdftotext) TBD')
    parser_search.add_argument( \
            '-T','--all-types',  \
            dest='types',action='store_const', \
            const=list(PDF_OBJ_TYPES.keys()),\
            help = 'tries all pdf object types, overriding --types')

    # Main arguments
    #parser.add_argument(    \
    #        '-r','--recursive-depth', \
    #        help = 'TODO - specifies whether the removed object   \
    #                should delete its parents or children as well')
    parser.add_argument(    \
            '-v','--verbose',   \
            dest='verbosity', action='count', default = 0,  \
            help = 'Verbosity, up to 4 levels by repeating v:   \
                    ERROR=1, WARN=2, INFO=3, DEBUG=4')
    parser.add_argument(    \
            'input',    \
            type=argparse.FileType('rb'),   \
            help = 'enter the name or path of a pdf')
    parser.add_argument(    \
            # this is an optional argument, uses input filename if an output not given
            'output',   \
            nargs='?',  \
            help = 'enter the name or path of pdf to write to')
    
    args = parser.parse_args()
    
    # create a safe output file object if a name is given or not
    if args.output == None:
        args.output = open(filenames.fileOut(writefile=args.input.name,ext='.pdf'),'wb')
    else:
        args.output = open(filenames.fileOut(writefile=args.output,ext='.pdf'),'wb')

    # under development: check types in those being implemented
    if args.func == cli_delete_pdf_search:
        for e in args.types:
            assert e in ['stream','dict']

    #print(args)
    logging.basicConfig(level=log_levels[args.verbosity])
    args.func(args)

    return


# Define Global variables    
PDF_STR_ENCODINGS = {
        # Using python's Format Specification mini-language

        # literal string (default): as unicode
        'c' : (lambda s : b''.join(bytes(f'{e:c}','utf-8') for e in s)),
        # Hex uncapitalized
        'x' : (lambda s : b''.join(bytes(f'{e:x}','utf-8') for e in s)), 
        # Hex capitalized
        'X' : (lambda s : b''.join(bytes(f'{e:X}','utf-8') for e in s))
        }

PDF_OBJ_TYPES = {
        # list all pdf direct object types
        # note that this script does not yet 
        # have an implementation to delete 
        # each type

        'stream'    :   'PDF_STREAM',
        'dict'      :   'PDF_DICT',
        'boolean'   :   'PDF_BOOL',
        'number'    :   'PDF_NUM',
        'string'    :   'PDF_STR',
        'name'      :   'PDF_NAME',
        'array'     :   'PDF_ARRAY',
        'null'      :   'PDF_NULL'
        }

LOG_LEVELS = {
        # list the logging verbosity levels from logging module

        0: logging.CRITICAL,
        1: logging.ERROR,
        2: logging.WARN,
        3: logging.INFO,
        4: logging.DEBUG,
        }


if __name__ == '__main__':
    cli()
    raise SystemExit()
