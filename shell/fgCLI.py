#!/usr/bin/python
"""
FutureGrid Command Line Interface

A great portion of this code has been taken from Cyberaide CoG kit shell 
(http://cogkit.svn.sourceforge.net/viewvc/cogkit/trunk)
cyberaide.org, cogkit.org
"""

import os
import cmd
import readline
import sys
from futuregrid.shell.fgShellUtils import fgShellUtils
from futuregrid.shell.fgShellRepo import fgShellRepo
import logging
from futuregrid.utils.fgConf import fgConf
from futuregrid.utils.fgLog import fgLog

class fgShell(cmd.Cmd, 
              fgShellUtils, 
              fgShellRepo):
    
    
    def __init__(self, silent=False):
        #DEBUG ("Loading Base Shell Commands")  ##CHANGE TO PYTHON LOGG      
        
        #Load Config
        self._conf=fgConf()                
        #Setup log        
        self._log=fgLog(self._conf.getLogFile(),self._conf.getLogLevel())
        
        cmd.Cmd.__init__(self) 
        fgShellUtils.__init__(self)       
        fgShellRepo.__init__(self)
        
        self.prompt = "fg> "
        self.silent = silent
        if self.silent:
            self.intro = ""
        else:
            self.intro = "Welcome to the FutureGrid Shell"
                
        ##Load History
        self.do_load("no argument needed")
        

    def do_help(self, args):
        """Get help on commands
        'help' or '?' with no arguments prints a list of commands for which help is available
        'help <command>' or '? <command>' gives help on <command>
        """
        ## The only reason to define this method is for the help text in the doc string
        cmd.Cmd.do_help(self, args)
    
       

        
    ##########################################################################
    # PYTHON AND SHELL EXECUTION
    ##########################################################################

    def default(self, line):
        """Called when the command prefix is not recognized.
        
        In that case we execute the line as Python code.
        If a unix command is used it is executed without the !.
        The unix commands are defined in a function called unix."""

        # Is the line just a comment?  If so, ignore it and do nothing.
        if line.strip().startswith("#"):
            return

        command = line.strip().split(" ", 1)[0]
        if unix(command):
            os.system(line)
        else:
            try:
                exec(line) in self._locals, self._globals
            except Exception, e:
                print e.__class__, ":", e

    ##########################################################################
    # QUIT
    ##########################################################################

    def do_EOF(self, arguments):
        """Terminates the shell when a file is piped to it.
        
        This command terminates the shell when an EOF is reached in the input
        stream that has been piped to the program."""
        print "\n"
        self.do_quit(arguments)

    def do_quit(self, arguments):
        """Terminates the shell, performing various clean-up actions."""

        #DEBUG("Terminating the shell")  #CHANGE TO PYTHON LOGS
        sys.exit(1)

    do_q = do_exit = do_quit

    def help_EOF(self):
        """Documentation for the EOF command."""

        print "The EOF character quits the command shell."
        print "This is useful for piping in commands from a script file."
        print "Functionally, this command is no different than 'quit'."

    def help_quit(self):
        """Documentation for the quit command."""

        print "The quit command terminates the application."
    

    ##############################
    #PRE and POST commands
    ##############################
    
    ## Override methods in Cmd object ##
    def preloop(self):
        """Initialization before prompting user for commands.
           Despite the claims in the Cmd documentaion, Cmd.preloop() is not a stub.
        """
        cmd.Cmd.preloop(self)   ## sets up command completion                
        self._locals  = {}      ## Initialize execution namespace for user
        self._globals = {}        

    def postloop(self):
        """Take care of any unfinished business.
           Despite the claims in the Cmd documentaion, Cmd.postloop() is not a stub.
        """
        cmd.Cmd.postloop(self)   ## Clean up command completion
        print "Exiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """
        if(self._script and line.strip() != "script end"):
            self._scriptList += [line.strip()]
        return line

    def postcmd(self, stop, line):
        """If you want to stop the console, return something that evaluates to true.
           If you want to do some post command processing, do it here.
        """        
        return stop

    def emptyline(self):    
        """Do nothing on empty input line"""
        pass

            
def runCLI(filename=None, silent=False, interactive=False):
    if filename == None:
        cli = fgShell(silent)
        cli.cmdloop()
    else:
        cli = fgShell(silent=True)
        cli.do_exec(filename)
        if interactive:
            cli.cmdloop()
             
def unix(command):
    """Only simple commands, cd is not supported."""

    return command in ("ls", "mkdir", "cp", "pwd")

                
if __name__ == '__main__':
    runCLI()

