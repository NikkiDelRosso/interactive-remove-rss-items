#!/usr/local/bin/python3
import argparse
import xml.etree.ElementTree as ET
import re
import os.path as path
import sys
try:
    from colorama import Fore, Back, Style
except:
    print("Unable to use colored output. Install colorama with `pip install colorama`")
    Fore = {
        'BLACK': "", 'RED': "", 'GREEN': "", 'YELLOW': "", 'BLUE': "", 'MAGENTA': "", 'CYAN': "", 'WHITE': "", 'RESET': ""
    }
    Back = {
        'BLACK': "", 'RED': "", 'GREEN': "", 'YELLOW': "", 'BLUE': "", 'MAGENTA': "", 'CYAN': "", 'WHITE': "", 'RESET': ""
    }
    Style = {
        'DIM': "", 'NORMAL': "", 'BRIGHT': "", 'RESET_ALL': ""
    }


def parseArgs():
    parser = argparse.ArgumentParser(description='Filter XML file.')
    parser.add_argument('input_file', metavar='INPUT_FILE', type=str,
                        help='input xml file')
    parser.add_argument('output_file', metavar='OUTPUT_FILE', type=str,
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
    parser.add_argument('--fuzzy', dest='use_fuzzy', action='store_const',
                         const=True, default=False,
                         help='Use fuzzy string matching for keep titles detection. Requires fuzzywuzzy to be installed.')
    return parser.parse_args()

class InteractiveRSSItemFilter:
    def __init__(self, verbose = False):
        self.itemsToRemove = []
        self.keepTitles = []
        self.keepTitlesLower = []
        self.verbose = verbose
        self.fuzzyEnabled = False

    def readKeepTitles(self, filename):
        self.printVerbose("Reading \"keep titles\" from %s" % filename)
        with open(filename, 'r') as fd:
            self.keepTitles = [line.rstrip('\n').strip() for line in fd]
            self.keepTitlesLower = [title.lower() for title in self.keepTitles]

    def useFuzzy(self):
        try:
            from fuzzywuzzy import fuzz
            self.fuzz = fuzz
            self.fuzzyEnabled = True
        except:
            print(Fore.RED + "Unable to uze fuzzy matching. Install fuzzywuzzy with `pip install fuzzywuzzy`" + Style.RESET_ALL)

    def checkKeepTitles(self, title):
        if self.fuzzyEnabled:
            for keepTitle in self.keepTitles:
                ratio = self.fuzz.ratio(title.strip(), keepTitle)
                if ratio >= 85:
                    print(Fore.GREEN + "** %d%% match with keep title: %s" % (ratio, keepTitle) + Style.RESET_ALL)
        else:
            if title.strip().lower() in self.keepTitlesLower:
                print(Fore.GREEN + "** Matches title in keep titles **" + Style.RESET_ALL)

    def run(self, infile, outfile):
        tree = ET.parse(infile)
        root = tree.getroot()
        namespaces = self.registerNamespaces(infile)

        try:
            self.traverse(root)
        except KeyboardInterrupt:
            print("\nInterrupted. Saving progress in output file.")

        self.removeItems(self.itemsToRemove)
        print("\nDone! Writing", outfile)
        tree.write(outfile, encoding="UTF-8", xml_declaration=True)

    def registerNamespaces(self, infile):
        for (prefix, uri) in [ node for _, node in ET.iterparse(infile, events=['start-ns']) ]:
            self.printVerbose("Registering namespace %s with uri %s" % (prefix, uri))
            ET.register_namespace(prefix, uri)

    def printVerbose(self, text):
        if (self.verbose):
            print(Style.DIM + "verbose:", text, Style.RESET_ALL)

    def keepOrRemove(self):
        loop = True
        while loop:
            input_str = input(Fore.CYAN + "  > y to keep, n to delete: " + Style.RESET_ALL)
            if re.match("^[yYnN]$", input_str):
                loop = False
                return input_str == 'Y' or input_str == 'y'

    def promptToKeepPost(self, parent, item):
        title = self.getTitle(item)
        print("\nTitle: %s" % title)
        self.checkKeepTitles(title)
        if self.keepOrRemove():
            print(Fore.GREEN + "Keeping item\n" + Style.RESET_ALL)
        else:
            print(Back.RED + Fore.WHITE + Style.BRIGHT + "Flagging item for removal" + Style.RESET_ALL + "\n")
            self.itemsToRemove.append((parent, item))

    def traverse(self, elem):
        i = 0
        for child in elem:
            if child.tag == "channel":
                self.printVerbose("Found <channel> tag. Going one level deeper.")
                self.traverse(child)
            elif child.tag == "item":
                i += 1
                self.printVerbose("<item> #%d" % i)
                self.promptToKeepPost(elem, child)
            else:
                self.printVerbose("Found <%s> tag - keeping" % (child.tag))

    def removeItems(self, itemsToRemove):
        for (parent, child) in itemsToRemove:
            parent.remove(child)
            self.printVerbose("Removing <%s /> with <title>%s</title>" % (child.tag, self.getTitle(child)))

    def getTitle(self, item):
        try:
            return item.find("title").text.encode(sys.stdout.encoding, errors='replace')
        except:
            return "(unable to display title of post)"

if __name__ == '__main__':
    args = parseArgs()

    if path.isfile(args.output_file) and not args.force_overwrite:
        print(Fore.RED + "Output file %s already exists. Specify a different filename or use --force-overwrite to override this check." % args.output_file + Fore.RESET)
        sys.exit(1)

    driver = InteractiveRSSItemFilter(verbose=args.verbose)
    if args.keep_titles_file:
        driver.readKeepTitles(args.keep_titles_file)
    if args.use_fuzzy:
        driver.useFuzzy()
    driver.run(args.input_file, args.output_file)
