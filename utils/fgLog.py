import logging
import logging.handlers
import os

#def (self, log_file="fg.log", module="root", level=logging.DEBUG):

loglevel=logging.DEBUG
log_file="fg.log"

log_filename = os.environ['HOME']+log_file
logger = logging.getLogger()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

handler = logging.FileHandler(log_filename)
handler.setFormatter(formatter)

ch = logging.StreamHandler()
ch.setFormatter(formatter)


def SetLogFile(log_file="fg.log"):
    log_file=log_file
    
def SetLogLevel(level=logging.DEBUG):
    loglevel=level
    logger.setLevel(level)
    ch.setLevel(logging.DEBUG)
    handler.setLevel(level)
    logger.addHandler(handler)
    logger.addHandler(ch)
    
    
def getLogFile():
     return logFile
     
def debug(text):
    log.debug(text)
     
def info(text):
    log.info(text)
     
def warning(text):
    log.warning(text)
     
def clear():
    os.remove(logFile)
     