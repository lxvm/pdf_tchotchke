#!/usr/bin/env python3

# redact.py
# Author: Lorenzo Van Muñoz
# Last Updated Jan 3, 2020

'''
This script redacts pdfs via removing objects one at a time.
The approach in this script is object-oriented and tries
to modify the pdf file directly by 1, deleting an object, 2 
deleting all references to that (indirect) object, 3 update 
all other object numbers and corresponding reference, and 4
reconstruct the xref table for the new pdf. An attempt will
also be made to remove watermarks with the tools herein. 
The representation of the pdf in terms of classes simply serves
for convenience while rewriting the pdf.
'''

import logging
import argparse 

from pdf_tchotchke.utils import filenames
from pdf_tchotchke.redaction.editor import *

# Define Global variables    
PDF_OBJ_TYPES = {
        # list all pdf direct object types
        # in the pdf 1.7 reference, section 3

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
    by or that reference to the given ones
    '''
    pass


# Command-line interface with shell and parsers

def cli_object_handler(args):
    '''
    deletes a specific 
    '''
    pass


def cli_search_handler(args):
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

    parser = argparse.ArgumentParser(   
            prog='redact',
            description='''A script to remove objects in a pdf''')
  
    subparsers = parser.add_subparsers(help='redaction method')
   
    # Setup the delete object command
    parser_object = subparsers.add_parser(  
            'objects',   
            help = 'delete indirect objects from pdf by their reference number'   
                    '. This is useful for debugging.')
    parser_object.set_defaults( 
            func=cli_object_handler)
    parser_object.add_argument( 
            '-o', '--object',   
            type=int, action='append',  
            help = 'a list of numbers corresponding to objects to delete')

    # Setup the delete search command
    parser_search = subparsers.add_parser(  
            'search', 
            help = 'delete all objects containing a particular search pattern')
    parser_search.set_defaults( 
            func=cli_search_handler)
    # search args
    parser_search.add_argument( 
            'patterns', 
            help = 'path to a text file with lines to search and remove')
    parser_search.add_argument( 
            '-f', '--formats',  
            choices=list(PDF_STR_ENCODINGS.keys()), default=['c'],  
            help = 'try deleting objects containing pattern as literal string ' 
                    '(\'c\') or hexadecimal(\'x\',\'X\')')
    parser_search.add_argument( 
            '-F', '--all-formats',  
            dest='formats', action='store_const',   
            const=list(PDF_STR_ENCODINGS.keys()),
            help = 'tries all string encodings, overriding --format')
    parser_search.add_argument( 
            '-t', '--types',    
            choices=list(PDF_OBJ_TYPES.keys()), default=['stream'],    
            action='append', nargs='+', 
            help = 'if the search patterns appears as text on the pdf canvas, '
                    'try deleting the specified types of objects and testing '  
                    'if they delete the desired text using an external module.'
                    '\nRequires: (?pdftotext) TBD')
    parser_search.add_argument( 
            '-T', '--all-types',    
            dest='types', action='store_const', 
            const=list(PDF_OBJ_TYPES.keys()),   
            help = 'tries all pdf object types, overriding --types')
   
    # Main arguments
    #parser.add_argument(    
    #        '-r', '--recursive-depth', 
    #        help = 'TODO - specifies whether the removed object   
    #                should delete its parents or children as well')
    parser.add_argument(   
            'options',   
            choices=['delete','info'],
            help = 'red\'actions\'')
    parser.add_argument(    
            '-v', dest='verbosity', 
            action='count', default = 0,  
            help = 'Verbosity, up to 4 levels by repeating v: '
                    'ERROR=1, WARN=2, INFO=3, DEBUG=4')
    parser.add_argument(    
            'input', 
            help = 'enter the name or path of a pdf')
    parser.add_argument(    
            '-o', dest='output', 
            help = 'enter the name or path of pdf to write to')
    
    args = parser.parse_args()
    
    args = filenames.getSafeArgsOutput(args, ext='.pdf', 
                                    overwrite=False, mode='wb')

    # under development: check types in those being implemented
    if args.func == cli_delete_pdf_search:
        for e in args.types:
            assert e in ['stream','dict']

    #print(args)
    logging.basicConfig(level=LOG_LEVELS[args.verbosity])
    logger = logging.getLogger('redact')
    args.func(args)

    args.input.close()
    args.output.close()

    return


if __name__ == '__main__':
    cli()
    raise SystemExit()
