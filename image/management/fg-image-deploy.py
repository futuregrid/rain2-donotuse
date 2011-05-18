#!/usr/bin/python
# Description: Command line front end for image generator
#
# Author: Andrew J. Younge
#

from optparse import OptionParser
import sys
import os
from types import *
import socket
from subprocess import * 
import logging
import logging.handlers
from xml.dom.minidom import Document,parse


#Eventually need to move these to a config file
xcat_port = 56789
base_url = "http://fg-gravel3.futuregrid.iu.edu/"

#Default Kernels to use for each deployment
default_xcat_kernel = '2.6.18-164.el5'
default_euca_kernel = '2.6.27.21-0.1-xen'

TEST_MODE=False

def main():
    
    #Set up logging
    log_filename = 'fg-image-deploy.log'
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


    parser = OptionParser()

    logger.info('Starting image deployer...')
    
    parser.add_option('-i', '--image', dest='image', help='Name of tgz file that contains manifest and img')

    parser.add_option('-s', '--nasaddr', dest='nasaddr', help='Address to upload the image file')
    parser.add_option("-t", "--tempdir", dest="tempdir", help="shared dir to upload the image")
    
    parser.add_option('-x', '--xcat', dest='xcat', help='Deploy image to xCAT, which is in the specified addr')
    parser.add_option('-e', '--euca', dest='euca', help='Deploy the image to Eucalyptus, which is in the specified addr')
    parser.add_option('-n', '--nimbus', dest='nimbus', help='Deploy the image to Nimbus, which is in the specified addr')

    parser.add_option("-u", "--user", dest="user", help="FutureGrid username")

    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debugging")
    parser.add_option("-k", "--kernel", dest="kernel", help="Specify the desired kernel (must be exact version and approved for use within FG")

    (ops, args) = parser.parse_args()
    
    
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)
        ch.setLevel(logging.INFO)

    #Variables

    global name
    global givenname
    global operatingsystem
    global version
    global arch
    global kernel
    global user
    global manifestfile
    imagefile = '' 
    global manifest    
    nasaddr=''
    tempdirserver=''
    tempdir="/tmp/"
    name=""
    
    try:
        user = os.environ['FG_USER']
    except KeyError:
        if type(ops.user) is not NoneType:
            user = ops.user
        else:
            print "Please, define FG_USER to indicate your user name"
            sys.exit() 

    #if type(os.getenv('FG_USER')) is not NoneType:
    #    user = os.getenv('FG_USER')
    #elif type(ops.user) is not NoneType:
    #   user = ops.user
    #TODO: authenticate user via promting for CERT or password to auth against LDAP 

	
    #Get image destination
    if type(ops.image) is not NoneType:
    	
    	logger.info('untar file with image and manifest')
    	stat=os.system("tar xvfz "+ops.image)
    	
    	if (stat!=0):
            print "Error: the files were not extracted"
    	    sys.exit(1)
    	
    	
    	name=(ops.image).split(".")[0]
    	tempdir+=name+"/"
    	
    	manifestname=name+".manifest.xml"
    	
        manifestfile = open(manifestname, 'r')
        manifest = parse(manifestfile)

        #Determine where image filename, assuming same directory
        parts = ops.image.split('.')
        
        #for i in range(0,len(parts)-2):
        #    if i == 0:
        #        imagefile = parts[i]
        #    else:
        #        imagefile = imagefile + '.' + parts[i]
        imagefile = name+'.img'
        logger.info('Using image: '+imagefile)    
        
        name = manifest.getElementsByTagName('name')[0].firstChild.nodeValue.strip()
        givenname = manifest.getElementsByTagName('givenname')
        operatingsystem = manifest.getElementsByTagName('os')[0].firstChild.nodeValue.strip()
        version = manifest.getElementsByTagName('version')[0].firstChild.nodeValue.strip()
        arch = manifest.getElementsByTagName('arch')[0].firstChild.nodeValue.strip()
        #kernel = manifest.getElementsByTagName('kernel')[0].firstChild.nodeValue.strip()

        logger.debug(name + " "+ operatingsystem+ " " + version +" "+ arch)

    else:
        parser.error('You must specify the image manifest file to deploy')
        logger.error('Manifest file not specified')
        sys.exit(1)

    #EUCALYPTUS
    if type(ops.euca) is not NoneType:

        if type(ops.kernel) is NoneType:
            kernel = default_euca_kernel
        else:
            kernel = ops.kernel
    
        #Mount the root image for final edits and compressing
        logger.info('Mounting image...')
        cmd = 'mkdir -p '+tempdir+''+ name
        runCmd(cmd)
        cmd = 'sudo mount -o loop ' + imagefile + ' '+tempdir+''+ name
        runCmd(cmd)

        #TODO: Pick kernel and ramdisk from available eki and eri

        #hardcoded for now
        eki = 'eki-78EF12D2'
        eri = 'eri-5BB61255'
 

        #Inject the kernel
        logger.info('Retrieving kernel '+kernel)
        runCmd('sudo wget '+base_url+'kernel/'+kernel+'.modules.tar.gz -O '+tempdir+''+kernel+'.modules.tar.gz')
        runCmd('sudo tar xfz '+tempdir+''+kernel+'.modules.tar.gz --directory '+tempdir+''+name+'/lib/modules/')
        logger.info('Injected kernel '+kernel)


        # Setup fstab
        fstab = '''
# Default Ubuntu fstab
 /dev/sda1       /             ext3     defaults,errors=remount-ro 0 0
 /dev/sda3    swap          swap     defaults              0 0
 proc            /proc         proc     defaults                   0 0
 devpts          /dev/pts      devpts   gid=5,mode=620             0 0
 '''

        f= open(tempdir+'/fstab', 'w')
        f.write(fstab)
        f.close()
        os.system('sudo mv -f '+tempdir+'/fstab '+tempdir+'rootimg/etc/fstab')
        logger.info('Injected fstab')

        #Done making changes to root fs
        runCmd('sudo umount '+tempdir+''+name)
        
        print 'Name-User: ' +name + '-'+ user

