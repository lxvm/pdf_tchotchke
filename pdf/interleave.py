#!/usr/bin/env python3

# interleave.py
# A script to automatic interleave lines between blocks in a text file
# Written by Lorenzo Van Muñoz
# Last Updated Dec 14 2020

import os,sys,filenames

# Start message
print("interleave.py - a script to interleave lines\n")

# Change to current working directory
os.chdir(os.getcwd())

filepath,outpath = filenames.fileio(ext=".txt")

# import file
with open(filepath,"r") as file:
    data = file.read()

# Get each line in file
lines = data.rstrip().split("\n")


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
        output.append(lines[entry_indices[int(i/2)]])
    else:
        output.append(lines[num_indices[int((i-1)/2)]])

# Write to file
with open(outpath,"w") as file:
    for line in output:
        file.write(line+"\n")

# End script
print("Lines interleaved")
sys.exit()
