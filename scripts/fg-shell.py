#! /usr/bin/env python
"""
FutureGrid Command Line Interface

Some code has been taken from Cyberade CoG kit shell (http://cogkit.svn.sourceforge.net/viewvc/cogkit/trunk)
"""

import sys
import os
import getopt

sys.path.append(os.getcwd())

from futuregrid.shell import fgCLI

def usage():
    """Prints the usage description.
    
    Intended to be invoked when an invalid option is encountered on the command
    line."""

    print "DESCRIPTION"
    print
    print "  The fg shell is a simple command line like shell that"
    print "  assists in running small numbers of jobs in an interactive"
    print "  or script fashion on FutureGrid."
    print
    print "EXAMPLES"
    print
    print "  > fg"
    print
    print "    starts the fg shell in interactive mode"
    print
    print "  > cat file | fg"
    print
    print "    pipes the lines in the file to the cog shell and terminates"
    print
    print "  > fg -f file"
    print
    print "    reads the lines of the files, runs them and terminates"
    print
    print "  > fg -f file -i"
    print "         executes all lines in file and switches to the interactive mode"
    print


def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], #IGNORE:W0612
                                   "hqif:",
                                   ["help", "quiet", "interactive", "file="])
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)

    script_file = None
    quiet = None
    interactive = None
    for option, argument in opts:
        if option in ("-h", "--help"):
            usage()
            sys.exit()
        if option in ("-f", "--file"):
            script_file = argument
        if option in ("-q", "--quiet"):
            quiet = True
        if option in ("-i", "--interactive"):
            interactive = True

    fgCLI.runCLI(script_file, quiet, interactive)

if __name__ == "__main__":
    main()