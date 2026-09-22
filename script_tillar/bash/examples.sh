#

# copy n rows from a source file to a new file, for testing purposes.  (e.g. 1000 rows from a 1M-row dataset)
head -n 1 "$1" > "$2" # copy header

# print count of rows any file
wc -l "$1"

watch nvidia-smi