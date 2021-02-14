#!/usr/bin/env python3

# patterns.py
# Author: Lorenzo Van Muñoz
# Last Updated Feb 13, 2021

import re

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

C = {# This is a collection of character types in pdfs

    'ws'    :   b'[\x00\x09\x0A\x0C\x0D\x20]', # white space Referencetable3.1
    # same as   b'[\x00\t\n\x0C\r ]'
    'del'   :   b'[%<>\[\]\{\}\(\)]', # all delimiters
    'sdel'  :   b'[%<\[\{\(]', # comment and delimiter starters
    'edel'  :   b'[>\]\}\)]', # delimiter enders
    'adel'  :   b'[^%<>\[\]\{\}\(\)]', # anything but delimiters
    'reg'   :   b'[^\x00\x09\x0A\x0C\x0D\x20%<>\[\]\{\}\(\)]',# everything else
    'name'  :   b'[^/\x00\x09\x0A\x0C\x0D\x20%<>\[\]\{\}\(\)]',# reg with /
    }

P = {# This is a collection of relevant patterns for parsing pdfs

    # Structural elements
    'pdf_h' :   re.compile(b'%PDF'),
    'pdf_hf':   re.compile(b'^(.+?)(?:\d+ \d+ obj.+endobj\n+)+(?:xref.+)(%%EOF\n*)$', re.DOTALL),
    'iobjs' :   re.compile(b'(\d+ \d+ obj.+?endobj\n+)+', re.DOTALL),
    'iobj'  :   re.compile(b'(\d+) (\d+) obj\n*(.+?)\n*endobj\n+', re.DOTALL),
    'xrefs' :   re.compile(b'(xref.+?)+(startxref.+)', re.DOTALL),
    'xref'  :   re.compile(b'xref\n((?:\d+ \d+ \n(?:\d{10} \d{5} [nf] \n)+)+\n*)(trailer\n+<<.+>>\n+)', re.DOTALL),
    'xblock':   re.compile(b''.join([b'(\d+) (\d+)', C['ws'], 
                                        b'*((?:\d{10} \d{5} [nf] \n)+)'])),
    'xitem' :   re.compile(b'(\d{10}) (\d{5}) ([nf]) \n'),
    # Direct object identifiers
    # for dictionaries and arrays, use the pdf_match.find('dicts'|'arrays')
    # method as it can return an iterator of the highest level matches of
    # potentially nested and sequential groups of these delimiters
    # If you use these regexps there are bound to be errors one way or another
    # If you need to remove the delimiters for either dict or array, on a 
    # string A, then the slice re.escape[2:-2] will remove them
    #'ditems':   re.compile(rb'(/\w+)(/[^/]+|[^/].+[\)\]>]|[^/]+)', re.DOTALL),
    #'dict'  :   re.compile(rb'<<\n*(.+?)\n*>>', re.DOTALL),
    #'array' :   re.compile(b'\[\n*(.+?)\n*\]'),
    'stream':   re.compile(b''.join([b'stream(.+?)endstream', C['ws'], b'+']),
                            re.DOTALL),
    'ref'   :   re.compile(b''.join([b'(\d+) \d+ R', C['ws'], b'*'])),
    'bool'  :   re.compile(b''.join([rb'true|false', C['ws'], b'*'])),
    'name'  :   re.compile(b''.join([b'/', C['name'], b'+'])),
    'null'  :   re.compile(b''.join([b'null', C['ws'], b'*'])),
    'numeric':  re.compile(b''.join([b'[+-]?\d*\.?\d+'])), 
    # optional sign, one or more numerals, at most one decimal point
    # read the reference about what is allowed in strings
    # also exclude the possibility of dictionary
    'string':   re.compile(b''.join([b'(?<!<)[[<]', b'.*?', b'[]>](?!>)', 
                            C['ws'], b'*']))
    }


