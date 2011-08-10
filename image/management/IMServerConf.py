"""
Class to read Image Management Server configuration
"""

import os
import ConfigParser
import string
import sys
import logging

configFileName = "config_server"

class IMServerConf(object):

    ############################################################
    # init
    ############################################################

    def __init__(self):
        super(IMServerConf, self).__init__()

        ###################################
        #These should be sent from the Shell. We leave it for now to have an independent tool.   
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
        ####################################

        #image server xcat
        self._xcat_port = 0
        self._xcatNetbootImgPath = ''
        self._http_server = ""
        self._log_xcat = ""
        self._logLevel_xcat = ""

        #image server moab
        self._moab_port = 0
        self._moabInstallPath = ""
        self._log_moab = ""
        self._timeToRestartMoab = 0
        self._logLevel_moab = ""
        
        self._logLevel_default = "DEBUG"
        self._logType = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        self._config = ConfigParser.ConfigParser()
        self._config.read(self._configfile)

    ############################################################
    # getConfigFile
    ############################################################
    def getConfigFile(self):
        return self._configfile
    
    #image server xcat    
    def getXcatPort(self):
        return self._xcat_port    
    def getXcatNetbootImgPath(self):
        return self._xcatNetbootImgPath
    def getHttpServer(self):
        return self._http_server
    def getLogXcat(self):
        return self._log_xcat
    def getLogLevelXcat(self):
        return self._logLevel_xcat
    
    #image server moab    
    def getMoabPort(self):
        return self._moab_port
    def getMoabInstallPath(self):
        return self._moabInstallPath
    def getLogMoab(self):
        return self._log_moab
    def getTimeToRestartMoab(self):
        return self._timeToRestartMoab
    def getLogLevelMoab(self):
        return self._logLevel_moab
            
    
    ############################################################
    # load_deployServerXcatConfig
    ############################################################
    def load_deployServerXcatConfig(self):        
        section = "DeployServerXcat"
        try:
            self._xcat_port = int(self._config.get(section, 'xcat_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No xcat_port option found in section " + section
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)
        try:
            self._xcatNetbootImgPath = os.path.expanduser(self._config.get(section, 'xcatNetbootImgPath', 0))
        except ConfigParser.NoOptionError:
            print "Error: No xcatNetbootImgPath option found in section " + section
            sys.exit(1)
        try:
            self._http_server = self._config.get(section, 'http_server', 0)
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section " + section
            sys.exit(1)
        try:
            self._log_xcat = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section " + section
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self._logLevel_xcat = eval("logging." + tempLevel)

      

    ############################################################
    # load_deployConfig
    ############################################################
    def load_deployServerMoabConfig(self):
        section = "DeployServerMoab"
        try:
            self._moab_port = int(self._config.get(section, 'moab_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No moab_port option found in section " + section
            sys.exit(1)  
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)              
        try:
            self._moabInstallPath = os.path.expanduser(self._config.get(section, 'moabInstallPath', 0))
        except ConfigParser.NoOptionError:
            print "Error: No moabInstallPath option found in section " + section
            sys.exit(1)
        try:
            self._timeToRestartMoab = int(self._config.get(section, 'timeToRestartMoab', 0))
        except ConfigParser.NoOptionError:
            print "Error: No timeToRestartMoab option found in section " + section
            sys.exit(1) 
        try:
            self._log_moab = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section " + section
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self._logLevel_moab = eval("logging." + tempLevel)



