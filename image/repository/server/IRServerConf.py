#!/usr/bin/env python
"""
utility class for static methods
"""

from random import randrange
import logging
import sys, os
import ConfigParser
import string
################
#BACKEND CONFIG
################

configFileName = "fg-server.conf"

class IRServerConf(object):

    ############################################################
    # init
    ############################################################

    def __init__(self):
        super(IRServerConf, self).__init__()
        
        #we configure this log because the server is executed remotly
        
        self._log=self.setup_logger()        
        self._fgpath = ""
        try:
            self._fgpath = os.environ['FG_PATH']
        except KeyError:
            self._fgpath = os.path.dirname(__file__) + "/../../../"

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
                    self._log.error("ERROR: configuration file "+configFileName+" not found")
                    sys.exit(1)
        
        #image repo server
        self._authorizedUsers=[]
        self._backend=""
        self._log_repo=""
        self._logLevel_repo=""
        self._idp = ""
        #image repo server backends
        self._address=""
        self._userAdmin=""
        self._configFile=""
        self._addressS=""
        self._userAdminS=""
        self._configFileS=""
        self._imgStore=""
                        
        self._logLevel_default = "DEBUG"
        self._logType = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        self._config = ConfigParser.ConfigParser()
        self._config.read(self._configfile)
               
    def setup_logger(self):
        #Setup auxiliar logging to record possible errors in this class
        logger = logging.getLogger("IRServerConf")
        logger.setLevel(logging.DEBUG)    
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(os.path.expanduser(os.path.dirname(__file__))+"/IRServerConf.log")
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False #Do not propagate to others
        
        return logger
    
    def getServerConfig(self):
        return self._configfile
    def getLogRepo(self):
        return self._log_repo
    def getLogLevelRepo(self):
        return self._logLevel_repo
    
    def getAuthorizedUsers(self):
        return self._authorizedUsers    
    def getBackend(self):
        return self._backend
    def getIdp(self):
        return self._idp
    
    def getAddress(self):
        return self._address
    def getUserAdmin(self):
        return self._userAdmin
    def getConfigFile(self):
        return self._configFile
    def getAddressS(self):
        return self._addressS
    def getUserAdminS(self):
        return self._userAdminS
    def getConfigFileS(self):
        return self._configFileS
    def getImgStore(self):
        return self._imgStore
    
    ############################################################
    # loadConfig
    ############################################################
    def loadRepoServerConfig(self):
        section="RepoServer"
        try:
            aux = self._config.get(section, 'authorizedusers', 0)
            aux1=aux.split(",")
            for i in aux1:
                if (i.strip()!=""):
                    self._authorizedUsers.append(i.strip())
        except ConfigParser.NoOptionError:
            self._log.error("No authorizedusers option found in section " + section)
            sys.exit(1)  
        except ConfigParser.NoSectionError:
            self._log.error("no section "+section+" found in the "+self._configfile+" config file")
            sys.exit(1)
        try:
            self._backend = self._config.get(section, 'backend', 0)
        except ConfigParser.NoOptionError:
            self._log.error("No backend option found in section " + section)
            sys.exit(1)          
        try:
            self._idp = self._config.get(section, 'idp', 0)
        except ConfigParser.NoOptionError:
            self._log.error("No idp option found in section " + section)
            sys.exit(1)  
        except ConfigParser.NoSectionError:
            self._log.error("no section "+section+" found in the "+self._configfile+" config file")
            sys.exit(1)
        try:
            self._log_repo = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            self._log.error("No log option found in section " + section)
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            self._log.warning("Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default)
            tempLevel = self._logLevel_default
        self._logLevel_repo = eval("logging." + tempLevel)
                
        #load backend storage configuration
        try:
            self._address = self._config.get(self._backend, 'address', 0)
        except ConfigParser.NoOptionError:
            self._log.error("No option address in section "+self._backend)
            sys.exit(1)
        except ConfigParser.NoSectionError:
            self._log.error("No section "+self._backend+" found in the "+self._configfile+" config file")
            sys.exit(1)   
        try:
            self._userAdmin = self._config.get(self._backend, 'userAdmin', 0)
        except ConfigParser.NoOptionError:
            self._log.error("No option userAdmin in section "+self._backend)
            sys.exit(1)
        try:
            self._configFile = os.path.expanduser(self._config.get(self._backend, 'configFile', 0))
        except ConfigParser.NoOptionError:
            self._log.error("No option configFile in section "+self._backend)
            sys.exit(1)
        #only for those config with secondary service
        if (self._backend != "mongodb" and self._backend != "mysql"):
            try:
                self._addressS = self._config.get(self._backend, 'addressS', 0)
            except ConfigParser.NoOptionError:
                self._log.error("No option addressS in section "+self._backend)
                sys.exit(1)
            try:
                self._userAdminS = self._config.get(self._backend, 'userAdminS', 0)
            except ConfigParser.NoOptionError:
                self._log.error("No option userAdminS in section "+self._backend)
                sys.exit(1)
            try:
                self._configFileS = os.path.expanduser(self._config.get(self._backend, 'configFileS', 0))
            except ConfigParser.NoOptionError:
                self._log.error("No option configFileS in section "+self._backend)
                sys.exit(1)        
        try:
            self._imgStore = os.path.expanduser(self._config.get(self._backend, 'imgStore', 0))
        except ConfigParser.NoOptionError:
            self._log.error("No option imgStore in section "+self._backend)
            sys.exit(1)       
        
                


