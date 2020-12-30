#!/usr/bin/env python3

# remover.py
# Author: Lorenzo Van Muñoz
# Last Updated Dec 23 2020
'''
A script to remove patterns in a file.
Designed with PDFs in mind. 
It reads in a document as a byte string 
and then tries identifying the text in
various encodings.
'''

import os 
import re 
import argparse
import difflib
import subprocess

from ..utils import filenames 

# Global variables
# Define available encodings of byte-strings with format specification mini-language
INT_ENCODINGS = {
        'c' : (lambda s : b''.join(bytes(f'{e:c}','utf-8') for e in s)), #Character unicode (default)
        'X' : (lambda s : b''.join(bytes(f'{e:X}','utf-8') for e in s)), #Hex capitalized
        'x' : (lambda s : b''.join(bytes(f'{e:x}','utf-8') for e in s)), #Hex uncapitalized
        'd' : (lambda s : b''.join(bytes(f'{e:d}','utf-8') for e in s)), #Decimal
        'o' : (lambda s : b''.join(bytes(f'{e:o}','utf-8') for e in s)), #Octal
        'b' : (lambda s : b''.join(bytes(f'{e:b}','utf-8') for e in s)) #Binary
        }
'''
# Define available re flags
RE_FLAGS = {
        'A' :   re.ASCII,
        'I' :   re.IGNORECASE,
        'L' :   re.LOCALE,
        'M' :   re.MULTILINE,
        'S' :   re.DOTALL,
        'X' :   re.VERBOSE,
        'U' :   re.UNICODE #default, same as none
        }
'''

def returnEnvRanges(file_obj,beg_env,end_env,search_range=False):
    '''
    Iterates once through a search range 
    '''


def findEnvAndMatchRanges(f,text_patterns,formats,beg_env,end_env):
    '''
    Searches for environments (including nested ones) and returns ranges of their indices in the file.
    If any of those environments contains a match with any of the patterns in any of the formats, these ranges are returned separately so they can be deleted.
    Also returns a dictionary with some results about how many matches were made in which formats.
    '''
    
    def searchLine(line,all_patterns,match_results):
        '''
        does the search for a line in all the patterns and documents which did it
        '''
        for j,format_group in enumerate(all_patterns):
            for k,pattern in enumerate(format_group):
                if bool(pattern.search(line)):
                    match_results[formats[j]][text_patterns[k]] += 1
                    return True
        return False

    # remove duplicates
    formats = list(set(formats))
    # these are all the utf-8 and numerically encoded search patterns grouped by format
    beg_pattern = re.compile(beg_env)
    end_pattern = re.compile(end_env)
    all_patterns = [ [re.compile(INT_ENCODINGS[f](p)) for p in text_patterns] for f in formats ]
    # we can infer the format based on the index of the group of the matched element in this list

    # initialize lists of ranges to return
    matched_envs = []
    unmatched_envs = []
    # initialize dictionary to count all matches made, grouped by format
    match_results = { e : { p : 0 for p in text_patterns} for e in formats }
    # initialize search caches
    beg_env_indices = []
    end_env_indices = []
    
    for i,line in enumerate(f):
        if bool(re.search(beg_pattern,line)):
            beg_env_indices.append([i,False])
        if bool(re.search(end_pattern,line)):
            end_env_indices.append(i)
        if bool(beg_env_indices):
            is_match = searchLine(line,all_patterns,match_results)
            if is_match:
                beg_env_indices[-1][1] = is_match
        if bool(beg_env_indices) and bool(end_env_indices):
            beg_index,beg_bool = beg_env_indices.pop()
            end_index = end_env_indices.pop()
            if beg_bool:
                # in the case of a pdf
                if end_env in [b'^endobj',b'^ET']:
                    matched_envs.append(range(  
                            beg_index+1,end_index))
                else:
                    matched_envs.append(range(  
                            beg_index,end_index+1))
            else:
                if end_env in [b'^endobj',b'^ET']:
                    unmatched_envs.append(range(    
                            beg_index+1,end_index))
                else:
                    unmatched_envs.append(range(    
                            beg_index,end_index+1))
    if bool(beg_env_indices) or bool(end_env_indices):
        print('remover.py Warning: Environment beginnings and endings are mismatched: The input file may be damaged')

    return matched_envs , unmatched_envs , match_results


