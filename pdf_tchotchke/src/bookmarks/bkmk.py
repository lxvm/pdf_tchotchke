#!/usr/bin/env python3

# bkmk.py
# Author: Lorenzo Van Muñoz
# Last updated Dec 26, 2020

'''
A script to generate pdf bookmarks in cpdf,gs,pdftk syntaxes

This script uses regular expressions to identify
relevant bookmark information and to typeset the syntaxes.
It also supports conversion between the different supported formats.

Anyone is welcome to use it or improve upon it. Hopefully it makes
the bookmark creation process easier for anyone needing to turn
tables of contents into bookmarks, especially for large documents 
such as textbooks.

Though it works as is, if it were to change in any way I would maybe
create a syntax class with reading/writing methods as an alternative
to the current dictionary bookmark system.

In addition, the only other 'difficult' part about this script is to
properly handle the detection of bookmark index/level and changing it 
between the different formats. For example, cpdf and pdftk directly
reference the current level of the entry, however gs/pdfmarks uses a
hierarchical structure where each entry may have 'children'/subentries.
Converting between these to has been implemented one way with while loops
and the other way using recursion. Hopefully these are the only generic
formats and any new ones are just minor variations of these.

Have fun and work fast!
'''

import re
import argparse

from pdftools.utils import filenames

# Global variable define available re flags
RE_FLAGS = {
        "A" :   re.ASCII,
        "I" :   re.IGNORECASE,
        "L" :   re.LOCALE,
        "M" :   re.MULTILINE,
        "S" :   re.DOTALL,
        "X" :   re.VERBOSE,
        "U" :   re.UNICODE
        }
# Global variable syntax data structure for supported syntaxes
BKMK_SYNTAX = {
        # Each syntax format has two properties: a print statement to
        # print data to that format and a sense statement which is a
        # regular expression to detect whether a line has that format
        # The data to print corresponds to (x,y,z) = (index,title,page)
        "cpdf"   : {
            "print" : (lambda x,y,z: f"{z} \"{x}\" {y}\n"),
            "sense" : r"(?P<index>\d+) \"(?P<title>.+)\" (?P<page>\d+).*"
            # View information is given by "[<page number></view command>]"
            },
        "gs"    : {
            # the minus sign before the count leaves the menu unexpanded
            "print" : (lambda x,y,z: f"[ /Count -{z} /Page {y} /Title ({x}) /OUT pdfmark\n"),
            "sense" : r"\[ /Count [-]*(?P<index>\d+) /Page (?P<page>\d+) /Title \((?P<title>.+)\) /OUT pdfmark.*"
            # In addition, the /View [</view command>] option and its variations can be added
            },
        "pdftk" : {
            "print" : (lambda x,y,z: f"BookmarkBegin\nBookmarkTitle: {x}\nBookmarkLevel: {z}\nBookmarkPageNumber: {y}\n"),
            "sense"  : r"BookmarkBegin.*\nBookmarkTitle: (?P<title>.+).*\nBookmarkLevel: (?P<index>\d+).*\nBookmarkPageNumber: (?P<page>\d+).*"
             }
    }


def whichSyntax(data):
    '''
    Tests whether the given entry is a bookmark

    Arguments:
        List : hopefully lines from a bookmark file

    Returns:
        String or Error : "cpdf" or "gs" syntax, None if not any syntax
    '''

    for e in list(BKMK_SYNTAX):
        if bool(re.search(BKMK_SYNTAX[e]["sense"],data)):
            return e
    raise UserWarning("The file is does not match any supported syntax")


def convertSyntax(data,output_syntax=None,offset=0):
    '''
    Converts one bookmark file syntax into another file.
    Should detect the input syntax automatically and write
    to the specified syntax.
    This isn't a necessary feature since if the bookmark file
    is already there, then just use the corresponding program
    to add the bookmarks.
    But maybe just do this for completeness.
    This can also renumber the pages by the given offset
    '''

    input_syntax = whichSyntax(data)
    if output_syntax == None:
        output_syntax = input_syntax
    
    titles,pages,indices = extractBkmkFile(
            data,BKMK_SYNTAX[input_syntax]["sense"])

    return writeBkmkFile(output_syntax,
            titles,
            [int(e) + offset for e in pages],
            indices,
            index_input_syntax=input_syntax)


