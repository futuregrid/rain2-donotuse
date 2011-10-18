#!/usr/bin/env python
"""
Description: IaaS image deployment server.  Customizes images and return them to the user side to deploy them in the 
corresponding IaaS framework
"""
__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.1'

from types import *
import re
import logging
import logging.handlers
import random
from random import randrange
import os
import sys
import socket, ssl
from multiprocessing import Process

from subprocess import *
#from xml.dom.ext import *
from xml.dom.minidom import Document, parseString, parse
import xmlrpclib
import time
from IMServerConf import IMServerConf

#Import client repository
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")
from image.repository.client.IRServiceProxy import IRServiceProxy
from utils.FGTypes import FGCredential
from utils import FGAuth


class IMDeployServerIaaS(object):

    def __init__(self):
        super(IMDeployServerIaaS, self).__init__()
        
        
        self.path = ""
        
        self.numparams = 7   #image path
        
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
        self._deployConf.load_deployServerIaasConfig() 
        
        self.port = self._deployConf.getIaasPort()
        self.http_server = self._deployConf.getHttpServerIaas()
        self.proc_max = self._deployConf.getProcMaxIaas()
                        
        self.tempdir = self._deployConf.getTempDirIaas()
        self.log_filename = self._deployConf.getLogIaas()
        self.logLevel = self._deployConf.getLogLevelIaas()
        
        self._ca_certs = self._deployConf.getCaCertsIaas()
        self._certfile = self._deployConf.getCertFileIaas()
        self._keyfile = self._deployConf.getKeyFileIaas()
        
        
        self.default_euca_kernel = '2.6.27.21-0.1-xen'
        self.default_openstack_kernel = '2.6.28-11-generic'
        self.default_kvm_centos5_kernel = '2.6.18-238.el5'
        self.default_kvm_ubuntu_kernel = '2.6.35-22-generic'
        
        print "\nReading Configuration file from " + self._deployConf.getConfigFile() + "\n"
        
        self.logger = self.setup_logger("")
        
        #Image repository Object
        verbose=False
        printLogStdout=False
        self._reposervice = IRServiceProxy(verbose,printLogStdout)
        
    def setup_logger(self, extra):
        #Setup logging        
        logger = logging.getLogger("DeployIaaS"+extra)
        logger.setLevel(self.logLevel)    
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.log_filename)
        handler.setLevel(self.logLevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False #Do not propagate to others
        
        return logger

    def start(self): ##DO IT parallel
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.port))
        sock.listen(1)
        self.logger.info('Starting Server on port ' + str(self.port))
        
        proc_list = []
        total_count = 0
        while True:        
            if len(proc_list) == self.proc_max:
                full = True
                while full:
                    for i in range(len(proc_list) - 1, -1, -1):
                        #self.logger.debug(str(proc_list[i]))
                        if not proc_list[i].is_alive():
                            #print "dead"                        
                            proc_list.pop(i)
                            full = False
                    if full:
                        time.sleep(self.refresh_status)
            
            total_count += 1
            #channel, details = sock.accept()
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
                proc_list.append(Process(target=self.process_client, args=(connstream,)))            
                proc_list[len(proc_list) - 1].start()
            except ssl.SSLError:
                self.logger.error("Unsuccessful connection attempt from: " + repr(fromaddr))
                self.logger.info("IaaS deploy server Request DONE")
            except socket.error:
                self.logger.error("Error with the socket connection")
                self.logger.info("IaaS deploy server Request DONE")
            except:
                self.logger.error("Uncontrolled Error: " + str(sys.exc_info()))
                if type(connstream) is ssl.SSLSocket: 
                    connstream.shutdown(socket.SHUT_RDWR)
                    connstream.close() 
                self.logger.info("IaaS deploy server Request DONE")
                        
     
    def auth(self, userCred):
        return FGAuth.auth(self.user, userCred)             
                
    def process_client(self, connstream):
        self.logger = self.setup_logger("." + str(os.getpid()))        
        self.logger.info('Accepted new connection')
        
        #receive the message
        data = connstream.read(2048)
        params = data.split(',')
        #print data
        #params[0] is image ID or image path
        #param [1] is the source of the image (repo,disk).
        #params[2] is the iaas cloud
        #params[3] is the kernel
        #params[4] is the user
        #params[5] is the user password
        #params[6] is the type of password
        
        imgID = params[0].strip()
        imgSource = params[1].strip()
        self.iaas = params[2].strip()
        self.kernel = params[3].strip()
        self.user = params[4].strip()
        passwd = params[5].strip()
        passwdtype = params[6].strip()
        
                       
        if len(params) != self.numparams:
            msg = "ERROR: incorrect message"
            self.errormsg(connstream, msg)
            return

        retry = 0
        maxretry = 3
        endloop = False
        while (not endloop):
            userCred = FGCredential(passwdtype, passwd)
            if (self.auth(userCred)):
                connstream.write("OK")
                endloop = True
            else:
                retry += 1
                if retry < maxretry:
                    connstream.write("TryAuthAgain")
                    passwd = connstream.read(2048)
                else:
                    msg = "ERROR: authentication failed"
                    endloop = True
                    self.errormsg(connstream, msg)
                    return

                self.logger.debug("image name " + nameimg)

        #create a unique directory
        auxdir = str(randrange(999999999999999999999999))
        localtempdir = self.tempdir + "/" + auxdir + "_0"
        while os.path.isfile(localtempdir):
            auxdir = str(randrange(999999999999999999999999))
            localtempdir = self.tempdir + "/" + auxdir + "_0"

        cmd = 'mkdir -p ' + localtempdir
        self.runCmd(cmd)

        if imgSource == "repo":
            #GET IMAGE from repo
            if not self._reposervice.connection():
                msg = "ERROR: Connection with the Image Repository failed"
                self.errormsg(connstream, msg)
                return
            else:
                self.logger.info("Retrieving image from repository")
                image = self._reposervice.get(self.user, passwd, self.user, "img", imgID, localtempdir)                  
                if image == None:
                    msg = "ERROR: Cannot get access to the image with imgId " + str(imgID)
                    self.errormsg(connstream, msg)
                    self._reposervice.disconnect()
                    return
                else:
                    self._reposervice.disconnect()
        else:
            connstream.write(localtempdir)
            status = connstream.read(1024)
            
            status = status.split(',')
            
            if len(status)==2:
                image = localtempdir + '/' + status[1].strip()
                if status[0].strip() != 'OK':                
                    msg = "ERROR: Receiving image from client: "+str(status)
                    self.errormsg(connstream, msg)
                    return
            else:
                msg = "ERROR: Message received from client is incorrect: "+str(status)
                self.errormsg(connstream, msg)
                return

        if not os.path.isfile(image):
            msg = "ERROR: file " + image + " not found"
            self.errormsg(connstream, msg)
            return
        
        #extracts image/manifest, read manifest
        if not self.handle_image(image, localtempdir, connstream):
            return            

        #self.preprocess()
        
        if (self.iaas == "euca"):
            self.euca_method(localtempdir)
        elif (self.iaas == "nimbus"):
            pass
        elif (self.iaas == "opennebula"):
            self.opennebula_method(localtempdir)
        elif (self.iaas == "openstack"):
            self.openstack_method(localtempdir)  
        
        #umount the image
        max_retry = 5
        retry_done = 0
        umounted = False
        #Done making changes to root fs
        while not umounted: 
            status = self.runCmd('sudo umount ' + localtempdir + '/temp')
            if status == 0:
                umounted = True
            elif retry_done == max_retry:
                umounted = True
                self.logger.error("Problems to umount the image")
            else:
                time.sleep(2)
                
        connstream.write(localtempdir + '/' + self.name + '.img,'+self.kernel+","+self.operatingsystem)

        #wait until client retrieve img
        self.logger.info("Wait until client get the image")
        connstream.read()
        #remove image
        cmd = 'rm -rf ' + localtempdir
        status = self.runCmd(cmd)
        
        try:
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()
        except:
            self.logger.error("ERROR: "+str(sys.exc_info()))
        self.logger.info("Image Deploy Request DONE")

    def euca_method(self, localtempdir): 

        #Select kernel version
        #This is not yet supported as we get always the same kernel
        self.logger.debug("kernel: " + self.kernel)
        if self.kernel == "None":
            self.kernel = self.default_euca_kernel
                      
        #Inject the kernel
        self.logger.info('Retrieving kernel ' + self.kernel)
        self.runCmd('wget ' + self.http_server + 'kernel/' + self.kernel + '.modules.tar.gz -O ' + localtempdir + '/' + self.kernel + '.modules.tar.gz')
        self.runCmd('sudo tar xfz ' + localtempdir + '/' + self.kernel + '.modules.tar.gz --directory ' + localtempdir + '/temp/lib/modules/')
        self.logger.info('Injected kernel ' + self.kernel)

        # Setup fstab
        fstab = '''
# Default fstab
 /dev/sda1       /             ext3     defaults,errors=remount-ro 0 0
 /dev/sda3    swap          swap     defaults              0 0
 proc            /proc         proc     defaults                   0 0
 devpts          /dev/pts      devpts   gid=5,mode=620             0 0
 '''

        f = open(localtempdir + '/fstab', 'w')
        f.write(fstab)
        f.close()
        self.runCmd('sudo mv -f ' + localtempdir + '/fstab ' + localtempdir + '/temp/etc/fstab')
        self.runCmd('sudo chown root:root ' + localtempdir + '/temp/etc/fstab')
        self.logger.info('fstab Injected')

        

    def openstack_method(self, localtempdir): #TODO

        #Select kernel version
        #This is not yet supported as we get always the same kernel
        self.logger.debug("kernel: " + self.kernel)
        if self.kernel == "None":
            self.kernel = self.default_openstack_kernel
                      
        #Inject the kernel
        self.logger.info('Retrieving kernel ' + self.kernel)
        self.runCmd('wget ' + self.http_server + 'kernel/' + self.kernel + '.modules.tar.gz -O ' + localtempdir + '/temp/' + self.kernel + '.modules.tar.gz')
        self.runCmd('sudo tar xfz ' + localtempdir + '/temp/' + self.kernel + '.modules.tar.gz --directory ' + localtempdir + '/temp/lib/modules/')
        self.logger.info('Injected kernel ' + kernel)

        # Setup fstab
        fstab = '''
# Default fstab
 /dev/sda1       /             ext3     defaults,errors=remount-ro 0 0
 /dev/sda3    swap          swap     defaults              0 0
 proc            /proc         proc     defaults                   0 0
 devpts          /dev/pts      devpts   gid=5,mode=620             0 0
 
 '''

        f = open(localtempdir + '/fstab', 'w')
        f.write(fstab)
        f.close()
        self.runCmd('sudo mv -f ' + localtempdir + '/fstab ' + localtempdir + '/temp/etc/fstab')
        self.runCmd('sudo chown root:root ' + localtempdir + '/temp/etc/fstab')
        self.logger.info('fstab Injected')

    def opennebula_method(self, localtempdir): 

        #Select kernel version
        #This is not yet supported as we get always the same kernel
        self.logger.debug("kernel: " + self.kernel)
                
        #download vmcontext.sh
        self.runCmd('sudo wget ' + self.http_server + "/opennebula/" + self.operatingsystem + '/vmcontext.sh -O ' + localtempdir + '/temp/etc/init.d/vmcontext.sh')
        self.runCmd('sudo chmod +x ' + localtempdir + '/temp/etc/init.d/vmcontext.sh')
        self.runCmd('sudo chown root:root ' + localtempdir + '/temp/etc/rc.local')

        device = "sda"
        rc_local = ""
        if self.operatingsystem == "ubuntu":
            #setup vmcontext.sh
            self.runCmd("sudo sudo chroot "+localtempdir+"/temp ln -s /etc/init.d/vmcontext.sh /etc/rc2.d/S01vmcontext.sh")
            device = "sda" 
            rc_local = "mount -t iso9660 /dev/sr0 /mnt \n"
            #delete persisten network rules
            self.runCmd("sudo rm -f "+localtempdir+"/temp/etc/udev/rules.d/70-persistent-net.rules")
            
            if self.kernel == "None":
                self.kernel = self.default_kvm_ubuntu_kernel 
            
        elif self.operatingsystem == "centos":
            #setup vmcontext.sh
            self.runCmd("sudo chroot "+localtempdir+"/temp chkconfig --add vmcontext.sh")
            if self.version == "5":
                device = "hda"
                rc_local = "mount -t iso9660 /dev/hdc /mnt \n"
            elif self.version == "6":
                device = "sda"
                rc_local = "mount -t iso9660 /dev/sr0 /mnt \n"  #in centos 6 is sr0            
                self.runCmd("sudo rm -f "+localtempdir+"/temp/etc/udev/rules.d/70-persistent-net.rules")
            
            if self.kernel == "None":
                self.kernel = self.default_kvm_centos5_kernel

        #Inject the kernel
        self.logger.info('Retrieving kernel ' + self.kernel)
        self.runCmd('wget ' + self.http_server + 'kernel/' + self.kernel + '.modules.tar.gz -O ' + localtempdir + '/' + self.kernel + '.modules.tar.gz')
        self.runCmd('sudo tar xfz ' + localtempdir + '/' + self.kernel + '.modules.tar.gz --directory ' + localtempdir + '/temp/lib/modules/')
        self.logger.info('Injected kernel ' + self.kernel)

        #customize rc.local
        rc_local += "if [ -f /mnt/context.sh ]; then \n"
        rc_local += "      . /mnt/init.sh \n"
        rc_local += "fi \n"
        rc_local += "umount /mnt \n\n"
        
        f_org = open(localtempdir + '/temp/etc/rc.local', 'r')
        f = open(localtempdir + '/rc.local', 'w')
        
        write_remain=False
        for line in f_org:
            if ( re.search('^#', line) or write_remain ):
                f.write(line)
            else:              
                f.write(rc_local)
                write_remain = True                
        f.close() 
        f_org.close()
        
        self.runCmd('sudo mv -f ' + localtempdir + '/rc.local ' + localtempdir + '/temp/etc/rc.local')
        self.runCmd('sudo chown root:root ' + localtempdir + '/temp/etc/rc.local')
        self.runCmd('sudo chmod 755 ' + localtempdir + '/temp/etc/rc.local')
        
        # Setup fstab
        fstab = "# Default fstab \n "
        fstab += "/dev/" + device + "       /             ext3     defaults,errors=remount-ro 0 0 \n"    
        fstab += "proc            /proc         proc     defaults                   0 0 \n"
        fstab += "devpts          /dev/pts      devpts   gid=5,mode=620             0 0 \n"
 
        f = open(localtempdir + '/fstab', 'w')
        f.write(fstab)
        f.close()
        self.runCmd('sudo mv -f ' + localtempdir + '/fstab ' + localtempdir + '/temp/etc/fstab')
        self.runCmd('sudo chown root:root ' + localtempdir + '/temp/etc/fstab')
        self.logger.info('fstab Injected')

    def handle_image(self, image, localtempdir, connstream):
        #print image
        success = True
        
        """   
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

        if os.path.isfile(localtempdir):
            exists = True
            i = 0       
            while (exists):            
                aux = fulldestpath + "_" + i.__str__()
                if os.path.isfile(aux):
                    i += 1
                else:
                    exists = False
                    localtempdir = aux + "/"

        cmd = 'mkdir -p ' + localtempdir
        self.runCmd(cmd)
        """
        
        realnameimg = ""
        self.logger.info('untar file with image and manifest')
        cmd = "tar xvfz " + image + " -C " + localtempdir
        self.logger.debug(cmd)        
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
        std = p.communicate()
        stat = 0
        if len(std[0]) > 0:
            realnameimg = std[0].split("\n")[0].strip().split(".")[0]            
        if p.returncode != 0:
            self.logger.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
            stat = 1

        cmd = 'rm -f ' + image 
        status = self.runCmd(cmd)
        
        if (stat != 0):
            msg = "Error: the files were not extracted"
            self.errormsg(connstream, msg)
            return False
        
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

        
        #create rootimg and temp directories
        cmd = 'mkdir -p ' + localtempdir + '/temp'
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: creating temp directory inside " + localtempdir
            self.errormsg(connstream, msg)
            return False

        #mount image to extract files
        cmd = 'sudo mount -o loop ' + localtempdir + '/' + self.name + '.img ' + localtempdir + '/temp'
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: mounting image"
            self.errormsg(connstream, msg)
            return False
        
        return True

    def errormsg(self, connstream, msg):
        self.logger.error(msg)
        try:
            connstream.write(msg)
            connstream.shutdown(socket.SHUT_RDWR)
            connstream.close()
        except:
            self.logger.debug("In errormsg: " + str(sys.exc_info()))
        self.logger.info("Image Deploy Request DONE")
    
    def runCmd(self, cmd):
        cmdLog = logging.getLogger('DeployIaaS.' + str(os.getpid()) + '.exec')
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

    server = IMDeployServerIaaS()
    server.start()

if __name__ == "__main__":
    main()
#END
