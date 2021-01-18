#!/usr/bin/env python3

# editor.py
# Author: Lorenzo Van Muñoz
# Last Updated Jan 3, 2020

'''
This module creates classes for a convenient representation of 
the structure of a pdf document and has some methods to add or 
remove (mainly remove) objects.

Notice that to a pdf, a page is just an object referencing others.

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

This process closely follows the example in Section G.6 of the 
PDF 1.7 reference, except that it actually deletes objects from the pdfs
instead of just their object references. That is, there is no revision history.

#Searching in PDF Basics
PDF reading applications read the file from back to front!
They first read the trailer dictionary, which contains a reference to 
document catalog (/Type/Catalog or /Root in trailer). This contains a reference
to the Page Tree object (/Type/Pages) which in turn references the individual 
page objects, which in turn reference the content streams that land on the page
Figure 3.5 of the pdf 1.7 reference shows this structure quite nicely.

At the level of the page object is where visible elements of the pdf may be
removed. For instance, there may be /Contents objects or /Annots objects or
/Watermark objects referenced as /XObjects in the Page /Resources dictionary 
which can be deleted.
'''

import re 
from io import BufferedReader, BufferedRandom
from functools import partial

import pdftotext

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
    #'ditems':   re.compile(rb'(/\w+)(/[^/]+|[^/].+[\)\]>]|[^/]+)', re.DOTALL),
    'dict'  :   re.compile(rb'<<\n*(.+?)\n*>>', re.DOTALL),
    'array' :   re.compile(b'\[\n*(.+?)\n*\]'),
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



### Base Classes

class pdf_objs:
    '''
    A collection of pdf_obj's
    initialized from an iterator and an origin
    '''
    def __init__(self, iterator, origin):
        self.els = iterator
        self.origin = origin


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
        return pattern.finditer(self.text)

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


class pdf_matches(pdf_objs):
    '''
    A collection of pdf_match objects
    initialized from an iterator of match objects (i.e. re.finditer)
    an origin, and an the type of object to initiate (by default, pdf_match)
    '''
    def __init__(self, iterator, origin, pdf_init=pdf_match):
        super().__init__((pdf_init(x, origin) for x in iterator), origin)


class pdf_match(pdf_obj):
    '''
    A base class for matches within pdf objects
    '''
    def __init__(self, m, origin):
        super().__init__(m.group(0), origin)
        self.match = m

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
        start = 0
        matches = []
        for m in pattern.finditer(self.match.string):
            if m.start() > self.end()-1: # break after search passes desired spot
                break
            elif m.end()-1 < self.start():
                continue
            else:
                yield(m)
        #return (m for m in pattern.finditer(self.match.string) 
        #        if self.start() <= m.start() and m.end() <= self.end())

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
                sbuffer.append(delim.start())
            else:
                depth -= 1
                if depth == 0: # is not nested
                    d_spans.append((sbuffer.pop(), delim.end()))
                else: # is nested (to include all matches, always do the line above)
                    sbuffer.pop()
        # a lambda function to get a match object based on start and stop
        match_me = (lambda x: next(self.finditer(re.compile(
                                re.escape(self.match.string[x[0]:x[1]])))))
        
        return (match_me(x) for x in sorted(d_spans)) # generator expression!

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
    def parse():
        con = re.compile(re.escape(next(self.finditer(P['array']).group(1))))
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
        con = re.compile(re.escape(next(self.finditer(P['dict'])).group(1)))
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
        xref = xrefs[0] # this is a match object
        self.where = xref.group(2)
        super().__init__(pdf_match(xref, origin).finditer(P['xref']), origin, pdf_xref)

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
        trlr = pdf_match(re.match(b'.+', self.match.group(2), re.S), origin=self)
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


### The main class for handling a pdf

