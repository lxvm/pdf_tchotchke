#!/usr/bin/env python3

# whiteout_re.py
# Author: Lorenzo Van Muñoz
# Last Updated Jan 1, 2021
'''
A script to remove patterns in a file.
Specifically PDF files. 
It reads in a document as a byte string 
and then tries identifying the text in
various encodings.
Unlike whiteout.py, this uses re's more 
parsimoniously and it will not succeed
in nested structures
'''

import os 
import re 
import argparse

import pdftotext

from pdf_tchotchke.utils import filenames 

# Global variables
# Define available encodings of byte-strings with format specification mini-language
INT_ENCODINGS = {
        'c' : (lambda s : b''.join(bytes(f'{e:c}', 'utf-8') for e in s)), #Character unicode (default)
        'X' : (lambda s : b''.join(bytes(f'{e:X}', 'utf-8') for e in s)), #Hex capitalized
        'x' : (lambda s : b''.join(bytes(f'{e:x}', 'utf-8') for e in s)) #Hex uncapitalized
        }
# Define all escape sequences in literal strings in pdfs (table 3.2, pdf1.7ref)
ESC_SEQS = set([rb'\n', rb'\r', rb'\t', rb'\b', rb'\f', rb'\(', rb'\)', rb'\\\\', rb'\ddd'])

# Begin text manipulations
def find_env_matches(og_file, text_patterns, formats, env_pattern):
    '''
    Uses re's to find the text patterns contained in the given environment in a
    file in any of the string or integer formats
    Arguments:
    - og_file: the byte string from open(input_file,'rb').read()
    - text_patterns: a list of byte strings to match for
    - formats: an iterable (list,set) of formats defined in INT_ENCODINGS
    - env: a string to use for regexp to match the pattern. Compiled with re.S
    Returns:
    - matched_envs: a list of re.match objects matching env and a pattern
    - unmatched_envs: a list of re.match objects matching env but not patterns
    - search results: a dictionary with results about which patterns matched
    '''
    def patterns_in_str(line, all_patterns, match_results):
        '''
        Tests to see if any of the search patterns are in the string
        Arguments:
        - line: a string to search
        - all_patterns: a list of lists of compiled re's
        - match_results: a dictionary to add search results info to
        Returns:
        - Boolean: True if matched else False
        '''
        for j, format_group in enumerate(all_patterns):
            for k, pattern in enumerate(format_group):
                if bool(pattern.search(line)):
                    match_results[formats[j]][text_patterns[k]] += 1
                    return True
        return False

    # compile the environment pattern
    env_pattern = re.compile(env_pattern, re.DOTALL)
    # compile the search patterns for matching, as byte strings
    all_patterns = [[re.compile(INT_ENCODINGS[f](p)) 
                        for p in text_patterns] for f in formats ]
    # we can infer the format based on the index of the group of the matched 
    # element in this list
    # initialize lists of matches to return
    matched_envs = []
    unmatched_envs = []
    # initialize dictionary to count all matches made, grouped by format
    match_results = { e : { p : 0 for p in text_patterns} for e in formats }
    # match only text
    exists_text = re.compile(rb'[\(<].*?[\)>] *?Tj')

    for env in env_pattern.finditer(og_file):
        if not exists_text.search(og_file[env.start() : env.end()]):
            unmatched_envs.append(env)
        elif patterns_in_str(env.group(0), all_patterns, match_results):
            matched_envs.append(env)
        else:
            unmatched_envs.append(env)
    return matched_envs, unmatched_envs, match_results


