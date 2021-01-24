#!/usr/bin/python
import argparse
import xml.etree.ElementTree as ET
import re
import os.path as path
import sys

def parseArgs():
    parser = argparse.ArgumentParser(description='Filter XML file.')
    parser.add_argument('input_file', metavar='I', type=str,
                        help='input xml file')
    parser.add_argument('output_file', metavar='O', type=str,
                        help='output xml file')
    parser.add_argument('--keep-titles', dest='keep_titles_file', type=str,
                        help='text list with titles to keep (one title per line)',
                        default=None)
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
        self.keepTitles = []
        self.verbose = verbose

    def readKeepTitles(self, filename):
        self.printVerbose("Reading \"keep titles\" from %s" % filename)
        with open(filename, 'r') as fd:
            self.keepTitles = [line.rstrip('\n').strip().lower() for line in fd]

    def inKeepTitles(self, title):
        return title.strip().lower() in self.keepTitles

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
        title = self.getTitle(item)
        print "\nTitle:", title
        if self.inKeepTitles(title):
            print "** Matches title in keep list **"
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
            self.printVerbose("Removing <" + child.tag + " /> with <title>" + self.getTitle(child) + "</title>")

    def getTitle(self, item):
        try:
            return item.find("title").text.encode(sys.stdout.encoding, errors='replace')
        except:
            return "(unable to display title of post)"

if __name__ == '__main__':
    args = parseArgs()
    infile = args.input_file
    outfile = args.output_file
    keepTitlesFile = args.keep_titles_file
    verbose = args.verbose

    if path.isfile(outfile) and not args.force_overwrite:
        print "Output file", outfile, "already exists. Specify a different filename."
        sys.exit(1)

    driver = InteractiveRSSItemFilter(verbose)
    if keepTitlesFile:
        driver.readKeepTitles(keepTitlesFile)
    driver.run(infile, outfile)
