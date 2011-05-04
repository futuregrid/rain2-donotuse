#!/usr/bin/python
"""
FutureGrid Command Line Interface

Rain
"""
import os
#import cmd
import readline
import sys
from futuregrid.shell import fgShellUtils
import logging
from futuregrid.utils import fgLog
from cmd2 import Cmd
from cmd2 import options
from cmd2 import make_option
import textwrap


class fgShellRain(Cmd):
    
    def __init__(self):
        #self._service = rain()
        print "Init Rain"
        
    def do_rainmove(self, args):        
        
        self.help_rainmove()
        
            
    def help_rainmove(self):
        msg = "RAIN move command: Move a node between between IaaS clouds to and from HPC. " +\
              "Available destination are: HPC, eucalyptus, nimbus\n "
        self.print_man("move <hostname> <destination>",msg)

    def do_raingroup(self, args):        
        
        self.help_raingroup()        
            
    def help_raingroup(self):
        msg = "RAIN group command: Define a group of nodes and reserve them. \n "
        self.print_man("group <hostname_list> <set_name>",msg)
        
    def do_raindeploy(self, args):        
        
        self.help_raindeploy()        
            
    def help_raindeploy(self):
        msg = "RAIN deploy command: Deploy an image in a particular set of nodes. " +\
              "The imgId refers to an image stored in the Image Repository or to the specification "+\
              "of an image that need to be generated\n "
        self.print_man("deploy <imgId> <infrastructure>",msg) 