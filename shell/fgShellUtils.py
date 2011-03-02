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
        self._hist=[]
    
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
                    
    def help_show():
        print "Show the available context in FG Shell"        
    
    #################################
    #GET
    #################################
        
    def do_get(self, args):
        """
        Generic get command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use=="repo"):
            self.do_repo_get(args)    
        
    ################################
    #PUT
    ################################
    
    def do_put(self,args):
        """
        Generic put command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use=="repo"):
            self.do_repo_put(args)
            
    ################################
    #REMOVE
    ################################
    
    def do_remove(self,args):
        """
        Generic remove command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use=="repo"):
            self.do_repo_remove(args)
             
    ################################
    #List
    ################################
    
    def do_list(self,args):
        """
        Generic list command that changes its behaviour depending on the 
        context specified with use command.
        """
        if(self._use=="repo"):
            self.do_repo_list(args)
            
    ##########################################################################
    # HISTORY
    ##########################################################################

    def do_history(self, line):
        """Print a list of commands that have been entered."""

        print self._hist

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

    def do_save(self, arguments):
        """Save history in the $HOME/.fg/hist.txt file 
        """
        #filename = os.path.join(self.FGSHELLDIR, "jobs.txt")
        ##DEBUG("Saving tasks to %s..." % filename)
        #self.tasks.checkpoint(filename)
    
        #filename = os.path.join(self._fgshelldir, "hist.txt")
        ##DEBUG("Saving command history to %s..." % filename)
        
        #with open(filename, "a") as f:
        #    for line in self._hist:
        #        f.write(line + "\n")
        pass
    
    def do_load(self, arguments):
        """Load history from the $HOME/.fg/hist.txt file
        """
        #filename = os.path.join(self.FGSHELLDIR, "jobs.txt")
        ##DEBUG("Loading tasks from %s..." % filename)
        #if os.path.exists(filename):
        #    self.tasks.restore(filename)
        #else:
            ##WARNING("Task file does not exist.  Continuing anyway...")
        filename = os.path.join(self._fgshelldir, "hist.txt")
        
        ##DEBUG("Loading command history from %s..." % filename)
        if os.path.exists(filename):
            with open(filename, "r") as f:
                for line in f:
                    line = line.strip()
                    self._hist.append(line)
            print "--------------------"
            print filename
            print "--------------------"
#            readline.read_history_file(histfile)
            fgLog.debug(self._hist)
            

            histfile = os.path.join(os.environ["HOME"], ".fg/hist.txt")
            try:
                readline.read_history_file(histfile)
            except IOError:
                print "ERROROR ERROR HALLO"
            print "--------------------"
            print histfile
            print "--------------------"

            atexit.register(readline.write_history_file, histfile)
            
            
            #print "LOADING DONE"
        else:
            ##WARNING("History file does not exist.  Continuing anyway...")
            pass