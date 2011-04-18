import os
import ConfigParser
import string
import logging
from futuregrid.utils import fgLog
import sys

class fgShellConf(object):

    ############################################################
    # getLogHistFile
    ############################################################
    
    def __init__(self):
        
      
        self._fgpath=""
        try:
            self._fgpath=os.environ['FG_PATH']
        except KeyError:
            print "Please, define FG_PATH to indicate where fg.py is"
            sys.exit() 
        
        ##DEFAULT VALUES##                
        self._loghistdir="~/.fg/"
        
        tempfile=os.path.expanduser(self._loghistdir)+"/config"
        
        if(os.path.isfile(tempfile)):            
            self._configfile=tempfile
        else:   
            self._configfile=self._fgpath+"/etc/config"
        
        self._logfile="" #self._loghistdir__+"/fg.log"
        self._histfile="" #self._loghistdir+"/hist.txt"        
        self._scriptfile=os.environ['PWD']+"/script"
        self._logLevel="DEBUG"  
        self._logType=["DEBUG","INFO","WARNING","ERROR"]
        
        self._banner=""
        
        self.loadConfig()
        
        
        ###TODO ADD SSH KEY TO SSH-ADD
        
    ############################################################
    # getLogHistFile
    ############################################################

    def getLogHistDir(self):
        return self._loghistdir    

    ############################################################
    # getConfigFile
    ############################################################

    def getConfigFile(self):
        return self._configfile

   ############################################################
    # getLogFile
    ############################################################

    def getLogFile(self):
        return self._logfile

   ############################################################
    # getHistFile
    ############################################################


    def getHistFile(self):
        return self._histfile
 
    ############################################################
    # getScriptFile
    ############################################################

    def getScriptFile(self):
        return self._scriptfile

    ############################################################
    # getLogLevel
    ############################################################

    def getLogLevel(self):
        return self._logLevel 

    ############################################################
    # getBanner
    ############################################################

    def getBanner(self):
        return self._banner

    ############################################################
    # loadConfig
    ############################################################
    def loadConfig(self):
        
        config = ConfigParser.ConfigParser()
        if(os.path.isfile(self._configfile)):
            config.read(self._configfile)
        else:
            print "Error: Config file not found"+self._configfile
            sys.exit(0)
            
        try:
            self._loghistdir=os.path.expanduser(config.get('DEFAULT', 'loghistdir', 0))        
        except ConfigParser.NoOptionError:
            print "Error: No option loghistdir in section LogHist"
            sys.exit(0)
        
        try:
            self._banner=self._fgpath+"/"+config.get('DEFAULT', 'banner', 0)        
        except ConfigParser.NoOptionError:
            print "Error: No option loghistdir in section LogHist"
            sys.exit(0)
        
        #Directory where history and logs are
        if not (os.path.isdir(self._loghistdir)):        
            os.system("mkdir "+self._loghistdir)
            
        try:    
            self._logfile=os.path.expanduser(config.get('LogHist', 'log', 0))        
        except ConfigParser.NoOptionError:
            print "Error: No option log in section LogHist"
            sys.exit(0)
        
        ##History
        try:
            self._histfile=os.path.expanduser(config.get('LogHist', 'history', 0))
        except ConfigParser.NoOptionError:
            print "Error: No option history in section LogHist"
            sys.exit(0)
            
        ##Script
        try:
            self._scriptfile=os.path.expanduser(config.get('LogHist', 'script', 0))
        except ConfigParser.NoOptionError:
            pass
        
        ##Log
        try:
            tempLevel=string.upper(config.get('LogHist', 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel=self._LogLevel
            
        if not (tempLevel in self._logType):
            print "Log level "+self._log_level+" not supported. Using the default one "+self._defaultLogLevel            
        self._logLevel=eval("logging."+tempLevel)
            
            
    