def find_matches_pdftotext(f, text_patterns, envs, og_file=None, raw=False):
    '''
    This processes the environments which weren't already matched by deleting them from the file, running pdftotext to see the difference with the original, 
    Arguments:
    f: file object in read bytes mode: the pdf to whiteout
    text_patterns: a list of byte strings to whiteout
    envs: a list of re.match objects of the env_pattern to test in f
    og_file: the string that is f.read(), optional
    '''
    def patterns_removed_pdftotext(og_text, new_text, patterns, brute_results):
        '''
        Returns True if a match was found and collect data about which pattern was matched
        Arguments:
        A string of the original text 
        A string of the edited text
        patterns: a list of compiled re patterns from text_patterns (not bytes)
        brute_results: a dictionary like { 'c' : {e:0 for e in text_patterns}}
            where text_patterns are strings that were compiled into patterns
        '''
        # check to see if the new text has at least one fewer instance of the 
        # search pattern
        for i, pattern in enumerate(patterns):
            if len(pattern.findall(og_text)) > len(pattern.findall(new_text)):
                brute_results['c'][text_patterns[i]] += 1
                return True
        return False
    
    # initialize search items
    brute_search_matches = []
    brute_search_unmatched = []
    # initialize data collector
    brute_results = { 'c' : { e : 0  for e in text_patterns } }
    # compile re's as strings (for pdftotext output)
    if raw:
        # since the pdftotext raw=True flag ignores whitespace, so we do
        patterns = [re.compile(''.join(e.decode('utf-8').split())) for e in text_patterns]
    else:
        patterns = [re.compile(e.decode('utf-8')) for e in text_patterns]
    
    # Using pdftotext python library to read text
    # all manipulations are done in memory so hopefull this is quick
    # produce original text
    og_text = pdftotext.PDF(f, raw=raw)
    # get original pdf file
    if not og_file:
        f.seek(0)
        og_file = f.read()
    # remove text in each range once, one by one, checking for diffs in each page
    tmp_pdf_file = filenames.fileOut(
                    re.sub('.pdf', '_tmp_whiteout_re.pdf', f.name),
                    overwrite=True)
    exists_text = re.compile(rb'[\(<].*?[\)>] *?Tj')
    for env in envs:
        with open(tmp_pdf_file, 'w+b') as g:
            # if the object has no text, skip it
            if not exists_text.search(og_file[env.start() : env.end()]):
                brute_search_unmatched.append(env)
                continue
            g.write(whiteout_pdf_str(og_file, env))
            g.seek(0)
            try:
                tmp_text = pdftotext.PDF(g, raw=raw)
            except pdftotext.Error as e:
                print(f'Warning: pdftotext.Error: {e}')
                brute_search_unmatched.append(env)
                continue
            try:
                is_match = False
                for i, page in enumerate(og_text):
                    if patterns_removed_pdftotext(page, tmp_text[i],
                                    patterns, brute_results):
                        new_patterns = whiteout_pdf_str(og_file, env, just_match=True)
                        # for some reason, some badly constructed pdfs may lose
                        # their text, as seen by pdftotext, if certain objects
                        # are lost then this throw of the whole thing
                        # I have only seen this happen when b' ' is a new
                        # pattern. So here is an exception case
                        if b' ' in new_patterns:
                            brute_search_unmatched.append(env)
                            continue 

                        is_match = True
                        # here is where I intercept the process, call
                        # and search for those new matches in the text and
                        # delete those using re's, update the matched_env list
                        # and unmatched_env list and call this function again
                        # for the environments that remain
                        new_matches, _, new_results = find_env_matches(
                            og_file, new_patterns, ['c'], rb'\n\d+ \d+ obj.*?endobj')
                        # this includes the original one! so we include it even
                        # if it is unique
                        # yay, lists are mutable so I can edit the list I'm
                        # iterating over, which is envs. 
                        # remove the new matches from the search space at the
                        # same time as adding them to the matched results
                        [brute_search_matches.append(envs.pop(i)) 
                                for i,m in enumerate(envs) if m.__repr__() in 
                                [e.__repr__() for e in new_matches]]
                        # I would like to update the search results with this
                        # added to the pattern matched in
                        # patterns_removed_pdftotext but here is a compromise
                        brute_results['c'].update(new_results['c'])
                        break
                    else:
                        pass
                if not is_match:
                    brute_search_unmatched.append(env)
            except BaseException as e:
                print(f'Warning: {e}')

    os.remove(tmp_pdf_file)

    return (brute_search_matches, brute_search_unmatched, brute_results)


def whiteout_pdf_str(file_str, match, just_match=False):
    '''
    This replaces the characters in a string with an equivalent number of spaces
    Restricts to the span of the match
    Arguments:
    file_str: a string containing the pdf file. e.g open(...).read()
    match: an re.match object
    just_match: a boolean
    Returns:
        if just_match:
        byte_str: just the text of the match in the text env
        else:
        byte_str: file_str with substitutions 
    '''
    p = re.compile(rb'([\(<])(.*?)([\)>] *?Tj\n)')
    if just_match:
        return [m.group(2) for m in p.finditer(file_str[match.start() :match.end()])]
    # due to additional insertions required of escape strings and the
    # character index approach, the matches are removed in reverse order
    else:
        for m in reversed(list(p.finditer(file_str[match.start() : match.end()]))):
            replace = b''.join([b'\xA0' for e in m.group(2)]) \
                    + b'\xA0'*sum([len(re.findall(e, m.group(2))) for e in ESC_SEQS])
            file_str = b''.join([file_str[ :match.start()+m.start()],
                                m.group(1), replace, m.group(3),
                                file_str[match.start()+m.end()+1: ]]) 
        return file_str


def print_search_dict(results):
    '''
    Prints the search dictionary in an easily readable format
    '''
    # formats are first level and patterns the second but I want to flip this when printing
    for pattern in results['c']:
        data = {e : results[e][pattern] for e in results.keys()}
        total = sum(data.values())
        print(f'Matched {total} times in total with format distribution {data}\n\t{pattern}\n')
    return 


