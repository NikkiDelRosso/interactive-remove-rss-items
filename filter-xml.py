#!/usr/bin/python
import argparse
import xml.etree.ElementTree as ET
import re
import os.path as path
import sys

def parseArgs():
    parser = argparse.ArgumentParser(description='Filter XML file.')
    parser.add_argument('input_file', metavar='I', type=str, nargs=1,
                        help='input xml file')
    parser.add_argument('output_file', metavar='O', type=str, nargs=1,
                        help='output xml file')
    parser.add_argument('--verbose', dest='verbose', action='store_const',
                        const=True, default=False,
                        help='Verbose output')
    return parser.parse_args()

def printVerbose(text):
    if (verbose):
        print "verbose:", text

def keepOrRemove():
    loop = True
    while loop:
        input_str = raw_input("  > y to keep, n to delete: ")
        if re.match("^[yYnN]$", input_str):
            loop = False
            return input_str == 'Y' or input_str == 'y'

def promptToKeepPost(parent, item):
    print "\nTitle:", item.find("title").text
    if keepOrRemove():
        print "Keeping item\n"
    else:
        print "Flagging item for removal\n"
        globalItemsToRemove.append((parent, item))

def traverse(elem):
    i = 0
    for child in elem:
        if child.tag == "channel":
            printVerbose("Found <channel> tag. Going one level deeper.")
            traverse(child)
        elif child.tag == "item":
            i += 1
            printVerbose("<item> #" + str(i))
            promptToKeepPost(elem, child)
        else:
            printVerbose("Found <" + child.tag + "> tag - keeping")

def removeItems(itemsToRemove):
    for (parent, child) in itemsToRemove:
        parent.remove(child)
        printVerbose("Removing <" + child.tag + "> with <title>" + child.find("title").text)


if __name__ == '__main__':
    globalItemsToRemove = []
    args = parseArgs()
    infile=args.input_file[0]
    outfile = args.output_file[0]

    if path.isfile(outfile):
        print "Output file", outfile, "already exists. Specify a different filename."
        sys.exit(1)

    tree = ET.parse(infile)
    root = tree.getroot()
    verbose = args.verbose

    try:
        traverse(root)
    except KeyboardInterrupt:
        print "\nInterrupted. Saving progress in output file."

    removeItems(globalItemsToRemove)
    print "\nDone! Writing", outfile
    tree.write(outfile)
