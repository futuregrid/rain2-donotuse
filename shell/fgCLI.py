#!/usr/bin/python
"""
FutureGrid Command Line Interface

A great portion of this code has been taken from Cyberaide CoG kit shell 
(http://cogkit.svn.sourceforge.net/viewvc/cogkit/trunk)
cyberaide.org, cogkit.org

We have also use source code from the python library cmd 
"""

import os
import cmd
import readline
import sys
from futuregrid.shell.fgShellUtils import fgShellUtils
from futuregrid.shell.fgShellRepo import fgShellRepo
from futuregrid.shell.fgShellHadoop import fgShellHadoop
from futuregrid.shell.fgShellConf import fgShellConf
import logging

from futuregrid.utils.fgLog import fgLog
from cmd2 import Cmd

class fgShell(fgShellUtils,
              Cmd,               
              fgShellRepo, fgShellHadoop):
    
    def __init__(self, silent=False):
        
        self._locals={}
        self._globals={}
        
        #Load Config
        self._conf=fgShellConf()                
        #Setup log  
        self._log=fgLog(self._conf.getLogFile(),self._conf.getLogLevel(),"FGShell", True)
        
        Cmd.__init__(self) 
        fgShellUtils.__init__(self)
        
        
        #Context        
        self.env=["repo","rain","hadoop",""]
        self.text={'repo':'Image Repository', 'rain':'Dynamic Provisioning', 'hadoop':'Apache Hadoop'}
        self._use=""
        self._contextOn=[] # initialized contexts
        
        #Help
        self._docHelp=[]
        self._undocHelp=[]
        self._specdocHelp=[]
        self.getDocUndoc("")
        
        self.prompt = "fg> "
        self.silent = silent
        if self.silent:
            self.intro = ""
        else:
            #self.intro = "\nWelcome to the FutureGrid Shell\n" +\
            #             "-------------------------------\n"
            self.intro=self.loadBanner(self._conf.getBanner())    
        ##Load History
        self.loadhist("no argument needed")
    
    ################################
    # USE
    ###############################
    def do_use(self,arg):
        
        if (arg in self.env and self._use!=arg):
            
            requirements=[]
            self._use=arg
            
            if self._use == "":
                welcomestr="\nChanging to default context"
            else:
                welcomestr="\nChanging to "+self._use+" context"
                
            print welcomestr
            dashstr=""
            for i in range(len(welcomestr)):
                dashstr+="-"
            print dashstr
                               
            self.getDocUndoc(arg)
            
            if (arg=="repo"):
                requirements=["Repo"]
            elif (arg=="hadoop"):
                requirements=["Hadoop"]
            #elif (arg=="rain"):
            #    requirements=["Repo","Gene","Rain"] #rain context requires initialize repo and generation             
            
            for i in requirements:
                if not i in self._contextOn: 
                    try:
                        eval("fgShell"+i+".__init__(self)")
                        self._contextOn.append(i)
                    except AttributeError:
                        print "The "+self._use+" context may not be initialized correctly"
                        self._log.error(str(sys.exc_info()))
            
            temp="" 
            if not (arg==""):
                temp="-"                             
            self.prompt = "fg"+temp+""+arg+">"
            
    def help_use(self):
        print "Change Context to a particular FG component"
        print "To see the available contexts use the contexts command"
    
    ############################
    #CONTEXTS
    ############################
    
    def do_contexts(self,argument):        
        print "FG Contexts:"
        print "-------------"           
        for i in self.env:
            print i       
                    
    def help_contexts(self):
        print "Show the available context in FG Shell"
            
    ##########################################################################
    # HISTORY
    ##########################################################################

    def do_history(self, line):
        """Print a list of commands that have been entered."""
        hist=[]
        for i in range(readline.get_current_history_length()):
            hist.append(readline.get_history_item(i+1))
        print hist
    do_hi=do_hist = do_history
    
    def do_historysession(self, line):
        """Print a list of commands that have been entered in the current session"""
        Cmd.do_history(self,line)
    
    do_his=do_hists = do_historysession
    
    ###########################
    #HELP 
    ###########################
    def complete_help(self, *args):
        #pass        
        listcmd=set(i for i in self._docHelp if i.startswith(args[0]))        
        return list(listcmd)
    
    def getDocUndoc(self,args):
        base_cmds=['exec','exit','help','history','quit','use','contexts','script']
        base_cmd2=['cmdenvironment','edit','li','load', 'pause','py','run','save','shell', 'shortcuts','set','show','historysession']
        base_cmds+=base_cmd2
        final_doc=[]
        final_undoc=[]
        spec_doc=[]
        names=dir(self.__class__)
        help = {}
        cmds_doc=[]
        cmds_undoc=[]
        use_doc=[]
        use_undoc=[]
        for name in names:
            if name[:5] == 'help_':
                help[name[5:]]=1
        names.sort()
        prevname = ''
        for name in names:
            if name[:3] == 'do_':
                if name == prevname:
                    continue
                prevname = name
                com=name[3:]
                if (args==""):
                    showit=True                    
                    for i in self.env:
                        if(i!="" and com.startswith(i)):
                            showit=False
                    if (showit):
                        if com in help:
                            cmds_doc.append(com)
                            del help[com]
                        elif getattr(self, name).__doc__:
                            cmds_doc.append(com)
                        else:
                            cmds_undoc.append(com)
                else:
                    if(com.startswith(args.strip())):
                        if com in help:
                            use_doc.append(com)
                            del help[com]
                        elif getattr(self, name).__doc__:
                            use_doc.append(com)
                        else:
                            use_undoc.append(com)
                    else:    
                        if com in help:
                            cmds_doc.append(com)
                            del help[com]
                        elif getattr(self, name).__doc__:
                            cmds_doc.append(com)
                        else:
                            cmds_undoc.append(com)
        for i in base_cmds:            
            if (i in cmds_doc):
                final_doc.append(i)
            elif (i in cmds_undoc):
                final_undoc.append(i)
        
        final_doc.sort()
        final_undoc.sort()

        if (args!=""):
                               
            for i in use_doc:
                if i[len(args.strip()):] in cmds_doc:
                    #final_doc.append(i[len(self._use):])
                    spec_doc.append(i[len(args.strip()):])
                elif i[len(args.strip()):] in cmds_undoc:
                    final_undoc.append(i[len(args.strip()):])
                else:
                    #final_doc.append(i)
                    spec_doc.append(i)
                    
            for i in use_undoc:
                if i[len(args.strip()):] in cmds_undoc:
                    final_undoc.append(i[len(args.strip()):])
                else:
                    final_undoc.append(i)             
        
            self._specdocHelp=spec_doc
        self._docHelp=final_doc
        self._undocHelp=final_undoc
    
    def do_print_man (self, args):
        "Print all manual pages organized by contexts"
        print "######################################################################"
        print "Generic commands (available in any context)\n"
        print "######################################################################"
        for i in self._docHelp:
            print "-------------------------------------------------------"
            print i
            print "-------------------------------------------------------"
            try:
                func = getattr(self, 'help_'+i)
                func()                
            except AttributeError:
                try:
                    doc=getattr(self, 'do_'+i).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))                      
                except AttributeError:
                    pass                    
                  
        for context in self.env:
            if (context != ""):
                print "######################################################################"
                print "\nSpecific Commands for the context: "+context
                print "######################################################################" 
                                     
                self.getDocUndoc(context)
                for i in self._specdocHelp:
                    #print "-------------------------------------------------------"
                    #print i
                    #print "-------------------------------------------------------"
                     
                    if (i.strip().startswith(context)):
                        i=i[len(context):]                                                
                    try:
                        func = getattr(self, 'help_'+context+i)
                        func()                
                    except AttributeError:
                        try:
                            doc=getattr(self, 'do_'+context+i).__doc__
                            if doc:
                                self.stdout.write("%s\n"%str(doc))                      
                        except AttributeError:
                            pass
                    print "\n"


    def do_help(self, args):
        """Get help on commands
        'help' or '?' with no arguments prints a list of commands for which help is available
        'help <command>' or '? <command>' gives help on <command>
        """
        allspec=[]
        if (args.strip()==""):
            print "\nA complete manual can be found in https://portal.futuregrid.org/man/fg-shell\n"
        ## The only reason to define this method is for the help text in the doc string
        if (self._use==""):
            #cmd.Cmd.do_help(self, args)
            self.customHelpNoContext(args)
            if (args.strip()==""):
                for i in self.env:
                    if i!="":
                        self.getDocUndoc(i)                
                        specdoc_header=self.text[i]+" commands. Execute \"use "+i+"\" to use them. (type help <topic>):"
                        cmd.Cmd.print_topics(self, specdoc_header, self._specdocHelp, 15, 80)                
                        allspec.extend(self._specdocHelp)
                self._specdocHelp= allspec
                print "Please select a CONTEXT by executing use <context_name>\n"+\
                      "Execute \'contexts\' command to see the available context names \n"
        else:
            self.customHelp(args)
            
    def customHelpNoContext(self,args):
        if args:
            try:
                func = getattr(self, 'help_'+self._use + args)                
            except AttributeError:
                try:
                    doc=getattr(self, 'do_'+self._use + args).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n"%str(self.nohelp % (args,)))
                return
            func()  
        else:
            self.getDocUndoc("")
                        
            doc_header="Generic Documented commands (type help <topic>):"
            undoc_header="Generic Undocumented commands (type help <topic>):"
            
            cmd.Cmd.print_topics(self, doc_header, self._docHelp, 15, 80)
            #cmd.Cmd.print_topics(self,cmd.Cmd.misc_header, help.keys(), 15,80)
            cmd.Cmd.print_topics(self, undoc_header, self._undocHelp, 15, 80)           
             
            
    def customHelp(self,args):
        if args:            
            if (args.strip().startswith(self._use)):
                args=args[len(self._use):]
            try:
                func = getattr(self, 'help_'+self._use + args)
            except AttributeError:                
                try:
                    doc=getattr(self, 'do_'+self._use + args).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n"%str(self.nohelp % (args,)))
                return
            func()  
        else:      
            self.getDocUndoc(self._use)
            
            doc_header="General documented commands in the "+self._use+" context (type help <topic>):"
            undoc_header="Undocumented commands in the "+self._use+" context (type help <topic>):"
            specdoc_header="Specific documented commands in the "+self._use+" context (type help <topic>):"
            
            cmd.Cmd.print_topics(self, doc_header, self._docHelp, 15, 80)
            cmd.Cmd.print_topics(self, specdoc_header, self._specdocHelp, 15, 80)
            #cmd.Cmd.print_topics(self,cmd.Cmd.misc_header, help.keys(), 15,80)
            cmd.Cmd.print_topics(self, undoc_header, self._undocHelp, 15, 80)
    
    ###########################
    #Command Completion
    ###########################
    def completenames(self, *args):
        listcmd=set(i for i in self._docHelp if i.startswith(args[0]))
        listcmd1=set(i for i in self._undocHelp if i.startswith(args[0]))
        listcmd2=set(i for i in self._specdocHelp if i.startswith(args[0]))
        return list(listcmd|listcmd1|listcmd2)
    
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

    #def do_quit(self, arguments):
    #    """Terminates the shell, performing various clean-up actions."""

        #DEBUG("Terminating the shell")  #CHANGE TO PYTHON LOGS
    #    self.postloop()
    #    exit(1)

    #do_q = do_exit = do_quit

    def help_EOF(self):
        """Documentation for the EOF command."""

        print "The EOF character quits the command shell."
        print "This is useful for piping in commands from a script file."
        print "Functionally, this command is no different than 'quit'."
    help_eof = help_EOF

    def help_quit(self):
        """Documentation for the quit command."""

        print "The quit command terminates the application."
    help_q = help_exit = help_quit   
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
        #print "\nExiting..."

    def precmd(self, line):
        """ This method is called after the line has been input but before
            it has been interpreted. If you want to modifdy the input line
            before execution (for example, variable substitution) do it here.
        """ 
        lastcmd=readline.get_history_item(readline.get_current_history_length())
        if(self._script and lastcmd.strip() != "script end"):
            self._scriptList += [lastcmd.strip()]
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

