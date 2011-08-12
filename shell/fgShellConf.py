#!/usr/bin/env python
import os
import ConfigParser
import string
import logging
from futuregrid.utils import fgLog
import sys

configFileName = "fg-client.conf"

class fgShellConf(object):

    ############################################################
    # getLogHistFile
    ############################################################

    def __init__(self):
        '''initialize the shell configuration'''

        self._fgpath = ""
        try:
            self._fgpath = os.environ['FG_PATH']
        except KeyError:
            self._fgpath = os.path.dirname(__file__) + "/../"

        ##DEFAULT VALUES##                
        self._loghistdir = "~/.fg/"

        self._configfile = os.path.expanduser(self._loghistdir) + "/" + configFileName
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

        self._logfile = "" #self._loghistdir__+"/fg.log"
        self._histfile = "" #self._loghistdir+"/hist.txt"        
        self._scriptfile = os.environ['PWD'] + "/script"
        self._logLevel = "DEBUG"
        self._logType = ["DEBUG", "INFO", "WARNING", "ERROR"]

        self.loadConfig()


        ###TODO ADD SSH KEY TO SSH-ADD

    ############################################################
    # getLogHistFile
    ############################################################

    def getLogHistDir(self):
        '''returns the directory of the history file'''
        return self._loghistdir

    ############################################################
    # getConfigFile
    ############################################################

    def getConfigFile(self):
        '''returns the configuration file'''
        return self._configfile

    ############################################################
    # getLogFile
    ############################################################

    def getLogFile(self):
        '''returns the logfile'''
        return self._logfile

    ############################################################
    # getHistFile
    ############################################################


    def getHistFile(self):
        '''returns the history file'''
        return self._histfile

    ############################################################
    # getScriptFile
    ############################################################

    def getScriptFile(self):
        '''returns the script file'''
        return self._scriptfile

    ############################################################
    # getLogLevel
    ############################################################

    def getLogLevel(self):
        '''returns the loglevel'''
        return self._logLevel

    ############################################################
    # loadConfig
    ############################################################
    def loadConfig(self):
        '''loads the configuration from the config file'''
        config = ConfigParser.ConfigParser()
        if(os.path.isfile(self._configfile)):
            config.read(self._configfile)
        else:
            print "Error: Config file not found" + self._configfile
            sys.exit(0)

        try:
            self._loghistdir = os.path.expanduser(config.get('DEFAULT', 'loghistdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No option loghistdir in section LogHist"
            sys.exit(0)


        #Directory where history and logs are
        if not (os.path.isdir(self._loghistdir)):
            os.system("mkdir " + self._loghistdir)

        try:
            self._logfile = os.path.expanduser(config.get('LogHist', 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No option log in section LogHist"
            sys.exit(0)

        ##History
        try:
            self._histfile = os.path.expanduser(config.get('LogHist', 'history', 0))
        except ConfigParser.NoOptionError:
            print "Error: No option history in section LogHist"
            sys.exit(0)

        ##Script
        try:
            self._scriptfile = os.path.expanduser(config.get('LogHist', 'script', 0))
        except ConfigParser.NoOptionError:
            pass

        ##Log
        try:
            tempLevel = string.upper(config.get('LogHist', 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._LogLevel

        if not (tempLevel in self._logType):
            print "Log level " + self._log_level + " not supported. Using the default one " + self._defaultLogLevel
        self._logLevel = eval("logging." + tempLevel)