##TODO. I think that this should be in deploy-server

        #Bucket folder
        runCmd('mkdir -p '+tempdir+''+ user)

        #Bundle Image
        cmd = 'euca-bundle-image --image '+tempdir+'' + name +'.img --destination '+tempdir+''+user+ ' --kernel ' + eki + ' --ramdisk ' + eri
        runCmd(cmd)

        #Upload bundled image
        cmd = 'bash -c \" cd '+tempdir+'; euca-upload-bundle --bucket ' + user + ' --manifest '+user+'/'+name+'.img.manifest.xml \"'
        os.system(cmd)    

        #Register image
        cmd = 'bash -c \" cd '+tempdir+'; euca-register '+user+'/'+name+'.img.manifest.xml \"'
        os.system(cmd)
    

    #XCAT
    elif type(ops.xcat) is not NoneType:
        
        if type(ops.nasaddr) is not NoneType:
            nasaddr=ops.nasaddr
        else:
            print "You need to specify the machine where you are going to upload the image"
            print "This is the login machine if the cluster"
            sys.exit(1)
        
        logger.info("server "+nasaddr)
           
        if type(ops.tempdir) is not NoneType:
            tempdirserver=ops.tempdir
        else:
            print "You need to specify a directory to upload the image"
            print "This is a directory in the login machine that is shared with the xCAT server machine"
            sys.exit(1)
        
        logger.info("server dir "+tempdirserver)
        
        #Select kernel version    
        if type(ops.kernel) is NoneType:
            kernel = default_xcat_kernel
        else:
            kernel = ops.kernel
    
        #Mount the root image for final edits and compressing
        logger.info('Mounting image...')
        cmd = 'mkdir -p '+tempdir+'/rootimg'
        runCmd(cmd)
        cmd = 'sudo mount -o loop ' + imagefile + ' '+tempdir+'/rootimg/'
        runCmd(cmd)


        logger.info('Installing torque')
        if(TEST_MODE):
            logger.info('Torque for minicluster')
            runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.5.1_minicluster/torque-2.5.1.tgz'+\
                   ' fg-gravel3.futuregrid.iu.edu/torque/torque-2.5.1_minicluster/var.tgz')   
            runCmd('sudo tar xfz torque-2.5.1.tgz -C '+tempdir+'/rootimg/usr/local/')
            runCmd('sudo tar xfz var.tgz -C '+tempdir+'/rootimg/')
            runCmd('sudo rm -f var.tgz torque-2.5.1.tgz')
            runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.5.1_minicluster/pbs_mom -O '+tempdir+'/rootimg/etc/init.d/pbs_mom')
            
            os.system('touch ./inittab')
            os.system('cat '+tempdir+'/rootimg/etc/inittab'+' > ./inittab')            
            f= open('./inittab', 'a')
            f.write("\n"+"pbs:35:respawn:/etc/init.d/pbs_mom start")        
            f.close()          
            os.system('sudo mv -f ./inittab '+tempdir+'/rootimg/etc/inittab')
            os.system('sudo chown root:root '+tempdir+'/rootimg/etc/inittab')
            
            
        else:#Later we should be able to chose the cluster where is deployed
            logger.info('Torque for India')    
            runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/conf/hosts_india -O '+tempdir+'/rootimg/etc/hosts')
            runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.4.8_india/opt.tgz'+\
                   ' fg-gravel3.futuregrid.iu.edu/torque/torque-2.4.8_india/var.tgz')   
            runCmd('sudo tar xfz opt.tgz -C '+tempdir+'/rootimg/')
            runCmd('sudo tar xfz var.tgz -C '+tempdir+'/rootimg/')
            runCmd('sudo rm -f var.tgz opt.tgz')            
            runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.4.8_india/pbs_mom -O '+tempdir+'/rootimg/etc/init.d/pbs_mom')
            
        runCmd('sudo chmod +x '+tempdir+'/rootimg/etc/init.d/pbs_mom')
        runCmd('sudo chroot '+tempdir+'/rootimg/ /sbin/chkconfig --add pbs_mom')
        runCmd('sudo chroot '+tempdir+'/rootimg/ /sbin/chkconfig pbs_mom on')  
        
        f= open(tempdir+'/config', 'w')
        f.write("opsys "+ operatingsystem + "-" + name+"\n"+"arch "+ arch)        
        f.close()
        
        os.system('sudo mv '+tempdir+'/config '+tempdir+'/rootimg/var/spool/torque/mom_priv/')
        os.system('sudo chown root:root '+tempdir+'/rootimg/var/spool/torque/mom_priv/config')

        #Inject the kernel
        logger.info('Retrieving kernel '+kernel)
        runCmd('sudo wget '+base_url+'kernel/'+kernel+'.modules.tar.gz -O '+tempdir+''+kernel+'.modules.tar.gz')
        runCmd('sudo tar xfz '+tempdir+''+kernel+'.modules.tar.gz --directory '+tempdir+'/rootimg/lib/modules/')
        logger.info('Injected kernel '+kernel)


        #Setup fstab
        fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
