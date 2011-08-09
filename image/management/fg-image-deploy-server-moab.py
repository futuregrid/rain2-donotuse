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

#Global vars
port = 56790
moabInstallPath = '/opt/moab/'

TEST_MODE = False
RESTARTMOAB = 5  #time that we wait to get the moab scheduler restarted (mschedctl -R)

numparams = 4   #prefix,name,os,arch

def main():

    #Check if we have root privs 
    if os.getuid() != 0:
        print "Sorry, you need to run with root privileges"
        sys.exit(1)

    #Setup logging
    log_filename = 'fg-image-deploy-server-moab.log'
        #logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt='%a, %d %b %Y %H:%M:%S',filemode='w',filename=log_filename,level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


    logging.info('Starting Server on port ' + str(port))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(1)
    while True:
        while True:

            channel, details = sock.accept()

            logging.info('Accepted new connection')

            #receive the message
            data = channel.recv(2048)
            params = data.split(',')

            #params[0] is prefix
            #params[1] is name
            #params[2] is operating system            
            #params[3] is arch
            #params[4] is machine (india, minicluster..)

            prefix = params[0]
            name = params[1]
            operatingsystem = params[2]
            arch = params[3]
            machine=params[4]

            moabstring = ""

            if machine =="minicluster":
                moabstring = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' ' + prefix + operatingsystem + '' + name + ' compute netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
                #moabstring = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' boottarget ' + prefix + operatingsystem + '' + name + ' netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
            elif machine =="india":
                moabstring = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' boottarget ' + prefix + operatingsystem + '' + name + ' netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'


            #This message inster the line in the images.txt file    
            logging.debug(moabstring)
            status = os.system(moabstring)

            if len(params) == numparams and status != 0:
            	logging.debug('error including image name in image.txt file')
                break
            else:
                channel.send('OK')
                channel.close()

            if TEST_MODE:
                cmd = 'mschedctl -R'
                status = runCmd(cmd)
            else:
	            if not os.path.isfile('/tmp/image-deploy-fork.lock'):
	            	os.system('touch /tmp/image-deploy-fork.lock')
	                child_pid = os.fork()
	                if child_pid == 0:
	                    logging.debug("Child Process: PID# %s" % os.getpid())
	                    time.sleep(RESTARTMOAB)
	                    cmd = 'mschedctl -R'
	                    status = runCmd(cmd)
	                    os.system('rm -f /tmp/image-deploy-fork.lock')
	                else:
	                    logging.debug("Parent Process: PID# %s" % os.getpid())


def runCmd(cmd):
    cmdLog = logging.getLogger('exec')
    cmdLog.debug(cmd)
    p = Popen(cmd.split(' '), stdout = PIPE, stderr = PIPE)
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