def createTocFromText(data,output_syntax=None,pattern="(?P<title>.+)\n(?P<page>\d+)",re_flags=re.U,edit=''):
    '''
    This function takes lines from a bookmarks in a raw text file and outputs them to a specified bookmark syntax.
    It also needs to ask interactively for the page offset to calculate the page numbering right.

    Arguments:
        String : has the content of f.read() from an input file generated from the text of a pdf TOC
        String : either "cpdf" or "gs", representing the output syntax
        String : a regular expression string containing (?P<page>\d+) and (?P<title>.+) groups to parse the page numbers and entry text from the input file
        re.FLAG : a regular expression flag defaulting to re.UNICODE
        String : a regexp to apply to all titles. e.g. to remove all leading numbers: r'^[\d\.]+\.'

    Return:
        String : the finalized bookmark entries
    '''
    
    if output_syntax == None:
        raise UserWarning('No output syntax has been specified. Aborting!')
    # check that given re has only the required fields
    re_pattern = re.compile(rf"{pattern}")
    assert set(['title','page']) == set(re_pattern.groupindex.keys())
    
    # initial data
    first_entry = re.search(re_pattern,data).group("title")
    first_page = re.search(re_pattern,data).group("page")
    if first_page == '' or first_entry == '':
        raise UserWarning(f'The first entry or page did not match: you may want to review {pattern}')
    
    # Ask for the page offset 
    offset_str = input(f"Enter the page in the pdf for the following TOC entry:\nText: {first_entry}\nPage: {first_page}\n> ")
    offset = int(offset_str) - int(first_page)

    # OPTIONAL delete regexp from the titles
    edits = {
            False   :   (lambda x : x),
            True    :   (lambda x : re.sub(edit,'',x))
            }
    
    titles,pages = extractBkmkFile(data,re_pattern)

    return writeBkmkFile(output_syntax,
            [edits[bool(edit)](e) for e in titles],
            [int(e) + offset for e in pages],
            [getCPDFIndexFromTitle(e) for e in titles],   
            index_input_syntax="cpdf")


def getCPDFIndexFromTitle(title):
    '''
    Determine the cpdf index of an entry (this is simplistic and the logic should be refined depending on the content)
    
    Arguments:
        String : ideally the title of a table of contents entry

    Returns:
        Integer : 0 if the line starts without an integer or an integer without trailing decimal
                  1 if the line starts with a decimal like X.X where X are integers
                  2 if the line starts with a double decimal like X.X.X
                  3 the pattern goes on
    '''
    
    repetitions = 0
    # This enforces no empty lines as well as getting index
    while bool(re.match("^\w+" + repetitions * "\.[0-9]+",title)):
        repetitions += 1
    # Note that this only outputs the cpdf convention! This is fixed by repairIndex()
    return repetitions - 1


def extractBkmkFile(data,pattern):
    '''
    This matches a regexp to a bkmk file, returning all the instances of each match group in its own list
    Returns a tuple with the lists
    '''
    # Must use this order! index must be last other wise the case from createTocFromFile() which has no index will fail
    preferred_order = {
        "title" : 1,
        "page"  : 2,
        "index" : 3
        }

    pattern = re.compile(pattern)
    groups = dict(pattern.groupindex)
    # this is the case where we are creating a new bkmk which doesn't yet have indices
    if len(groups.keys()) == 2:
        del preferred_order['index']

    # in the preferred order, list all matches in each group as its own list (possibly a permutation bsed on the ordering of the matching group)
    return [ [ e[groups[i]-1].strip() for e in re.findall(pattern,data) ] for i in list(preferred_order.keys()) ]


def writeBkmkFile(output_syntax,titles,pages,indices,index_input_syntax=""):
    '''
    I was doing this over 5 times in the code so decided to centralize it
    This takes in lists with the titles, pages, indices, and exports a string in the requested format
    '''

    bkmks = ""
    for i,_ in enumerate(indices):
        bkmks +=  BKMK_SYNTAX[output_syntax]["print"](    
                titles[i],pages[i],indices[i])
    if output_syntax == index_input_syntax or not bool(index_input_syntax):
        return bkmks 
    else: # the index input syntax is not the same as the output syntax
        return repairIndex(bkmks,index_input_syntax) # careful, recursion


