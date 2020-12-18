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
# Cpdf  and Ghostscript/pdfmark syntaxes are supported.

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
            "sense" : r"",
            },
        "gs"    : {
            "print" : (lambda x,y,z: f"[ \Count {x} \Page {z} \Title ({y}) \OUT pdfmark\n"),
            "sense" : r""
            }
        }


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

def whichSyntax(entry):
    '''
    Tests whether the given entry is a  bookmark

    Arguments:
        String : hopefully a line from a bookmark file

    Returns:
        String or None : "cpdf" or "gs" syntax, None if not any syntax
    '''
    pass

def convertSyntax(entries,newsyntax):
    '''
    Converts one bookmark file syntax into another file.
    Should detect the input syntax automatically and write
    to the specified syntax.
    This isn't a necessary feature since if the bookmark file
    is already there, then just use the corresponding program
    to add the bookmarks.
    But maybe just do this for completeness.
    '''
    pass

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

    print("bkmk.py - a script to manipulate pdf bookmarks\n")
    # Define command-line arguments
    parser = argparse.ArgumentParser(description = \
            ''' \
            a script to manipulate pdf bookmarks    \
            ''')
    # This should have a required action, i.e. "convert" or "create"
    # and an output format, i.e. "cpdf" or "gs"
    # TODO: accept filenames from commandline

    parser.add_argument("action", choices=["create","convert"], help="take action", default="create")
    parser.add_argument("format", choices=list(BKMK_SYNTAX), help="choose format",default=list(BKMK_SYNTAX)[0])
    parser.add_argument("-i","--input", help="input file")
    parser.add_argument("-o","--output", help="output file")

    args = parser.parse_args()  

    filenames.fileOperate(createTocFromText, \
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
