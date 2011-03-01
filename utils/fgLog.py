import logging
import logging.handlers
import os

class fgLog(object):

    def __init__(log_file="fg.log", level=logging.DEBUG):
        self.loglevel = level
        self.log_file = log_file
    
        fgshelldir = os.environ['HOME'] + "/.fg/"
        
        log_filename = fgshelldir + log_file
    
        if not (os.path.isdir(fgshelldir)):
            os.system("mkdir " + fgshelldir) 
    
        logger = logging.getLogger()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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
         
    def clear():
        os.remove(log_filename)
     
