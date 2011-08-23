#!/usr/bin/env python
"""
Command line front end for image deployment
"""

__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.1'

from optparse import OptionParser
import sys
import os
from types import *
import socket
from subprocess import *
import logging
import logging.handlers
from xml.dom.minidom import Document, parse
from IMClientConf import IMClientConf

default_euca_kernel = '2.6.27.21-0.1-xen'
class IMDeploy(object):
    ############################################################
    # __init__
    ############################################################
    def __init__(self, kernel, user, logger):
        super(IMDeploy, self).__init__()

        
        self.kernel = kernel
        self.user = user        
        self.logger = logger

        self.machine = ""  #(india or minicluster or ...)
        self.loginmachine = ""
        self.shareddirserver = "" 
               
        """
        #from manifest
        self.name = ""
        self.givenname = ""
        self.operatingsystem = ""
        self.version = ""
        self.arch = ""
        """
        
        #Load Configuration from file
        self._deployConf = IMClientConf()
        self._deployConf.load_deployConfig()        
        self._xcat_port = self._deployConf.getXcatPort()
        self._moab_port = self._deployConf.getMoabPort()
        self._http_server = self._deployConf.getHttpServer()
        self.tempdir = self._deployConf.getTempDir()  #root of the temporal directory to extract image



    #This need to be redo
    def euca_method(self):
                
        if isinstance(self.kernel, NoneType):
            self.kernel = default_euca_kernel

        #Mount the root image for final edits and compressing
        self.logger.info('Mounting image...')
        cmd = 'mkdir -p ' + self.tempdir + '' + self.name
        self.runCmd(cmd)
        cmd = 'sudo mount -o loop ' + self.imagefile + ' ' + self.tempdir + '' + self.name
        self.runCmd(cmd)

        #TODO: Pick kernel and ramdisk from available eki and eri

        #hardcoded for now
        eki = 'eki-78EF12D2'
        eri = 'eri-5BB61255'


        #Inject the kernel
        self.logger.info('Retrieving kernel ' + kernel)
        self.runCmd('sudo wget ' + self._http_server + 'kernel/' + self.kernel + '.modules.tar.gz -O ' + self.tempdir + '' + self.kernel + '.modules.tar.gz')
        self.runCmd('sudo tar xfz ' + self.tempdir + '' + self.kernel + '.modules.tar.gz --directory ' + self.tempdir + '' + self.name + '/lib/modules/')
        self.logger.info('Injected kernel ' + kernel)


        # Setup fstab
        fstab = '''
# Default Ubuntu fstab
 /dev/sda1       /             ext3     defaults,errors=remount-ro 0 0
 /dev/sda3    swap          swap     defaults              0 0
 proc            /proc         proc     defaults                   0 0
 devpts          /dev/pts      devpts   gid=5,mode=620             0 0
 '''

        f = open(self.tempdir + '/fstab', 'w')
        f.write(fstab)
        f.close()
        os.system('sudo mv -f ' + self.tempdir + '/fstab ' + self.tempdir + 'rootimg/etc/fstab')
        self.logger.info('Injected fstab')

        #Done making changes to root fs
        self.runCmd('sudo umount ' + self.tempdir + '' + self.name)

        print 'Name-User: ' + self.name + '-' + self.user

