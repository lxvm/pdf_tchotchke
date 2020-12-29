#!/bin/sh

# preparePDF.sh
# A script to do nice things to the PDFs in some directory
# Author: Lorenzo Van Munoz
# Last Updated: Dec 24, 2020

echo preparePDF.sh

# modify these lines to make the script be specific
# regexp for the filenames
# textual patterns to remove 
# order to merge documents
OUT_PATH=finished.pdf
PDF_PATTERN=*.pdf
DIR_PATTERN=patterns
#BEG_PATTERN=^BT
#END_PATTERN=^ET

FILE_LIST=$(ls $PDF_PATTERN)

# uncompress the pdf files first
for file in $FILE_LIST;
do 
	onefile="$(echo $file | sed -e 's/^/tmp_uncompressed_/')" ;
	# decompress the pdf
	cpdf -decompress $file -o $onefile &
	# use the ampersand: a parallel for loop drastically speeds things up
	# actually the shell is just starting a new process for each iteration
done
sleep 1s

for file in $FILE_LIST;
do 
	onefile="$(echo $file | sed -e 's/^/tmp_uncompressed_/')" ;
	twofile="$(echo $file | sed -e 's/^/tmp_removed_/')" ;
	# remove the text in $DIR_PATTERN
	remover.py pdf -F -B $DIR_PATTERN $onefile $twofile -v &
	# recompress the pdf
done
sleep 1s

for file in $FILE_LIST;
do 
	twofile="$(echo $file | sed -e 's/^/tmp_removed_/')" ;
	thrfile="$(echo $file | sed -e 's/^/final_/')" ;
	# recompress the pdf
	#cpdf -gs gs -gs-malformed-force $twofile -o $thrfile -gs-quiet;
	cpdf -compress $twofile -o $thrfile  &
	# use the ampersand: a parallel for loop drastically speeds things up
done

exit
sleep 1s

cpdf -merge $(echo $(ls | grep final)) -o $OUT_PATH

sleep 1s

rm tmp_*.pdf

cpdf -squeeze $OUT_PATH -o $OUT_PATH

# TODO

# merge the document

# squeeze the document

# add bookmarks to the document

exit
