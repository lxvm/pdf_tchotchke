# filenames.py
# This module has some simple file I/O functions for UNIX systems 

import os,re

def fileio(ext=""):
    '''
    This function interactively asks for an input file name, an output file name, and does some sanity checks.
    
    Arguments:
        String: a file extension (this is appended to the output file if not present already)

    Returns:
        Tuple of strings: (input_file_path,output_file_path)
    '''
    # This try block asks the person for the input and output file names and validates them
    try:
        # Ask person for filename (if in current directory) or filepath
        filename = input("Enter file name (if in current directory) or file path > ")
        
        # Sanity check 
        if not isinstance(filename, str) or not filename:
            raise ValueError("The input is not a string or is empty")
        # Parse the input to get the full path
        if os.path.exists(filename):
            filepath = filename
            filedir = os.path.dirname(filename)
        else:
            raise FileNotFoundError(f"\"{filename}\" is not a valid file name or does not exist")

        # Ask person for output file name
        outname = input("Enter output file name (to output to current directory) or file path > ")

        # Sanity check 
        if not isinstance(outname, str) or not outname:
            raise ValueError("The input is not a string or is empty")
        # append file extension if requested and not present in input
        if bool(ext):
            # check that it is an extension, otherwise you can't write to file
            if not bool(re.match("^.\w+",ext)):
                raise ValueError("file extension does not conform")
            if not (ext in outname):
                outname += ext
        # If output file name already exists, choose a backup so as not to overwrite
        if os.path.exists(outname):
            raise UserWarning
        # Check for write permissions in output directory
        elif not os.access((os.path.dirname(outname) or os.getcwd()),os.W_OK):
            raise PermissionError(f"{os.path.dirname(outname) or os.getcwd()} is not a writable directory")

    except UserWarning:
        # A safe name to not overwrite any files
        safename = "safe_output_0"
        while os.path.exists(safename):
            safename = (lambda x : x[:-1] + str(int(x[-1])+1))(safename)
        outname = filedir + safename + ".txt"
        print(f"UserWarning: {outname} is already taken: Saving to {outpath} instead")

    return (filepath,outname)
