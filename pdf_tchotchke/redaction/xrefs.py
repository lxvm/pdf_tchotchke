#!/usr/bin/env python3

# xrefs.py
# Author: Lorenzo Van Muñoz
# Last Updated Feb 13, 2021

import re

from .patterns import *
from .parser import *
from .dobjects import *
from .iobjects import *

### Xref Classes

class pdf_xrefs(pdf_matches):
    '''
    A class for extracting information from a collection of xrefs
    Is initialized from a re.finditer object
    This is tricky because not only could there be multiple xref sections, 
    but we also want to track the startxref block, so see the re P['xrefs']
    '''
    def __init__(self, iterator, origin):
        xrefs = list(iterator)
        try:
            assert len(xrefs)==1
        except AssertionError:
            raise AssertionError('bad pdf? more than one startxref in document')
        self.match= xrefs[0] # this is a match object
        self.where = self.match.group(2)
        super().__init__(pdf_match(self.match, origin).finditer(P['xref']), origin, pdf_xref)
        

    def xrefs(self):
        return self.els

    def trailer(self):
        return list(self.xrefs())[-1].trailer()

class pdf_xref(pdf_match):
    '''
    A class to represent a single xref
    Initialized from a re.match object
    '''
    def trailer(self):
        return pdf_dict(next(self.find('dicts')), origin=self)

    def blocks(self):
        return (pdf_xblock(x, origin=self) for x in self.finditer(P['xblock']))

class pdf_xblock(pdf_match):
    '''
    A class to represent a block within an xref
    Initialized from a re.match object
    '''
    def start(self):
        return int(self.match.group(1))

    def len(self):
        return int(self.match.group(2))
    
    def items(self):
        return (pdf_xitem(x, origin=self) for x in P['xitem'].finditer(self.match.group(3)))
        
class pdf_xitem(pdf_match):
    '''
    A class to represent a single entry in an xref block
    Initialized from a re.match object
    '''
    def offset(self):
        return int(self.match.group(1))

    def gen(self):
        return int(self.match.group(2))

    def state(self):
        return self.match.group(3)

