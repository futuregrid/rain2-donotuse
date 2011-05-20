import logging
import logging.handlers

class fgLog():

    def __init__(self, logfile, loglevel, whois, verbose):
        self._logger = logging.getLogger(whois)
        self._formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                
        handler = logging.FileHandler(logfile)        
        handler.setFormatter(self._formatter)
        self._logger.setLevel(loglevel)
        handler.setLevel(loglevel)
        self._logger.addHandler(handler)
        
        #This is to print in the stout the same that in the log
        if(verbose):
            ch = logging.StreamHandler()
            ch.setLevel(loglevel)
            ch.setFormatter(self._formatter)
            self._logger.addHandler(ch)


        
    def getLogFile(self):
         return self._logfile
         
    def debug(self,text):        
        self._logger.debug(text)
         
    def info(self,text):
        self._logger.info(text)
         
    def warning(self,text):       
        self._logger.warning(text)
    
    def error(self,text):        
        self._logger.error(text)
         
    def clear(self):
        os.remove(self._logfile)
