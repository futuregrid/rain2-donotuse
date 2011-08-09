"""
Class to read Image Management Client configuration
"""

import os
import ConfigParser
import string
import sys

class ImageClientConf(object):

    ############################################################
    # init
    ############################################################

    def __init__(self):
        super(ImageClientConf, self).__init__()

        ###################################
        #These should be sent from the Shell. We leave it for now to have an independent tool.   
        self._fgpath = ""
        try:
            self._fgpath = os.environ['FG_PATH']
        except KeyError:
            self._fgpath = "../../"

        ##DEFAULT VALUES##
        self._loghistdir = "~/.fg/"

        tempfile = os.path.expanduser(self._loghistdir) + "/config"

        if(os.path.isfile(tempfile)):
            self._configfile = tempfile
        else:
            self._configfile = os.path.expanduser(self._fgpath) + "/etc/config"
        ####################################

        #image generation
        self._serverdir = ""
        self._serveraddr = ""

        #image deploy
        self._xcat_port = 0
        self._moab_port = 0
        self._http_server = ""
        self._tempdir = ""

        #deploy-machines        
        self._shareddir = ""
        self._loginmachine = ""
        self._moabmachine = ""
        self._xcatmachine = ""

        self._config = ConfigParser.ConfigParser()
        if(os.path.isfile(self._configfile)):
            self._config.read(self._configfile)
        else:
            print "Error: Config file not found" + self._configfile
            sys.exit(0)
            


    ############################################################
    # getConfigFile
    ############################################################
    def getConfigFile(self):
        return self._configfile
    
    #Image Generation
    ############################################################
    # getServerdir
    ############################################################
    def getServerdir(self):
        return self._serverdir
    ############################################################
    # getServeraddr
    ############################################################
    def getServeraddr(self):
        return self._serveraddr

    #Image deployment
    ############################################################
    # getXcatPort
    ############################################################
    def getXcatPort(self):
        return self._xcat_port
    ############################################################
    # getMoabPort
    ############################################################
    def getMoabPort(self):
        return self._moab_port
    ############################################################
    # getHttpServer
    ############################################################
    def getHttpServer(self):
        return self._http_server
            
    def getTempDir(self):
        return self._tempdir

    def getSharedDir(self):
        return self._shareddir
    def getLoginMachine(self):
        return self._loginmachine
    def getMoabMachine(self):
        return self._moabmachine
    def getXcatMachine(self):
        return self._xcatmachine
    
    ############################################################
    # load_generationConfig
    ############################################################
    def load_generationConfig(self):        
        
        #Server dir where the software is installed
        try:
            self._serverdir = os.path.expanduser(self._config.get('Generation', 'serverdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No serverdir option found in section Generation"
            sys.exit(0)
        #Server address
        try:
            self._serveraddr = os.path.expanduser(self._config.get('Generation', 'serveraddr', 0))
        except ConfigParser.NoOptionError:
            print "Error: No serveraddr option found in section Generation"
            sys.exit(0)
        
        try:
            self._logfile_gen = os.path.expanduser(self._config.get('Generation', 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section Generation"
            sys.exit(0)
      

    ############################################################
    # load_deployConfig
    ############################################################
    def load_deployConfig(self):
                
        try:
            self._xcat_port = int(os.path.expanduser(self._config.get('Deploy', 'xcat_port', 0)))
        except ConfigParser.NoOptionError:
            print "Error: No xcat_port option found in section Deploy"
            sys.exit(0)        
        try:
            self._moab_port = int(os.path.expanduser(self._config.get('Deploy', 'moab_port', 0)))
        except ConfigParser.NoOptionError:
            print "Error: No moab_port option found in section Deploy"
            sys.exit(0)         
        try:
            self._http_server = os.path.expanduser(self._config.get('Deploy', 'http_server', 0))
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section Deploy"
            sys.exit(0)
        try:
            self._tempdir = os.path.expanduser(self._config.get('Deploy', 'tempdir', 0))
        except ConfigParser.NoOptionError:
            self._tempdir = "./" 

    ############################################################
    # load_machineConfig
    ############################################################
    def load_machineConfig(self, machine):
                
        try:
            self._shareddir = os.path.expanduser(self._config.get(machine, 'shareddir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No shareddir option found in section " + machine
            sys.exit(0)        
        try:
            self._loginmachine = os.path.expanduser(self._config.get(machine, 'loginmachine', 0))
        except ConfigParser.NoOptionError:
            print "Error: No loginmachine option found in section " + machine
            sys.exit(0)         
        try:
            self._moabmachine = os.path.expanduser(self._config.get(machine, 'moabmachine', 0))
        except ConfigParser.NoOptionError:
            print "Error: No moabmachine option found in section " + machine
            sys.exit(0)
        try:
            self._xcatmachine = os.path.expanduser(self._config.get(machine, 'xcatmachine', 0))
        except ConfigParser.NoOptionError:
            print "Error: No xcatmachine option found in section " + machine
            sys.exit(0) 

