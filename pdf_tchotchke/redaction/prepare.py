#!/usr/bin/env python3

# prepare.py
# Author: Lorenzo Van Muñoz
# Last Updated Jan 1, 2021

'''
This python script is a replacement for preparePDF.sh.
It allows more flexibility in choosing which command line program
to use for the compression and decompression of pdf streams.
Optionally this could be extended to use a python library such as
PyPDF2/4 or pdfrw for the compression instead.
'''

import os
import re
import argparse
import subprocess
from multiprocessing import Pool

from pdf_tchotchke.redaction import redact, whiteout, whiteout_re


PDF_PROGRAMS = {
    # a dict of free command-line utilities for editing pdfs
    # that have a compression/decompression ability
    # cpdf compresses the output most, then mutool, then qpdf, then pdftk
    'mutool'    :   {# when merging does compression by default
        'compress'  :   (lambda x, y: rf'mutool clean -z {x} {y}'),
        'decompress':   (lambda x, y: rf'mutool clean -d {x} {y}'),
        'merge'     :   (lambda x, y: rf'mutool merge -o {y} -O compress {x}')},
    'qpdf'      :   {# does compression by default on outputs
        'compress'  :   (lambda x, y: rf'qpdf {x} {y}'),
        'decompress':   (lambda x, y: rf'qpdf --stream-data=uncompress {x} {y}'),
        'merge'     :   (lambda x, y: rf'qpdf --empty --pages {x} -- y')},
    'cpdf'      :   {# Definitely the most efficient at compressing (2x mutool)
        'compress'  :   (lambda x, y: rf'cpdf -compress {x} -o {y}'),
        'decompress':   (lambda x, y: rf'cpdf -decompress {x} -o {y}'),
        'merge'     :   (lambda x, y: rf'cpdf -merge -squeeze {x} -o {y}')},
    'pdftk'     :   {# I don't think compresion really changes anything, haha
        'compress'  :   (lambda x, y: rf'pdftk {x} output {y} compress'),
        'decompress':   (lambda x, y: rf'pdftk {x} output {y} uncompress'),
        'merge'     :   (lambda x, y: rf'pdftk {x} cat output {y} compress')},
    }


def get_tmp_file_names(file_pattern):
    '''
    Predetermine all the temporary file names/folders to use while processing
    Also create those folders
    '''
    # make tmp dirs
    prefix = os.path.abspath(os.path.dirname(file_pattern))
    name   = os.path.basename(file_pattern)
    tmp_folders = ['tmp_uncompressed', 'tmp_redacted', 'tmp_recompressed']
    try: 
        for folder in [os.path.join(prefix, e) for e in tmp_folders]:
            os.mkdir(folder)
    except FileExistsError:
        pass
    p = re.compile(rf'{name}')
    pdfs_in  = [e.path #re.sub(r'([\(\)])', r'\\\g<1>', e.path) 
                for e in os.scandir(prefix) if p.search(e.name)]
   # print('Matched these files for processing:')
   # for e in pdfs_in:
   #     print(e)

    pdfs_unc = [os.path.join(prefix, 'tmp_uncompressed', os.path.basename(e)) for e in pdfs_in]
    pdfs_red = [os.path.join(prefix, 'tmp_redacted', os.path.basename(e)) for e in pdfs_in]
    pdfs_cmp = [os.path.join(prefix, 'tmp_recompressed', os.path.basename(e)) for e in pdfs_in]
    
    return pdfs_in, pdfs_unc, pdfs_red, pdfs_cmp


def clean_tmp_files(pdfs_unc, pdfs_red, pdfs_cmp):
    '''
    Delete all the temporary files and folders if the program succeeds
    '''
    for each in [pdfs_unc, pdfs_red, pdfs_cmp]:
        try:
            for e in each:
                os.remove(e)
        except OSError as e:
            print(f'OSError: {e}: not all tmp files were deleted: will continue')
        except FileNotFoundError:
            pass
        try:
            os.rmdir(os.path.dirname(each[0]))
        except OSError as e:
            print(f'OSError: {e}: not all tmp files were deleted: will continue')
        except FileNotFoundError:
            pass
    print('tmp files removed')

    return


def press_pdfs(pdfs_in, pdfs_out, method, prog, parallel=False):
    '''
    (De)compress all of the input pdfs
    arguments
    Handle exception if choice of mutool, qpdf, cpdf, or pdftk isn't working
    '''
    if method not in ['compress', 'decompress']:
        raise ValueError('Invalid compression choice: expected either'
                        ' \'compress\' or \'decompress\'')
    commands = [PDF_PROGRAMS[prog][method](e, pdfs_out[i]).split() 
                for i, e in enumerate(pdfs_in)]
    if parallel:
        with Pool() as pool:
            try:
                pool.map(subprocess.run, commands)
            except FileNotFoundError as f:
                raise FileNotFoundError(f'{f}: Check that {prog} is installed')
    else:
        try:
            for command in commands:
                subprocess.run(command)
        except FileNotFoundError as f:
            raise FileNotFoundError(f'{f}: Check that {prog} is installed')

    return


def merge_pdfs(pdfs_cmp, output, prog):
    '''
    Merge together all the compressed, redacted pdfs
    '''
    try:
        cat_names = (lambda names: ''.join([name+' ' for name in names])[:-1])
        #print(PDF_PROGRAMS[prog]['merge'](cat_names(pdfs_cmp), output).split())
        subprocess.run(PDF_PROGRAMS[prog]['merge'](cat_names(pdfs_cmp), output).split())
        print(f'files merged and saved to {output}')
    except subprocess.CalledProcessError as e:
        raise UserWarning(e)
    
    return


