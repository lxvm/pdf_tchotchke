#!/usr/bin/env python3

# dobjects.py
# Author: Lorenzo Van Muñoz
# Last Updated Feb 13, 2021

import re

from .patterns import *
from .parser import *

### Direct Object Classes

class pdf_stream(pdf_match):
    '''
    A filler class for streams. If you ever need methods for streams, add here!
    '''
    pass

class pdf_bool(pdf_match):
    '''
    A filler class for bools
    '''
    pass

class pdf_numeric(pdf_match):
    '''
    A filler class for numeric
    '''
    pass

class pdf_null(pdf_match):
    '''
    A filler class for nulls
    '''
    pass

class pdf_name(pdf_match):
    '''
    A filler class for names
    '''
    pass

class pdf_ref(pdf_match):
    '''
    A class to represent pdf references to indirect objects
    Is initialized from a re.match object and a pdf_obj (the origin)
    '''
    def dest(self):
        return self.match.group(1)

class pdf_array(pdf_match):
    '''
    A class for arrays in pdfs
    '''
    def parse(): #lol can't find an easier way to remove delimiters than to slice
        con = re.compile(re.escape(next(self.find('arrays')).group(0))[2:-2])
        return pdf_match(next(self.finditer(con)), self).parse()


class pdf_dict(pdf_match):
    '''
    A class for dictionaries, which have key value pairs
    '''
    def parse(self):
        '''
        Break up a dictionary into key value pairs and evaluate the values into
        the appropriate classes
        '''
        con = re.compile(re.escape(self.text[2:-2]))
        items = pdf_match(next(self.finditer(con)), self).parse().els # pdf_objs
        # sort the items by span
        assert len(items) > 0 and len(items) % 2 == 0
        items = [e for _,e in sorted(zip([i.start() for i in items], items))]
        items = [(a, b) for a, b in zip(items[::2], items[1::2])]
        # assert they are of class : pdf_name ,pdf_obj, ... alternating
        for a, b in items:
            assert type(a)==pdf_name and issubclass(type(b), pdf_obj)
        # return a dictionary 
        return {e[0] : e[1] for e in items}

    def names(self, search=[]):
        '''
        Provide a list of names to search through and return the corresponding entries
        '''
        dct = self.parse()
        #print([e.text for e in dct.keys()])
        insearch = lambda x: any([word in x for word in search])
        return [dct[e] for e in dct if insearch(e.text)]

