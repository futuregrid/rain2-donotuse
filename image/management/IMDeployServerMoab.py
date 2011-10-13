#!/usr/bin/env python
"""
xCAT image deployment server that DO REGISTER AN IMAGE IN MOAB.
"""

__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.1'


import socket, ssl
import sys
import os
from subprocess import *
import logging
import logging.handlers
import time
from IMServerConf import IMServerConf

class IMDeployServerMoab(object):

    def __init__(self):
        super(IMDeployServerMoab, self).__init__()
        
        self.numparams = 4   #prefix,name,os,arch
        
        self.prefix = ""
        self.name = ""
        self.operatingsystem = ""
        self.arch = ""
        self.machine = ""
        
        #load from config file
        self._deployConf = IMServerConf()
        self._deployConf.load_deployServerMoabConfig() 
        self.port = self._deployConf.getMoabPort()
        self.moabInstallPath = self._deployConf.getMoabInstallPath()
        self.log_filename = self._deployConf.getLogMoab()
        #self.timeToRestartMoab = self._deployConf.getTimeToRestartMoab()  #time that we wait to get the moab scheduler restarted (mschedctl -R)
        self.logLevel = self._deployConf.getLogLevelMoab()
        self._ca_certs = self._deployConf.getCaCertsMoab()
        self._certfile = self._deployConf.getCertFileMoab()
        self._keyfile = self._deployConf.getKeyFileMoab()
        
        print "\nReading Configuration file from "+self._deployConf.getConfigFile()+"\n"
        
        self.logger = self.setup_logger()
                
    
    def setup_logger(self):
        #Setup logging
        logger = logging.getLogger("DeployMoab")
        logger.setLevel(self.logLevel)    
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.log_filename)
        handler.setLevel(self.logLevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False #Do not propagate to others
        
        return logger
    
    def start(self):  
        
        self.logger.info('Starting Server on port ' + str(self.port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.port))
        sock.listen(1)
        while True:
            newsocket, fromaddr = sock.accept()
            connstream = 0
            try:
                connstream = ssl.wrap_socket(newsocket,
                              server_side=True,
                              ca_certs=self._ca_certs,
                              cert_reqs=ssl.CERT_REQUIRED,
                              certfile=self._certfile,
                              keyfile=self._keyfile,
                              ssl_version=ssl.PROTOCOL_TLSv1)
                self.process_client(connstream)
            except ssl.SSLError:
                self.logger.error("Unsuccessful connection attempt from: " + repr(fromaddr))
            finally:
                if connstream is ssl.SSLSocket:
                    connstream.shutdown(socket.SHUT_RDWR)
                    connstream.close()
                

    def process_client(self, connstream):
        self.logger.info('Accepted new connection')
        #receive the message
        data = connstream.read(2048)
        params = data.split(',')

        #params[0] is prefix
        #params[1] is name
        #params[2] is operating system            
        #params[3] is arch
        #params[4] is machine (india, minicluster..)

        self.prefix = params[0]
        self.name = params[1]
        self.operatingsystem = params[2]
        self.arch = params[3]
        self.machine = params[4]

        moabstring = ""    
        if self.machine == "minicluster":
            moabstring = 'echo \"' + self.prefix + self.operatingsystem + '' + self.name + ' ' + self.arch + ' ' + self.prefix + \
                        self.operatingsystem + '' + self.name + ' compute netboot\" | sudo tee -a ' + self.moabInstallPath + '/tools/msm/images.txt > /dev/null'
            #moabstring = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' boottarget ' + prefix + operatingsystem + '' + name + ' netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
        elif self.machine == "india":
            moabstring = 'echo \"' + self.prefix + self.operatingsystem + '' + self.name + ' ' + self.arch + ' boottarget ' + \
                        self.prefix + self.operatingsystem + '' + self.name + ' netboot\" | sudo tee -a ' + self.moabInstallPath + '/tools/msm/images.txt > /dev/null'


        #This message inster the line in the images.txt file    
        self.logger.debug(moabstring)
        status = os.system(moabstring)

        if len(params) == self.numparams and status != 0:
            msg = 'Error including image name in image.txt file'
            self.logger.debug(msg)
            connstream.write(msg)
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()
            return
        else:
            connstream.write('OK')
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()

        cmd = 'sudo ' + moabInstallPath + '/bin/mschedctl -R'
        status = self.runCmd(cmd)
        
        self.logger.info("Image Deploy Moab DONE")
        
        """
        if not os.path.isfile('/tmp/image-deploy-fork.lock'):
        	os.system('touch /tmp/image-deploy-fork.lock')
            child_pid = os.fork()
            if child_pid == 0:
                self.logger.debug("Child Process: PID# %s" % os.getpid())
                time.sleep(self.timeToRestartMoab)
                cmd = 'mschedctl -R'
                status = self.runCmd(cmd)
                os.system('rm -f /tmp/image-deploy-fork.lock')
            else:
                self.logger.debug("Parent Process: PID# %s" % os.getpid())
        """

    def runCmd(self, cmd):
        cmdLog = logging.getLogger('DeployMoab.exec')
        cmdLog.debug(cmd)
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
        std = p.communicate()
        status = 0
        if len(std[0]) > 0:
            cmdLog.debug('stdout: ' + std[0])
            cmdLog.debug('stderr: ' + std[1])
        if p.returncode != 0:
            cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
            status = 1
            #sys.exit(p.returncode)
        return status

def main():

    #Check if we have root privs 
    #if os.getuid() != 0:
    #    print "Sorry, you need to run with root privileges"
    #    sys.exit(1)

    print "\n The user that executes this must have sudo with NOPASSWD for \"tee -a\" and \"mschedctl -R\" commands"

    server = IMDeployServerMoab()
    server.start()

if __name__ == "__main__":
    main()
#END
