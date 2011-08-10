#!/usr/bin/python2.7
# Description: xCAT image deployment server that DO REGISTER AN IMAGE IN MOAB. 
#
# Author: Andrew J. Younge, Javier Diaz
#


import socket
import sys
import os
from subprocess import *
import logging
import logging.handlers
import time
from IMServerConf import IMServerConf

def main():

    #Check if we have root privs 
    if os.getuid() != 0:
        print "Sorry, you need to run with root privileges"
        sys.exit(1)

    server = DeployMoabServer()
    server.start()
    
class DeployMoabServer(object):

    def __init__(self):
        super(DeployMoabServer, self).__init__()
        
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
        self.timeToRestartMoab = self._deployConf.getTimeToRestartMoab()  #time that we wait to get the moab scheduler restarted (mschedctl -R)
        self.logLevel = self._deployConf.getLogLevelMoab()
        
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
            while True:
    
                channel, details = sock.accept()
    
                self.logger.info('Accepted new connection')
    
                #receive the message
                data = channel.recv(2048)
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
                                self.operatingsystem + '' + self.name + ' compute netboot\" >> ' + self.moabInstallPath + '/tools/msm/images.txt'
                    #moabstring = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' boottarget ' + prefix + operatingsystem + '' + name + ' netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
                elif self.machine == "india":
                    moabstring = 'echo \"' + self.prefix + self.operatingsystem + '' + self.name + ' ' + self.arch + ' boottarget ' + \
                                self.prefix + self.operatingsystem + '' + self.name + ' netboot\" >> ' + self.moabInstallPath + '/tools/msm/images.txt'
    
    
                #This message inster the line in the images.txt file    
                self.logger.debug(moabstring)
                status = os.system(moabstring)
    
                if len(params) == self.numparams and status != 0:
                    msg = 'Error including image name in image.txt file'
                    self.logger.debug(msg)
                    channel.send(msg)
                    channel.close()
                    break
                else:
                    channel.send('OK')
                    channel.close()
    
                
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

if __name__ == "__main__":
    main()
#END
