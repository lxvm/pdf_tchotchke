#!/usr/bin/env python3

# editor.py
# Author: Lorenzo Van Muñoz
# Last Updated Feb 13, 2021

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

from .patterns import *
from .dobjects import *
from .iobjects import *
from .xrefs import *
from .parser import *


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

    def get_root(self):
        '''
        gets the root object
        '''
        d = self.get_xrefs().trailer().parse()
        ref = [d[e] for e in d if b'Root' in e.text][0]

        return next(self.get_iobjs().iobjs([ref.dest()]))

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
        h_offset = P['pdf_h'].search(header).start()
        n_entries = 1 # 1 from the header
        xtext = b''.join([b'0'*(10-h_offset),
            bytes(str(h_offset), 'utf-8'), b' 65535 f \n'])
        if repair:
            preamble = header
        # create the xitem for each indirect object
        for iobj in iobjs.iobjs():
            n_entries += 1
            offset = bytes(str(iobj.start()), 'utf-8')
            # here is a quick and dirty solution
            xtext += b''.join([b'0'*(10-len(offset)), offset, b' 00000 n \n'])
            # probably the more correct thing is to import the xrefs at the
            # beginning and keep the generation info but substitute the offset
            #xtext += re.sub(rb'\d{10}', b'0'*(10-len(offset))+offset, item)
            if repair:
                preamble += iobj.text
        # also update the length of the trailer and the new startxref position
        n_entries = bytes(str(n_entries), 'utf-8')
        new_xref = b''.join([b'xref\n0 ', n_entries, b'\n', xtext, b'trailer\n',
            re.sub(rb'/Size \d+', rb'/Size '+n_entries, 
                xrefs.trailer().text), b'\nstartxref\n', 
                bytes(str(xrefs.match.start()), 'utf-8'), b'\n'])
        if repair:
            self.text = b''.join([preamble, new_xref, eof])
        else:
            return new_xref


if __name__ == '__main__':
    raise SystemExit()
