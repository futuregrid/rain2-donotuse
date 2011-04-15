"""
Class to read Image Repository Client configuration
"""

import os
import ConfigParser
import string
import sys
import logging


class IRClientConf(object):
    
    def __init__(self):
        super(IRClientConf, self).__init__()
        
        ###################################
        #These should be sent from the Shell. We leave it for now to have an independent IR.   
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
        ####################################
        
        #IR Server Config file
        self._irconfig=".IRconfig"
        self._serverdir=""
        self._serveraddr=""
        #IR Client Config
        self._backend = ""
        self._fgirimgstore = ""        
        
        self._logfile="" #self._loghistdir__+"/fg.log"
        self._logLevel="DEBUG"  
        self._logType=["DEBUG","INFO","WARNING","ERROR"]
        
        self.loadConfig()        
        
        self._backends = ["mongodb","mysql","swiftmysql","swiftmongo","cumulusmysql","cumulusmongo"] #available backends
        self._setupBackend()
        
        ###TODO ADD SSH KEY TO SSH-ADD
        
    
    def getLogHistDir(self):
        return self._loghistdir    
    def getConfigFile(self):
        return self._configfile
    def getLogFile(self):
        return self._logfile
    def getLogLevel(self):
        return self._logLevel
    def getIrconfig(self):
        return self._irconfig
    def getBackend(self):
        return self._backend
    def getFgirimgstore(self):
        return self._fgirimgstore 
    def getServerdir(self):
        return self._serverdir
    def getServeraddr(self):
        return self._serveraddr
    
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
        
        #Directory where history and logs are
        if not (os.path.isdir(self._loghistdir)):        
            os.system("mkdir "+self._loghistdir)
            
        try:    
            self._logfile=os.path.expanduser(config.get('Repo', 'log', 0))        
        except ConfigParser.NoOptionError:
            print "Error: No option log in section Repo"
            sys.exit(0)
        
        ##Log
        try:
            tempLevel=string.upper(config.get('Repo', 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel=self._LogLevel
            
        if not (tempLevel in self._logType):
            print "Log level "+self._log_level+" not supported. Using the default one "+self._defaultLogLevel            
        self._logLevel=eval("logging."+tempLevel)
     
        #Server dir
        try:    
            self._serverdir=os.path.expanduser(config.get('Repo', 'serverdir', 0))        
        except ConfigParser.NoOptionError:
            print "Error: No option serverdir in section Repo"
            sys.exit(0)
        #Server address
        try:    
            self._serveraddr=os.path.expanduser(config.get('Repo', 'serveraddr', 0))        
        except ConfigParser.NoOptionError:
            print "Error: No option serveraddr in section Repo"
            sys.exit(0)
         #Server address
        try:    
            self._irconfig=os.path.expanduser(config.get('Repo', 'IRConfig', 0))        
        except ConfigParser.NoOptionError:
            print "Error: No option IRconfig in section Repo"
            sys.exit(0)
            
    def _setupBackend (self):  
        userId = os.popen('whoami', 'r').read().strip()        
        if not os.path.isfile(self._irconfig):
            cmdexec = " '" + self._serverdir + \
                    "IRService.py --getBackend " "'"
        
            print "Requesting Server Config"
            #aux=self._rExec(userId, cmdexec)
            cmdssh = "ssh " + userId + "@" + self._serveraddr
            aux=os.popen(cmdssh+cmdexec).read().strip()  
            aux=aux.split("\n")
            
            self._backend=aux[0].strip()
            self._fgirimgstore=aux[1].strip()
            try:
                f = open(self._irconfig, "w")
                f.write(self._backend+'\n')
                f.write(self._fgirimgstore)
                f.close()
            except(IOError),e:
                print "Unable to open the file", self._irconfig, "Ending program.\n", e
        else:
            print "Reading Server Config from "+self._irconfig
            try:
                f = open(self._irconfig, "r")
                self._backend=f.readline()
                if not (self._backend.strip() in self._backends):
                    print "Error in local config. Please remove file: "+self._irconfig
                    exit(0)
                self._fgirimgstore=f.readline()
                f.close()
            except(IOError),e:
                print "Unable to open the file", self._irconfig, "Ending program.\n", e       
    