def findPDFMatchesBruteForce(f,text_patterns,env_matches):
    '''
    This processes the environments which weren't already matched by deleting them from the file, running pdftotext to see the difference with the original, 
    '''

    def searchDiff(diff_str,patterns,brute_results):
        '''
        Returns True if a match was found and collect data about which pattern was matched
        '''
        for i,pattern in enumerate(patterns):
            if bool(pattern.search(diff_str)):
                brute_results['c'][text_patterns[i]] += 1
                return True
        return False
    

    # initialize search items
    brute_search_matches = []
    brute_search_unmatched = []
    # initialize data collector
    brute_results = { 'c' : { e : 0  for e in text_patterns } }
    # compile re's
    patterns = [re.compile(e) for e in text_patterns]
    
    # Using pdftotext, though this may be less fast because there is more file reading and writing
    # produce original text
    og_text_path = re.sub('\.pdf','.txt',f.name)
    subprocess.run(['pdftotext',f.name,og_text_path])
    og_text = open(og_text_path,'r').read()
    # create name for temporary pdfs for doing diff
    tmp_pdf_path = filenames.fileOut(writefile='tmp_'+f.name)
    tmp_text_path = filenames.fileOut(writefile='tmp_'+og_text_path)
    
    # remove each range one by one until but restoring them
    f.seek(0)
    pdf = f.readlines()
    for rng in env_matches:
        with open(tmp_pdf_path,'wb') as g:
            g.writelines([ replacePDFTextWithSpace(e) if i in rng else e for i,e in enumerate(pdf) ])
        try:
            subprocess.run(['pdftotext',tmp_pdf_path,tmp_text_path])
            if searchDiff(b''.join([ bytes(e[1:],'utf-8')   
                    for i,e in enumerate(difflib.unified_diff(  
                    og_text,open(tmp_text_path,'r').read())) 
                    if i > 2]), patterns, brute_results):
                brute_search_matches.append(rng)
            else:
                brute_search_unmatched.append(rng)
        except:
            brute_search_unmatched.append(rng)
    os.remove(tmp_pdf_path)
    # if it doesn't write successfully, there won't be a file
    if os.path.exists(tmp_text_path):
        os.remove(tmp_text_path)

    return (brute_search_matches,brute_search_unmatched,brute_results)
    
    '''
    # Using PyPDF2: doesn't like it when deleting things: 'NumberObject' object is not subscriptable : invalid literal for int() with base 10: b'f'
    # get original text
    og_pdf = PyPDF2.PdfFileReader(f)
    og_pdf_text = ''
    for i in range(og_pdf.getNumPages()):
        og_pdf_text += og_pdf.getPage(i).extractText()

    # remove each range one by one until but restoring them
    f.seek(0)
    pdf = f.readlines()
    # create name for temporary files for doing diff
    tmp_pdf_path = filenames.fileOut(writwefile='tmp_'+f.name)
    for rng in env_matches:
        print(pdf[rng.start:rng.stop])
        mod_pdf = pdf[:]
        del mod_pdf[rng.start:rng.stop]
        with open(tmp_pdf_path,'w+b') as g:
            g.writelines(mod_pdf)
            try:
                #remove the last slice in the document
                tmp_pdf = PyPDF2.PdfFileReader(g)
                tmp_pdf_text = ''
                for i in range(tmp_pdf.getNumPages()):
                    tmp_pdf_text += tmp_pdf.getPage(i).extractText()
                diff = difflib.unified_diff(og_pdf_text,tmp_pdf_text)
                print([e for e in diff])
                if searchDiff(diff,patterns,brute_results):
                    brute_search_matched.append(rng)
                else:
                    brute_search_unmatched.append(rng)
            except Exception as e:
                print(e)
                brute_search_unmatched.append(rng)
        #os.remove(tmp_pdf_name)
    '''



