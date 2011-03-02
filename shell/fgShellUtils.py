#! /usr/bin/env python
"""
FutureGrid Command Line Interface

Some code has been taken from Cyberade CoG kit shell (http://cogkit.svn.sourceforge.net/viewvc/cogkit/trunk)
"""

import os
import cmd
import readline
import atexit

from futuregrid.utils import fgUtil
from futuregrid.utils import fgLog

class fgShellUtils(cmd.Cmd):
    
    
    def __init__(self):
        self._fgshelldir=fgUtil.getShellDir()
        self.env=["repo","rain",""]
        self._use=""
    
    def getArgs(self,args):
        """
        Convert the string args to a list of arguments
        """
        aux=args.strip()
        argsList=[]
                
        if(aux!=""):        
            values=aux.split(" ")
            for i in values:
                istriped=i.strip()
                if (istriped != ""):
                    argsList.append(istriped)            
        return argsList  
       
    ################################
    # USE
    ###############################
    def do_use(self,arg):
        
        if (arg in self.env):
            self._use=arg
            temp="" 
            if not (arg==""):
                temp="-"                       
            self.prompt = "fg"+temp+""+arg+">"
            
    def help_use(self):
        print "Change Context to a particular FG component"
        print "To see the available contexts use the show command"
    
    def do_show(self,argument):        
        print "FG Contexts:"
        print "-------------"           
        for i in self.env:
            print i       
                    
    def help_show(self):
        print "Show the available context in FG Shell"        
    
    #################################
    #GET
    #################################
        
    def do_get(self, args):
        """
        Generic get command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use!=""):
            command="self.do_"+self._use+"get(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a get method"
        else:
            print "You need to provide a Context using the use command"
        
        
    ################################
    #PUT
    ################################
    
    def do_put(self,args):
        """
        Generic put command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use!=""):
            command="self.do_"+self._use+"put(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a put method"
        else:
            print "You need to provide a Context using the use command"
            
    ################################
    #REMOVE
    ################################
    
    def do_remove(self,args):
        """
        Generic remove command that changes its behaviour depending on the 
        context specified with use command.
        """        
        if(self._use!=""):
            command="self.do_"+self._use+"remove(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a remove method"
        else:
            print "You need to provide a Context using the use command"
             
    ################################
    #List
    ################################
    
    def do_list(self,args):
        """
        Generic list command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use!=""):
            command="self.do_"+self._use+"list(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a list method"
        else:
            print "You need to provide a Context using the use command"
            
    ##########################################################################
    # HISTORY
    ##########################################################################

    def do_history(self, line):
        """Print a list of commands that have been entered."""
        hist=[]
        for i in range(readline.get_current_history_length()):
            hist.append(readline.get_history_item(i+1))
        print hist
    do_h = do_hist = do_history
    
    ##########################################################################
    # LOAD
    ##########################################################################

    def do_exec(self, script_file):
        """Runs the specified script file with the command-line interpreter.
        
        Lines from the script file are printed out with a '>' preceding them,
        for clarity."""

        if script_file.strip() == "":
            self.help_exec()
            return

        if os.path.exists(script_file):
            with open(script_file, "r") as f:
                for line in f:
                    print ">", line   # runCLI originally had "line.strip()" here.
                    self.onecmd(line)
        else:
            ##ERROR('"%s" does not exist, could not evaluate it.' % script_file) #CHANGE TO PYTHON LOG
            pass

    def help_exec(self):
        print "Runs the specified script file."
        print
        print "Syntax:"
        print "   do_exec <script_file>"
        print
        print "Lines from the script file are printed out with a '>' preceding"
        print "them, for clarity."
    
    #####################################
    # IO
    #####################################
    
    def do_load(self, arguments):
        """Load history from the $HOME/.fg/hist.txt file
        """
            
        histfile = os.path.join(os.environ["HOME"], ".fg/hist.txt")
        try:
            readline.read_history_file(histfile)
        except IOError:
            print "ERROROR ERROR HALLO"
        print "--------------------"
        print histfile
        print "--------------------"

        atexit.register(readline.write_history_file, histfile)
            
            
        