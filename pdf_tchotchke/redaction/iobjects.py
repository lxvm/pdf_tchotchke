#!/usr/bin/env python3

# iobjects.py
# Author: Lorenzo Van Muñoz
# Last Updated Feb 13, 2021

import re

from .patterns import *
from .parser import *
from .dobjects import *

### Indirect Object Classes

class pdf_iobjs(pdf_matches):
    '''
    A base class for a collection of pdf indirect objects
    Is initialized from a re.match object
    '''
    def __init__(self, iterator, origin):
        super().__init__(iterator, origin, pdf_iobj)

    def iobjs(self, nums=None):
        if nums==None:
            return self.els
        else:
            assert type(nums) == list
            return (iobj for iobj in self.els if iobj.num() in nums)

    def search_objs(self, pattern):
        '''
        Finds all indirect objects containing the search patterns and returns a
        pdf_iobjs object containing them
        #TODO the problem is that a pdf_iobjs object can only be instantiated 
        from a single re.match object whereas this search may create several
        '''
        return pdf_iobjs((iobj for iobj in self.matches if iobj.search(pattern)), self.origin)
        #matched_objs_text = \
        #    b''.join([e.text for e in self.iobjs if e.search(pattern, repl)])
        #return pdf_iobjs(P['iobjs'].search(matched_objs_text), origin=self.origin)
        #
    # other ideas for methods:
    # get references info
    # get unused objs
    # remove objs
    # insert objs

class pdf_iobj(pdf_match):
    '''
    A base class for a pdf indirect object
    Is initialized from a re.match object
    '''
    def num(self):
        return self.match.group(1)
    
    def gen(self):
        return self.match.group(2)

    def contents(self):
        return self.match.group(3)
        
    def refs(self):
        return (pdf_ref(x, origin=self) for x in P['ref'].finditer(self.text))

    def parse(self):
        '''
        Break up the object's contents into a pdf_matches object.
        Takes in the contents of a pdf_obj object excluding the obj/endobj keywords
        '''
        con = re.compile(re.escape(self.contents()))
        return pdf_match(next(self.finditer(con)), self).parse()

    def dict(self):
        '''
        finds a returns the dictionaries in an object
        '''
        dicts = [e for e in self.parse().els if type(e)==pdf_dict]
        if len(dicts) == 1:
            return dicts[0]
        elif len(dicts) >= 1:
            return dicts
        else:
            return None
    
