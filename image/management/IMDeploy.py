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
import socket, ssl
from subprocess import *
import logging
import logging.handlers
from xml.dom.minidom import Document, parse

from getpass import getpass
import hashlib

from IMClientConf import IMClientConf

default_euca_kernel = '2.6.27.21-0.1-xen'
class IMDeploy(object):
    ############################################################
    # __init__
    ############################################################
    def __init__(self, kernel, user, logger, passwd):
        super(IMDeploy, self).__init__()

        
        self.kernel = kernel
        self.user = user        
        self.logger = logger
        self.passwd = passwd

        self.machine = ""  #(india or minicluster or ...)
        self.loginmachine = ""
        self.shareddirserver = "" 
        
        #Load Configuration from file
        self._deployConf = IMClientConf()
        self._deployConf.load_deployConfig()        
        self._xcat_port = self._deployConf.getXcatPort()
        self._moab_port = self._deployConf.getMoabPort()
        self._http_server = self._deployConf.getHttpServer()        
        self._ca_certs = self._deployConf.getCaCertsDep()
        self._certfile = self._deployConf.getCertFileDep()
        self._keyfile = self._deployConf.getKeyFileDep()

        self.tempdir = "" #DEPRECATED

    #This need to be redo
    def euca_method(self):
                
        if isinstance(self.kernel, NoneType):
            self.kernel = default_euca_kernel
            
        """
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
        """

        #CONTACT IMDeployServerIaaS to customize image ...

        print 'Name-User: ' + self.name + '-' + self.user

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
        
        """
        urlparts = image.split("/")
        self.logger.debug(str(urlparts))
        if len(urlparts) == 1:
            nameimg = urlparts[0].split(".")[0]
        elif len(urlparts) == 2:
            nameimg = urlparts[1].split(".")[0]
        else:
            nameimg = urlparts[len(urlparts) - 1].split(".")[0]

        
        #REMOVE THIS. WE ONLY ALLOW DEPLOY IMAGES FROM REPOSITORY
        #NOW IT IS NOT NEEDED THE SHAREDDIRSERVER.
        
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
        """
        
        #xCAT server                
        self.logger.info('Connecting to xCAT server')

        #msg = self.name + ',' + self.operatingsystem + ',' + self.version + ',' + self.arch + ',' + self.kernel + ',' + self.shareddirserver + ',' + self.machine
        
        #self.shareddirserver + '/' + nameimg + '.tgz, '
        
        #Notify xCAT deployment to finish the job
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            xcatServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED)
            xcatServer.connect((self.xcatmachine, self._xcat_port))
            
            moabstring = ""
            
            msg =  str(image) + ', ' + str(self.kernel) + ', ' + self.machine + ', ' + str(self.user) + ', ' + str(self.passwd) + ", ldappassmd5" 
            self.logger.debug('Sending message: ' + msg)
            
            xcatServer.write(msg)
                        
            endloop = False
            fail = False
            while not endloop:
                ret = xcatServer.read(1024)
                if (ret == "OK"):
                    print "Your image request is being processed"
                    endloop = True
                elif (ret == "TryAuthAgain"):
                    print "Permission denied, please try again. User is "+self.user
                    m = hashlib.md5()
                    m.update(getpass())
                    passwd = m.hexdigest()
                    xcatServer.write(passwd)
                else:
                    print ret
                    endloop = True
                    fail = True
            
            if not fail:            
                #print msg
                ret = xcatServer.read(1024)
                #check if the server received all parameters
                if ret != 'OK':
                    self.logger.error('Incorrect reply from the xCat server:' + ret)
                    sys.exit(1)
                #recieve the prefix parameter from xcat server
                moabstring = xcatServer.read(2048)
                self.logger.debug("String received from xcat server " + moabstring)
                params = moabstring.split(',')
                imagename = params[0] + '' + params[2] + '' + params[1]
                self.logger.info('Connecting to Moab server')	    
                moabstring += ',' + self.machine
        
                self.logger.debug('Sending message: ' + moabstring)    
        except ssl.SSLError:
            self.logger.error("CANNOT establish SSL connection. EXIT")
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            moabServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED)
            moabServer.connect((self.moabmachine, self._moab_port))
            moabServer.write(moabstring)
            ret = moabServer.read(100)
            if ret != 'OK':
                self.logger.error('Incorrect reply from the Moab server:' + ret)
                sys.exit(1)
    
            self.logger.info('Your image has been deployed in xCAT as ' + imagename + '. Please allow a few minutes for xCAT to register the image before attempting to use it.')
        except ssl.SSLError:
            self.logger.error("CANNOT establish SSL connection. EXIT")

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
    logger.propagate = False #Do not propagate to others

    debugLevel = logging.INFO
 
    user = ""

    parser = OptionParser()

    logger.info('Starting image deployer...')

    parser.add_option('-i', '--image', dest='image', help='Name of tgz file that contains manifest and img')
    parser.add_option('-r', '--imgid', dest='imgid', help='Id of the image stored in the repository')

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

    try:
        user = os.environ['FG_USER']
    except KeyError:
        if type(ops.user) is not NoneType:
            user = ops.user
        else:
            logger.debug("you need to specify you user name. It can be donw using the FG_USER variable or the option -u/--user")
            sys.exit(1)

    print "Please insert the password for the user "+ops.user+""
    m = hashlib.md5()
    m.update(getpass())
    passwd = m.hexdigest()

    imgdeploy = IMDeploy(ops.kernel, user, logger, passwd)
    #Define the type

    if not isinstance(ops.image, NoneType) and not isinstance(ops.imgid, NoneType):
        parser.error('You only can not use -i/--image and -r/--imgid at the same time')
        sys.exit(1)
    elif not isinstance(ops.image, NoneType):
        if not  os.path.isfile(ops.image):
            parser.error('You need to specify a tgz that contains the image and the manifest (-i option)')
            logger.error('Image file not found')
            sys.exit(1)

    #EUCALYPTUS
    if not isinstance(ops.euca, NoneType):
        imgdeploy.euca_method()
    #XCAT
    elif not isinstance(ops.xcat, NoneType):
        if isinstance(ops.imgid, NoneType):
            parser.error('You need to specify the id of the image that you want to deploy (-r/--imgid option) \n'+ 
                          'The parameter -i/--image cannot be used with this type of deployment')
            sys.exit(1)
        else:
            imgdeploy.xcat_method(ops.xcat, ops.imgid)

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

