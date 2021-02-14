#!/usr/bin/env python3

# parser.p
# Author: Lorenzo Van Muñoz
# Last Updated Feb 13, 2021

'''
It might be a stretch to call this a parser
since it mainly uses regular expressions to dismantle a pdf
'''

import re

from .patterns import *

### Base Classes

class my_match:
    '''
    A mutable representation of Re.Match objects
    Instantiated from an re.Match object plus an offset
    to account for where the string is located in the pdf file
    to do searching more efficiently
    '''
    def __init__(self, match, offset=0):
        self.match = match
        self.string = match.string
        self.offset = offset

    def span(self, group=0):
        return((self.match.span(group)[0] + self.offset,
               self.match.span(group)[1] + self.offset))

    def start(self, group=0):
        return(self.match.start(group)+self.offset)

    def end(self, group=0):
        return(self.match.end(group)+self.offset)

    def group(self, *args, **kwargs):
        return(self.match.group(*args, **kwargs))

    def groups(self, *args, **kwargs):
        return(self.match.groups())

    def groupdict(self):
        return(self.match.groupdict())


class pdf_obj:
    '''
    A base class for things with text in pdfs.
    The text can be edited so that small changes can be applied to larger
    objects
    '''
    def __init__(self, text, origin):
        assert isinstance(text, bytes)
        self.text = text
        self.origin = origin

    def search(self, pattern):
        '''
        Calls pattern.search(self.text) to do a literal search in obj.
        repl can be a string or a function, pattern is a compiled re.Pattern
        '''
        return pattern.search(self.text)

    def finditer(self, pattern):
        '''
        Calls pattern.finditer(self.text) to do a literal search in obj.
        repl can be a string or a function, pattern is a compiled re.Pattern
        '''
        yield from (my_match(e) for e in pattern.finditer(self.text))

    def sub(self, pattern, repl):
        '''
        Calls pattern.sub(repl, self.text) to do a literal search/repl in obj.
        repl can be a string or a function, pattern is a compiled re.Pattern
        '''
        self.text = pattern.sub(repl, self.text)

    def delete(self, spans):
        '''
        Give this function an iterator of spans (tuples such as (n, m) with m > n)
        and *IN PLACE* delete those corresponding indices from self.text
        '''
        for span in spans:
            assert isinstance(span, tuple) and len(span)==2 and span[0] < span[1]

        indices = set()
        # delete duplicates
        [indices.update(range(*span)) for span in spans]
        new_spans = list()
        end_span = 0
        prev = 0
        # recreate contiguous spans
        for index in sorted(indices, reverse=True):
            if index != prev-1:
                if end_span:
                    new_spans.append((prev, end_span))
                end_span = index + 1
            prev = index
        new_spans.append((prev, end_span))
        # note that the new spans are already in reverse order
        for span in new_spans:
            self.text = b''.join([self.text[:span[0]], self.text[span(1):]])


class pdf_objs:
    '''
    A collection of pdf_obj's
    initialized from an iterator and an origin
    '''
    def __init__(self, iterator, origin):
        self.els = iterator
        self.origin = origin


class pdf_match(pdf_obj):
    '''
    A base class for matches within pdf objects
    '''
    def __init__(self, m, origin):
        super().__init__(m.group(0), origin)
        self.match = my_match(m)

    def span(self, group=0):
        return self.match.span(group)

    def start(self, group=0):
        return self.match.start(group)
    
    def end(self, group=0):
        return self.match.end(group)

    def len(self):
        return self.end() - self.start()

    def finditer(self, pattern):
        '''
        Overrides the method from pdf_obj so that the search is performed on 
        the original text and returns only if the match is inside self.span().
        Calls pattern.finditer(self.match.string) to do a literal search in obj.
        repl can be a string or a function, pattern is a compiled re.Pattern
        '''
        yield from (my_match(m, self.match.start())
                    for m in pattern.finditer(self.text))

    def find(self, option):
        '''
        Because regular expressions can't match nested + consecutive dicts
        easily, this reverts to finding dicts by matching << >>
        Though this function finds all the dictionaries, it only returns the
        highest level (unnested) consecutive ones
        '''
        options =   {   'dicts' :   
                        {   'start' : re.compile(b'<<'), 
                            'end'   : re.compile(b'>>')},
                        'arrays': 
                        {   'start' : re.compile(b'\['),
                            'end'   : re.compile(b']')},
                    }
        assert option in options.keys()

        ms   = list(self.finditer(options[option]['start']))
        me   = list(self.finditer(options[option]['end']))
        try:
            assert len(ms) == len(me)
        except AssertionError as e:
            raise AssertionError(f'{e}: mismatched delimiters')
        depth   = 0 # a counter to measure nesting depth.
        sbuffer = []
        d_spans = []
        # iterate over the delimiters, sorted by start position
        # to not select by depth, eliminate the depth variable and always append
        for delim in [e for _,e in sorted(zip([i.start() for i in ms+me], ms+me))]:
            if delim.group(0) in [b'<<', b'[']:
                depth += 1
                sbuffer.append(delim.match.start())
            else:
                depth -= 1
                if depth == 0: # is not nested
                    d_spans.append((sbuffer.pop(), delim.match.end()))
                else: # is nested (to include all matches, always do the line above)
                    sbuffer.pop()

        for x in sorted(d_spans):
             for y in self.finditer(re.compile(re.escape(
                                      self.text[x[0]:x[1]]))):
                 yield y


    def parse(self):
        '''
        Break up the object's contents into a pdf_matches object.
        This is intended to parse an indirect object or dictionary 
        into constituent direct objects
        '''
        els = [] # short for elements
        ids = [] # short for indices (spans, really)
        dicts = (pdf_dict(x, origin=self) for x in self.find('dicts'))
        arrays = (pdf_array(x, origin=self) for x in self.find('arrays'))
        streams = (pdf_stream(x, origin=self) for x in self.finditer(P['stream']))
        booleans = (pdf_bool(x, origin=self) for x in self.finditer(P['bool']))
        refs = (pdf_ref(x, origin=self) for x in self.finditer(P['ref']))
        numerics = (pdf_numeric(x, origin=self) for x in self.finditer(P['numeric']))
        nulls = (pdf_null(x, origin=self) for x in self.finditer(P['null']))
        names = (pdf_name(x, origin=self) for x in self.finditer(P['name']))
        
        # find the largest nonoverlapping objects and return those in a
        # dictionary sorted by type
        def in_span(x, y):
            if bool(y):
                return any((z[0] <= x[0] <= x[1] <= z[1] for z in y))
            else:
                return False
        # careful, the order of this list matters and should go from generic to specific
        for t in [dicts, arrays, streams, names, refs, booleans, numerics, nulls]:
            for o in t:
                if in_span(o.span(), ids):
                    continue
                else:
                    els.append(o)
                    ids.append(o.span())

        return pdf_objs(els, origin=self)


class pdf_matches(pdf_objs):
    '''
    A collection of pdf_match objects
    initialized from an iterator of match objects (i.e. re.finditer)
    an origin, and an the type of object to initiate (by default, pdf_match)
    '''
    def __init__(self, iterator, origin, pdf_init=pdf_match):
        super().__init__((pdf_init(x, origin) for x in iterator), origin)

