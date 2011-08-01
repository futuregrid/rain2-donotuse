'''@package futuregrid.utils
'''

import sys

class sysCheck():

    def __init__(self):
        self.checkPythonVersion()

    def checkPythonVersion(self):
        print "SYSTEM INFO"
        print "==========="
        if (sys.version_info < (2,7) ):
            sys.exit ("please upgreade to at least python version 2.7")
        else :
            print "Python Version: " + sys.version