def deleteTextFromPDF(args):
    '''
    This will whiteout / replace with spaces the search text.
    The default scope for whiting out is a single pdf object at a time.
    This is preferred because the object tends to be the basic unit of text
    on the page and it will DRASTICALLY speed up the brute force option 
    compared to replacing the text environments one by one.
    '''
    # get the original text patterns to search, and separately those patterns in all requested encodings
    with args.patterns as p:
        text_patterns = list(set([ e.strip() for e in p ]))
    with args.input as f:
        search_env_matches, env_matches, search_results = \
                findEnvAndMatchRanges(
                        f, text_patterns, args.format, 
                        args.beg_env, args.end_env)
        
        if args.verbose:
            print(f'Generic results: {f.name}')
            printSearchDict(search_results)
        
        all_matched_indices = set()
        [all_matched_indices.update(set(rng)) for rng in search_env_matches]
        all_unmatched_env_indices = set()
        [all_unmatched_env_indices.update(set(rng)) for rng in env_matches]

        # Create regexp to substitute matched lines with spaces
        
        if args.brute_force:
            print('Brute Force!')
            f.seek(0)
            brute_search_matches,brute_search_unmatched, brute_results =   \
                    findPDFMatchesBruteForce(f, text_patterns, env_matches)
            # add the indices of the new matches
            [all_matched_indices.update(set(rng)) for rng in brute_search_matches]
            # remove the indices of new ranges that were matched
            final_unmatched_envs = set()
            [final_unmatched_envs.update(set(rng)) for rng in brute_search_unmatched]
            all_unmatched_env_indices.intersection(final_unmatched_envs) 
        # write the final edited pdf
        with open(filenames.fileOut(writefile=args.output,ext='.pdf'),'wb') as g:
            f.seek(0)
            # omit the matched lines when writing
            for i,line in enumerate(f):
                if args.keep_nested:
                    if i in all_matched_indices and i not in all_unmatched_env_indices:
                        g.write(replacePDFTextWithSpace(line))
                elif i in all_matched_indices:
                    g.write(replacePDFTextWithSpace(line))
                else:
                    g.write(line)

        if args.show_indices:
            print(all_matched_indices)
        if args.verbose:
            if args.brute_force:
                print(f'With Brute Force: {f.name}')
                printSearchDict(brute_results)

    return    


def replacePDFTextWithSpace(line,enc='utf-8'):
    '''
    This replaces the characters in a string with an equivalent number of spaces
    '''
    p = re.compile(b'^(?P<beg>[\(<])(?P<text>.*)(?P<end>[\)>] *Tj)$')
    match = p.match(line)
    if bool(match):
        # adding b' '*len(re.findall(b'\\\\\\\\',match.group('text'))) because sometimes I've seen lines with multiple backslashes and only these lines need an extra space because otherwise the pdf displays an empty box
        return match.group('beg') + b' ' * len(re.findall(b'\\\\\\\\',match.group('text'))) + re.sub(b'.',b' ',match.group('text')) + match.group('end') + b'\n'
    else:
        return line


def deleteGeneric(args):
    '''
    Find and delete matched environments.
    If there is a matched environment which contains an unmatched nested environment, the default behavior is to delete the whole match
    '''
    with args.patterns as p:
        text_patterns = [ e.strip() for e in p ]
    with args.input as f:
        search_env_matches,env_matches,search_results = findEnvAndMatchRanges(
                f, text_patterns,  
                args.format, args.beg_env, args.end_env)

        all_matched_indices = set()
        for rng in search_env_matches:
            all_matched_indices.union(set(rng))
        all_unmatched_env_indices = set()
        for rng in env_matches:
            all_unmatched_env_indices.union(set(rng))

        with open(filenames.fileOut(writefile=args.output,ext='.pdf'),'wb') as g:
            f.seek(0)
            for i,line in enumerate(f):
                if args.keep_nested:
                    if i in all_matched_indices and i not in all_unmatched_env_indices:
                        continue
                elif i in all_matched_indices:
                    continue
                else:
                    g.write(line)
        if args.show_indices:
            print(all_matched_indices)

        if args.verbose:
            print(f'Generic results: {f.name}')
            printSearchDict(search_results)

    return


