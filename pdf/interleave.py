#!/usr/bin/env python3

# interleave.py
# A script to automatic interleave lines between blocks in a text file
# Written by Lorenzo Van Muñoz
# Last Updated Dec 17 2020

import argparse , filenames

def interleave(lines):
    '''
    Read a file with alternating blocks of entries and page numbers and interleave them so that they alternate line by line

    Arguments:
        List : containing strings read in from a pdf's TOC

    Returns:
        List : a permutation of the list elements from the input
    '''

    # identify numerical lines representing page numbers
    num_indices = []
    entry_indices = []
    for i,e in enumerate(lines):
        # ensure no empty lines
        if not bool(e):
            raise ValueError("Input file contains empty lines not allowed")
        if e.isdigit():
            num_indices.append(i)
        else:
            entry_indices.append(i)

    output = []
    # perform the permutations (entries alternate with numbers)
    for i,_ in enumerate(lines):
        if i % 2 == 0:
            output.append(lines[entry_indices[int(i/2)]] + "\n")
        else:
            output.append(lines[num_indices[int((i-1)/2)]] + "\n")
            
    return output


def main():
    '''
    This handles the input and output and command line arguments for interleaving.py
    '''
    
    #define command line arguments
    parser = argparse.ArgumentParser(   \
            description='''a script to interleave lines''')

    parser.add_argument("-i","--input", \
            help="input file name")
    parser.add_argument("-o","--output",    \
            help="output file name")

    args = parser.parse_args()  

    print("interleave.py - a script to interleave lines\n")

    filenames.fileOperate(interleave,   \
        newlines=False,  \
        readfile=args.input, writefile=args.output,   \
        readext=".txt",writeext=".txt")
    
    print("Lines interleaved")
    return

if __name__ == "__main__":
    main()
    raise SystemExit