def repairIndex(bkmks,index_input_syntax):
    '''
    This function preserves the syntax of a bkmk file but repairs the indices to match that syntax.
    This function is necessary because each of formats has its own convention.
    For instance the index in cpdf is starts from 0 and refers to how many levels deep into the TOC that entry is.
    The pdftk index is the same logic as cpdf but 1-indexed (add 1 to the cpdf index).
    In gs, the index given by /Count N  means that that entry has N child entries in the next sublevel.

    Arguments:
        String  :   The bookmark file
        String  :   (Optional) The index input syntax (this can be detected regardless)

    Returns:
        String  :   The finalized bookmark file
    '''

    output_syntax = whichSyntax(bkmks)

    if output_syntax == index_input_syntax:
        return bkmks
                    
    else:
        titles,pages,indices = extractBkmkFile(bkmks,BKMK_SYNTAX[output_syntax]["sense"])
        indices = [int(e) for e in indices]

        # convert!
        if output_syntax == "gs": # 
            # convert cpdf or pdftk index to gs index (works because this is a comparison method)
            for i,e in enumerate(indices):
                indices[i] = 0
                try:
                    # finds the number of subsequent indices 1 larger than the current one before the next index which has the same value as the current one
                    counter = 0
                    while indices[i + 1 + counter] != e:
                        if indices[i + 1 + counter] == e + 1:
                            indices[i] += 1
                        counter += 1
                except IndexError:
                    pass

        else: # outputting to cpdf or pdftk
            if index_input_syntax == "gs":
                # convert gs to cpdf
                # in this loop, we go from end to beginning and get the cpdf index at each step
                    # each run through this loops determines how many of the preceeding entries are parents of indices[i]
                def recursiveDeleteTerminalBranches(roots):
                    '''
                    This takes in a list and removes terminal branches until there are none
                    '''
                    tree = roots[:]
                    for i,e in list(enumerate(tree))[::-1]:
                        if bool(e):
                            try:
                                # if every index in that range is zero, it is a terminal branch
                                # note that if tree[i] is in the range(e) (i.e. len(tree[i+1:i+1+e]) < len(range(e)))
                                # then there is match, so we won't delete it, as desired
                                if tree[i+1:i+1+e] == [0 for x in range(e)]:
                                    # replace e with a zero but remove e entries
                                    del tree[i:i+e]
                                    # prune the tree
                                    tree = recursiveDeleteTerminalBranches(tree)
                                else:
                                    continue
                            except IndexError:
                                continue
                        else:
                            continue

                    #print(tree)
                    return tree

                results = [0 for e in indices]
                fast_search = 0
                for i,_ in enumerate(indices):
                    results[i] = len([x for x in recursiveDeleteTerminalBranches(indices[fast_search:i]) if x > 0])
                    # if the entry has no parent, ignore all the preceeding entries
                    if results[i] == 0:
                        fast_search = i
                indices = results

                if output_syntax == "pdftk":
                    # convert cpdf to pdftk by adding 1
                    indices = [ e + 1 for e in indices ]

            elif index_input_syntax == "pdftk": # output_syntax == "cpdf"
                # convert pdftk to cpdf by subtracting 1
                indices = [ e - 1 for e in indices ]

            else: # converting cpdf to pdftk by adding 1
                indices = [ e + 1 for e in indices ]

    return writeBkmkFile(output_syntax,titles,pages,indices)


def create(args):
    '''
    Calls the right functions to make things create
    '''
    filenames.fileOperate(createTocFromText, 
            readfile=args.input, 
            writefile=args.output,   
            readext=".txt",writeext=".txt", 
            output_syntax=args.syntax, 
            pattern=args.pattern,   
            re_flags=RE_FLAGS[args.re_flags],   
            edit=args.edit)
    return


def convert(args):
    '''
    Calls the right functions to make things convert
    '''
    filenames.fileOperate(convertSyntax, 
            readfile=args.input, 
            writefile=args.output,   
            readext=".txt",writeext=".txt", 
            output_syntax=args.syntax, 
            offset=args.number)
    return


def cli():
    '''
    Run the bkmk.py script.
    This handles its command-line arguments and executes the requested functions.
    '''


    # Define command-line arguments
    parser = argparse.ArgumentParser(prog='bkmk.py',   
            description='''a script to produce pdf bookmarks''')

    subparsers = parser.add_subparsers(help='action!')
    # Subparsers for each command
    parser_convert = subparsers.add_parser("convert",   
            help="change a bookmark file syntax or renumber the pages")
    parser_convert.set_defaults(func=convert)
    # convert arguments
    parser_convert.add_argument("-n","--number",default=0,type=int,    
            help="apply an offset to all page numbers")

    parser_create = subparsers.add_parser("create", 
            help="create bookmarks from a raw TOC file")
    parser_create.set_defaults(func=create)
    # create arguments
    parser_create.add_argument("-p","--pattern",default="(?P<title>.+)\n(?P<page>\d+)",  
            help="regexp to read the input file containing (?P<page>\d+) and (?P<title>.+) groups")
    parser_create.add_argument("-r","--re-flags", choices=list(RE_FLAGS),  
            help="optionally add a regexp flag to specify --pattern", default="U")
    parser_create.add_argument("-e","--edit",  
            help="apply a regexp to the title, e.g. to removing leading numbers: r'^[\d\.]+\.'", default="")
    
    # Main arguments
    parser.add_argument("syntax", choices=list(BKMK_SYNTAX),    
            help="choose bookmark output format")
    parser.add_argument("input", 
            help="input file name")
    parser.add_argument("output",nargs='?',    
            help="output file name")

    args = parser.parse_args()  
    
    # create a safe output file name if given or not given
    if args.output == None:
        args.output = filenames.fileOut(writefile=args.input,ext='.txt')

    print("bkmk.py - a script to manipulate pdf bookmarks\n")
    
    args.func(args)

    # Close script
    print("\nBookmarks finished!")
    return


# run script if called from command line
if __name__ == "__main__":
    cli()    
    raise SystemExit()