def handle_redact(args):
    '''
    This uses the internal redact api to run redaction
    accepts the paths to the patterns file, uncompressed pdf, and redacted file
    returns nothing, but prints verbose output
    '''
    patterns, file_unc, file_red = args
    print('NYI')
    pass


def handle_whiteout(args):
    '''
    This uses the internal whiteout api to run whiteout
    accepts the paths to the patterns file, uncompressed pdf, and redacted file
    returns nothing, but prints verbose output
    '''
    patterns, file_unc, file_red, brute_force, verbose, raw = args
    with open(patterns, 'rb') as p:
        with open(file_unc, 'rb') as i:
            with open(file_red, 'wb') as o:
                whiteout.deleteTextFromPDF(p, i, o, ['c', 'x', 'X'], 
                        verbose=verbose, brute_force=brute_force, raw=raw)
    return

def handle_whiteout_re(args):
    '''
    This uses the internal whiteout_re api to run whiteout_re
    accepts the paths to the patterns file, uncompressed pdf, and redacted file
    as a list
    returns nothing, but prints verbose output
    '''
    patterns, file_unc, file_red, brute_force, verbose, raw = args
    with open(patterns, 'rb') as p:
        with open(file_unc, 'rb') as i:
            with open(file_red, 'wb') as o:
                whiteout_re.whiteout_pdf_text(p, i, o, ['c', 'x', 'X'], 
                        verbose=verbose, brute_force=brute_force, raw=raw)
    return


def handle_action(action, patterns, pdfs_unc, pdfs_red, parallel=False,
        brute_force=False, verbose=False, raw=False):
    '''
    This function handles the redaction
    Arguments:
    action: a key in ACTIONS
    patterns: the path to a file containing the patterns
    pdfs_unc: a list of paths of pdfs to transform
    pdfs_red: a list of path of pdfs to write to
    '''
    if parallel:
        with Pool() as pool:
            try:
                pool.map(ACTIONS[action], 
                        [(patterns, e, pdfs_red[i], brute_force, verbose, raw) 
                            for i,e in enumerate(pdfs_unc)])
            except BaseException as e:
                print(f'Warning: {e}')
    else:
        for i,e in enumerate(pdfs_unc):
            ACTIONS[action]([patterns, e, pdfs_red[i], brute_force, verbose,
                raw])
    return


def autoredact(action, prog, patterns, file_pattern, output, parallel=False,
        brute_force= False,verbose=False, raw=False, debug=False):
    '''
    This function orchestrates the redaction.
    '''
    # obtain pdfs to redact
    pdfs_in, pdfs_unc, pdfs_red, pdfs_cmp = \
        get_tmp_file_names(file_pattern)
    press_pdfs(pdfs_in, pdfs_unc, 'decompress', prog, parallel)
    # do the redaction here by calling redact with multiprocessing.Pool()
    handle_action(action, patterns, pdfs_unc, pdfs_red, parallel, brute_force, verbose, raw)
    # wrap up pdfs
    press_pdfs(pdfs_red, pdfs_cmp, 'compress', prog, parallel)
    merge_pdfs(pdfs_cmp, output, prog)
    if not debug:
        clean_tmp_files(pdfs_unc, pdfs_red, pdfs_cmp)
    
    return


def cli():
    '''
    This defines the command line interface for prepare.py
    '''
    parser = argparse.ArgumentParser(
            prog='prepare',
            description='''A script to redact and merge pdfs in a directory''', 
            epilog='''The merge order is determined by os.listdir(), so 
                        rename/reorder to the desired result beforehand.''')
    parser.add_argument(
            'action', choices=ACTIONS.keys(),
            help='choose what to do to the pdf')
    parser.add_argument(
            'prog', choices=PDF_PROGRAMS.keys(),
            help='chose an external command-line utility to de/compress pdfs')
    parser.add_argument(
            'patterns',
            help='the path to a file whose lines are strings to remove')
    parser.add_argument(
            '-f', dest='file_pattern', default='.+\.pdf$',
            help='a regexp identifying the directory and its files to prepare'
                ' if left empty, tries all pdf files in the directory')
    parser.add_argument(
            '-o', dest='output', default='autoredact_output.pdf',
            help='a file name to write to')
    parser.add_argument(
            '-P', dest='parallel', action='store_true',
            help='Run the redaction in parallel as opposed to serially.'
                ' This will use all cores on your computer and so be careful.'
                ' This may be more error-prone too.')
    parser.add_argument(
            '-B', dest='brute_force', action='store_true',
            help='Run the redaction using pdftotext to match all readable text.'
                ' This will take longer, but most likely removes more.')
    parser.add_argument(
            '-v', dest='verbose', action='store_true',
            help='print some statistics about pattern matches')
    parser.add_argument(
            '-R', dest='raw', action='store_true',
            help='give the raw flag to pdftotext. May be faster.')
    parser.add_argument(
            '-D', dest='debug', action='store_true',
            help='Don\'t delete the temporary files')
            
    args = parser.parse_args()

    autoredact(args.action, args.prog, args.patterns, args.file_pattern,
            args.output, args.parallel, args.brute_force, args.verbose,
            args.raw, args.debug)

    return


ACTIONS = {
    'redact'    :   handle_redact,
    'whiteout'  :   handle_whiteout,
    'whiteout_re':  handle_whiteout_re
    }


if __name__ == '__main__':
    cli()
    raise SystemExit()
