import os
import re

# file containing find/replace expressions separated by "\t-\t"
fnrExpressions = "humanrdr.txt"

# directory with the files on which to apply fnr
fnrDir = "soas-segmentation-biluo/out"

# new file prefix with following syntax _foo_
newPrefix = "_2_"

# path to dir for output / optional
outDir = ''

def getRegex(fnrExpressions):
    # extracts a list of fnr expressions from fnr.txt
    regexList = []
    with open(fnrExpressions, 'r', encoding='utf8') as fp:
        lines = fp.readlines()
    for line in lines:
        line = line.strip('\n\r')
        find, replace = line.split("\t-\t",1)
        regexList.append([find, replace])
    return regexList

def fnr(string, fnrExpressions):
    list = getRegex(fnrExpressions)
    for pair in list:
        string = re.sub(pair[0], pair[1], string)
    return string

for dname, dirs, files in os.walk(fnrDir):
    for fname in files:
        if fname[:1] != '_':
            iPath = os.path.join(dname, fname)
            oPath = os.path.join(dname, f"{newPrefix}{fname}")

            with open(iPath, 'r', encoding='utf-8') as f:
                raws = f.read()
                s = fnr(raws, fnrExpressions)
            
            with open(oPath, "w") as f:
                f.write(s)