##TODO. I think that this should be in deploy-server

        #Bucket folder
        self.runCmd('mkdir -p ' + self.tempdir + '' + self.user)

        #Bundle Image
        cmd = 'euca-bundle-image --image ' + self.tempdir + '' + self.name + '.img --destination ' + self.tempdir + '' + self.user + ' --kernel ' + eki + ' --ramdisk ' + eri
        self.runCmd(cmd)

        #Upload bundled image
        cmd = 'bash -c \" cd ' + self.tempdir + '; euca-upload-bundle --bucket ' + self.user + ' --manifest ' + self.user + '/' + self.name + '.img.manifest.xml \"'
        os.system(cmd)

        #Register image
        cmd = 'bash -c \" cd ' + self.tempdir + '; euca-register ' + self.user + '/' + self.name + '.img.manifest.xml \"'
        os.system(cmd)

       

    def xcat_method(self, xcat, image):
        
        #Load Machines configuration
        xcat = xcat.lower()
        if (xcat == "india" or xcat == "india.futuregrid.org"):
            self.machine = "india"
        elif (xcat == "minicluster" or xcat == "tm1r" or xcat == "tm1r.tidp.iu.futuregrid.org"):
            self.machine = "minicluster"
        else:
            self.logger.error("Machine name not recognized")
            sys.exit(1)
        
        self._deployConf.load_machineConfig(self.machine)
        self.loginmachine = self._deployConf.getLoginMachine()
        self.xcatmachine = self._deployConf.getXcatMachine()
        self.moabmachine = self._deployConf.getMoabMachine()        
        self.shareddirserver = self._deployConf.getSharedDir()

        self.logger.debug("login machine " + self.loginmachine)
        self.logger.debug("xcat machine " + self.xcatmachine)
        self.logger.debug("moab machine " + self.moabmachine)
        self.logger.debug("shared dir between login machine and xcat machine" + self.shareddirserver)
        #################
        

        
        urlparts = image.split("/")
        self.logger.debug(str(urlparts))
        if len(urlparts) == 1:
            nameimg = urlparts[0].split(".")[0]
        elif len(urlparts) == 2:
            nameimg = urlparts[1].split(".")[0]
        else:
            nameimg = urlparts[len(urlparts) - 1].split(".")[0]

        
        #Copy the image to the Shared directory.
        if (self.loginmachine == "localhost" or self.loginmachine == "127.0.0.1"):
            self.logger.info('Copying the image to the right directory')
            cmd = 'cp ' + image + ' ' + self.shareddirserver + '/' + nameimg + '.tgz'
            self.logger.info(cmd)
            self.runCmd(cmd)
        else:                    
            self.logger.info('Uploading image. You may be asked for ssh/paraphrase password')
            cmd = 'scp ' + image + ' ' + self.user + '@' + self.loginmachine + ':' + self.shareddirserver + '/' + nameimg + '.tgz'
            self.logger.info(cmd)
            self.runCmd(cmd)
        
        #xCAT server                
        self.logger.info('Connecting to xCAT server')

        #msg = self.name + ',' + self.operatingsystem + ',' + self.version + ',' + self.arch + ',' + self.kernel + ',' + self.shareddirserver + ',' + self.machine
        
        msg=self.shareddirserver + '/' + nameimg + '.tgz, '+str(self.kernel)
        self.logger.debug('Sending message: ' + msg)

        #Notify xCAT deployment to finish the job
        xcatServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        xcatServer.connect((self.xcatmachine, self._xcat_port))

        xcatServer.send(msg)
        #check if the server received all parameters
        ret = xcatServer.recv(1024)
        if ret != 'OK':
            self.logger.error('Incorrect reply from the xCat server:' + ret)
            sys.exit(1)

        #recieve the prefix parameter from xcat server
        moabstring = xcatServer.recv(2048)
        self.logger.debug("String receved from xcat server " + moabstring)

        self.logger.info('Connecting to Moab server')

        moabstring += ',' + self.machine

        self.logger.debug('Sending message: ' + moabstring)

        moabServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        moabServer.connect((self.moabmachine, self._moab_port))
        moabServer.send(moabstring)
        ret = moabServer.recv(100)
        if ret != 'OK':
            self.logger.error('Incorrect reply from the Moab server:' + ret)
            sys.exit(1)


        self.logger.info('Image deployed to xCAT. Please allow a few minutes for xCAT to register the image before attempting to use it.')


    def runCmd(self, cmd):
        cmdLog = logging.getLogger('DeployClient.exec')
        cmdLog.debug(cmd)
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
        std = p.communicate()
        if len(std[0]) > 0:
            cmdLog.debug('stdout: ' + std[0])
        #cmdLog.debug('stderr: '+std[1])

        #cmdLog.debug('Ret status: '+str(p.returncode))
        if p.returncode != 0:
            cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
            sys.exit(p.returncode)



def main():

    logger = logging.getLogger("DeployClient")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    #handler = logging.FileHandler(log_filename)
    #handler.setLevel(logging.DEBUG)
    #handler.setFormatter(formatter)
    #logger.addHandler(handler)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    logger.propagate=False #Do not propagate to others

    debugLevel = logging.INFO
 
    user = ""

    parser = OptionParser()

    logger.info('Starting image deployer...')

    parser.add_option('-i', '--image', dest='image', help='Name of tgz file that contains manifest and img')

    #parser.add_option('-s', '--nasaddr', dest = 'nasaddr', help = 'Address to upload the image file. Login machine')
    #parser.add_option("-t", "--tempdir", dest = "shareddirserver", help = "shared dir to upload the image")
    #parser.add_option('-m', '--moab', dest = 'moab', help = 'Address of the machine that has Moab. (localhost if not specified)')

    parser.add_option('-x', '--xcat', dest='xcat', help='Deploy image to xCAT. The argument is the machine name (minicluster, india ...)')
    parser.add_option('-e', '--euca', dest='euca', help='Deploy the image to Eucalyptus, which is in the specified addr')
    parser.add_option('-n', '--nimbus', dest='nimbus', help='Deploy the image to Nimbus, which is in the specified addr')

    parser.add_option("-u", "--user", dest="user", help="FutureGrid username")

    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debug logs")
    parser.add_option("-k", "--kernel", dest="kernel", help="Specify the desired kernel (must be exact version and approved for use within FG). Not yet supported")

    (ops, args) = parser.parse_args()

    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit(1)

    if not ops.debug:        
        ch.setLevel(logging.INFO)

    #defining FG user
    try:
        user = os.environ['FG_USER']
    except KeyError:
        if not isinstance(ops.user, NoneType):
            user = ops.user
        else:
            parser.error("Please, define FG_USER to indicate your user name or specify it by using the -u option")
            logger.error("User not specified")
            sys.exit(1)

    imgdeploy = IMDeploy(ops.kernel, user, logger)
    #Define the type

    #Get image destination
    if isinstance(ops.image, NoneType) or not  os.path.isfile(ops.image):
        parser.error('You need to specify a tgz that contains the image and the manifest (-i option)')
        logger.error('Image file not found')
        sys.exit(1)

    #EUCALYPTUS
    if not isinstance(ops.euca, NoneType):
        imgdeploy.euca_method()
    #XCAT
    elif not isinstance(ops.xcat, NoneType):        
        imgdeploy.xcat_method(ops.xcat, ops.image)

    #NIMBUS
    elif not isinstance(ops.nimbus, NoneType):
        #TODO
        roar = 0
        logger.info("This is not yet implemented")
    else:
        logger.error('Deployment type not specified')
        parser.error('You need to specify at least one deployment destination type: xcat (-x option), euca (-e option) or nimbus(-n option)')
        sys.exit(1)


if __name__ == "__main__":
    main()
#END

