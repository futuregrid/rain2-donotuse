#!/usr/bin/python
"""
FutureGrid Command Line Interface

Image Repository
"""
import os
import cmd
import readline
import sys
from fgShellUtils import fgShellUtils
import IRServiceProxy

class fgShellRepo(cmd.Cmd):
    
    def __init__(self):
        self.service = IRServiceProxy.IRServiceProxy()
    
    def do_repo_get(self, args):
        """Get an image or only the URI by id
           <img OR uri> <imgId> 
        """
        values=args.split(" ")                
        if (len(values)==2):
            print self.service.get(os.popen('whoami', 'r').read().strip(), values[0], values[1])
        else:
            self.help_repo_get()
            
    def help_repo_get(self):
        print  "This command get two arguments <img OR uri> <imgId>"