class pdf_redactor(pdf_obj):
    '''
    A class for redacting a pdf
    can be instantiated from a readable 
    bytes-type file object or from a byte string
    '''
    def __init__(self, text, origin=None):
        if isinstance(text, (BufferedReader, BufferedRandom)):
            text.seek(0)
            super().__init__(text.read(), text)
            text.seek(0)
        else:
            super().__init__(text, origin)

    def get_parts(self):
        '''
        Return the header, indirect objects, xrefs, and footer as a list
        '''
        m = P['pdf_hf'].match(self.text)
        return [m.group(1), self.get_iobjs(), self.get_xrefs(), m.group(2)]

    def get_iobjs(self):
        '''
        Returns a pdf_iobjs instance with every iobj in self
        '''
        return pdf_iobjs(self.finditer(P['iobj']), origin=self)
    
    def get_xrefs(self):
        '''
        Returns an pdf_xrefs instance with every pdf_xref in self
        '''
        return pdf_xrefs(self.finditer(P['xrefs']), origin=self)

    def check_xref(self):
        '''
        Returns true if the location of all objects in the pdf matches the xref
        '''
        header, iobjs, xrefs, _ = self.get_parts()
        # get the object numbers and offsets from the objects
        o_offsets = [(0, P['pdf_h'].search(header).start())]
        l = len(header)
        [o_offsets.append(tuple([int(iobj.num()), iobj.start()+l])) 
                for iobj in iobjs.iobjs()]
        # get the object numbers and offsets from the xrefs
        x_offsets = []
        for xref in xrefs.xrefs():
            for block in xref.blocks():
                for i, item in enumerate(block.items()):
                    x_offsets.append(tuple([block.start() + i, item.offset()]))
        return x_offsets == o_offsets

    def del_objs(self, objs):
        '''
        Accepts a pdf_objs object and *IN PLACE* remove each pdf_obj within
        This is a LOW LEVEL function. Try not to use it at all because it is
        brazenly unaware of the structure of the pdf document other than how it
        rebuilds the xref table
        '''
        def reverse_sort_objs(objs):
            '''
            Reverse sort objects by number to prevent issues while deleting
            '''
            return [o for _,o in sorted(zip([e.num for e in objs], objs), reverse=True)]

        objs = list(objs.objs())
        obj_nums = []
        for obj in reverse_sort_objs(objs):
            # remove that object
            p = re.compile(b''.join([b'\n', obj.num(), b' \d+ obj.+?endobj\n+']), re.S)
            self.text = p.sub(b'\n', self.text)
            # remove all object references to that object, update others
            def update_refs(m):
                if m.group(1) < obj.num():
                    return m.group(0)
                elif m.group(1) == obj.num():
                    return b''
                elif m.group(1) > obj.num():
                    return b''.join([bytes(str(int(m.group(1))-1), 'utf-8'), m.group(2)])
            self.text = re.sub(b'(\d+)( \d+ (?:R|obj))', update_refs, self.text)
            # save the number of that object
            obj_nums.append(int(obj.num()))
        # iterate over the xrefs and get the text of those to remove
        obj_refs = []
        for xref in self.get_xrefs().xrefs():
            for block in xref.blocks():
                for i, item in enumerate(block.items()):
                    if block.start+i in obj_nums:
                        obj_refs.append(item.text)
        # delete the xrefs corresponding to those objects
        for ref in obj_refs:
            self.text = re.sub(ref, b'', self.text)
            
        # repair xref
        self.make_xref(repair=True)


    def make_xref(self, repair=False):
        '''
        Creates an xref for the pdf document
        If repair is false, then returns an xref.
        If repair is true, then injects the new xref in the pdf in place.
        '''
        header, iobjs, xrefs, eof = self.get_parts()
        l = len(header)
        h_offset = P['pdf_h'].search(header).start()
        n_entries = 1 # 1 from the header
        xtext = b''.join([b'0'*(10-len(h_offset)),
            bytes(str(h_offset), 'utf-8'), b' 65535 f \n'])
        if repair:
            preamble = header
        # create the xitem for each indirect object
        for iobj in iobjs.iobjs():
            n_entries += 1
            offset = bytes(str(iobj.start()+l), 'utf-8')
            # here is a quick and dirty solution
            xtext += b''.join([b'0'*(10-len(offset)), offset, b' 00000 n \n'])
            # probably the more correct thing is to import the xrefs at the
            # beginning and keep the generation info but substitute the offset
            #xtext += re.sub(rb'\d{10}', b'0'*(10-len(offset))+offset, item)
            if repair:
                preamble += iobj.text
        # also update the length of the trailer and the new startxref position
        n_entries = bytes(str(n_entries), 'utf-8')
        new_xref = b''.join([b'xref\n0 ', n_entries, b'\n', xtext, 
            re.sub(rb'/Size \d+', rb'/Size '+n_entries, 
                next(xrefs.xrefs()).trailer()), b'startxref\n', 
                bytes(str(xrefs.match.start()), 'utf-8'), b'\n'])
        if repair:
            self.text = b''.join([preamble, new_xref, eof])
        else:
            return new_xref


if __name__ == '__main__':
    raise SystemExit()
