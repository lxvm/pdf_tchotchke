#!/usr/bin/env python3

# decoder.py
# Author: Lorenzo Van Muñoz
# Last Updated Dec 19 2020

# A script to decode some blocks of pdf

import re , zlib , argparse

def decode(pdffile):
    '''
    This reads in a pdf file a decompresses /FlateDecode blocks to easily read
    One could then try to decompress what is in the blocks by first extracting
    the utf-8 or utf-16 bytes from the other pdf-specific commands and decoding
    those bytes to see the unicode itself, if any of it is human-readable
    '''

    # read in pdf as byte-string
    pdf = open(pdffile, "rb").read()
    # compile pdf 'stream' regexp
    stream = re.compile(rb'.*?FlateDecode.*?stream(.*?)endstream', re.S)
    # find all unique streams
    matches = set(stream.findall(pdf))
    # decompress the strings 
    for i,s in enumerate(matches):
        s = s.strip(b'\r\n')
        try:
            print(zlib.decompress(s))
            print("")
            # you can try the .decode('utf-16') method on these byte strings
            # but you should probably remove all the other postscript/pdf 
            # markings to try and read any text from the bytes
        except:
            pass

    return

def main():
    '''
    This handles arguments for this function
    '''
    
    parser = argparse.ArgumentParser(   \
        description='''A script to read pdf encodings''')
    
    parser.add_argument("filename",   \
        help="enter the name of path of a pdf")
    
    args = parser.parse_args()

    decode(args.filename)

    return
    

if __name__ == "__main__":
    main()
    raise SystemExit
