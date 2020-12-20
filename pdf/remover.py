#!/usr/bin/env python3

# remover.py
# Author: Lorenzo Van Muñoz
# Last Updated Dec 19 2020

# A script to remove patterns in a file

import re , filenames , argparse

def searchLines(text=[rb''],pattern=rb'',startfrom=0,direction='+',reflag=re.A):
    '''
    finds the next instance of the search string in the text (a list of strings) starting from the given index
    also specify the search direction: '+' for forwards, '-' for backwards
    returns the index of the first match in the text and true or false for whether the string was found in that direction
    An option 'nopass' could be implemented to stop the program from searching beyond a certain index (must be consistent with the direction, so if direction is + then startfrom <= nopass and if direction is - then startfrom >= nopass. a value of -1 means either the beginning or end of file
    Nopass is not necessary for remove_uncompressed because of the logic used in that function.
    '''
    
    # if search string is empty, return the starting line
    if not bool(pattern):
        return (startfrom, False)
    else:
        # sign convention for directions
        sign = {'+' : 1 , '-' : -1}
        try:
            # start searching from the given start line
            count = 0
            # keep looking in lines forwards or backwards till line is matched
            while not bool(re.search(pattern,text[startfrom + count],reflag)):
                count += sign[direction]
            return (startfrom + count, True)
        except IndexError:
            #print(f'UserWarning: search string not found in {direction} direction')
            return (startfrom,False)


def remove_uncompressed(pdf,pattern=rb'',beg_env=rb'',end_env=rb'',p_reflag=re.A,b_reflag=re.A,e_reflag=re.A):
    '''
    This function examines an uncompressed pdf.
    If it finds the desired pattern (string or regexp), it removes all instances of the pattern andthe specified  environment block containing it
    To remove the pattern without environment, pass the empty string (default behavior) to the _env args
    '''

    # if search string is empty, exit
    if not bool(pattern):
        print('search string is empty: ending program!')
        return
    # create a set to track indicies to remove (each element in a set is unique)
    indices_to_remove = set()
    # a counter to skip lines in the search
    jumpto = 0
    # a counter to print how many times the pattern was found
    instances = 0
    # loop through lines in pdf to match them
    for i,e in enumerate(pdf):
        # skip ahead if you've been told to
        if i >= jumpto:
            # find the next instance of the pattern 
            nextP, foundP = searchLines(pdf,pattern=pattern,startfrom=i,direction='+',reflag=p_reflag)
            # if the search pattern was not found, stop searching
            if not foundP:
                break
            else:
                instances += 1

            # find the nearest instance of beg_env
            nextB, foundB  = searchLines(pdf,pattern=beg_env,startfrom=nextP,direction='-',reflag=b_reflag)
            # find the nearest instance of end_env
            nextE, foundE = searchLines(pdf,pattern=end_env,startfrom=nextP,direction='+',reflag=e_reflag)
            # if beg_env and end_env were not found together, print a warning
            if foundB != foundE:
                raise UserWarning(' matching beginning and ending of environment not found: file may be corrupted or search strings for the environment incorrect')
            # Since pattern was found, and if both environment patterns were found, remove the range of 
            elif foundB and foundE:
                indices_to_remove.update(list(range(nextB,nextE+1)))
            # Since the pattern was found on some line but neither environment patterns were found,remove only the line containing the pattern
            else:
                indices_to_remove.add(nextP)

            # tell the loop to skip ahead however far the searches got to 
            # the behavior is to skip ahead to end_env, which is pattern
            # if end_env was not found, which is beg_env if patter was not found
            jumpto = nextE + 1
        else:
            # debugging
            #print(e,i)
            continue

    # delete the matched text blocks from the pdf
    # do this from the beginning to end of file to
    # not move around list elements
    for i in sorted(indices_to_remove,reverse=True):
        del pdf[i]
    print(f'\nPattern deleted {instances} times!\n')

    return pdf


def main():
    '''
    Finds all matches of a given pattern in a file and removes matches which repeat more than once
    '''
    formats = {
            # Each flag is followed by its format function
            None : (lambda s : s),
            "X" : (lambda s : ''.join(f'{ord(e):X}' for e in s))
            }
    re_flags = {
            # for all options read help(re)
            # Default to matching ASCII strings
            None : re.A,
            # Ignorecase
            'I' : re.I,
            }

    parser = argparse.ArgumentParser(   \
        description='''A script to remove patterns from a file''')
  
    parser.add_argument("pattern",  \
            help="provide a string or python regexp to search for")
    parser.add_argument("-i","--input",   \
            help="enter the name or path of a pdf")
    parser.add_argument("-o","--output",   \
            help="enter the name or path to write to")
    parser.add_argument("-b","--beg-env", \
            help="string or python regexp to match the beginning of a text block containing the main pattern")
    parser.add_argument("-e","--end-env", \
            help="string or python regexp to match the beginning of a text block containing the main pattern")
    parser.add_argument("-f","--format",choices=list(formats),  \
            help="do not call this flag if you want the none value. convert the search pattern using Python's 'Format Specification Mini-Language'")
    parser.add_argument("-r","--re-flags", choices=list(re_flags), \
            help="call this flag if you need to send a special regexp to all searches")
    parser.add_argument("--bytes",action="store_true",  \
            help="this flag makes the entire search based on byte-strings")
    
    args = parser.parse_args()

    # get default search settings
    search_pattern = formats[args.format](args.pattern)
    search_beg_env = args.beg_env
    search_end_env = args.end_env
    writemode = 'w'
    readmode = 'r'

    # apply modifications for byte
    if args.bytes:
        search_pattern = bytes(search_pattern,'utf-8')
        search_beg_env = bytes(search_beg_env,'utf-8')
        search_end_env = bytes(search_end_env,'utf-8')
        writemode = 'wb'
        readmode = 'rb'

    # handle regexp flags
    p_flag = re_flags[args.re_flags]
    b_flag = re_flags[args.re_flags]
    e_flag = re_flags[args.re_flags]

    filenames.fileOperate(remove_uncompressed,  \
            newlines=True,  \
            readfile=args.input,    \
            writefile=args.output,  \
            readext='',writeext='', \
            readmode=readmode,  \
            writemode=writemode,   \
            pattern=search_pattern, \
            beg_env=search_beg_env, \
            end_env=search_end_env, \
            p_reflag=p_flag,b_reflag=b_flag,e_reflag=e_flag)

    return


if __name__ == "__main__":
    main()
    raise SystemExit
