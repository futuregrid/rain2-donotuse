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

#Global vars
port = 56789
numparams = 5   #name,os,version,arch,kernel
xcatInstallPath = '/install/netboot/'
moabInstallPath = '/opt/moab/'

TEST_MODE=True

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
	
	    #Fix name so that it removes dashes
	    oldName = params[0]
	    params[0] = params[0].replace('-', '.')
	
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
	    if params[1] == 'ubuntu' or params[1] == 'debian':
	        prefix = 'rhels5.4'
	
	    #Build filesystem
	
	    #Create Directory structure
	    #/install/netboot/<name>/<arch>/compute/
	    path = xcatInstallPath + prefix + params[1] + '.' + params[0] + '/' + params[3] + '/compute/'
	    cmd = 'mkdir -p ' + path
	    runCmd(cmd)
	
	    tempdir=params[5]
	    
	    #make assumption that the img file has been uploaded to /tmp
	    cmd = 'mv '+tempdir+'/rootimg.gz ' + path + 'rootimg.gz'
	    runCmd(cmd)
	
	    cmd = 'mkdir -p ' + path + 'rootimg'
	    runCmd(cmd)
	
	    cmd = 'cd ' + path + '; gunzip -c rootimg.gz | cpio -i'
	    os.system(cmd) #because of the pipe
	
	
	    #cmd = 'tar xfz '+path + 'rootimg.tar.gz --directory ' + path
	    #runCmd(cmd)
	
	    #cmd = 'mv ' +path + oldName + ' '+ path + 'rootimg'
	    #runCmd(cmd)
	
	
	    cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/initrd.gz -O ' + path+'/initrd.gz'
	    runCmd(cmd)
	
	    cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/kernel -O ' + path+'/kernel'
	    runCmd(cmd)
	
	    #Add entry to the osimage table
	    cmd = 'chtab osimage.imagename=\"' + params[1] + '.' + params[0] + '\" osimage.profile=\"compute\" osimage.imagetype=\"linux\" osimage.provmethod=\"netboot\" osimage.osname=\"' + params[1] + '\" osimage.osvers=\"' + prefix + params[1] + '.' + params[0] + '\" osimage.osarch=\"' + params[3] + '\"'
	    runCmd(cmd)
	
	    #Pack image
	    cmd = 'packimage -o ' + prefix + params[1] + '.' + params[0] + ' -p compute -a ' + params[3]
	    runCmd(cmd)
	
	    if (TEST_MODE):
		    #TODO: Testing only, will remove in the future
		    #Do a nodeset
		    cmd = 'nodeset tc1 netboot=' + prefix + params[1] + '.' + params[0] + '-' + params[3] + '-compute'
		    runCmd(cmd)
		    runCmd('rpower tc1 boot')
	
	    #Configure Moab
	
	    cmd = 'echo \"' + params[1] + '-' + params[0] + ' ' + params[3] + ' ' + params[1] + '-' + params[2] + ' compute netboot\" >> ' + moabInstallPath + 'images.txt'
	    print cmd
	    os.system(cmd)
	
	    cmd = 'mschedctl -R'
	    runCmd(cmd)

def runCmd(cmd):
    cmdLog = logging.getLogger('exec')
    cmdLog.debug(cmd)
    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
    std = p.communicate()
    if len(std[0]) > 0:
	    cmdLog.debug('stdout: ' + std[0])
	    cmdLog.debug('stderr: ' + std[1])
    if p.returncode != 0:
        cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
        sys.exit(p.returncode)


if __name__ == "__main__":
                main()
#END