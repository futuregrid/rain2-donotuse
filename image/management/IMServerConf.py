#!/usr/bin/env python
"""
Class to read Image Management Server configuration
"""

import os
import ConfigParser
import string
import sys
import logging

configFileName = "fg-server.conf"

class IMServerConf(object):

    ############################################################
    # init
    ############################################################

    def __init__(self):
        super(IMServerConf, self).__init__()

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
                    print "ERROR: configuration file "+configFileName+" not found"
                    sys.exit(1)
        
        #image generation server
        self._gen_port = 0
        self._proc_max = 0
        self._refresh_status = 0
        self._vmfile_centos = ""
        self._vmfile_rhel = ""
        self._vmfile_ubuntu ="" 
        self._vmfile_debian = ""
        self._xmlrpcserver = ""
        self._bridge = ""
        self._serverdir = ""
        self._addrnfs = ""
        self._tempdirserver_gen = ""
        self._tempdir_gen = ""
        self._http_server_gen = ""
        self._bcfg2_url = ""
        self._bcfg2_port = 0
        self._log_gen = ""
        self._logLevel_gen=""


        #image server xcat
        self._xcat_port = 0
        self._xcatNetbootImgPath = ''
        self._http_server = ""
        self._log_xcat = ""
        self._logLevel_xcat = ""
        self._test_xcat = ""

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
    
    #image generation server
    def getGenPort(self):
        return self._gen_port
    def getProcMax():
        return self._proc_max
    def getRefreshStatus():
        self._refresh_status
    def getVmFileCentos(self):
        return self._vmfile_centos
    def getVmFileRhel(self):
        return self._vmfile_rhel
    def getVmFileUbuntu(self):
        return self._vmfile_ubuntu
    def getVmFileDebian(self): 
        return self._vmfile_debian
    def getXmlRpcServer(self):
        return self._xmlrpcserver
    def getBridge(self):
        return self._bridge
    def getServerDir(self):
        return self._serverdir
    def getAddrNfs(self):
        return self._addrnfs
    def getTempDirServerGen(self):
        return self._tempdirserver_gen
    def getTempDirGen(self):
        return self._tempdir_gen
    def getHttpServerGen(self):
        return self._http_server_gen
    def getBcfg2Url(self):
        return self._bcfg2_url
    def getBcgf2Port(self):
        return self._bcfg2_port
    def getLogGen(self):
        return self._log_gen
    def getLogLevelGen(self):
        return self._logLevel_gen
    
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
    def getTestXcat(self):
        return self._test_xcat
    
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
    # load_generateServerConfig
    ############################################################
    def load_generateServerConfig(self):        
        section = "GenerateServer"
        try:
            self._gen_port = int(self._config.get(section, 'port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No port option found in section " + section
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)
        try:
            self._proc_max = int(self._config.get(section, 'proc_max', 0))
        except ConfigParser.NoOptionError:
            print "Error: No proc_max option found in section " + section
            sys.exit(1)
        try:
            self._refresh_status = int(self._config.get(section, 'refresh', 0))
        except ConfigParser.NoOptionError:
            print "Error: No refresh option found in section " + section
            sys.exit(1)
        try:
            self._vmfile_centos = os.path.expanduser(self._config.get(section, 'vmfile_centos', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_centos option found in section " + section
            sys.exit(1)
        try:
            self._vmfile_rhel = os.path.expanduser(self._config.get(section, 'vmfile_rhel', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_rhel option found in section " + section
            sys.exit(1)
        try:
            self._vmfile_ubuntu = os.path.expanduser(self._config.get(section, 'vmfile_ubuntu', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_ubuntu option found in section " + section
            sys.exit(1)
        try:
            self._vmfile_debian = os.path.expanduser(self._config.get(section, 'vmfile_debian', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_debian option found in section " + section
            sys.exit(1)
        try:
            self._xmlrpcserver = self._config.get(section, 'xmlrpcserver', 0)
        except ConfigParser.NoOptionError:
            print "Error: No xmlrpcserver option found in section " + section
            sys.exit(1)
        try:
            self._bridge = self._config.get(section, 'bridge', 0)
        except ConfigParser.NoOptionError:
            print "Error: No bridge option found in section " + section
            sys.exit(1)
        try:
            self._serverdir = os.path.expanduser(self._config.get(section, 'serverdir', 0))
        except ConfigParser.NoOptionError:
            self._serverdir=None
        try:
            self._addrnfs = self._config.get(section, 'addrnfs', 0)
        except ConfigParser.NoOptionError:
            print "Error: No addrnfs option found in section " + section
            sys.exit(1)
        try:
            self._tempdirserver_gen = os.path.expanduser(self._config.get(section, 'tempdirserver', 0))
        except ConfigParser.NoOptionError:
            print "Error: No tempdirserver option found in section " + section
            sys.exit(1)
        try:
            self._tempdir_gen = os.path.expanduser(self._config.get(section, 'tempdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No tempdir option found in section " + section
            sys.exit(1)            
        try:
            self._http_server_gen = self._config.get(section, 'http_server', 0)
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section " + section
            sys.exit(1)
        try:
            self._bcfg2_url = self._config.get(section, 'bcfg2_url', 0)
        except ConfigParser.NoOptionError:
            print "Error: No bcfg2_url option found in section " + section
            sys.exit(1)
        try:
            self._bcfg2_port = int(self._config.get(section, 'bcfg2_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No bcfg2_port option found in section " + section
            sys.exit(1)
        try:
            self._log_gen = os.path.expanduser(self._config.get(section, 'log', 0))
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
        self._logLevel_gen = eval("logging." + tempLevel)
    
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
        try:
             aux = string.lower(self._config.get(section, 'test_mode', 0))
             if aux == "true":
                 self._test_xcat=True
             else:
                 self._test_xcat=False
        except ConfigParser.NoOptionError:
            self._test_xcat=False
      

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



