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
    parser.add_argument('--force-overwrite', dest='force_overwrite', action='store_const',
                        const=True, default=False,
                        help='Force overwriting the output file')
    return parser.parse_args()

class InteractiveRSSItemFilter:
    def __init__(self, verbose = False):
        self.itemsToRemove = []
        self.verbose = verbose

    def run(self, infile, outfile):
        tree = ET.parse(infile)
        root = tree.getroot()
        namespaces = self.registerNamespaces(infile)

        try:
            self.traverse(root)
        except KeyboardInterrupt:
            print "\nInterrupted. Saving progress in output file."

        self.removeItems(self.itemsToRemove)
        print "\nDone! Writing", outfile
        tree.write(outfile, encoding="UTF-8", xml_declaration=True)

    def registerNamespaces(self, infile):
        for (prefix, uri) in [ node for _, node in ET.iterparse(infile, events=['start-ns']) ]:
            self.printVerbose("Registering namespace %s with uri %s" % (prefix, uri))
            ET.register_namespace(prefix, uri)

    def printVerbose(self, text):
        if (self.verbose):
            print "verbose:", text

    def keepOrRemove(self):
        loop = True
        while loop:
            input_str = raw_input("  > y to keep, n to delete: ")
            if re.match("^[yYnN]$", input_str):
                loop = False
                return input_str == 'Y' or input_str == 'y'

    def promptToKeepPost(self, parent, item):
        print "\nTitle:", item.find("title").text
        if self.keepOrRemove():
            print "Keeping item\n"
        else:
            print "Flagging item for removal\n"
            self.itemsToRemove.append((parent, item))

    def traverse(self, elem):
        i = 0
        for child in elem:
            if child.tag == "channel":
                self.printVerbose("Found <channel> tag. Going one level deeper.")
                self.traverse(child)
            elif child.tag == "item":
                i += 1
                self.printVerbose("<item> #" + str(i))
                self.promptToKeepPost(elem, child)
            else:
                self.printVerbose("Found <" + child.tag + "> tag - keeping")

    def removeItems(self, itemsToRemove):
        for (parent, child) in itemsToRemove:
            parent.remove(child)
            self.printVerbose("Removing <" + child.tag + " /> with <title>" + child.find("title").text + "</title>")


if __name__ == '__main__':
    args = parseArgs()
    infile = args.input_file[0]
    outfile = args.output_file[0]
    verbose = args.verbose

    if path.isfile(outfile) and not args.force_overwrite:
        print "Output file", outfile, "already exists. Specify a different filename."
        sys.exit(1)

    driver = InteractiveRSSItemFilter(verbose)
    driver.run(infile, outfile)
