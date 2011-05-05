#!/usr/bin/python
# Description: xCAT image deployment server.  Deploys images given by fg-image-deploy onto xCAT bare metal 
#
# Author: Andrew J. Younge
#


import socket
import sys
import os
from subprocess import *

#Global vars
port = 56789
numparams = 5     #name,os,version,arch,kernel
xcatInstallPath = '/install/netboot/'
moabInstallPath = '/opt/moab/'

def main():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(1)
    while True:

        channel,details = sock.accept()

        #receive the message
        data = channel.recv(2048)
        params = data.split(',')
        
        if len(params) == numparams:
            channel.send('OK')
            channel.close()
        else:
            print "ERROR: incorrect message"
            channel.send('ERROR')
            channel.close()
            sys.exit(1)

        
        #Build filesystem

        #Create    Directory structure
        #/install/netboot/<name>/<arch>/compute/
        path = xcatInstallPath + params[1] + '-' +params[0] + '/' + params[3] + '/compute/' 
        cmd = 'mkdir -p ' + path 
        runCmd(cmd)    

        #make assumption that the img file has been uploaded to /tmp
        imagefilename = '/tmp/'+params[0]+'.tar.gz'
        
        #Configure xCAT 

        cmd = 'mv ' + imagefilename + ' ' + path + 'rootimg.tar.gz'
        runCmd(cmd)

        cmd = 'tar xfz '+path + 'rootimg.tar.gz --directory ' + path 
        runCmd(cmd)

        cmd = 'mv ' +path + params[0] + ' '+ path + 'rootimg'
        runCmd(cmd)

        cmd = 'cp /install/kernels/initrd.gz ' + path
        runCmd(cmd)

        cmd = 'cp /install/kernels/kernel ' + path
        runCmd(cmd)


        cmd = 'chtab osimage.imagename=\"'+params[1]+'-'+params[0]+'\" osimage.profile=\"compute\" osimage.imagetype=\"linux\" osimage.provmethod=\"netboot\" osimage.osname=\"'+params[1]+'\" osimage.osvers=\"'+params[2]+'\" osimage.osarch=\"'+params[3]+'\"'
        runCmd(cmd)

        #Configure Moab

        cmd = 'echo \"'+ params[1]+'-'+params[0] + ' ' + params[3] + ' ' + params[1]+'-'+params[2] + ' compute netboot\" >> ' + moabInstallPath + 'images.txt'
        print cmd
        os.system(cmd)

        cmd = 'mschedctl -R'
        runCmd(cmd)

def runCmd(cmd):
        #cmdLog = logging.getLogger('exec')
        #cmdLog.debug(cmd)
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE) 
        std = p.communicate()
        if len(std[0]) > 0: 
            print 'stdout: '+std[0]
            print 'stderr: '+std[1]
        if p.returncode != 0:
            print 'Command: '+cmd+' failed, status: '+str(p.returncode)+' --- '+std[1]
            sys.exit(p.returncode)


if __name__ == "__main__":
        main()
#END
