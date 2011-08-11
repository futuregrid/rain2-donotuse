#!/usr/bin/env python
"""
Class to read Image Management Client configuration
"""

__author__ = 'Javier Diaz'
__version__ = '0.1'

import os
import ConfigParser
import string
import sys

configFileName = "config"

class IMClientConf(object):

    ############################################################
    # init
    ############################################################

    def __init__(self):
        super(IMClientConf, self).__init__()

 
        self._fgpath = ""
        try:
            self._fgpath = os.environ['FG_PATH']
        except KeyError:
            self._fgpath = os.path.dirname(__file__) + "/../../"

        ##DEFAULT VALUES##
        self._localpath = "~/.fg/"

        self._configfile = os.path.expanduser(self._localpath) + "/" + configFileName
        #print self._configfile
        if not os.path.isfile(self._configfile):
            self._configfile = os.path.expanduser(self._fgpath) + "/etc/" + configFileName
            #print self._configfile
            if not os.path.isfile(self._configfile):
                self._configfile = os.path.expanduser(os.path.dirname(__file__)) + "/" + configFileName
                #print self._configfile

                if not os.path.isfile(self._configfile):   
                    print "ERROR: configuration file not found"
                    sys.exit(1)

        #image generation
        self._serverdir = ""
        self._serveraddr = ""
        self._user=""

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
        self._config.read(self._configfile)

    ############################################################
    # getConfigFile
    ############################################################
    def getConfigFile(self):
        return self._configfile
    
    #Image Generation
    def getServerdir(self):
        return self._serverdir
    def getServeraddr(self):
        return self._serveraddr
    def getUser(self):
        return self._user

    #Image deployment
    def getXcatPort(self):
        return self._xcat_port
    def getMoabPort(self):
        return self._moab_port
    def getHttpServer(self):
        return self._http_server            
    def getTempDir(self):
        return self._tempdir

    #Machines information
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
        
        section="Generation"
        try:
            self._serverdir = os.path.expanduser(self._config.get(section, 'serverdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No serverdir option found in section "+section
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)
        #Server address
        try:
            self._serveraddr = self._config.get(section, 'serveraddr', 0)
        except ConfigParser.NoOptionError:
            print "Error: No serveraddr option found in section "+section
            sys.exit(1)
        
        try:
            self._user = os.path.expanduser(self._config.get(section, 'user', 0))
        except ConfigParser.NoOptionError:
            print "Error: No user option found in section "+section
            sys.exit(1)
      

    ############################################################
    # load_deployConfig
    ############################################################
    def load_deployConfig(self):
        
        section = "Deploy"        
        try:
            self._xcat_port = int(self._config.get(section, 'xcat_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No xcat_port option found in section "+section
            sys.exit(1)  
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)      
        try:
            self._moab_port = int(self._config.get(section, 'moab_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No moab_port option found in section "+section
            sys.exit(1)         
        try:
            self._http_server = self._config.get(section, 'http_server', 0)
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section "+section
            sys.exit(1)
        try:
            self._tempdir = os.path.expanduser(self._config.get(section, 'tempdir', 0))
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
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)      
        try:
            self._loginmachine = self._config.get(machine, 'loginmachine', 0)
        except ConfigParser.NoOptionError:
            print "Error: No loginmachine option found in section " + machine
            sys.exit(1)         
        try:
            self._moabmachine = self._config.get(machine, 'moabmachine', 0)
        except ConfigParser.NoOptionError:
            print "Error: No moabmachine option found in section " + machine
            sys.exit(1)
        try:
            self._xcatmachine = self._config.get(machine, 'xcatmachine', 0)
        except ConfigParser.NoOptionError:
            print "Error: No xcatmachine option found in section " + machine
            sys.exit(1) 

