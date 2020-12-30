#!/usr/bin/env python3

# prepare.py
# Author: Lorenzo Van Muñoz
# Last Updated Dec 29, 2020

'''
This python script is a replacement for preparePDF.sh.
It allows more flexibility in choosing which command line program
to use for the compression and decompression of pdf streams.
Optionally this could be extended to use a python library such as
PyPDF2/4 or pdfrw for the compression instead.
'''

import os
import argparse
import subprocess
from shlex import split
from multiprocessing import Pool

import .redact

PDF_PROGRAMS = {
    # a dict of free command-line utilities for editing pdfs
    # that have a compression/decompression ability
    # cpdf compresses the output most, then mutool, then qpdf, then pdftk
    'mutool'    :   {# when merging does compression by default
        'compress'  :   (lambda x, y: f'mutool clean -d {x} {y}'),
        'decompress':   (lambda x, y: f'mutool clean -z {x} {y}'),
        'merge'     :   (lambda x, y: f'mutool create -o {y} {cat_names(x)}')},
    'qpdf'      :   {# does compression by default on outputs
        'compress'  :   (lambda x, y: f'qpdf {x} {y}'),
        'decompress':   (lambda x, y: f'qpdf --stream-data=uncompress {x} {y}'),
        'merge'     :   (lambda x, y: f'qpdf --empty --pages {cat_names(x)} -- y')},
    'cpdf'      :   {# Definitely the most efficient at compressing (2x mutool)
        'compress'  :   (lambda x, y: f'cpdf -compress {x} -o {y}'),
        'decompress':   (lambda x, y: f'cpdf -decompress {x} -o {y}'),
        'merge'     :   (lambda x, y: f'cpdf -merge -squeeze {cat_names(x)} -o {y}')},
    'pdftk'     :   {# I don't think compresion really changes anything, haha
        'compress'  :   (lambda x, y: f'pdftk {x} output {y} compress'),
        'decompress':   (lambda x, y: f'pdftk {x} output {y} uncompress'),
        'merge'     :   (lambda x, y: f'pdftk {cat_names(x)} cat output {y} compress')},
    }

def cat_names(names):
    '''
    Takes in a list of strings and returns them concatenated with 
    '''
    output = ''
    for name in names:
        output += name + ' '

    return output[:-1]


def get_tmp_file_names(file_pattern):
    '''
    Predetermine all the temporary file names/folders to use while processing
    Also create those folders
    '''
    # make tmp dirs
    prefix = os.path.dirname(file_pattern)
    name   = os.path.basename(file_pattern)
    try: 
        os.mkdir(os.path.join(prefix, 'tmp_uncompressed'))
        os.mkdir(os.path.join(prefix, 'tmp_redacted'))
        os.mkdir(os.path.join(prefix, 'tmp_recompressed'))
    except FileExistsError:
        pass

    p = re.compile(rf'{name}')
    pdfs_in  = [os.path.join(prefix, e) for e in os.scandir(prefix) if p.search(e)]
    print('Matched these files for processing:')
    for e in pdfs_in:
        print(e)

    pdfs_unc = [os.path.join(prefix, 'tmp_uncompressed', os.path.basename(e)) for e in pdfs_in]
    pdfs_red = [os.path.join(prefix, 'tmp_redacted', os.path.basename(e)) for e in pdfs_in]
    pdfs_cmp = [os.path.join(prefix, 'tmp_recompressed', os.path.basename(e)) for e in pdfs_in]

    return pdfs_in, pdfs_unc, pdfs_red, pdfs_cmp


def clean_tmp_files(pdfs_unc, pdfs_red, pdfs_cmp):
    '''
    Delete all the temporary files and folders if the program succeeds
    '''
    try:
        for e in pdfs_unc:
            os.remove(e)
        for e in pdfs_red:
            os.remove(e)
        for e in pdfs_cmp:
            os.remove(e)
        os.rmdir(os.path.basename(pdfs_unc[0]))
        os.rmdir(os.path.basename(pdfs_cmp[0]))
        os.rmdir(os.path.basename(pdfs_cmp[0]))
    except OSError as e:
        print(f'OSError: {e}: not all tmp files were deleted: will continue')
        pass
    except FileNotFoundError:
        pass
    print('tmp files removed')

    return

def press_pdfs(pdfs_in, pdfs_out, method, prog):
    '''
    (De)compress all of the input pdfs
    arguments
    Handle exception if choice of mutool, qpdf, cpdf, or pdftk isn't working
    '''
    if method not in ['compress', 'decompress']:
        raise ValueError('Invalid compression choice: expected either
                \'compress\' or \'decompress\'')
    commands = [split(PDF_PROGRAMS[prog][method](e, pdfs_out[i])) 
                for i, e in enumerate(pdfs_in)]

    with Pool() as pool:
        try:
            pool.map(subprocess.run, commands)
        except subprocess.CalledProcessError as e:
            raise UserWarning(e)
        except FileNotFoundError as f:
            raise FileNotFoundError(f'{f}: Check that {prog} is installed')

    return


def merge_pdfs(pdfs_cmp, output, prog)
    '''
    Merge together all the compressed, redacted pdfs
    '''
    try:
        subprocess.run(PDF_PROGRAMS[prog]['merge'](pdfs_cmp, output))
    except subprocess.CalledProcessError as e:
        raise UserWarning(e)
    print(f'files merged and saved to {output}')
    
    return


def autoredact(args):
    '''
    Given the command-line arguments, this function orchestrates the redaction.
    '''
    pdfs_in, pdfs_unc, pdfs_red, pdfs_cmp =
        get_tmp_file_names(args.file_pattern)
    press_pdfs(pdfs_in, pdfs_unc, 'decompress', args.prog)
    # do the redaction here by calling redact with multiprocessing.Pool()
    press_pdfs(pdfs_red, pdfs_cmp, 'compress', args.prog)
    merge_pdfs(pdfs_cmp, args.output, args.prog)

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
    parser.set_defaults(func=autoredact)
    parser.add_argument(
            'prog', choices=(PDF_PROGRAMS.keys()),
            help='chose an external command-line utility to de/compress pdfs')
    parser.add_argument(
            'patterns',
            help='the path to a file whose lines are strings to remove')
    parser.add_argument(
            '-f', '--file-pattern',
            help='a regexp identifying the directory and its files to prepare'
                ' if left empty, tries all files in the directory')
    parser.add_argument(
            '-o', '--output', default='autoredact_output.pdf',
            help='a file name to write to')
            
    args = parser.parse_args()

    args.func()

    return

if __name__ == '__main__':
    cli()
    raise SystemExit()
