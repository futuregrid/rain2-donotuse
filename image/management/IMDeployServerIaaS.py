#!/usr/bin/env python
"""
Description: IaaS image deployment server.  Customizes images and return them to the user side to deploy them in the 
corresponding IaaS framework
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
from xml.dom.minidom import Document, parse

#Import client repository
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__) + "/../")
from repository.client.IRServiceProxy import IRServiceProxy

class IMDeployServerIaaS(object):

    def __init__(self):
        super(IMDeployServerIaaS, self).__init__()
        
        
        self.path = ""
        
        self.numparams = 4   #image path
        
        self.name = ""
        self.givenname = ""
        self.operatingsystem = ""
        self.version = ""
        self.arch = ""                
        self.kernel = ""
        self.user = ""
        self.iaas = ""

        #load from config file
        self._deployConf = IMServerConf()
        self._deployConf.load_deployServerXcatConfig() 
        
        self.port = self._deployConf.getXcatPort()
        self.http_server = self._deployConf.getHttpServer()
                        
        self.tempdir = self._deployConf.getTempDirIaaS()
        self.log_filename = self._deployConf.getLogIaaS()
        self.logLevel = self._deployConf.getLogLevelIaaS()
        
        self._ca_certs = self._deployConf.getCaCertsIaaS()
        self._certfile = self._deployConf.getCertFileIaaS()
        self._keyfile = self._deployConf.getKeyFileIaaS()
                
        
        print "\nReading Configuration file from " + self._deployConf.getConfigFile() + "\n"
        
        self.logger = self.setup_logger()
        
        #Image repository Object
        self._reposervice = IRServiceProxy(False)
        
    def setup_logger(self):
        #Setup logging
        logger = logging.getLogger("DeployXcat")
        logger.setLevel(self.logLevel)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.log_filename)
        handler.setLevel(self.logLevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        
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
                #print connstream
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
        #print data
        #params[0] is image ID or image path
        #param [1] is the source of the image (repo,disk).
        #params[2] is the kernel
        #params[3] is the user
        #params[4] is the iaas cloud
        
        imgID = params[0]
        imgSource = params[1].strip()
        self.kernel = params[2].strip()
        self.user = params[3].strip()
        self.iaas = params[4].strip()
                       
        if len(params) != self.numparams:
            msg = "ERROR: incorrect message"
            self.errormsg(connstream, msg)
            return

        #GET IMAGE from repo
        self.logger.info("Retrieving image from repository")
        image = self._reposervice.get(self.user, "img", imgID, self.tempdir)      
        if image == None:
            msg = "ERROR: Cannot get access to the image with imgId " + image
            self.errormsg(connstream, msg)
            return            
        ################

        if not os.path.isfile(image):
            msg = "ERROR: file " + image + " not found"
            self.errormsg(connstream, msg)
            return
        
        #extracts image/manifest, read manifest 
        localtempdir = ""
        if not self.handle_image(image, localtempdir, connstream):
            return            

        

        #Select kernel version
        #This is not yet supported as we get always the same kernel
        self.logger.debug("kernel: " + self.kernel)

        
        if (self.cloud == "euca"):
            self.euca_method()
        elif (self.cloud == "nimbus"):
            pass
        elif (self.cloud == "opennebula"):
            pass
        elif (self.cloud == "openstack"):
            pass    
        
        #connstream.write("OK")

        #wait until client retrieve img
        connstream.read()
        #remove files
        cmd = 'rm -rf ' + image + " " + localtempdir        
        status = self.runCmd(cmd)
            
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()
            

    def euca_method(self): #JUST COPIED. NEED TO BE MODIFIED
        
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

    def handle_image(self, image, localtempdir, connstream):
        #print image
        success = True   
        urlparts = image.split("/")
        #print urlparts
        self.logger.debug("urls parts: " + str(urlparts))
        if len(urlparts) == 1:
            nameimg = urlparts[0].split(".")[0]
        elif len(urlparts) == 2:
            nameimg = urlparts[1].split(".")[0]
        else:
            nameimg = urlparts[len(urlparts) - 1].split(".")[0]

        self.logger.debug("image name " + nameimg)

        localtempdir = self.tempdir + "/" + nameimg + "_0"

        cmd = 'mkdir -p ' + localtempdir
        self.runCmd(cmd)

        realnameimg = ""
        self.logger.info('untar file with image and manifest')
        cmd = "sudo tar xvfz " + image + " -C " + localtempdir
        self.logger.debug(cmd)        
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
        std = p.communicate()
        stat = 0
        if len(std[0]) > 0:
            realnameimg= std[0].split("\n")[0].strip().split(".")[0]            
        if p.returncode != 0:
            self.logger.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
            stat = 1

        if (stat != 0):
            msg = "Error: the files were not extracted"
            self.errormsg(connstream, msg)
            success = False
        else:
            self.manifestname = realnameimg + ".manifest.xml"
    
            manifestfile = open(localtempdir + "/" + self.manifestname, 'r')
            manifest = parse(manifestfile)
    
            self.name = ""
            self.givenname = ""
            self.operatingsystem = ""
            self.version = ""
            self.arch = ""        
    
            self.name = manifest.getElementsByTagName('name')[0].firstChild.nodeValue.strip()
            self.givenname = manifest.getElementsByTagName('givenname')
            self.operatingsystem = manifest.getElementsByTagName('os')[0].firstChild.nodeValue.strip()
            self.version = manifest.getElementsByTagName('version')[0].firstChild.nodeValue.strip()
            self.arch = manifest.getElementsByTagName('arch')[0].firstChild.nodeValue.strip()
            #kernel = manifest.getElementsByTagName('kernel')[0].firstChild.nodeValue.strip()
    
            self.logger.debug(self.name + " " + self.operatingsystem + " " + self.version + " " + self.arch)
            success = True

        return success

    def errormsg(self, connstream, msg):
        self.logger.error(msg)
        connstream.write(msg)
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()
    
    def runCmd(self, cmd):
        cmd = 'sudo ' + cmd
        cmdLog = logging.getLogger('DeployXcat.exec')
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

    server = IMDeployServerXcat()
    server.start()

if __name__ == "__main__":
    main()
#END
