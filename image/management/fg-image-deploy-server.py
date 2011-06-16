#!/usr/bin/python
# Description: xCAT image deployment server.  Deploys images given by fg-image-deploy onto xCAT bare metal
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
port = 56789
numparams = 6   #name,os,version,arch,kernel,dir
xcatInstallPath = '/install/netboot/'
moabInstallPath = '/opt/moab/'

TEST_MODE=True
RESTARTMOAB=5  #time that we wait to get the moab scheduler restarted (mschedctl -R)

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
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)
    #ch.setFormatter(formatter)
    #ogger.addHandler(ch)
    
    
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
        
            if not os.path.isfile(tempdir+'/'+oldName+'.img.tgz'):
                logging.error('file not found')
                break
        
            if len(params) == numparams:
                channel.send('OK')
                channel.close()
            else:
                logging.error("ERROR: incorrect message")
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
            
        
            cmd = 'mkdir -p ' + path + 'rootimg '+ path + 'temp'
            status=runCmd(cmd)
        
            if status != 0:
                break
        
            #cmd = 'cd ' + path + '; gunzip -c rootimg.gz | cpio -i'
            
            
            cmd =  'tar xfz '+ tempdir +'/'+oldName+'.img.tgz -C '+ path
            status=runCmd(cmd) 
        
            if status != 0:
                break
            
            cmd =  'rm -f '+ tempdir +'/'+oldName+'.img.tgz'
            status=runCmd(cmd) 
        
            if status != 0:
                break
            
            cmd =  'mount -o loop '+ path +''+oldName+'.img '+ path +'temp'
            status=runCmd(cmd) 
        
            if status != 0:
                break
            
            #if os.path.isdir(path +'temp'):
            #    print 'the directory exists'
                             
            cmd =  'cp -r '+ path +'temp/* '+ path +'rootimg/'
            print cmd
            status=os.system(cmd) 
        
            if status != 0:
                break
            
            cmd =  'umount '+ path +'temp' 
            status=runCmd(cmd) 
            cmd= 'rm -rf '+ path +'temp '+ path +''+oldName+'.img'
            status=runCmd(cmd)
        
            if status != 0:
                break
            
            #cmd = 'tar xfz '+path + 'rootimg.tar.gz --directory ' + path
            #runCmd(cmd)
        
            #cmd = 'mv ' +path + oldName + ' '+ path + 'rootimg'
            #runCmd(cmd)     

  
            if (operatingsystem=="ubuntu"):
                cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/specialubuntu/initrd.gz -O ' + path+'/initrd.gz'
                status=runCmd(cmd)
            
                if status != 0:
                    break
            
                cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/specialubuntu/kernel -O ' + path+'/kernel'
                status=runCmd(cmd)
                
                if status != 0:
                    break
            else:
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
            cmd = 'chtab osimage.imagename=' + prefix + operatingsystem + '' + name + '-'+arch+'-netboot-compute osimage.profile=compute osimage.imagetype=linux osimage.provmethod=netboot osimage.osname=linux osimage.osvers=' + prefix + operatingsystem + '' + name + ' osimage.osarch=' + arch + ''
            
            status=os.system(cmd)
            
#include row in linuximage table?
            #if the row exists it will give an error
            #if status != 0:
            #    break
            
            #Pack image
            cmd = 'packimage -o ' + prefix + operatingsystem + '' + name + ' -p compute -a ' + arch
            status=runCmd(cmd)
        
            if status != 0:
                break

            #create directory that contains initrd.img and vmlinuz
            tftpimgdir='/tftpboot/xcat/'+ prefix + operatingsystem + '' + name+'/'+arch
            cmd = 'mkdir -p '+tftpimgdir
            status=runCmd(cmd)

            if status != 0:
                break
            if (operatingsystem=="ubuntu"):
                cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/tftp/xcat/ubuntu10/'+arch+'/initrd.img -O ' +tftpimgdir+'/initrd.img'
                status=runCmd(cmd)
    
                if status != 0:
                    break
    
                cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/tftp/xcat/ubuntu10/'+arch+'/vmlinuz -O ' +tftpimgdir+'/vmlinuz'
                status=runCmd(cmd)

                if status != 0:
                    break
            else:
                cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/tftp/xcat/centos5/'+arch+'/initrd.img -O ' +tftpimgdir+'/initrd.img'
                status=runCmd(cmd)
    
                if status != 0:
                    break
    
                cmd = 'wget fg-gravel3.futuregrid.iu.edu/kernel/tftp/xcat/centos5/'+arch+'/vmlinuz -O ' +tftpimgdir+'/vmlinuz'
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
            if TEST_MODE:
                cmd = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' ' + prefix + operatingsystem + '' + name + ' compute netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
            else:
                cmd = 'echo \"' + prefix + operatingsystem + '' + name + ' ' + arch + ' boottarget compute netboot\" >> ' + moabInstallPath + '/tools/msm/images.txt'
                #INSERT row in boottarget??
                
                
            logging.debug(cmd)
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
	                    logging.debug("Child Process: PID# %s" % os.getpid())
	                    time.sleep(RESTARTMOAB)
	                    cmd = 'mschedctl -R'
	                    status=runCmd(cmd)
	                    os.system('rm -f /tmp/image-deploy-fork.lock')
	                else:
	                    logging.debug( "Parent Process: PID# %s" % os.getpid())                    
            

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