149.165.145.50:/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
 '''
        f= open(tempdir+'/fstab', 'w')
        f.write(fstab)
        f.close()
        os.system('sudo mv -f '+tempdir+'/fstab '+tempdir+'rootimg/etc/fstab')
        logger.info('Injected fstab')

        #NOTE: May move to an image repository system in the future
        logger.info('Compressing image')
        #Its xCAT, so use gzip with cpio compression.
        cmd = 'sudo bash -c \" cd '+tempdir+'; find rootimg/. | cpio -H newc -o | gzip -9 > '+tempdir+'/rootimg.gz\"'
        os.system(cmd) #use system because of the pipes

        #cmd = 'sudo tar cfz '+tempdir+'' + name + '.tar.gz --directory '+tempdir+' ' + name 

        cmd = 'sudo umount '+tempdir+'rootimg'
        runCmd(cmd)
        
        #Copy the image to the Shared directory.        
        logger.info('Uploading image. You may be asked for ssh/paraphrase password')
        cmd = 'scp '+tempdir+'rootimg.gz ' + user + '@' + nasaddr + ':'+tempdirserver+'/'+name+'.gz'
        logger.info(cmd)
        runCmd(cmd)
        
        
        #if name is in tempdir string then del tempdir, else only rootimg
        logger.info('sudo rm -rf '+tempdir)
        runCmd("sudo rm -rf "+tempdir)
        
        #remove local img and manifest
        runCmd("rm -f "+manifestname+" "+imagefile)

        #xCAT server
        dest = ops.xcat
        
        logger.info('Connecting to xCAT server')

        msg = name+','+operatingsystem+','+version+','+arch+','+kernel+','+tempdirserver
        logging.debug('Sending message: ' + msg)

        #Notify xCAT deployment to finish the job
        xcatServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        xcatServer.connect((dest, xcat_port))

        xcatServer.send(msg)
        ret = xcatServer.recv(100)
        if ret != 'OK':
            logger.error('Incorrect reply from the server:'+ret)
            sys.exit(1)

        logger.info('Image deployed to xCAT. Please allow a few minutes for xCAT to register the image before attempting to use it.')
        
    
    #NIMBUS
    elif type(ops.nimbus) is not NoneType:
        #TODO
        roar = 0    
    #else:
    #    parser.error('You must specify at least one deployment destination type (xcat|euca|nimbus)')
    #    logger.error('Deployment type not specified')
    #        sys.exit(1)

    #


    

def runCmd(cmd):
    cmdLog = logging.getLogger('exec')
    cmdLog.debug(cmd)
    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE) 
    std = p.communicate()
    if len(std[0]) > 0: 
        cmdLog.debug('stdout: '+std[0])
    #cmdLog.debug('stderr: '+std[1])

    #cmdLog.debug('Ret status: '+str(p.returncode))
    if p.returncode != 0:
        cmdLog.error('Command: '+cmd+' failed, status: '+str(p.returncode)+' --- '+std[1])
        sys.exit(p.returncode)





if __name__ == "__main__":
    main()
#END


