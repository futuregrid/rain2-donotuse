#!/usr/bin/env python
"""
Description: xCAT image deployment server WITHOUT the MOAB PART.  Customizes and Deploys images given by IMDeploy onto 
# xCAT bare metal
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
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")
from image.repository.client.IRServiceProxy import IRServiceProxy
from utils.FGTypes import FGCredential
from utils import FGAuth

class IMDeployServerXcat(object):

    def __init__(self):
        super(IMDeployServerXcat, self).__init__()
        
        
        self.prefix = ""
        self.path = ""
        
        self.numparams = 6   #image path
        
        self.name = ""
        self.givenname = ""
        self.operatingsystem = ""
        self.version = ""
        self.arch = ""
        self.kernel = ""
        
        self.machine = "" #india, minicluster,...
        self.user = ""
        self.userCred = None

        #load from config file
        self._deployConf = IMServerConf()
        self._deployConf.load_deployServerXcatConfig() 
        self.port = self._deployConf.getXcatPort()
        self.xcatNetbootImgPath = self._deployConf.getXcatNetbootImgPath()
        self.http_server = self._deployConf.getHttpServer()
        self.log_filename = self._deployConf.getLogXcat()
        self.logLevel = self._deployConf.getLogLevelXcat()
        self.test_mode = self._deployConf.getTestXcat()
        self.tempdir = self._deployConf.getTempDirXcat()
        self._ca_certs = self._deployConf.getCaCertsXcat()
        self._certfile = self._deployConf.getCertFileXcat()
        self._keyfile = self._deployConf.getKeyFileXcat()
        #Default Kernels to use for each deployment
        self.default_xcat_kernel_centos = self._deployConf.getDXKernelCentos()
        self.default_xcat_kernel_ubuntu = self._deployConf.getDXKernelUbuntu()
        
        
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
            connstream = None
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
            except socket.error:
                self.logger.error("Error with the socket connection")
            except:
                self.logger.error("Uncontrolled Error: " + str(sys.exc_info()))
                if type(connstream) is ssl.SSLSocket: 
                    connstream.shutdown(socket.SHUT_RDWR)
                    connstream.close()       
 
    def auth(self):
        return FGAuth.auth(self.user, self.userCred)                 
                
    def process_client(self, connstream):
        self.logger.info('Accepted new connection')        
        #receive the message
        data = connstream.read(2048)
        params = data.split(',')
        #print data
        #params[0] is image ID
        #params[1] is the kernel
        #params[2] is the machine
        #params[3] is the user
        #params[4] is the user password
        #params[5] is the type of password
        
        imgID = params[0]
        self.kernel = params[1].strip()
        self.machine = params[2].strip()
        self.user = params[3].strip()
        passwd = params[4].strip()
        passwdtype = params[5].strip()
              
        if len(params) != self.numparams:
            msg = "ERROR: incorrect message"
            self.errormsg(connstream, msg)
            return

        retry=0
        maxretry=3
        endloop = False
        while ( not endloop ):
            self.userCred = FGCredential(passwdtype,passwd)
            if (self.auth()):
                connstream.write("OK")
                endloop = True
            else:
                connstream.write("TryAuthAgain")
                retry+=1
                if retry < maxretry:
                    passwd = connstream.read(2048)
                else:
                    msg="ERROR: authentication failed"
                    endloop = True
                    self.errormsg(connstream, msg)
                    return
        #print "---Auth works---"
        #GET IMAGE from repo
        self.logger.info("Retrieving image from repository")
        image = self._reposervice.get(self.user, "img", imgID, self.tempdir)      
        if image == None:
            msg = "ERROR: Cannot get access to the image with imgId " + str(imgID)
            self.errormsg(connstream, msg)
            return            
        ################

        if not os.path.isfile(image):
            msg = "ERROR: file " + image + " not found"
            self.errormsg(connstream, msg)
            return

        #extracts image/manifest, read manifest and copy image right directory
        if not self.handle_image(image, connstream):
            return            

        #Select kernel version
        #This is not yet supported as we get always the same kernel
        self.logger.debug("kernel: " + self.kernel)
        if self.kernel == "None":
            if (self.operatingsystem == "ubuntu"):
                self.kernel = self.default_xcat_kernel_ubuntu                        
            elif (self.operatingsystem == "centos"):
                self.kernel = self.default_xcat_kernel_centos
        
        #create directory that contains initrd.img and vmlinuz
        tftpimgdir = '/tftpboot/xcat/' + self.prefix + self.operatingsystem + '' + self.name + '/' + self.arch
        cmd = 'mkdir -p ' + tftpimgdir
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: creating tftpboot directories"
            self.errormsg(connstream, msg)
            return
        
        if (self.operatingsystem == "ubuntu"):
            
            #############################
            #Insert client stuff for ubuntu. To be created. We may use the same function but Torque binaries and network config must be different
            ############################
            status = self.customize_ubuntu_img()
                    
            #getting initrd and kernel customized for xCAT
            cmd = 'wget ' + self.http_server + '/kernel/specialubuntu/initrd.gz -O ' + self.path + '/initrd-stateless.gz'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying initrd.gz"
                self.errormsg(connstream, msg)
                return    
            cmd = 'wget ' + self.http_server + '/kernel/specialubuntu/kernel -O ' + self.path + '/kernel'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying kernel"
                self.errormsg(connstream, msg)
                return
            
            #getting generic initrd and kernel 
            cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/ubuntu10/' + self.arch + '/initrd.img -O ' + tftpimgdir + '/initrd.img'
            status = self.runCmd(cmd)

            if status != 0:
                msg = "ERROR: retrieving/copying initrd.img"
                self.errormsg(connstream, msg)
                return

            cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/ubuntu10/' + self.arch + '/vmlinuz -O ' + tftpimgdir + '/vmlinuz'
            status = self.runCmd(cmd)

            if status != 0:
                msg = "ERROR: retrieving/copying vmlinuz"
                self.errormsg(connstream, msg)
                return
            
        else: #Centos                    
            status = self.customize_centos_img()
            if status != 0:
                msg = "ERROR: customizing the image. Look into server logs for details"
                self.errormsg(connstream, msg)
                return    
            
            #getting initrd and kernel customized for xCAT
            cmd = 'wget ' + self.http_server + '/kernel/initrd.gz -O ' + self.path + '/initrd-stateless.gz'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying initrd.gz"
                self.errormsg(connstream, msg)
                return    
            cmd = 'wget ' + self.http_server + '/kernel/kernel -O ' + self.path + '/kernel'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying kernel"
                self.errormsg(connstream, msg)
                return
            
            #getting generic initrd and kernel
            cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/centos5/' + self.arch + '/initrd.img -O ' + tftpimgdir + '/initrd.img'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying initrd.img"
                self.errormsg(connstream, msg)
                return    
            cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/centos5/' + self.arch + '/vmlinuz -O ' + tftpimgdir + '/vmlinuz'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying vmlinuz"
                self.errormsg(connstream, msg)
                return
        
        cmd = "rm -rf " + self.path + "temp "
        self.runCmd(cmd)
                                          
        #XCAT tables                
        cmd = 'chtab osimage.imagename=' + self.prefix + self.operatingsystem + '' + self.name + '-' + self.arch + '-netboot-compute osimage.profile=compute '\
                'osimage.imagetype=linux osimage.provmethod=netboot osimage.osname=linux osimage.osvers=' + self.prefix + self.operatingsystem + '' + self.name + \
                ' osimage.osarch=' + self.arch + ''
        self.logger.debug(cmd)
        if not self.test_mode:
            status = os.system("sudo " + cmd)

        if (self.machine == "india"):
            cmd = 'chtab boottarget.bprofile=' + self.prefix + self.operatingsystem + '' + self.name + ' boottarget.kernel=\'xcat/netboot/' + self.prefix + \
                  self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/kernel\' boottarget.initrd=\'xcat/netboot/' + self.prefix + self.operatingsystem + \
                  '' + self.name + '/' + self.arch + '/compute/initrd-stateless.gz\' boottarget.kcmdline=\'imgurl=http://172.29.202.149/install/netboot/' + self.prefix + \
                  self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/rootimg.gz console=ttyS0,115200n8r\''                          
            self.logger.debug(cmd)
            if not self.test_mode:
                status = os.system("sudo " + cmd)

        #Pack image
        cmd = 'packimage -o ' + self.prefix + self.operatingsystem + '' + self.name + ' -p compute -a ' + self.arch
        self.logger.debug(cmd)
        if not self.test_mode:
            status = self.runCmd(cmd)
        else:
            status = 0
        #    
        if status != 0:
            msg = "ERROR: packimage command"
            self.errormsg(connstream, msg)
            return
        
        #This should be done by qsub/msub by calling nodeset.
        anotherdir = '/tftpboot/xcat/netboot/' + self.prefix + self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/'
        cmd = 'mkdir -p ' + anotherdir
        status = self.runCmd(cmd)
        cmd = 'cp ' + self.path + '/initrd-stateless.gz ' + self.path + '/kernel ' + anotherdir
        status = self.runCmd(cmd)
        #############
        
        """
        #Do a nodeset
        cmd = 'nodeset tc1 netboot=' + prefix + operatingsystem + '' + name + '-' + arch + '-compute'
        self.runCmd(cmd)
        self.runCmd('rpower tc1 boot')
        """

        connstream.write("OK")    
        self.logger.debug("sending to the client the info needed to register the image in Moab")

        moabstring = self.prefix + ',' + self.name + ',' + self.operatingsystem + ',' + self.arch    
        self.logger.debug(moabstring)    
        connstream.write(moabstring)
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()
            

    def handle_image(self, image, connstream):
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

        #Hook for Debian based systems to work in xCAT                
        if self.operatingsystem == 'ubuntu' or self.operatingsystem == 'debian':
            self.prefix = 'centos'
        else:
            self.prefix = ''

        #Build filesystem    
        #Create Directory structure
        #/install/netboot/<name>/<arch>/compute/
        self.path = self.xcatNetbootImgPath + self.prefix + self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/'
        
        if os.path.isdir(self.path):
            msg = "ERROR: The image already exists"
            self.errormsg(connstream, msg)
            return False
        
        #create rootimg and temp directories
        cmd = 'mkdir -p ' + self.path + 'rootimg ' + self.path + 'temp'
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: creating directory rootimg"
            self.errormsg(connstream, msg)
            return False

        cmd = "chmod 777 " + self.path + "temp"
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: modifying temp dir permissons"
            self.errormsg(connstream, msg)
            return False

        cmd = 'mv -f ' + localtempdir + "/" + realnameimg + ".img " + self.path
        #print cmd
        status = self.runCmd(cmd) 
        if status != 0:
            msg = "ERROR: creating directory rootimg"
            self.errormsg(connstream, msg)
            return False
        
        cmd = 'rm -rf ' + localtempdir
        status = self.runCmd(cmd)

        #mount image to extract files
        cmd = 'mount -o loop ' + self.path + '' + self.name + '.img ' + self.path + 'temp'
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: mounting image"
            self.errormsg(connstream, msg)
            return False
        #copy files keeping the permission (-p parameter)
        cmd = 'cp -rp ' + self.path + 'temp/* ' + self.path + 'rootimg/'                
        status = os.system("sudo " + cmd)    
        if status != 0:
            msg = "ERROR: copying image"
            self.errormsg(connstream, msg)
            return False    
        cmd = 'umount ' + self.path + 'temp'
        status = self.runCmd(cmd)
        #we need to read the manifest if we send here the image from the repository directly
        cmd = 'rm -f ' + self.path + '' + self.name + '.img ' + self.path + '' + self.name + '.manifest.xml'
        status = self.runCmd(cmd)    
        if status != 0:
            msg = "ERROR: unmounting image"
            self.errormsg(connstream, msg)
            return False

        return True

    #MERGE both customize because are almost the same

    def customize_ubuntu_img(self):
        status = 0
        fstab = ""
        
        #services will install, but not start
        f = open(self.path + '/temp/_policy-rc.d', 'w')
        f.write("#!/bin/sh" + '\n' + "exit 101" + '\n')
        f.close()        
        self.runCmd('mv -f ' + self.path + '/temp/_policy-rc.d ' + self.path + '/rootimg/usr/sbin/policy-rc.d')        
        self.runCmd('chmod +x ' + self.path + '/rootimg/usr/sbin/policy-rc.d')
        
        self.logger.info('Installing torque')
        
        status = self.runCmd('chroot ' + self.path + '/rootimg/ apt-get -y install torque-mom')
        
        if(self.machine == "minicluster"):
            self.logger.info('Torque for minicluster')                        
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.5.1_minicluster/pbs_environment -O ' +\
                                  self.path + '/rootimage/var/lib/torque/pbs_environment')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.5.1_minicluster/server_name -O ' +\
                                  self.path + '/rootimage/var/lib/torque/server_name')
            
            self.logger.info('Configuring network')
            status = self.runCmd('wget ' + self.http_server + '/conf/ubuntu/netsetup_minicluster.tgz -O ' + self.path + 'netsetup_minicluster.tgz')

            self.runCmd('tar xfz ' + self.path + 'netsetup_minicluster.tgz -C ' + self.path + '/rootimg/etc/')
            self.runCmd('chmod +x ' + self.path + '/rootimg/etc/netsetup/netsetup.sh')
            self.runCmd('cp '+ self.path + '/rootimg/etc/netsetup/netsetup.sh ' + self.path + '/rootimg/etc/rc2.d/S20netsetup')
            self.runCmd('cp '+ self.path + '/rootimg/etc/netsetup/netsetup.sh ' + self.path + '/rootimg/etc/rc3.d/S20netsetup')
            self.runCmd('cp '+ self.path + '/rootimg/etc/netsetup/netsetup.sh ' + self.path + '/rootimg/etc/rc4.d/S20netsetup')
            self.runCmd('cp '+ self.path + '/rootimg/etc/netsetup/netsetup.sh ' + self.path + '/rootimg/etc/rc5.d/S20netsetup')
            self.runCmd('rm -f ' + self.path + 'netsetup_minicluster.tgz')
            
            os.system('cat ' + self.path + '/rootimg/etc/hosts' + ' > ' + self.path + '/temp/_hosts') #Create it in a unique directory
            f = open(self.path + '/temp/_hosts', 'a')
            f.write("\n" + "172.29.200.1 t1 tm1" + '\n' + "172.29.200.3 tc1" + '\n' + "149.165.145.35 tc1r.tidp.iu.futuregrid.org tc1r" + '\n' + \
                    "172.29.200.4 tc2" + '\n' + "149.165.145.36 tc2r.tidp.iu.futuregrid.org tc2r" + '\n')
            f.close()
            self.runCmd('mv -f ' + self.path + '/temp/_hosts ' + self.path + '/rootimg/etc/hosts')
            self.runCmd('chown root:root ' + self.path + '/rootimg/etc/hosts')
            self.runCmd('chmod 644 ' + self.path + '/rootimg/etc/hosts')

            self.runCmd('mkdir -p ' + self.path + '/rootimg/root/.ssh')
            f = open(self.path + '/temp/_authorized_keys', 'a') #Create it in a unique directory
            f.write("\n" + "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8KYKqxO3IXcJQ6xoAyrzewWPbZUrt+iPlpo/JiXoGkkfshT445QgNksQcJke8AHbIFZ"
                    "ctt8A7an5uC6y8sLmfKjAO2kP1acUoXtQ/0NQXVphdk1Cxxd0TW1Z0Kf+jX82vOCeJQHS0GBsLZmB2N/7Ch3cZMW/lt+RPbMMDob9zq"
                    "hWnDdikh67txjwNpM8qNjGcVqXoIL/V7Ue4pOvoj2egFmOdkA/w+5xUm45zqUZSE473fLyoYvpXPHM8GBlhGegYIQpKPUbgZjNwTQr1"
                    "uNUWs1l5ezvgZlmA8A4ciWrBC5qAN/qudvbS40rxagfNIuzNh4A2QuOxlv7CmwDCP3rrw== jdiaz@tm1" + '\n')
            f.close()
            self.runCmd('mv ' + self.path + '/temp/_authorized_keys ' + self.path + '/rootimg/root/.ssh/authorized_keys')

            self.runCmd('chown root:root ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            self.runCmd('chmod 600 ' + self.path + '/rootimg/root/.ssh/authorized_keys')


            fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
172.29.200.1:/export/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''

        elif(self.machine == "india"):#Later we should be able to chose the cluster where is deployed
            self.logger.info('Torque for India')
            
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/pbs_environment -O ' +\
                                  self.path + '/rootimage/var/lib/torque/pbs_environment')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/server_name -O ' +\
                                  self.path + '/rootimage/var/lib/torque/server_name')
            
            self.logger.info('Configuring network')
            status = self.runCmd('wget ' + self.http_server + '/conf/ubuntu/netsetup.sh_india -O ' + self.path + '/rootimg/etc/init.d/netsetup.sh')
            self.runCmd('chmod +x ' + self.path + '/rootimg/etc/init.d/netsetup.sh')
            self.runCmd('cp '+ self.path + '/rootimg/etc/init.d/netsetup.sh ' + self.path + '/rootimg/etc/rc2.d/S20netsetup')
            self.runCmd('cp '+ self.path + '/rootimg/etc/init.d/netsetup.sh ' + self.path + '/rootimg/etc/rc3.d/S20netsetup')
            self.runCmd('cp '+ self.path + '/rootimg/etc/init.d/netsetup.sh ' + self.path + '/rootimg/etc/rc4.d/S20netsetup')
            self.runCmd('cp '+ self.path + '/rootimg/etc/init.d/netsetup.sh ' + self.path + '/rootimg/etc/rc5.d/S20netsetup')
            #self.runCmd('chroot ' + self.path + '/rootimg/ /sbin/chkconfig --add netsetup.sh')
            
            status = self.runCmd('wget ' + self.http_server + '/conf/hosts_india -O ' + self.path + '/rootimg/etc/hosts')
            self.runCmd('mkdir -p ' + self.path + '/rootimg/root/.ssh')
 
            f = open(self.path + '/temp/_authorized_keys', 'a') #Create it in a unique directory
            f.write("\n" + "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsAaCJFcGUXSmA2opcQk/HeuiJu417a69KbuWNjf1UqarP7t0hUpMXQnlc8+yfi"
                      "fI8FpoXtNCai8YEPmpyynqgF9VFSDwTp8use61hBPJn2isZha1JvkuYJX4n3FCHOeDlb2Y7M90DvdYHwhfPDa/jIy8PvFGiFkRLSt1kghY"
                      "xZSleiikl0OxFcjaI8N8EiEZK66HAwOiDHAn2k3oJDBTD69jydJsjExOwlqZoJ4G9ScfY0rpzNnjE9sdxpJMCWcj20y/2T/oeppLmkq7aQtu"
                      "p8JMPptL+kTz5psnjozTNQgLYtYHAcfy66AKELnLuGbOFQdYxnINhX3e0iQCDDI5YQ== jdiaz@india.futuregrid.org" + "\n")
            f.close()
            self.runCmd('mv ' + self.path + '/temp/_authorized_keys ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            self.runCmd('chown root:root ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            self.runCmd('chmod 600 ' + self.path + '/rootimg/root/.ssh/authorized_keys')

            #self.runCmd('chroot '+self.path+'/rootimg/ /sbin/chkconfig --add pbs_mom')
            #self.runCmd('chroot '+self.path+'/rootimg/ /sbin/chkconfig pbs_mom on')       

            fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
149.165.146.145:/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''

            #self.runCmd('chmod +x ' + self.path + '/rootimg/etc/init.d/pbs_mom')

            #Modifying rc.local to restart network and start pbs_mom at the end            
            #os.system('cat ' + self.path + '/rootimg/etc/rc.d/rc.local' + ' > ' + self.path + '/temp/_rc.local') #Create it in a unique directory
            #f = open(self.path + '/temp/_rc.local', 'a')
            #f.write("\n" + "sleep 10" + "\n" + "/etc/init.d/pbs_mom start" + '\n')
            #f.close()
            #self.runCmd('mv -f ' + self.path + '/temp/_rc.local ' + self.path + '/rootimg/etc/rc.d/rc.local')
            #self.runCmd('chown root:root ' + self.path + '/rootimg/etc/rc.d/rc.local')
            #self.runCmd('chmod 755 ' + self.path + '/rootimg/etc/rc.d/rc.local')


        f = open(self.path + '/temp/config', 'w')
        f.write("opsys " + self.prefix + self.operatingsystem + "" + self.name + "\n" + "arch " + self.arch)
        f.close()

        self.runCmd('mv ' + self.path + '/temp/config ' + self.path + '/rootimg/var/lib/torque/mom_priv/')
        self.runCmd('chown root:root ' + self.path + '/rootimg/var/lib/torque/mom_priv/config')
        self.runCmd('chmod ga+rwxt ' + self.path + '/rootimg/var/lib/torque/undelivered/')
        self.runCmd('mkdir -p ' + self.path + '/rootimg/var/lib/torque/spool/')
        self.runCmd('chmod ga+rwxt ' + self.path + '/rootimg/var/lib/torque/spool/')

        #Setup fstab
        f = open(self.path + '/temp/fstab', 'w')
        f.write(fstab)
        f.close()
        self.runCmd('mv -f ' + self.path + '/temp/fstab ' + self.path + 'rootimg/etc/fstab')
        self.runCmd('chown root:root ' + self.path + '/rootimg/etc/fstab')
        self.runCmd('chmod 644 ' + self.path + '/rootimg/etc/fstab')
        self.logger.info('Injected fstab')
        
        #Inject the kernel
        self.logger.info('Retrieving kernel ' + self.kernel)
        status = self.runCmd('wget ' + self.http_server + '/kernel/' + self.kernel + '.modules.tar.gz -O ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.runCmd('tar xfz ' + self.path + '' + self.kernel + '.modules.tar.gz --directory ' + self.path + '/rootimg/lib/modules/')
        self.runCmd('rm -f ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.logger.info('Injected kernel ' + self.kernel)

        self.runCmd('rm -f ' + self.path + '/rootimg/usr/sbin/policy-rc.d')

        return status

    def customize_centos_img(self):
        status = 0
        fstab = ""
        self.logger.info('Installing torque')
        if(self.machine == "minicluster"):
            self.logger.info('Torque for minicluster')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.5.1_minicluster/torque-2.5.1.tgz -O ' + self.path + '/torque-2.5.1.tgz')            
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.5.1_minicluster/var.tgz -O ' + self.path + '/var.tgz')            
            self.runCmd('tar xfz ' + self.path + '/torque-2.5.1.tgz -C ' + self.path + '/rootimg/usr/local/')
            self.runCmd('tar xfz ' + self.path + '/var.tgz -C ' + self.path + '/rootimg/')            
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.5.1_minicluster/pbs_mom -O ' + self.path + '/rootimg/etc/init.d/pbs_mom')            
            self.runCmd('rm -f ' + self.path + '/torque-2.5.1.tgz ' + self.path + '/var.tgz')

            self.logger.info('Configuring network')
            status = self.runCmd('wget ' + self.http_server + '/conf/centos/netsetup_minicluster.tgz -O ' + self.path + 'netsetup_minicluster.tgz')

            self.runCmd('tar xfz ' + self.path + 'netsetup_minicluster.tgz -C ' + self.path + '/rootimg/etc/')
            self.runCmd('mv -f '+ self.path + '/rootimg/etc/netsetup/netsetup.sh ' + self.path + '/rootimg/etc/init.d/netsetup.sh')
            self.runCmd('chmod +x ' + self.path + '/rootimg/etc/init.d/netsetup.sh')
            self.runCmd('chroot ' + self.path + '/rootimg/ /sbin/chkconfig --add netsetup.sh')
            self.runCmd('rm -f ' + self.path + 'netsetup_minicluster.tgz')
            
            os.system('cat ' + self.path + '/rootimg/etc/hosts' + ' > ' + self.path + '/temp/_hosts') #Create it in a unique directory
            f = open(self.path + '/temp/_hosts', 'a')
            f.write("\n" + "172.29.200.1 t1 tm1" + '\n' + "172.29.200.3 tc1" + '\n' + "149.165.145.35 tc1r.tidp.iu.futuregrid.org tc1r" + '\n' + \
                    "172.29.200.4 tc2" + '\n' + "149.165.145.36 tc2r.tidp.iu.futuregrid.org tc2r" + '\n')
            f.close()            
            self.runCmd('mv -f ' + self.path + '/temp/_hosts ' + self.path + '/rootimg/etc/hosts')
            self.runCmd('chown root:root ' + self.path + '/rootimg/etc/hosts')
            self.runCmd('chmod 644 ' + self.path + '/rootimg/etc/hosts')

            self.runCmd('mkdir -p ' + self.path + '/rootimg/root/.ssh')
            f = open(self.path + '/temp/_authorized_keys', 'a') #Create it in a unique directory
            f.write("\n" + "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA8KYKqxO3IXcJQ6xoAyrzewWPbZUrt+iPlpo/JiXoGkkfshT445QgNksQcJke8AHbIFZ"
                    "ctt8A7an5uC6y8sLmfKjAO2kP1acUoXtQ/0NQXVphdk1Cxxd0TW1Z0Kf+jX82vOCeJQHS0GBsLZmB2N/7Ch3cZMW/lt+RPbMMDob9zq"
                    "hWnDdikh67txjwNpM8qNjGcVqXoIL/V7Ue4pOvoj2egFmOdkA/w+5xUm45zqUZSE473fLyoYvpXPHM8GBlhGegYIQpKPUbgZjNwTQr1"
                    "uNUWs1l5ezvgZlmA8A4ciWrBC5qAN/qudvbS40rxagfNIuzNh4A2QuOxlv7CmwDCP3rrw== jdiaz@tm1" + '\n')
            f.close()
            self.runCmd('mv ' + self.path + '/temp/_authorized_keys ' + self.path + '/rootimg/root/.ssh/authorized_keys')

            self.runCmd('chown root:root ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            self.runCmd('chmod 600 ' + self.path + '/rootimg/root/.ssh/authorized_keys')


            fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
172.29.200.1:/export/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''

        elif(self.machine == "india"):#Later we should be able to chose the cluster where is deployed
            self.logger.info('Torque for India')            
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/opt.tgz -O ' + self.path + '/opt.tgz')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/var.tgz -O ' + self.path + '/var.tgz')
            self.runCmd('tar xfz ' + self.path + '/opt.tgz -C ' + self.path + '/rootimg/')
            self.runCmd('tar xfz ' + self.path + '/var.tgz -C ' + self.path + '/rootimg/')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/pbs_mom -O ' + self.path + '/rootimg/etc/init.d/pbs_mom')
            self.runCmd('rm -f ' + self.path + '/opt.tgz ' + self.path + '/var.tgz')
            
            self.logger.info('Configuring network')
            status = self.runCmd('wget ' + self.http_server + '/conf/centos/netsetup.sh_india -O ' + self.path + '/rootimg/etc/init.d/netsetup.sh')
            self.runCmd('chmod +x ' + self.path + '/rootimg/etc/init.d/netsetup.sh')
            self.runCmd('chroot ' + self.path + '/rootimg/ /sbin/chkconfig --add netsetup.sh')
            
            status = self.runCmd('wget ' + self.http_server + '/conf/hosts_india -O ' + self.path + '/rootimg/etc/hosts')
            self.runCmd('mkdir -p ' + self.path + '/rootimg/root/.ssh')
 
            f = open(self.path + '/temp/_authorized_keys', 'a') #Create it in a unique directory
            f.write("\n" + "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsAaCJFcGUXSmA2opcQk/HeuiJu417a69KbuWNjf1UqarP7t0hUpMXQnlc8+yfi"
                      "fI8FpoXtNCai8YEPmpyynqgF9VFSDwTp8use61hBPJn2isZha1JvkuYJX4n3FCHOeDlb2Y7M90DvdYHwhfPDa/jIy8PvFGiFkRLSt1kghY"
                      "xZSleiikl0OxFcjaI8N8EiEZK66HAwOiDHAn2k3oJDBTD69jydJsjExOwlqZoJ4G9ScfY0rpzNnjE9sdxpJMCWcj20y/2T/oeppLmkq7aQtu"
                      "p8JMPptL+kTz5psnjozTNQgLYtYHAcfy66AKELnLuGbOFQdYxnINhX3e0iQCDDI5YQ== jdiaz@india.futuregrid.org" + "\n")
            f.close()
            self.runCmd('mv ' + self.path + '/temp/_authorized_keys ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            self.runCmd('chown root:root ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            self.runCmd('chmod 600 ' + self.path + '/rootimg/root/.ssh/authorized_keys')

            #self.runCmd('chroot '+self.path+'/rootimg/ /sbin/chkconfig --add pbs_mom')
            #self.runCmd('chroot '+self.path+'/rootimg/ /sbin/chkconfig pbs_mom on')       

            fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
149.165.146.145:/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''

        self.runCmd('chmod +x ' + self.path + '/rootimg/etc/init.d/pbs_mom')

        #Modifying rc.local to restart network and start pbs_mom at the end
        #os.system('touch ./_rc.local')
        os.system('cat ' + self.path + '/rootimg/etc/rc.d/rc.local' + ' > ' + self.path + '/temp/_rc.local') #Create it in a unique directory
        f = open(self.path + '/temp/_rc.local', 'a')
        f.write("\n" + "sleep 10" + "\n" + "/etc/init.d/pbs_mom start" + '\n')
        f.close()
        self.runCmd('mv -f ' + self.path + '/temp/_rc.local ' + self.path + '/rootimg/etc/rc.d/rc.local')
        self.runCmd('chown root:root ' + self.path + '/rootimg/etc/rc.d/rc.local')
        self.runCmd('chmod 755 ' + self.path + '/rootimg/etc/rc.d/rc.local')


        f = open(self.path + '/temp/config', 'w')
        f.write("opsys " + self.operatingsystem + "" + self.name + "\n" + "arch " + self.arch)
        f.close()

        self.runCmd('mv ' + self.path + '/temp/config ' + self.path + '/rootimg/var/spool/torque/mom_priv/')
        self.runCmd('chown root:root ' + self.path + '/rootimg/var/spool/torque/mom_priv/config')

        #Setup fstab
        f = open(self.path + '/temp/fstab', 'w')
        f.write(fstab)
        f.close()
        self.runCmd('mv -f ' + self.path + '/temp/fstab ' + self.path + 'rootimg/etc/fstab')
        self.runCmd('chown root:root ' + self.path + '/rootimg/etc/fstab')
        self.runCmd('chmod 644 ' + self.path + '/rootimg/etc/fstab')
        self.logger.info('Injected fstab')
        
        #Inject the kernel
        self.logger.info('Retrieving kernel ' + self.kernel)
        status = self.runCmd('wget ' + self.http_server + '/kernel/' + self.kernel + '.modules.tar.gz -O ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.runCmd('tar xfz ' + self.path + '' + self.kernel + '.modules.tar.gz --directory ' + self.path + '/rootimg/lib/modules/')
        self.runCmd('rm -f ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.logger.info('Injected kernel ' + self.kernel)

        return status

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

    print "\n The user that executes this must have sudo with NOPASSWD"

    server = IMDeployServerXcat()
    server.start()

if __name__ == "__main__":
    main()
#END
