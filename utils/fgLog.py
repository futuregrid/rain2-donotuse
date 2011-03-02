import logging
import logging.handlers
import os
from futuregrid.utils import fgUtil

loglevel = logging.DEBUG
log_file = "fg.log"

fgshelldir = fgUtil.getShellDir()
log_filename = fgshelldir + log_file

if not (os.path.isdir(fgshelldir)):
    os.system("mkdir " + fgshelldir) 

logger = logging.getLogger("FutureGrid")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def setupLog(log_file="fg.log", level=logging.DEBUG):
    log_filename = fgshelldir + log_file
    handler = logging.FileHandler(log_filename)
    handler.setFormatter(formatter)
    loglevel = level
    logger.setLevel(level)
    handler.setLevel(level)
    logger.addHandler(handler)    
    
def getLogFile():
     return log_filename
     
def debug(text):
    logger.debug(text)
     
def info(text):
    logger.info(text)
     
def warning(text):
    logger.warning(text)

def error(text):
    logger.error(text)
     
def clear():
    os.remove(log_filename)
     
