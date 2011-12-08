#!/usr/bin/env python
"""
Description: xCAT image deployment server WITHOUT the MOAB PART.  Customizes and Deploys images given by IMDeploy onto 
# xCAT bare metal
"""
__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.9'

import socket, ssl
import sys
import os
from subprocess import *
import logging
import logging.handlers
import time
from IMServerConf import IMServerConf
from xml.dom.minidom import Document, parse
import string

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
        verbose=False
        printLogStdout=False
        self._reposervice = IRServiceProxy(verbose,printLogStdout)
        
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
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.port))
        sock.listen(1)
        self.logger.info('Starting Server on port ' + str(self.port))
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
            finally:
                self.logger.info("Image Deploy Request DONE") 
 
    def auth(self, userCred):
        return FGAuth.auth(self.user, userCred)                 
                
    def process_client(self, connstream):
        start_all = time.time()
        self.logger.info('Accepted new connection')        
        #receive the message
        data = connstream.read(2048)
        self.logger.debug("received data: " + data)
        params = data.split(',')
        #print data
        #params[0] is image ID
        #params[1] is the kernel
        #params[2] is the machine
        #params[3] is the user
        #params[4] is the user password
        #params[5] is the type of password
        
        imgID = params[0].strip()
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
            userCred = FGCredential(passwdtype,passwd)
            if (self.auth(userCred)):
                connstream.write("OK")
                endloop = True
            else:
                retry+=1
                if retry < maxretry:
                    connstream.write("TryAuthAgain")
                    passwd = connstream.read(2048)
                else:
                    msg="ERROR: authentication failed"
                    endloop = True
                    self.errormsg(connstream, msg)
                    return
        
        if imgID == "list":
            #get list of directories
            #send it back separated by commas              
            cmd = "ls " + self.xcatNetbootImgPath
            p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
            std = p.communicate()
            if p.returncode != 0:
                self.logger.debug(std[1])                              
                msg="ERROR: Trying to get the xCAT image list. Exit status: "+std[1]        
                self.errormsg(connstream, msg)
                return
            else:
                aux = std[0].split()
                xcatimagelist = ",".join(aux)            
                self.logger.debug("xCAT image list: " + str(xcatimagelist))    
                connstream.write(xcatimagelist)
                connstream.shutdown(socket.SHUT_RDWR)
                connstream.close()            
                self.logger.info("Image Deploy Request (list) DONE")            
                return
        
        #check if there is enough space in /install/netboot
        #subprocess.Popen
        df = Popen(["df","/install/netboot/"], stdout=PIPE, stderr=PIPE)        
        output = df.communicate()
        if len(output[0]) > 0:
            self.logger.debug('df stdout: ' + output[0])
            self.logger.debug('df stderr: ' + output[1])        
        try:    
            usage_percent = int(output[0].split("\n")[1].split()[4].split("%")[0])                    
            if usage_percent > 85:
                msg="ERROR: Image cannot be deployed due to low disk space. Please contact with your system administrator"            
                self.errormsg(connstream, msg)
                return
        except:
            msg="ERROR: Trying to determine the disk usage of /install/netboot partition. Exit status: "+str(sys.exc_info())            
            self.errormsg(connstream, msg)
            return
        
        #GET IMAGE from repo
        if not self._reposervice.connection():
            msg = "ERROR: Connection with the Image Repository failed"
            self.errormsg(connstream, msg)
            return
        else:
            self.logger.info("Retrieving image from repository")
            
            start = time.time()
            
            image = self._reposervice.get(self.user, passwd, self.user, "img", imgID, self.tempdir)
            
            end = time.time()
            self.logger.info('TIME retrieve image from repo:' + str(end - start))
                              
            if image == None:
                msg = "ERROR: Cannot get access to the image with imgId " + str(imgID)
                self.errormsg(connstream, msg)
                self._reposervice.disconnect()
                return
            else:
                self._reposervice.disconnect()
        ################

        if not os.path.isfile(image):
            msg = "ERROR: file " + image + " not found"
            self.errormsg(connstream, msg)
            return

        
        start = time.time()
        
        #extracts image/manifest, read manifest and copy image right directory
        if not self.handle_image(image, connstream):
            return            
        
        end = time.time()
        self.logger.info('TIME untar image and copy to the right place:' + str(end - start))
        
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
        
        start = time.time()
        
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
            
        elif (self.operatingsystem == "centos"): #Centos                    
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
            cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/centos'+self.version+'/' + self.arch + '/initrd.img -O ' + tftpimgdir + '/initrd.img'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying initrd.img"
                self.errormsg(connstream, msg)
                return    
            cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/centos'+self.version+'/' + self.arch + '/vmlinuz -O ' + tftpimgdir + '/vmlinuz'
            status = self.runCmd(cmd)    
            if status != 0:
                msg = "ERROR: retrieving/copying vmlinuz"
                self.errormsg(connstream, msg)
                return
        
        cmd = "rm -rf " + self.path + "temp "
        self.runCmd(cmd)
                                          
        #XCAT tables                
        cmd = 'tabch osimage.imagename=' + self.prefix + self.operatingsystem + '' + self.name + '-' + self.arch + '-netboot-compute osimage.profile=compute '\
                'osimage.imagetype=linux osimage.provmethod=netboot osimage.osname=linux osimage.osvers=' + self.prefix + self.operatingsystem + '' + self.name + \
                ' osimage.osarch=' + self.arch + ''
        self.logger.debug(cmd)
        if not self.test_mode:
            if(self.machine == "minicluster"):
                status = os.system("sudo " + cmd)
            else:
                status = os.system(cmd)

        if (self.machine == "india"):
            cmd = 'tabch boottarget.bprofile=' + self.prefix + self.operatingsystem + '' + self.name + ' boottarget.kernel=\'xcat/netboot/' + self.prefix + \
                  self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/kernel\' boottarget.initrd=\'xcat/netboot/' + self.prefix + self.operatingsystem + \
                  '' + self.name + '/' + self.arch + '/compute/initrd-stateless.gz\' boottarget.kcmdline=\'imgurl=http://172.29.202.149/install/netboot/' + self.prefix + \
                  self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/rootimg.gz console=ttyS0,115200n8r\''                          
            self.logger.debug(cmd)
            if not self.test_mode:
                #status = os.system("sudo " + cmd)
                status = os.system(cmd) #No sudo needed if the user that run IMDeployServerXcat has been configured to execute tabch

        end = time.time()
        self.logger.info('TIME customize image, retrieve kernels and update xcat tables:' + str(end - start))

        #Pack image
        start = time.time()
        cmd = 'packimage -o ' + self.prefix + self.operatingsystem + '' + self.name + ' -p compute -a ' + self.arch + ' > /dev/null'
        self.logger.debug(cmd)        
        if not self.test_mode:
            #status = s.system("sudo " +cmd)
            if(self.machine == "minicluster"):
                status = os.system("sudo " + cmd) 
            else:
                status = os.system(cmd) #No sudo needed if the user that run IMDeployServerXcat has been configured to execute packimage
        else:            
            status = 0            
        #    
        end = time.time()
        self.logger.info('TIME xcat packimage:' + str(end - start))
        
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

        connstream.write('OK')    
        self.logger.debug("sending to the client the info needed to register the image in Moab")

        moabstring = self.prefix + ',' + self.name + ',' + self.operatingsystem + ',' + self.arch    
        self.logger.debug(moabstring)    
        connstream.write(moabstring)
        connstream.shutdown(socket.SHUT_RDWR)
        connstream.close()
        
        
        end_all = time.time()
        self.logger.info('TIME walltime image deploy xcat:' + str(end_all - start_all))
        self.logger.info("Image Deploy Request DONE")
            

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
        self.logger.debug("sudo "+cmd)          
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
                                  self.path + '/rootimage/var/spool/torque/pbs_environment')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.5.1_minicluster/server_name -O ' +\
                                  self.path + '/rootimage/var/spool/torque/server_name')
            
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
            
            #only user with running job can login
            os.system('echo \"account     required      pam_listfile.so file=/etc/authusers item=user sense=allow onerr=fail\" | sudo tee -a  ' +\
                       self.path + '/rootimg/etc/pam.d/system-auth > /dev/null')
            self.runCmd('wget ' + self.http_server + '/conf/authusers -O ' +\
                                  self.path + '/rootimg/etc/authusers')
            
            self.logger.info('Torque for India')
            
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/pbs_environment -O ' +\
                                  self.path + '/rootimg/var/spool/torque/pbs_environment')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/server_name -O ' +\
                                  self.path + '/rootimg/var/spool/torque/server_name')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/prologue -O ' +\
                                  self.path + '/rootimg/var/spool/torque/mom_priv/prologue')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/epilogue -O ' +\
                                  self.path + '/rootimg/var/spool/torque/mom_priv/epilogue')
            self.runCmd('chmod +x ' + self.path + '/rootimg/var/spool/torque/mom_priv/epilogue '+ self.path + '/rootimg/var/spool/torque/mom_priv/prologue')            
            self.runCmd('cp -f ' + self.path + '/rootimg/var/spool/torque/mom_priv/epilogue '+ self.path + '/rootimg/var/spool/torque/mom_priv/epilogue.parallel')
            self.runCmd('cp -f ' + self.path + '/rootimg/var/spool/torque/mom_priv/prologue '+ self.path + '/rootimg/var/spool/torque/mom_priv/prologue.parallel')
            
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
            f.write("ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA99x6IYp0xXE0zK+BPWZHrOzWHik+fMzJNQ/8/Joy3mGHkDUnFEwFGzP5jPEZa9ut4iFeOj"
                    "x7rDC820lmHYm+vVkRFYOyuMgSRymeSah30epMX+vPJjpYtRqoN7JdeC4Jyv3FX+sr8CfVMa1wv+Chp2nQZH81rdBVxkRzXTzmZRAq2bKo"
                    "E4N2OSbiz5DH6xD2B9Z89wYNnLRJH5SuvG9wNu6ey7OM10EUZwgmcHQXf48q3ZE7Fd/4fAJ8SNKP8JuxnrbOQGjlEwsIhXqwK5PQYQWlrm"
                    "ksUUOxGNkgf+Fm0eYKtez5kyHIqbjJ8aqCb7wOlS9RBDomfv1etEYTa2CmfQ==" + "\n") #root i136
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

        self.runCmd('mv ' + self.path + '/temp/config ' + self.path + '/rootimg/var/spool/torque/mom_priv/')
        self.runCmd('chown root:root ' + self.path + '/rootimg/var/spool/torque/mom_priv/config')
        #elf.runCmd('chmod ga+rwxt ' + self.path + '/rootimg/var/spool/torque/undelivered/')
        #self.runCmd('mkdir -p ' + self.path + '/rootimg/var/spool/torque/spool/')
        #self.runCmd('chmod ga+rwxt ' + self.path + '/rootimg/var/spool/torque/spool/')

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

        #this is for LDAP auth and mount home dirs. Later, we may control if we install this or not.
        
        #try this other way
        #chroot maverick-vm /bin/bash -c 'DEBIAN_FRONTEND=noninteractive apt-get -y --force-yes install linux-image-server'
        #env DEBIAN_FRONTEND="noninteractive" chroot /tmp/javi3789716749 /bin/bash -c 'apt-get --force-yes -y install ldap-utils libpam-ldap libpam-ldap libnss-ldap nss-updatedb libnss-db'
        self.logger.info('Configuring LDAP access')
        self.runCmd('wget '+ self.http_server +'/ldap/nsswitch.conf -O ' + self.path + '/rootimg/etc/nsswitch.conf')
        self.runCmd('mkdir -p ' + self.path + '/rootimg/etc/ldap/cacerts ' + self.path + '/rootimg/N/u')
        self.runCmd('wget '+ self.http_server +'/ldap/cacerts/12d3b66a.0 -O ' + self.path + '/rootimg/etc/ldap/cacerts/12d3b66a.0')
        self.runCmd('wget '+ self.http_server +'/ldap/cacerts/cacert.pem -O ' + self.path + '/rootimg/etc/ldap/cacerts/cacert.pem')
        self.runCmd('wget '+ self.http_server +'/ldap/ldap.conf -O ' + self.path + '/rootimg/etc/ldap.conf')
        self.runCmd('wget '+ self.http_server +'/ldap/openldap/ldap.conf -O ' + self.path + '/rootimg/etc/ldap/ldap.conf')
        os.system('sudo sed -i \'s/openldap/ldap/g\' ' + self.path + '/rootimg/etc/ldap/ldap.conf')
        os.system('sudo sed -i \'s/openldap/ldap/g\' ' + self.path + '/rootimg/etc/ldap.conf')

        self.logger.info('Installing LDAP packages')
        ldapexec = "/tmp/ldap.install"
        os.system('echo "#!/bin/bash \nexport DEBIAN_FRONTEND=noninteractive \napt-get ' + \
                  '-y install ldap-utils libnss-ldapd nss-updatedb libnss-db" >' + self.path + '/rootimg/' + ldapexec)
        os.system('chmod +x ' + self.path + '/rootimg/' + ldapexec)
        self.runCmd('chroot ' + self.path + '/rootimg/ ' + ldapexec)

        #I think this is not needed
        #self.runCmd('wget '+ self.http_server +'/ldap/sshd_ubuntu -O ' + self.path + '/rootimg/usr/sbin/sshd')
        #os.system('echo "UseLPK yes" | sudo tee -a ' + self.path + '/rootimg/etc/ssh/sshd_config > /dev/null')
        #os.system('echo "LpkLdapConf /etc/ldap.conf" | sudo tee -a ' + self.path + '/rootimg/etc/ssh/sshd_config > /dev/null')
        
        #/etc/nslcd.conf should be configured automatically, if not we need to put base and uri

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
            
            #only user with running job can login
            os.system('echo \"account     required      pam_listfile.so file=/etc/authusers item=user sense=allow onerr=fail\" | sudo tee -a  ' +\
                       self.path + '/rootimg/etc/pam.d/system-auth > /dev/null')
            self.runCmd('wget ' + self.http_server + '/conf/authusers -O ' + self.path + '/rootimg/etc/authusers')
            
            self.logger.info('Torque for India')            
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/opt.tgz -O ' + self.path + '/opt.tgz')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/var.tgz -O ' + self.path + '/var.tgz')
            self.runCmd('tar xfz ' + self.path + '/opt.tgz -C ' + self.path + '/rootimg/')
            self.runCmd('tar xfz ' + self.path + '/var.tgz -C ' + self.path + '/rootimg/')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/pbs_mom -O ' + self.path + '/rootimg/etc/init.d/pbs_mom')
            self.runCmd('rm -f ' + self.path + '/opt.tgz ' + self.path + '/var.tgz')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/prologue -O ' +\
                                  self.path + '/rootimg/var/spool/torque/mom_priv/prologue')
            status = self.runCmd('wget ' + self.http_server + '/torque/torque-2.4.8_india/epilogue -O ' +\
                                  self.path + '/rootimg/var/spool/torque/mom_priv/epilogue')
            self.runCmd('chmod +x ' + self.path + '/rootimg/var/spool/torque/mom_priv/epilogue '+ self.path + '/rootimg/var/spool/torque/mom_priv/prologue')
            self.runCmd('cp -f ' + self.path + '/rootimg/var/spool/torque/mom_priv/epilogue '+ self.path + '/rootimg/var/spool/torque/mom_priv/epilogue.parallel')
            self.runCmd('cp -f ' + self.path + '/rootimg/var/spool/torque/mom_priv/prologue '+ self.path + '/rootimg/var/spool/torque/mom_priv/prologue.parallel')
            
            
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
            f.write("ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA99x6IYp0xXE0zK+BPWZHrOzWHik+fMzJNQ/8/Joy3mGHkDUnFEwFGzP5jPEZa9ut4iFeOj"
                    "x7rDC820lmHYm+vVkRFYOyuMgSRymeSah30epMX+vPJjpYtRqoN7JdeC4Jyv3FX+sr8CfVMa1wv+Chp2nQZH81rdBVxkRzXTzmZRAq2bKo"
                    "E4N2OSbiz5DH6xD2B9Z89wYNnLRJH5SuvG9wNu6ey7OM10EUZwgmcHQXf48q3ZE7Fd/4fAJ8SNKP8JuxnrbOQGjlEwsIhXqwK5PQYQWlrm"
                    "ksUUOxGNkgf+Fm0eYKtez5kyHIqbjJ8aqCb7wOlS9RBDomfv1etEYTa2CmfQ==" + "\n") #root i136
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
172.29.202.115:/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''
#149.165.146.145


        #desactivate both interfaces
        os.system('echo "ONBOOT=no" | sudo tee -a ' + self.path + '/rootimg/etc/sysconfig/network-scripts/ifcfg-eth1 > /dev/null')
        os.system('echo "ONBOOT=no" | sudo tee -a ' + self.path + '/rootimg/etc/sysconfig/network-scripts/ifcfg-usb0 > /dev/null')
                
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

