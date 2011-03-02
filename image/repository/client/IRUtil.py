"""
utility class for static methods
"""


from random import randrange
import os
import ConfigParser
import string
import logging
import sys
from futuregrid.utils import fgLog #This should the the final one
"""
#To execute IRClient for tests
sys.path.append("/home/javi/imagerepo/ImageRepo/src/futuregrid/") #Directory where fg.py is
from utils import fgLog
"""
import sys

try:
    __fgpath__=os.environ['FG_PATH']
except KeyError:
    print "Please, define FG_PATH to indicate where fg.py is"
    sys.exit() 

##DEFAULT VALUES##
__configfile__=__fgpath__+"/etc/config"
__loghistdir__=__fgpath__+"/.fg/"
__logfile__=__loghistdir__+"/fg.log"
__histfile__=__loghistdir__+"/hist.txt"        

def getImgId():
    imgId = str(randrange(9999999999999))
    return imgId

def getLogHistDir():
    return __loghistdir__

def getConfigFile():
    return __configfile__

def loadConfig():
    
    config = ConfigParser.ConfigParser()
    if(os.path.isfile(__configfile__)):
        config.read(__configfile__)
    else:
        print "Error: Config file not found"+__configfile__
        sys.exit(0)
    try:
        __loghistdir__=os.path.expanduser(config.get('LogHist', 'loghistdir', 0))
    except ConfigParser.NoOptionError:
        pass
    
    if not (os.path.isdir(__loghistdir__)):        
        os.system("mkdir "+__loghistdir__)
    try:    
        __logfile__=os.path.expanduser(config.get('LogHist', 'log', 0))
    except ConfigParser.NoOptionError:
        pass
    try:
        __histfile__=os.path.expanduser(config.get('LogHist', 'history', 0))
    except ConfigParser.NoOptionError:
        pass
    
    try:
        log_level=string.upper(config.get('LogHist', 'log_level', 0))
    except ConfigParser.NoOptionError:
        log_level=fgLog.defaultloglevel
        
    if not (log_level in fgLog.logType):
        print "Log level "+log_level+" not supported. Using the default one "+fgLog.defaultloglevel
        log_level=eval("logging."+fgLog.defaultloglevel)
    else:
        log_level=eval("logging."+log_level)
        
    fgLog.setupLog(__logfile__,log_level)    