def printSearchDict(results):
    '''
    Prints the search dictionary in an easily readable format
    '''
    # formats are first level and patterns the second but I want to flip this when printing
    for pattern in results['c']:
        data = { e : results[e][pattern] for e in results.keys() }
        total = sum(data.values())
        print(f'Removed {total} times in total with format distribution {data}\n\t{pattern}\n')
    return 


def cli():
    '''
    Setup the command line interface. run 'remover.py -h' for help.
    '''

    parser = argparse.ArgumentParser(   
            prog='whiteout',
            description='''A script to remove patterns in text environments''',    
            epilog='''E.g., in LaTeX, to delete all 'center' environments with 
                the string \LaTeX, call `$remover.py generic patterns.txt 
                input.tex output.tex -b '\\begin{center}' -e '\\end{center}'` 
                where patterns.txt contains the line `\LaTeX`.''')
  
    subparsers = parser.add_subparsers(help='Available actions')
   
    # Setup the generic deleting tool
    parser_generic = subparsers.add_parser('generic',   
            help='delete ascii patterns in any file')
    parser_generic.set_defaults(func=deleteGeneric)
    
    # Setup the deleteTextFromPDF command
    parser_pdf = subparsers.add_parser(
            'pdf', 
            help='delete text patterns from a pdf, by default ascii')
    parser_pdf.set_defaults(func=deleteTextFromPDF)
    parser_pdf.add_argument(
            '-f', '--format', action='append', nargs='+', 
            choices=list(INT_ENCODINGS), default=['c'],
            help='Try deleting the search pattern in any of the integer' 
                'encodings in Python\'s \'Format Specification Mini-Language\''
                'in addition to ascii')
    parser_pdf.add_argument(
            '-F', '--all-formats', dest='format',
            action='store_const', const=list(INT_ENCODINGS),
            help='Overrides --format and tries all available formats')
    parser_pdf.add_argument(
            '-B', '--brute-force', action='store_true',    
            help='For non-ASCII text blocks in a pdf, uses pdftotext to read'
                'its contents, and removes them if they match the patterns')


    # Main arguments
    parser.add_argument(
            'patterns', type=argparse.FileType('rb'), 
            help='enter the name of path of a text file with lines to remove')
    parser.add_argument(
            'input', type=argparse.FileType('rb'),   
            help='enter the name or path of a pdf')
    parser.add_argument(
            '-o', '--output',
            help='enter the name or path to write to')
    parser.add_argument(
            '-s', '--show_indices', action='store_true',  
            help='print all of the matched indices')
    parser.add_argument(
            '-k', '--keep-nested', action='store_true',   
            help='this changes the default behavior so that nested'
                ' environments which have no matches, but are contained in a'
                ' matched environment, aren\'t removed')
    parser.add_argument('-v', '--verbose', action='store_true',   
            help='print information about the match results')

    def mybytes(string):
        return bytes(string,'utf-8')
    parser.add_argument(
            '-b', '--beg-env',
            type=mybytes, default=b'^\d+ 0 obj',
            help='string or python regexp to match the beginning of a text'
                ' block containing the main pattern')
    parser.add_argument(
            '-e', '--end-env',
            type=mybytes, default=b'^endobj',
            help='string or python regexp to match the beginning of a text'
                ' block containing the main pattern')
    
    args = parser.parse_args()

    args = filenames.getSafeArgsOutput(args,mode='wb')

    args.func(args)

    args.input.close()
    args.output.close()

    return


if __name__ == '__main__':
    cli()
    raise SystemExit()