#HARDCODED FOR NOW UNTIL I SOLVE THE PROBLEMS WITH THIS VERSION        
        if (self.version == "6"):
            self.kernel="2.6.32-71.el6"
        
        status = self.runCmd('wget ' + self.http_server + '/kernel/' + self.kernel + '.modules.tar.gz -O ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.runCmd('tar xfz ' + self.path + '' + self.kernel + '.modules.tar.gz --directory ' + self.path + '/rootimg/lib/modules/')
        self.runCmd('rm -f ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.logger.info('Injected kernel ' + self.kernel)

        
        self.logger.info('Installing LDAP packages')
        if (self.version == "5"):
            self.runCmd('chroot ' + self.path + '/rootimg/ yum -y install openldap-clients nss_ldap')
            self.runCmd('wget '+ self.http_server +'/ldap/nsswitch.conf -O ' + self.path + '/rootimg/etc/nsswitch.conf')
        elif (self.version == "6"):
            self.runCmd('chroot ' + self.path + '/rootimg/ yum -y install openldap-clients nss-pam-ldapd sssd')                       
            self.runCmd('wget '+ self.http_server +'/ldap/nsswitch.conf_centos6 -O ' + self.path + '/rootimg/etc/nsswitch.conf')
            self.runCmd('wget '+ self.http_server +'/ldap/sssd.conf_centos6 -O ' + self.path + '/rootimg/etc/sssd/sssd.conf')
            self.runCmd('chmod 600 '+ self.path + '/rootimg/etc/sssd/sssd.conf')
            self.runCmd('chroot ' + self.path + '/rootimg/ chkconfig sssd on')
            
        self.logger.info('Configuring LDAP access')
        
        self.runCmd('mkdir -p ' + self.path + '/rootimg/etc/openldap/cacerts ' + self.path + '/rootimg/N/u')
        self.runCmd('wget '+ self.http_server +'/ldap/cacerts/12d3b66a.0 -O ' + self.path + '/rootimg/etc/openldap/cacerts/12d3b66a.0')
        self.runCmd('wget '+ self.http_server +'/ldap/cacerts/cacert.pem -O ' + self.path + '/rootimg/etc/openldap/cacerts/cacert.pem')
        self.runCmd('wget '+ self.http_server +'/ldap/ldap.conf -O ' + self.path + '/rootimg/etc/ldap.conf')
        self.runCmd('wget '+ self.http_server +'/ldap/openldap/ldap.conf -O ' + self.path + '/rootimg/etc/openldap/ldap.conf')
        os.system('sudo sed -i \'s/enforcing/disabled/g\' ' + self.path + '/rootimg/etc/selinux/config')

        self.runCmd('wget '+ self.http_server +'/ldap/sshd_centos'+ self.version + ' -O ' + self.path + '/rootimg/usr/sbin/sshd')
        os.system('echo "UseLPK yes" | sudo tee -a ' + self.path + '/rootimg/etc/ssh/sshd_config > /dev/null')
        os.system('echo "LpkLdapConf /etc/ldap.conf" | sudo tee -a ' + self.path + '/rootimg/etc/ssh/sshd_config > /dev/null')

        return status

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
