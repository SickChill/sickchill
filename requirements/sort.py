import sys
import re

if not len(sys.argv) == 2:
    print('Usage: python {} requirements-file'.format(sys.argv[0]))
    sys.exit(1)

file = sys.argv[1]

print('Sorting [{}]...'.format(file))

def sort_key(val):
    comment = re.search(r'^[#!]+\s', val)
    if comment:
        return val[comment.end(0):].lower()
    return val.lower()

with open(file, 'r') as in_file:
    lines = sorted(in_file.readlines(), key=sort_key)

with open(file, 'wb') as out_file:  # use 'wb' to avoid CR-LF
    for line in lines:
        out_file.write(line)

print('Done')
