import logging
import logging.handlers
import os

# kjcjlk
class fgLog():

    def __init__(self, logfile, loglevel, whois, verbose):
        '''initializes the log file. the parameters are as follows
        logfile: name of the log file
        loglevel: setting of the log level 
        TODO: explain what the loglevels do
        whois: name associated with the log
        verbose: if True prints some information to stdout
        '''
        self._logger = logging.getLogger(whois)
        self._formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        self._logger.setLevel(loglevel)

        handler = logging.FileHandler(logfile)
        # handlers.RotatingFileHandler(logfile, maxBytes=2048, backupCount=5)

        handler.setFormatter(self._formatter)

        handler.setLevel(loglevel)
        self._logger.addHandler(handler)
        self._logger.propagate = False

        # This is to print in the stdout the same that in the log
        if(verbose):
            ch = logging.StreamHandler()
            ch.setLevel(loglevel)
            ch.setFormatter(self._formatter)
            self._logger.addHandler(ch)



    def getLogFile(self):
        '''returns the log file'''
        return self._logfile

    def debug(self, text):
        '''includes a debug message of "text" into the log file'''
        self._logger.debug(text)

    def info(self, text):
        '''includes an info message of "text" into the log file'''
        self._logger.info(text)

    def warning(self, text):
        '''includes a warning message of "text" into the log file'''
        self._logger.warning(text)

    def error(self, text):
        '''includes an error message of "text" into the log file'''
        self._logger.error(text)

    def clear(self):
        '''removes the log file'''
        os.remove(self._logfile)
