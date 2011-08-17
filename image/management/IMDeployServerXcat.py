#!/usr/bin/env python
"""
Description: xCAT image deployment server WITHOUT the MOAB PART.  Customizes and Deploys images given by IMDeploy onto 
# xCAT bare metal
"""
__author__ = 'Javier Diaz, Andrew Young'
__version__ = '0.1'

import socket
import sys
import os
from subprocess import *
import logging
import logging.handlers
import time
from IMServerConf import IMServerConf



class IMDeployServerXcat(object):

    def __init__(self):
        super(IMDeployServerXcat, self).__init__()
        
        
        self.prefix = ""
        self.path = ""
        
        self.numparams = 7   #name,os,version,arch,kernel,dir,machine
        
        self.name = ""
        self.operatingsystem = ""
        self.version = ""
        self.arch = ""
        self.kernel = ""
        self.tempdir = ""
        self.machine = "" #india, minicluster,...


        #load from config file
        self._deployConf = IMServerConf()
        self._deployConf.load_deployServerXcatConfig() 
        self.port = self._deployConf.getXcatPort()
        self.xcatNetbootImgPath = self._deployConf.getXcatNetbootImgPath()
        self.http_server = self._deployConf.getHttpServer()
        self.log_filename = self._deployConf.getLogXcat()
        self.logLevel = self._deployConf.getLogLevelXcat()
        self.test_mode = self._deployConf.getTestXcat()
        
        print "\nReading Configuration file from "+self._deployConf.getConfigFile()+"\n"
        
        self.logger = self.setup_logger()
        
        
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
        sock.listen(100) #Maximum of unaccepted connections
        while True:
            while True:
    
                self.logger.info('Accepted new connection')
                channel, details = sock.accept()                
                #receive the message
                data = channel.recv(2048)
                params = data.split(',')
    
                #params[0] is name
                #params[1] is operating system
                #params[2] is version
                #params[3] is arch
                #params[4] is kernel
                #params[5] is dir where img is placed
                #params[6] is the targeted machine (india, minicluster..) 
                
                self.name = params[0]    
                self.operatingsystem = params[1]    
                self.version = params[2]    
                self.arch = params[3]
                self.kernel = params[4]
                self.tempdir = params[5]
                self.machine = params[6]
    
    
                if len(params) != self.numparams:
                    msg = "ERROR: incorrect message"
                    self.errormsg(channel, msg)
                    break
    
                if not os.path.isfile(self.tempdir + '/' + self.name + '.tgz'):
                    msg = "ERROR: file not found"
                    self.errormsg(channel, msg)
                    break
    
                #Hook for Debian based systems to work in xCAT                
                if self.operatingsystem == 'ubuntu' or self.operatingsystem == 'debian':
                    self.prefix = 'rhels5.4'
    
                #Build filesystem    
                #Create Directory structure
                #/install/netboot/<name>/<arch>/compute/
                self.path = self.xcatNetbootImgPath + self.prefix + self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/'
                
                if os.path.isdir(self.path):
                    msg = "ERROR: The image already exists"
                    self.errormsg(channel, msg)
                    break
                
                cmd = 'mkdir -p ' + self.path + 'rootimg ' + self.path + 'temp'
                status = self.runCmd(cmd)    
                if status != 0:
                    msg = "ERROR: creating directory rootimg"
                    self.errormsg(channel, msg)
                    break
    
                #extract image. This can be changed later
                cmd = 'tar xfz ' + self.tempdir + '/' + self.name + '.tgz -C ' + self.path
                status = self.runCmd(cmd)    
                if status != 0:
                    msg = "ERROR: extracting image"
                    self.errormsg(channel, msg)
                    break                    
                cmd = 'rm -f ' + self.tempdir + '/' + self.name + '.tgz ' 
                status = self.runCmd(cmd)
    
                #mount image to extract files
                cmd = 'mount -o loop ' + self.path + '' + self.name + '.img ' + self.path + 'temp'
                status = self.runCmd(cmd)    
                if status != 0:
                    msg = "ERROR: mounting image"
                    self.errormsg(channel, msg)
                    break
                #copy files keeping the permission (-p parameter)
                cmd = 'cp -rp ' + self.path + 'temp/* ' + self.path + 'rootimg/'                
                status = os.system(cmd)    
                if status != 0:
                    msg = "ERROR: copying image"
                    self.errormsg(channel, msg)
                    break    
                cmd = 'umount ' + self.path + 'temp'
                status = self.runCmd(cmd)
                #we need to read the manifest if we send here the image from the repository directly
                cmd = 'rm -rf ' + self.path + 'temp ' + self.path + '' + self.name + '.img ' + self.path + '' + self.name + '.manifest.xml'
                status = self.runCmd(cmd)    
                if status != 0:
                    msg = "ERROR: unmounting image"
                    self.errormsg(channel, msg)
                    break
    
                #create directory that contains initrd.img and vmlinuz
                tftpimgdir = '/tftpboot/xcat/' + self.prefix + self.operatingsystem + '' + self.name + '/' + self.arch
                cmd = 'mkdir -p ' + tftpimgdir
                status = self.runCmd(cmd)    
                if status != 0:
                    break
                
                if (self.operatingsystem == "ubuntu"):
                    
                    #############################
                    #Insert client stuff for ubuntu. To be created. We may use the same function but Torque binaries and network config must be different
                    ############################
                                 
                    #getting initrd and kernel customized for xCAT
                    cmd = 'wget ' + self.http_server + '/kernel/specialubuntu/initrd.gz -O ' + self.path + '/initrd-stateless.gz'
                    status = self.runCmd(cmd)    
                    if status != 0:
                        msg = "ERROR: retrieving/copying initrd.gz"
                        self.errormsg(channel, msg)
                        break    
                    cmd = 'wget ' + self.http_server + '/kernel/specialubuntu/kernel -O ' + self.path + '/kernel'
                    status = self.runCmd(cmd)    
                    if status != 0:
                        msg = "ERROR: retrieving/copying kernel"
                        self.errormsg(channel, msg)
                        break
                    
                    #getting generic initrd and kernel 
                    cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/ubuntu10/' + self.arch + '/initrd.img -O ' + tftpimgdir + '/initrd.img'
                    status = self.runCmd(cmd)
    
                    if status != 0:
                        msg = "ERROR: retrieving/copying initrd.img"
                        self.errormsg(channel, msg)
                        break
    
                    cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/ubuntu10/' + self.arch + '/vmlinuz -O ' + tftpimgdir + '/vmlinuz'
                    status = self.runCmd(cmd)
    
                    if status != 0:
                        msg = "ERROR: retrieving/copying vmlinuz"
                        self.errormsg(channel, msg)
                        break
                    
                else: #Centos
                    #Insert client stuff
                    status = self.customize_centos_img()
                    if status != 0:
                        msg = "ERROR: customizing the image. Look into server logs for details"
                        self.errormsg(channel, msg)
                        break    
                    
                    #getting initrd and kernel customized for xCAT
                    cmd = 'wget ' + self.http_server + '/kernel/initrd.gz -O ' + self.path + '/initrd-stateless.gz'
                    status = self.runCmd(cmd)    
                    if status != 0:
                        msg = "ERROR: retrieving/copying initrd.gz"
                        self.errormsg(channel, msg)
                        break    
                    cmd = 'wget ' + self.http_server + '/kernel/kernel -O ' + self.path + '/kernel'
                    status = self.runCmd(cmd)    
                    if status != 0:
                        msg = "ERROR: retrieving/copying kernel"
                        self.errormsg(channel, msg)
                        break
                    
                    #getting generic initrd and kernel
                    cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/centos5/' + self.arch + '/initrd.img -O ' + tftpimgdir + '/initrd.img'
                    status = self.runCmd(cmd)    
                    if status != 0:
                        msg = "ERROR: retrieving/copying initrd.img"
                        self.errormsg(channel, msg)
                        break    
                    cmd = 'wget ' + self.http_server + '/kernel/tftp/xcat/centos5/' + self.arch + '/vmlinuz -O ' + tftpimgdir + '/vmlinuz'
                    status = self.runCmd(cmd)    
                    if status != 0:
                        msg = "ERROR: retrieving/copying vmlinuz"
                        self.errormsg(channel, msg)
                        break
                                    
                #XCAT tables                
                cmd = 'chtab osimage.imagename=' + self.prefix + self.operatingsystem + '' + self.name + '-' + self.arch + '-netboot-compute osimage.profile=compute '\
                        'osimage.imagetype=linux osimage.provmethod=netboot osimage.osname=linux osimage.osvers=' + self.prefix + self.operatingsystem + '' + self.name + \
                        ' osimage.osarch=' + self.arch + ''
                self.logger.debug(cmd)
                if not self.test_mode:
                    status = os.system(cmd)
    
                if (self.machine == "india"):
                    cmd = 'chtab boottarget.bprofile=' + self.prefix + self.operatingsystem + '' + self.name + ' boottarget.kernel=\'xcat/netboot/' + self.prefix + \
                          self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/kernel\' boottarget.initrd=\'xcat/netboot/' + self.prefix + self.operatingsystem + \
                          '' + self.name + '/' + self.arch + '/compute/initrd-stateless.gz\' boottarget.kcmdline=\'imgurl=http://172.29.202.149/install/netboot/' + self.prefix + \
                          self.operatingsystem + '' + self.name + '/' + self.arch + '/compute/rootimg.gz console=ttyS0,115200n8r\''                          
                    self.logger.debug(cmd)
                    if not self.test_mode:
                        status = os.system(cmd)
    
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
                    self.errormsg(channel, msg)
                    break
                
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
    
                channel.send("OK")    
                self.logger.debug("sending to the client the info needed to register the image in Moab")    
                moabstring = self.prefix    
                self.logger.debug(moabstring)    
                channel.send(moabstring)
                channel.close()
            


    def customize_centos_img(self):
        status = 0
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
            self.runCmd('chmod +x ' + self.path + '/rootimg/etc/netsetup/netsetup.sh')
            self.runCmd('rm -f ' + self.path + 'netsetup_minicluster.tgz')

            os.system('cat ' + self.path + '/rootimg/etc/hosts' + ' > ' + self.path + '/_hosts') #Create it in a unique directory
            f = open(self.path + '/_hosts', 'a')
            f.write("\n" + "172.29.200.1 t1 tm1" + '\n' + "172.29.200.3 tc1" + '\n' + "149.165.145.35 tc1r.tidp.iu.futuregrid.org tc1r" + '\n' + \
                    "172.29.200.4 tc2" + '\n' + "149.165.145.36 tc2r.tidp.iu.futuregrid.org tc2r" + '\n')
            f.close()
            os.system('mv -f ' + self.path + '/_hosts ' + self.path + '/rootimg/etc/hosts')
            os.system('chown root:root ' + self.path + '/rootimg/etc/hosts')
            os.system('chmod 644 ' + self.path + '/rootimg/etc/hosts')

            self.runCmd('mkdir -p ' + self.path + '/rootimg/root/.ssh')
            f = open(self.path + '/_authorized_keys', 'a') #Create it in a unique directory
            f.write("ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA5uo1oo4+/wzKl+4hfaD/cf4MF6WDrWnG8wtufSk4ThOvCfc4a1BiEUZ+O71"
                      "u1qzgbvi0TnA+tc3fS9mU2zrBZeIL1eB2VkK4cjzltIS6pthm8tFUCtS1hHYupnftC/1Hbzo2zJB+nGAfIznmkYATiVvulwl6SudV"
                      "RKM2SUahWsGXh4JkZqt4vAAuBVifFwE3axh3g9nji8wq4ITYjzTWDsogbcwsJNXpF9dkyuDg5xQmEszUsGSug3hA4aVrgs36cnLNG"
                      "5i+zWlwmA31IV+6Yyx1+s6YYp6YG8GNiuL1vZUYrnvfmRbm24eUc7cU4Dz6hBfI2wqjDkCU15HRM0ZV3Q== root@tm1" + '\n')
            f.close()
            os.system('mv ' + self.path + '/_authorized_keys ' + self.path + '/rootimg/root/.ssh/authorized_keys')

            os.system('chown root:root ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            os.system('chmod 600 ' + self.path + '/rootimg/root/.ssh/authorized_keys')


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
 
            f = open('./_authorized_keys', 'a') #Create it in a unique directory
            f.write("\n" + "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsAaCJFcGUXSmA2opcQk/HeuiJu417a69KbuWNjf1UqarP7t0hUpMXQnlc8+yfi"
                      "fI8FpoXtNCai8YEPmpyynqgF9VFSDwTp8use61hBPJn2isZha1JvkuYJX4n3FCHOeDlb2Y7M90DvdYHwhfPDa/jIy8PvFGiFkRLSt1kghY"
                      "xZSleiikl0OxFcjaI8N8EiEZK66HAwOiDHAn2k3oJDBTD69jydJsjExOwlqZoJ4G9ScfY0rpzNnjE9sdxpJMCWcj20y/2T/oeppLmkq7aQtu"
                      "p8JMPptL+kTz5psnjozTNQgLYtYHAcfy66AKELnLuGbOFQdYxnINhX3e0iQCDDI5YQ== jdiaz@india.futuregrid.org" + "\n")
            f.close()
            os.system('mv ./_authorized_keys ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            os.system('chown root:root ' + self.path + '/rootimg/root/.ssh/authorized_keys')
            os.system('chmod 600 ' + self.path + '/rootimg/root/.ssh/authorized_keys')

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
            os.system('cat ' + self.path + '/rootimg/etc/rc.d/rc.local' + ' > ./_rc.local') #Create it in a unique directory
            f = open('./_rc.local', 'a')
            f.write("\n" + "sleep 10" + "\n" + "/etc/init.d/pbs_mom start" + '\n')
            f.close()
            os.system('mv -f ./_rc.local ' + self.path + '/rootimg/etc/rc.d/rc.local')
            os.system('chown root:root ' + self.path + '/rootimg/etc/rc.d/rc.local')
            os.system('chmod 755 ' + self.path + '/rootimg/etc/rc.d/rc.local')


            f = open(self.path + '/config', 'w')
            f.write("opsys " + self.operatingsystem + "" + self.name + "\n" + "arch " + self.arch)
            f.close()

            os.system('mv ' + self.path + '/config ' + self.path + '/rootimg/var/spool/torque/mom_priv/')
            os.system('chown root:root ' + self.path + '/rootimg/var/spool/torque/mom_priv/config')

        #Setup fstab
        f = open(self.path + '/fstab', 'w')
        f.write(fstab)
        f.close()
        os.system('mv -f ' + self.path + '/fstab ' + self.path + 'rootimg/etc/fstab')
        self.logger.info('Injected fstab')
        
        #Inject the kernel
        self.logger.info('Retrieving kernel ' + self.kernel)
        status = self.runCmd('wget ' + self.http_server + '/kernel/' + self.kernel + '.modules.tar.gz -O ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.runCmd('tar xfz ' + self.path + '' + self.kernel + '.modules.tar.gz --directory ' + self.path + '/rootimg/lib/modules/')
        self.runCmd('rm -f ' + self.path + '' + self.kernel + '.modules.tar.gz')
        self.logger.info('Injected kernel ' + self.kernel)

        return status

    def errormsg(self, channel, msg):
        self.logger.error(msg)
        channel.send(msg)
        channel.close()
    
    def runCmd(self, cmd):
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
    if os.getuid() != 0:
        print "Sorry, you need to run with root privileges"
        sys.exit(1)

    server = IMDeployServerXcat()
    server.start()

if __name__ == "__main__":
    main()
#END
