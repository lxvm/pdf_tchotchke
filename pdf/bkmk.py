#!/usr/bin/env python3

# bkmk.py
# A script to generate pdf bookmarks in cpdf syntax
# Written by Lorenzo Van Muñoz
# Last updated Dec 14 2020

# This script imports a txt file whose lines come in text and page number pairs.
# It then places these pairs into an array.
# A numbering adjustment is then made to the page numbers.
# The index level of each bookmark entry is inferred using some simple rules.
# Then the array is written to a txt file with the correct syntax for cpdf bookmarks.

import os,sys,filenames,re

# Start script
print("bkmk.py - a script to make pdf bookmarks\n")

# Change working directory to directory where script was called from
# whereas the script is run from sys.path[0]
os.chdir(os.getcwd())

filepath,outpath = filenames.fileio(ext=".txt")

# import file
with open(filepath,"r") as file:
    # read in file as a contiguous string
    data = file.read()

# Get each line in file (excluding empty line and newline characters)
lines = data.rstrip().split("\n")

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
    #TODO make n option to delete the numbers for the final TOC
    #import re
    repetitions = 0
    # This enforces no empty lines as well as getting index
    while bool(re.match("^\w+" + repetitions * "\.[0-9]+",entry)):
        repetitions += 1
    return repetitions - 1

# there has to be an even number of lines (entries come in pairs)
length = len(lines)
assert length % 2 == 0

# Ask for the page offset 
offset_str = input(f"Enter the page in the pdf for the following TOC entry:\nText: {lines[0]}\nPage:{lines[1]}\n> ")
offset = int(offset_str) - int(lines[1])

# finish and export bookmarks
entries = []
with open(outpath,"w") as output:
    for i in range(int(length/2)):
        # Check that even line numbers are digits (roman numerals not allowed)
        assert lines[2*i+1].isdigit()
        # Compile each entry with structure[index, text, page number]
        entries.append([getIndex(lines[2*i]),lines[2*i],lines[2*i+1]])
        # Apply page offset
        entries[i][2] = int(entries[i][2]) + offset
        # Write to file with cpdf syntax
        output.write(f"{entries[i][0]} \"{entries[i][1]}\" {entries[i][2]}\n")

# Close script
print("\nBookmarks finished!")
sys.exit()
