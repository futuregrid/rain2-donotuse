#!/usr/bin/python
# Description: xCAT image deployment server.  Deploys images given by fg-image-deploy onto xCAT bare metal
#
# Author: Andrew J. Younge
#


import socket
import sys
import os
from subprocess import *
import logging
import logging.handlers
import time

#Global vars
port = 56789
numparams = 6   #name,os,version,arch,kernel,dir
xcatInstallPath = '/install/netboot/'
moabInstallPath = '/opt/moab/'

TEST_MODE=True


#TODO. Modify this to have a generic server that also deploy eucalyptus

def main():

    #Setup logging
    log_filename = 'fg-image-deploy-server-xcat.log'
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
        
            #params[0] is name
            #params[1] is operating system
            #params[2] is version
            #params[3] is arch
            #params[4] is kernel
            #params[5] is dir where img is placed
        
            #Fix name so that it removes dashes
            oldName = params[0]
            name = params[0]#.replace('-', '.')
        
        
            operatingsystem=params[1]
            
            version=params[2]
            
            arch=params[3]
            kernel=params[4]
            tempdir=params[5]
        
        
            if len(params) == numparams:
                channel.send('OK')
                channel.close()
            else:
                print "ERROR: incorrect message"
                channel.send('ERROR')
                channel.close()
                sys.exit(1)
        
            #Hook for Debian based systems to work in xCAT
            prefix = ''
            if operatingsystem == 'ubuntu' or operatingsystem == 'debian':
                prefix = 'rhels5.4'
        
            #Build filesystem
        
            #Create Directory structure
            #/install/netboot/<name>/<arch>/compute/
            path = xcatInstallPath + prefix + operatingsystem + '' + name + '/' + arch + '/compute/'
            cmd = 'mkdir -p ' + path
            status=runCmd(cmd)
            
            cmd = 'mv '+tempdir+'/'+oldName+'.gz ' + path + 'rootimg.gz'
            status=runCmd(cmd)
        
            if status != 0:
                break
        
            cmd = 'mkdir -p ' + path + 'rootimg'
            status=runCmd(cmd)
        
            if status != 0:
                break
        
            cmd = 'cd ' + path + '; gunzip -c rootimg.gz | cpio -i'
            status=os.system(cmd) #because of the pipe
        
            if status != 0:
                break
            
            #cmd = 'tar xfz '+path + 'rootimg.tar.gz --directory ' + path
            #runCmd(cmd)
        
            #cmd = 'mv ' +path + oldName + ' '+ path + 'rootimg'
            #runCmd(cmd)        
        
            cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/initrd.gz -O ' + path+'/initrd.gz'
            status=runCmd(cmd)
        
            if status != 0:
                break
        
            cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/kernel -O ' + path+'/kernel'
            status=runCmd(cmd)
            
            if status != 0:
                break
        
            #Add entry to the osimage table
            #this it seems to be done by packimage
            #cmd = 'chtab osimage.imagename=\"' + operatingsystem + '.' + name + '\" osimage.profile=\"compute\" osimage.imagetype=\"linux\" osimage.provmethod=\"netboot\" osimage.osname=\"' + operatingsystem + '\" osimage.osvers=\"' + prefix + operatingsystem + '.' + name + '\" osimage.osarch=\"' + arch + '\"'
            #status=runCmd(cmd)
            
#include row in linuximage table?
        
            #if status != 0:
            #    break
            
            #Pack image
            cmd = 'packimage -o ' + prefix + operatingsystem + '' + name + ' -p compute -a ' + arch
            status=runCmd(cmd)
        
            if status != 0:
                break
            """        
            if (TEST_MODE):
                #TODO: Testing only, will remove in the future
                #Do a nodeset
                cmd = 'nodeset tc1 netboot=' + prefix + operatingsystem + '' + name + '-' + arch + '-compute'
                runCmd(cmd)
                runCmd('rpower tc1 boot')
            """        
            #Configure Moab
        
            #cmd = 'echo \"' + operatingsystem + '-' + name + ' ' + arch + ' ' + operatingsystem + '-' + version + ' compute netboot\" >> ' + moabInstallPath + 'images.txt'
            cmd = 'echo \"' + operatingsystem + '' + name + ' ' + arch + ' ' + operatingsystem + '-' + version + ' compute netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
            print cmd
            status=os.system(cmd)
            
            if status != 0:
            	logging.debug('error including image name in image.txt file')
                break
            
            if TEST_MODE:
                cmd = 'mschedctl -R'
                status=runCmd(cmd)
            else:
	            if not os.path.isfile('/tmp/image-deploy-fork.lock'):
	            	os.system('touch /tmp/image-deploy-fork.lock')
	                child_pid = os.fork()
	                if child_pid == 0:
	                    print "Child Process: PID# %s" % os.getpid()
	                    time.sleep(300)
	                    cmd = 'mschedctl -R'
	                    status=runCmd(cmd)
	                    os.system('rm -f /tmp/image-deploy-fork.lock')
	                else:
	                    print "Parent Process: PID# %s" % os.getpid()                    
            

def runCmd(cmd):
    cmdLog = logging.getLogger('exec')
    cmdLog.debug(cmd)
    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
    std = p.communicate()
    status=0
    if len(std[0]) > 0:
        cmdLog.debug('stdout: ' + std[0])
        cmdLog.debug('stderr: ' + std[1])
    if p.returncode != 0:
        cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
        status=1
        #sys.exit(p.returncode)
    return status

if __name__ == "__main__":
                main()
#END