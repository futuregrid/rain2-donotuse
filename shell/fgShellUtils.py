#! /usr/bin/env python
"""
FutureGrid Command Line Interface

Some code has been taken from Cyberade CoG kit shell (http://cogkit.svn.sourceforge.net/viewvc/cogkit/trunk)
"""

import os
#import cmd
import readline
import atexit
import sys
import textwrap
from cmd2 import Cmd

class fgShellUtils(Cmd):


    def __init__(self):

        self._script = False
        self._scriptList = []
        self._scriptFile = self._conf.getScriptFile()


    ############################################################

    def getArgs(self, args):
        """
        Convert the string args to a list of arguments
        """
        aux = args.strip()
        argsList = []

        if(aux != ""):
            values = aux.split(" ")
            for i in values:
                istriped = i.strip()
                if (istriped != ""):
                    argsList.append(istriped)
        return argsList

    ############################################################
    #SCRIPT
    ############################################################

    def do_script(self, arg):
        args = self.getArgs(arg)
        if not self._script:
            self._scriptList = []
            if(len(args) == 0):  #default file NO force
                if not (os.path.isfile(self._scriptFile)):
                    print "Script module activated"
                    self._script = True
                else:
                    print "File " + self._scriptFile + " exists. Use argument force to overwrite it"
            elif(len(args) == 1):
                if(args[0] == "end"):
                    print "Script is not active."
                elif(args[0] == "force"):  ##default file force
                    print "Script module activated "
                    self._script = True
                else:    #custom file NO force
                    print "Script module activated"
                    self._scriptFile = os.path.expanduser(args[0])
                    if not (os.path.isfile(self._scriptFile)):
                        self._script = True
                    else:
                        print "File " + self._scriptFile + " exists. Use argument force to overwrite it"
            elif(len(args) == 2):  ##custom file and maybe force
                if (args[0] == "force"):
                    print "Script module activated"
                    self._scriptFile = os.path.expanduser(args[1])
                    self._script = True
                if (args[1] == "force"):
                    print "Script module activated"
                    self._scriptFile = os.path.expanduser(args[0])
                    self._script = True
            else:
                self.help_script()
        elif(len(args) == 1):
            if(args[0] == "end"):
                print "Ending Script module and storing..."
                self._script = False
                with open(self._scriptFile, "w") as f:
                    for line in self._scriptList:
                        f.write(line + "\n")
            else:
                print "Script is activated. To finish it use: script end"
        else:
            print "Script is activated. To finish it use: script end"

    def help_script(self):
        message = " When Script is active, all commands executed are stored " + \
        "in a file. Activate it by executing: script [file]. If no argument is " + \
        "provided, the file will be called \'script\' and will be located in your " + \
        "current directory. To finish and store the commands use: script end"
        self.print_man("script [file]", message)

    ############################################################
    # manual
    ############################################################

    def print_man(self, name, msg):
        print "----------------------------------------------------------------------"
        print "%s" % (name)
        print "----------------------------------------------------------------------"
        man_lines = textwrap.wrap(textwrap.dedent(msg), 64)
        for line in man_lines:
            print "    %s" % (line)
        print ""

    def do_manual (self, args):
        "Print all manual pages organized by contexts"
        print "######################################################################"
        print "Generic commands (available in any context)\n"
        print "######################################################################"
        for i in self._docHelp:

            try:
                func = getattr(self, 'help_' + i)
                func()
            except AttributeError:
                try:
                    doc = getattr(self, 'do_' + i).__doc__
                    if doc:
                        print "----------------------------------------------------------------------"
                        print "%s" % (i)
                        print "----------------------------------------------------------------------"
                        self.stdout.write("%s\n" % str(doc))
                        print ""
                except AttributeError:
                    pass

        for context in self.env:
            if (context != ""):
                print "######################################################################"
                print "\nSpecific Commands for the context: " + context
                print "######################################################################"

                self.getDocUndoc(context)
                for i in self._specdocHelp:

                    if (i.strip().startswith(context)):
                        i = i[len(context):]
                    try:
                        func = getattr(self, 'help_' + context + i)
                        func()
                    except AttributeError:
                        try:
                            doc = getattr(self, 'do_' + context + i).__doc__
                            if doc:
                                print "----------------------------------------------------------------------"
                                print "%s" % (i)
                                print "----------------------------------------------------------------------"
                                self.stdout.write("%s\n" % str(doc))
                        except AttributeError:
                            pass
                    print ""

    """
    def do_manual (self, args):
        all_manpages = ['use',
               'show',
               'history',
               'historysession',
               'print_man',
               'help',
               'EOF',
               'hadooprunjob',
               'repotest',
               'repohistimg',
               'repohistuser',
               'repouseradd',
               'repouserdel',
               'repouserlist',
               'reposetuserquota',
               'reposetuserrole',
               'reposetuserstatus',
               'repolist',
               'repomodify',
               'reposetpermission',
               'repoget',
               'repoput',
               'reporemove',
               'script',
               'manual',
               'runjob',
               'get',
               'modify',
               'setpermission',
               'put',
               'remove',
               'list',
               'useradd',
               'userdel',
               'userlist',
               'setuserquota',
               'setuserrole',
               'setuserstatus',
               'histimg',
               'histuser',
               'exec']
        for manualpage in all_manpages:
            self.print_man(manualpage,manualpage)
#            eval("self.help_"+manualpage+"()")
        this_function_name = sys._getframe().f_code.co_name
        print this_function_name
    """
    def generic_error(self):
        print "    Please select a CONTEXT by executing use <context_name>.\n" + \
                  "    Execute \'contexts\' command to see the available context names. \n" + \
                  "    Help information is also different depending on the context. \n" + \
                  "    Note that this command may not be available in all CONTEXTS."

    def generic_help(self):
        msg = "Generic command that changes its behaviour depending on the CONTEXT. "
        for line in textwrap.wrap(msg, 64):
            print "    %s" % (line)
        print ""
        self.generic_error()


    #################################
    #Run JOB
    #################################    

    def do_runjob(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "runjob(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a runjob method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()

    help_runjob = generic_help

        #################################
    #Run JOB
    #################################    

    def do_runscript(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "runscript(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a runscript method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()

    help_runjob = generic_help

    #################################
    #GET
    #################################

    def do_get(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "get(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a get method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_get = generic_help

    #################################
    #MODIFY
    #################################

    def do_modify(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "modify(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a modify method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_modify = generic_help

    #################################
    #Set permission
    #################################

    def do_setpermission(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "setpermission(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a setpermission method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_setpermission = generic_help

    ################################
    #PUT
    ################################

    def do_put(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "put(\"" + args + "\")"
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a put method"
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_put = generic_help

    ################################
    #REMOVE
    ################################

    def do_remove(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "remove(\"" + args + "\")"
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a remove method"
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_remove = generic_help

    #def do_prueba(self,args):
    #    """Prueba Help"""
    #    pass         

    ################################
    #List
    ################################

    def do_list(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "list(\"" + args + "\")"
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a list method"
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_list = generic_help

    #################################
    #User Add
    #################################

    def do_useradd(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "useradd(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a useradd method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_useradd = generic_help

    #################################
    #User Del
    #################################

    def do_userdel(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "userdel(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a userdel method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_userdel = generic_help

    #################################
    #User List
    #################################

    def do_userlist(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "userlist(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a userlist method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_userlist = generic_help

    #################################
    #Set User Quota
    #################################

    def do_setuserquota(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "setuserquota(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a setuserquota method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_setuserquota = generic_help
    #################################
    #Set User Role
    #################################

    def do_setuserrole(self, args):
        if(self._use != ""):
            command = "self.do_" + self._use + "setuserrole(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a setuserrole method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_setuserrole = generic_help
    #################################
    #Set User Status
    #################################

    def do_setuserstatus(self, args):

        if(self._use != ""):
            command = "self.do_" + self._use + "setuserstatus(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a setuserstatus method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_setuserstatus = generic_help

    #################################
    #Hist img
    #################################

    def do_histimg(self, args):

        if(self._use != ""):
            command = "self.do_" + self._use + "histimg(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a histimg method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_histimg = generic_help

    #################################
    #Hist users
    #################################

    def do_histuser(self, args):

        if(self._use != ""):
            command = "self.do_" + self._use + "histuser(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a histuser method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_histuser = generic_help


    #################################
    #Move nodes
    #################################

    def do_move(self, args):

        if(self._use != ""):
            command = "self.do_" + self._use + "move(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a move method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_move = generic_help

    #################################
    #Group nodes
    #################################

    def do_group(self, args):

        if(self._use != ""):
            command = "self.do_" + self._use + "group(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a group method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_group = generic_help

    #################################
    #Deploy nodes
    #################################

    def do_deploy(self, args):

        if(self._use != ""):
            command = "self.do_" + self._use + "deploy(\"" + args + "\")"
            #print command
            try:
                eval(command)
            except AttributeError:
                print "The " + self._use + " context does not have a deploy method "
                self._log.error(str(sys.exc_info()))
        else:
            self.generic_error()
    help_deploy = generic_help

    ##########################################################################
    # LOAD
    ##########################################################################

    def do_exec(self, script_file):

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
        msg = "Runs the specified script file. Lines from the script file are " + \
        "printed out with a '>' preceding them, for clarity."
        self.print_man("exec <script_file>", msg)


    #####################################
    # IO
    #####################################

    def loadhist(self, arguments):
        """Load history from the $HOME/.fg/hist.txt file
        """
        histfile = self._conf.getHistFile()

        try:
            readline.read_history_file(histfile)
        except IOError:
            #print "error"
            pass

        atexit.register(readline.write_history_file, histfile)

    def loadBanner(self, bannerfile):
        """Load banner from a file"""
        banner = ""
        try:
            f = open(bannerfile, "r")
            output = f.readlines()
            f.close()
            for i in output:
                banner += i

        except:
            banner = "\nWelcome to the FutureGrid Shell\n" + \
                     "-------------------------------\n"
        return banner

