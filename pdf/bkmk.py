#!/usr/bin/env python3

# bkmk.py
# A script to generate pdf bookmarks in cpdf syntax
# Written by Lorenzo Van Muñoz
# Last updated Dec 17 2020

# This script imports a txt file whose lines come in text and page number pairs.
# It then places these pairs into an array.
# A numbering adjustment is then made to the page numbers.
# The index level of each bookmark entry is inferred using some simple rules.
# Then the array is written to a txt file with the correct bookmark syntax.
# Cpdf and Ghostscript/pdfmark and pdftk syntaxes are supported.

# Start with defintions
import re , filenames , argparse

# Global variable syntax data structure
BKMK_SYNTAX = {
        # Each syntax format has two properties: a print statement to
        # print data to that format and a sense statement which is a
        # regular expression to detect whether a line has that format
        # The data to print corresponds to (x,y,z) = (index,title,page)
        "cpdf"   : {
            "print" : (lambda x,y,z: f"{x} \"{y}\" {z}\n"),
            "sense" : r"(?P<index>\d+) \"(?P<title>.+)\" (?P<page>\d+).*"
            },
        "gs"    : {
            "print" : (lambda x,y,z: f"[ /Count {x} /Page {z} /Title ({y}) /OUT pdfmark\n"),
            "sense" : r"\[ /Count (?P<index>\d+) /Page (?P<page>\d+) /Title \((?P<title>.+)\) /OUT pdfmark.*"
            },
        "pdftk" : {
            "print" : (lambda x,y,z: f"BookmarkTitle: {y}\nBookmarkLevel: {x}\nBookmarkPageNumber: {z}\n"),
            "sense"  : r"BookmarkTitle: (?P<title>.+)\nBookmarkLevel: (?P<index>\d+)\nBookmarkPageNumber: (?P<page>\d+).*"
             }
    }


def whichSyntax(entries):
    '''
    Tests whether the given entry is a  bookmark

    Arguments:
        List : hopefully lines from a bookmark file

    Returns:
        String or Error : "cpdf" or "gs" syntax, None if not any syntax
    '''

    if "BookmarkBegin" in entries[0]:
        return "pdftk"

    for e in list(BKMK_SYNTAX):
        if bool(re.match(BKMK_SYNTAX[e]["sense"],entries[0])):
            return e
    raise UserWarning("The first line of file is does not match any supported syntax")


def convertSyntax(entries,syntax):
    '''
    Converts one bookmark file syntax into another file.
    Should detect the input syntax automatically and write
    to the specified syntax.
    This isn't a necessary feature since if the bookmark file
    is already there, then just use the corresponding program
    to add the bookmarks.
    But maybe just do this for completeness.
    '''

    detected = whichSyntax(entries)
    output = []
    if syntax == "pdftk":
        output.append("BookmarkBegin\n")

    for i,entry in enumerate(entries):
        if detected == "pdftk":
            # have to get around the fact that pdftk bookmark lines come in trios
            if i % 3 == 1:
                matches = re.search(BKMK_SYNTAX["pdftk"]["sense"],"\n".join(entries[i:i+3])+"\n")
                (index,title,page) = (matches.group("index"),matches.group("title"),matches.group("page"))
                output.append(BKMK_SYNTAX[syntax]["print"](index,title,page))
            continue
        else:
            matches = re.search(BKMK_SYNTAX[detected]["sense"],entry)
            (index,title,page) = (matches.group("index"),matches.group("title"),matches.group("page"))
            output.append(BKMK_SYNTAX[syntax]["print"](index,title,page))

    return output


def getIndex(entry):
    '''
    Determine the index of an entry (this is simplistic and the logic should be refined depending on the content)
    
    Arguments:
        String : ideally a line from a table of contents

    Returns:
        Integer : 0 if the line starts without an integer or an integer without trailing decimal
                  1 if the line starts with a decimal like X.X where X are integers
                  2 if the line starts with a double decimal like X.X.X
                  3 the pattern goes on
    '''
    #TODO make an option to delete the numbers for the final TOC
    
    repetitions = 0
    # This enforces no empty lines as well as getting index
    while bool(re.match("^\w+" + repetitions * "\.[0-9]+",entry)):
        repetitions += 1
    return repetitions - 1


def createTocFromText(data,syntax):
    '''
    This function takes lines from a bookmarks in a raw text file and outputs them to a specified bookmark syntax.
    It also needs to ask interactively for the page offset to calculate the page numbering right.

    Arguments:
        List : has the content of f.readlines() from an input file generated from the text of a pdf TOC and should have bookmark text entries on the odd numbered lines with corresponding pagenumbers on the even numbered lines
        String : either "cpdf" or "gs", representing the output syntax

    Return:
        List : a list of strings where the strings are the finalized bookmark entries
    '''
    
    formatfn = BKMK_SYNTAX[syntax]["print"]
    # there has to be an even number of lines (entries come in pairs)
    length = len(data)
    assert length % 2 == 0
    # Ask for the page offset 
    offset_str = input(f"Enter the page in the pdf for the following TOC entry:\nText: {data[0]}\nPage:{data[1]}\n> ")
    offset = int(offset_str) - int(data[1])

    output = []
    # finish and export bookmarks
    if syntax == "pdftk":
        output.append("BookmarkBegin\n")
    for i in range(int(length/2)):
        # Check that even line numbers are digits (roman numerals not allowed)
        assert data[2*i+1].isdigit()
        # Compile entry
        output.append(formatfn( \
            getIndex(data[2*i]),   \
            data[2*i], \
            (int(data[2*i+1]) + offset)))

    return output


def completeTOC():
    '''
    This function calls either cpdf or gs to complete the pdf with its bookmarks.
    Should use the subprocess module.
    Needs to ask for the pdf file to add the bookmarks to.
    '''
    pass


def main():
    '''
    Run the bkmk.py script.
    This handles its command-line arguments and executes the requested functions.
    '''

    # Define available commands
    commands = {
            "create" : createTocFromText,
            "convert" : convertSyntax
            }

    # Define command-line arguments
    parser = argparse.ArgumentParser(   \
            description='''a script to produce pdf bookmarks''')

    parser.add_argument("action", choices=list(commands),   \
            help="choose an action")
    parser.add_argument("format", choices=list(BKMK_SYNTAX),    \
            help="choosebookmark output format")
    parser.add_argument("-i","--input", \
            help="input file name")
    parser.add_argument("-o","--output",    \
            help="output file name")

    args = parser.parse_args()  

    print("bkmk.py - a script to manipulate pdf bookmarks\n")

    filenames.fileOperate(commands[args.action], \
            newlines=False,  \
            readfile=args.input, writefile=args.output,   \
            readext=".txt",writeext=".txt", \
            syntax=args.format)

    # Close script
    print("\nBookmarks finished!")
    return


# run script if called from command line
if __name__ == "__main__":
    main()    
    raise SystemExit
