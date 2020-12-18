#!/usr/bin/env python3

# filenames.py
# This module has some simple file I/O functions for UNIX systems 
# It is a wrapper for the builtin os module to make file reading/writing
# easy and reliable

# Features safe writing to file by modifying file name,
# verifies readability/writability for requested paths,
# it only does not accept an empty filename or non-extant
# files to read.
# Also integrates the filename acquisition process with
# external modules to do functions on files

import os

def checkExists(filename):
    '''
    Checks for the existence of a filename or path likely to be used as input

    Arguments:
        String : a filename or path

    Returns:
        Boolean : True if it is nonempty and exists, else False
    '''
    
    # Sanity check and also a helpful error message
    if not isinstance(filename, str) or not filename:
        raise ValueError("The input is not a string or is empty")
    # Parse the input to get the full absolute path
    return os.path.exists(filename)


def appendExt(filename,ext=""):
    '''
    Appends an extension to a filename if not already present

    Arguments:
        String : a filename
        String : a file extension

    Returns:
        String : a filename having the extension
    '''

    if bool(ext):
        # check that it is an extension, otherwise you can't write to file
        if not (ext[0] == "." and ext[1:].isalpha()):
            raise ValueError("file extension must begin with period and be followed by alphabetical characters")
        elif not (ext in filename):
            filename += ext

    return filename


def getSafePath(takenname):
    '''
    Creates a file name in the current directory which won't overwrite any existing files.

    Arguments:
        String : the filename that is already taken by another file

    Returns:
        String : a new filename that can be written to
    '''
    
    # A safe name to not overwrite any files
    # Separate the filename from the leftmost period which marks the extension
    path_components = takenname.split(".",1)
    safepath = path_components[0]
    if len(path_components) <= 1:
        ext = ""
    else:
        ext = "." + path_components[1] 
    # add _(#) to the end of file name
    count = 0
    while os.path.exists(safepath + ext):
        safepath = path_components[0] + f"_({count})"
        count += 1
    safepath += ext
    print(f"UserWarning: {takenname} is already taken: Saving to {safepath} instead")
    # Check for write permissions in write dir for backups
    if not os.access(os.path.dirname(safepath),os.W_OK):
        raise PermissionError(f"{os.path.dirname(safepath)} is not a writable directory")

    return safepath


def readSafe(filename):
    '''
    Checks that a filename exists, checks read permissions, and returns filename if successful

    Arguments:
        String : a filename to read in

    Returns:
        String : the verified filename to read in with absolute path
    '''

    # Return the absolute file path only if it exists
    if checkExists(filename):
        return os.path.abspath(filename)
    else:
        raise FileNotFoundError(f"\"{filename}\" is not a valid file name or does not exist")


def writeSafe(filename):
    '''
    Checks that a filename is safe to write to, or supplies one

    Arguments:
        String : a filename to write to

    Returns:
        String : a safe filename to write to with absolute path
    '''

    # Retrieve absolute paths (works for all potential filenames)
    filename = os.path.abspath(filename) 
    # If output file name already exists, choose a backup so as not to overwrite
    if checkExists(filename):
        filename = getSafePath(filename)
    # Check for write permissions in output directory
    elif not os.access((os.path.dirname(filename)),os.W_OK):
        raise PermissionError(f"{os.path.dirname(filename)} is not a writable directory")

    return filename


def fileIn(readfile="",ext=""):
        '''
        This function interactively asks for an input file name and does some sanity checks.
        
        Arguments:
            String : (optional) an input filename to check and which will prevent the program from interactions
            String : (optional) a file extension (so the programmer can be lazy)
            
        Returns:
            String : output_file_path : this is an absolute path as this may be helpful
        '''

        # when being automated (a nontrivial filename requested) nobody is asked for input
        filename = readfile
        # Ask person for filename (if in current directory) or filepath
        if not bool(filename):
            filename = input("Enter name of or path to the file to read > ")
        # Check the filename and return the absolute path
        return readSafe(appendExt(filename,ext))


def fileOut(writefile="",ext=""):
    '''
    This function interactively asks for an output file name and does some sanity checks.
    
    Arguments:
        String : (optional) a file name to check automatically which will suppress interactions
        String: (optional) a file extension (this is appended to the output file if not present already)

    Returns:
        String: output_file_path : is an absolute path as this may be helpful
    '''

    filename = writefile
    # Ask person for output file name if not automated
    if not bool(filename):
        filename = input("Enter name of or path to the file to write > ")
    # validate and return path while appending extension
    return writeSafe(appendExt(filename,ext))

def fileIO(readfile="",writefile="",readext="",writeext=""):
    '''
    This function interactively asks for an input file name, an output file name, and does some sanity checks.
    It comes with several optional arguments, allowing it simply to check for the validity of given file names instead of asking for new ones.
    
    Arguments:
        String : a filename that will be read from (optional)
        String : a filename that will be written to (optional)
        String : a file extension (optional) (this is appended to the output file if not present already)
        Note that the ext argument is used when writefile is specified. This behavior can be changed

    Returns:
        Tuple of strings: (input_file_path,output_file_path) : these are absolute paths as this may be helpful
    '''

    return (fileIn(readfile,readext),fileOut(writefile,writeext))


def fileOperate(function,newlines=False,readfile="",writefile="",readext="",writeext="",*args,**kwargs):
    '''
    Accepts a function and input/output files, and applies the function to the input, writing the results to the output
    
    Arguments:
        Function : This is the function which will do something to the data file
        *args : positional arguments to Function
        **kwargs : keyword arguments to Function
        Boolean : True if newlines should be passed in the data to function, False if not
        String : filename to read to
        String : filename to write to
        String : extension for the input file
        String : extension for the output file

    Returns:
        None, though it will write a new file according to "writefile"
    '''

    readfile,writefile = fileIO(readfile,writefile,readext,writeext)
    
    with open(readfile,"r") as f:
        data = f.readlines()
    if not newlines:
        data = [e.rstrip() for e in data]

    output = function(data,*args,**kwargs)
    assert type(output) == list

    with open(writefile,"w") as g:
        for e in output:
            g.write(e)

    return


# Begin module test
if __name__ == "__main__":
    print(fileIO(readfile="log",writefile="log",readext=".txt",writeext=".txt"))
    fileOperate(lambda x:["testing" + e for e in x],newlines=True)
    # Test 4 possibilities:
    # read in file that exists
    # try to read in file that does not exist
    # try to write to a new file
    # try to overwrite an existing file
    # Test extra things
    # give all sorts of funny paths for it to figure out
    # try with and without extension and input path features
    # make sure
    raise SystemExit