def reverse_sort_matches(matches):
    '''
    This take in a list of match objects and sort them in descending order by
    the value of their start attribute. Returns a sorted list of these objects.
    '''
    starts = [m.start() for m in matches]
    return [m for _,m in sorted(zip(starts, matches), reverse=True)]


# Main script
def whiteout_pdf_text(pattern_file, input_file, output_file, formats, 
        env_pattern=rb'\n\d+ \d+ obj.*?endobj', raw=False, brute_force=False, 
        verbose=False, show_matches=False):
    '''
    Find and delete matched environments.
    If there is a matched environment which contains an unmatched nested environment, the default behavior is to delete the whole match
    Arguments:
    patterns: a readable file object (the strings to remove) in string mode
    input_file: a readable file object (the document) in bytes mode
    output_file: a writeable file object (the output) in bytes mode
    formats: A list with strings in whiteout.INT_ENCODINGS.keys()
    env_pattern: the environment pattern to match
    brute_force: Boolean: whether to remove text using pdftotext
    verbose: Boolean: Print some results about deleting
    show_matches: Boolean: Show the line-numbers being deleted 
    (the bool arguments should be recast with the logging module)
    '''
    with pattern_file as p:
        text_patterns = [e.strip() for e in p]
    with input_file as f:
        og_file = f.read()
        f.seek(0)
        search_matched_envs, search_unmatched_envs, search_results = \
            find_env_matches(og_file, text_patterns, formats, env_pattern)
        if brute_force:
            print(f'Brute Force! {f.name}')
            f.seek(0)
            new_matched_envs, search_unmatched_envs, brute_results =   \
                find_matches_pdftotext(f, text_patterns, 
                                        search_unmatched_envs, og_file, raw)
            search_matched_envs += new_matched_envs

    with output_file as g:
        # whiteout replaces each matching byte with a space so indices same
        new_file = og_file
        # due to additional insertions required of escape strings and the
        # character index approach, the matches are removed in reverse order
        for m in reverse_sort_matches(search_matched_envs):
            new_file = whiteout_pdf_str(new_file, m)
        g.write(new_file)

    if show_matches:
        print('Matched ranges:')
        [print(e) for e in search_matched_envs]
        print('Unmatched ranges:')
        [print(e) for e in search_unmatched_envs]
    if verbose:
        print(f'Search results: {input_file.name}')
        print(f'{len(search_matched_envs)} matches removed')
        print_search_dict(search_results)
        if brute_force:
            print(f'Pdftotext search:')
            print_search_dict(brute_results)

    return


# begin cli arg handling to core functions
def cli():
    '''
    Setup the command line interface. run 'whiteout_re -h' for help.
    '''
    parser = argparse.ArgumentParser(   
            prog='whiteout_re',
            description='''A script to remove patterns in pdf text''')    
    # Main arguments
    parser.add_argument(
            'patterns', type=argparse.FileType('rb'), 
            help='enter the name of path of a text file with lines to remove')
    parser.add_argument(
            'input',   
            help='enter the name or path of a pdf')
    parser.add_argument(
            '-o', dest='output',
            help='enter the name or path to write to')
    parser.add_argument(
            '-f', dest='format', 
            default=set('c'), type=(lambda x: list(set(['c'] + [e for e in x]))),
            help='Delete literal or hex encodings of the search pattern.'
                ' Options \'cxX\'.')
    parser.add_argument(
            '-F', dest='format',
            action='store_const', const=list(INT_ENCODINGS.keys()),
            help='Overrides --format and tries all available formats')
    def mybytes(string):
        return bytes(string, 'utf-8')
    parser.add_argument(
            '-e', dest='env_pattern',
            type=mybytes, default=rb'\n\d+ \d+ obj.*?endobj',
            help='non-greedy (?) python regexp to match text environment.'
                ' Will be compiled with re.DOTALL flag. eg: \'beg.*?end\'')
    parser.add_argument(
            '-R', dest='raw', action='store_true',
            help='call pdftotext with the raw flag (good if no big images)')
    parser.add_argument(
            '-B', dest='brute_force', action='store_true',    
            help='For unmatched text blocks in a pdf, uses pdftotext to read'
                'its contents, and whites them out if they match the patterns')
    parser.add_argument(
            '-s', dest='show_matches', action='store_true',  
            help='print all of the match objects')
    parser.add_argument('-v', dest='verbose', action='store_true',   
            help='print information about the match results')

    
    args = parser.parse_args()

    args.input, args.output = filenames.fileIO(args.input, args.output,
            overwrite=True)
    with open(args.input,'rb') as args.input:
        with open(args.output,'wb') as args.output:
            whiteout_pdf_text(args.patterns, args.input, args.output, args.format,
                args.env_pattern, args.raw, args.brute_force, args.verbose, args.show_matches)

    return


if __name__ == '__main__':
    cli()
    raise SystemExit()
