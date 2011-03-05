#! /usr/bin/env python
"""
FutureGrid Command Line Interface

Some code has been taken from Cyberade CoG kit shell (http://cogkit.svn.sourceforge.net/viewvc/cogkit/trunk)
"""

import os
import cmd
import readline
import atexit
import sys

class fgShellUtils(cmd.Cmd):
    
    
    def __init__(self):
        
        self._script=False
        self._scriptList=[]
        self._scriptFile=self._conf.getScriptFile()
    
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
    
    ####################
    #SCRIPT
    #################
    def do_script(self,arg):
        args=self.getArgs(arg)
        if not self._script:
            self._scriptList=[]
            if(len(args)==0):  #default file NO force
                if not (os.path.isfile(self._scriptFile)):
                    print "Script module activated"
                    self._script=True                    
                else:
                    print "File "+self._scriptFile+" exists. Use argument force to overwrite it"
            elif(len(args)==1):
                if(args[0]=="end"):
                    print "Script is not active."
                elif(args[0]=="force"):  ##default file force
                    print "Script module activated "
                    self._script=True                    
                else:    #custom file NO force
                    print "Script module activated"
                    self._scriptFile=os.path.expanduser(args[0])
                    if not (os.path.isfile(self._scriptFile)):                        
                        self._script=True                        
                    else:
                        print "File "+self._scriptFile+" exists. Use argument force to overwrite it"                    
            elif(len(args)==2):  ##custom file and maybe force
                if (args[0]=="force"):
                    print "Script module activated"
                    self._scriptFile=os.path.expanduser(args[1])                    
                    self._script=True                    
                if (args[1]=="force"):
                    print "Script module activated"
                    self._scriptFile=os.path.expanduser(args[0])                    
                    self._script=True                    
            else:
                self.help_script()
        elif(len(args)==1):
            if(args[0]=="end"):
                print "Ending Script module and storing..."
                self._script=False
                with open(self._scriptFile, "w") as f:
                    for line in self._scriptList:
                        f.write(line + "\n")
            else:
                print "Script is activated. To finish it use: script end"
        else:
            print "Script is activated. To finish it use: script end"
            
    def help_script(self):
        print "When Script is active, all commands executed are stored in a file \n" +\
              "    Activate it by executing: script <file> or just script to use the default file (`pwd`/script)\n" +\
              "    To finish and store the commands use: script end"
            
    #################################
    #GET
    #################################
        
    def do_get(self, args):    
        """
        Generic get command that changes its behaviour depending on the 
        context specified with the use command.
        """    
        if(self._use!=""):            
            command="self.do_"+self._use+"get(\""+args+"\")"
            print command
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a get method "
                self._log.error(str(sys.exc_info()))
        else:
            print "You need to provide a Context executing the use <context> \n"+ \
                  "You can see the available Contexts by executing show "
    
    #################################
    #MODIFY
    #################################
        
    def do_modify(self, args):
        """
        Generic get command that changes its behaviour depending on the 
        context specified with the use command.
        """
        if(self._use!=""):            
            command="self.do_"+self._use+"modify(\""+args+"\")"
            print command
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a modify method "
                self._log.error(str(sys.exc_info()))
        else:
            print "You need to provide a Context executing the use <context> \n"+ \
                  "You can see the available Contexts by executing show " 
    
    #################################
    #Set permission
    #################################
        
    def do_setpermission(self, args):
        """
        Generic setpermission command that changes its behaviour depending on the 
        context specified with the use command.
        """
        if(self._use!=""):            
            command="self.do_"+self._use+"setpermission(\""+args+"\")"
            print command
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a setpermission method "
                self._log.error(str(sys.exc_info()))
        else:
            print "You need to provide a Context executing the use <context> \n"+ \
                  "You can see the available Contexts by executing show "
               
    ################################
    #PUT
    ################################
    
    def do_put(self,args):
        """
        Generic put command that changes its behaviour depending on the 
        context specified with the use command.
        """
        if(self._use!=""):
            command="self.do_"+self._use+"put(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a put method"
                self._log.error(str(sys.exc_info()))
        else:
            print "You need to provide a Context executing the use <context> \n"+ \
                  "You can see the available Contexts by executing show "
            
    ################################
    #REMOVE
    ################################
    
    def do_remove(self,args):
        """
        Generic remove command that changes its behaviour depending on the 
        context specified with the use command.
        """        
        if(self._use!=""):
            command="self.do_"+self._use+"remove(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a remove method"
                self._log.error(str(sys.exc_info()))
        else:
            print "You need to provide a Context executing the use <context> \n"+ \
                  "You can see the available Contexts by executing show "
    
    def do_prueba(self,args):
        """Prueba Help"""
        pass         
    ################################
    #List
    ################################
    
    def do_list(self,args):
        """
        Generic list command that changes its behaviour depending on the 
        context specified with the use command.
        """
        if(self._use!=""):
            command="self.do_"+self._use+"list(\""+args+"\")"
            try:
                eval(command)
            except AttributeError:
                print "The "+self._use+" context does not have a list method"
                self._log.error(str(sys.exc_info()))
        else:
            print "You need to provide a Context executing the use <context> \n"+ \
                  "You can see the available Contexts by executing show "
            
    ##########################################################################
    # HISTORY
    ##########################################################################

    def do_history(self, line):
        """Print a list of commands that have been entered."""
        hist=[]
        for i in range(readline.get_current_history_length()):
            hist.append(readline.get_history_item(i+1))
        print hist
    do_hist = do_history
    
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
    
    def loadhist(self, arguments):
        """Load history from the $HOME/.fg/hist.txt file
        """
        histfile=self._conf.getHistFile()
        
        try:
            readline.read_history_file(histfile)
        except IOError:
            print "error"
            pass

        atexit.register(readline.write_history_file, histfile)
            
            
        