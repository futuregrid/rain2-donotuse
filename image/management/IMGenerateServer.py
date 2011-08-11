#!/usr/bin/env python
"""
Server that manage the image generation by provisioning VM and interacting with IMGenerateScript
"""
__author__ = 'Javier Diaz'
__version__ = '0.1'

from optparse import OptionParser
from types import *
import re
import logging
import logging.handlers
import random
import os
import sys
import socket
from subprocess import *
#from xml.dom.ext import *
from xml.dom.minidom import Document, parseString
import xmlrpclib
import time
from IMServerConf import IMServerConf

def main():
    

    parser = OptionParser()

    #help is auto-generated
    parser.add_option("-o", "--os", dest="os", help="specify destination Operating System")
    parser.add_option("-v", "--version", dest="version", help="Operating System version")
    parser.add_option("-a", "--arch", dest="arch", help="Destination hardware architecture")
    parser.add_option("-l", "--auth", dest="auth", help="Authentication mechanism")
    parser.add_option("-s", "--software", dest="software", help="Software stack to be automatically installed")
    parser.add_option("-u", "--user", dest="user", help="FutureGrid username")
    parser.add_option("-n", "--name", dest="givenname", help="Desired recognizable name of the image")
    parser.add_option("-e", "--description", dest="desc", help="Short description of the image and its purpose")

    (ops, args) = parser.parse_args()

    imgenserver = IMGenerateServer(ops.os, ops.version, ops.arch, ops.auth, ops.software, ops.user, ops.givenname, ops.desc)
    imgenserver.generate()

class IMGenerateServer(object):

    def __init__(self, os, version, arch, auth, software, user, givenname, desc):
        super(IMGenerateServer, self).__init__()

        #*********************
        #Static Configuration.
        #*********************        
        #this is to login in the VM. This MUST be root because IMGenerateScript needs this access.
        self.rootId = 'root'         
        
        #this is the user that requested the image
        self.user = user
        self.os = os
        self.version = version
        self.arch = arch
        self.auth = auth
        self.software = software        
        self.givenname = givenname
        self.desc = desc
        
        #load configuration
        self._genConf = IMServerConf()
        self._genConf.load_generateServerConfig()
        self.vmfile_centos = self._genConf.getVmFileCentos()
        self.vmfile_rhel = self._genConf.getVmFileRhel()
        self.vmfile_ubuntu = self._genConf.getVmFileUbuntu()
        self.vmfile_debian = self._genConf.getVmFileDebian()        
        self.xmlrpcserver = self._genConf.getXmlRpcServer()
        self.bridge = self._genConf.getBridge()
        self.serverdir = self._genConf.getServerDir()
        if self.serverdir == None:
            self.serverdir = os.path.expanduser(os.path.dirname(__file__))        
        self.addrnfs = self._genConf.getAddrNfs()  
        self.tempdirserver = self._genConf.getTempDirServerGen()        
        self.tempdir = self._genConf.getTempDirGen()
        
        self.http_server = self._genConf.getHttpServerGen()
        self.bcfg2_url = self._genConf.getBcfg2Url()
        self.bcfg2_port = self._genConf.getBcgf2Port()
        
        self.log_filename = self._genConf.getLogGen()
        self.logLevel = self._genConf.getLogLevelGen()
    
        self.logger = self.setup_logger()
                
    
    def setup_logger(self):
        #Setup logging
        logger = logging.getLogger("GenerateServer")
        logger.setLevel(self.logLevel)    
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.log_filename)
        handler.setLevel(self.logLevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False #Do not propagate to others
        
        return logger    
    
    
    def generate(self):
    
        self.logger.info('Starting Image generator server')
        #it will have the IP of the VM
        vmaddr = ""
        vmfile = ""
        options = ''   
                
        if self.os == "ubuntu":
            vmfile = self.vmfile_ubuntu
        elif self.os == "debian":
            vmfile = self.vmfile_debian
        elif self.os == "rhel":
            vmfile = self.vmfile_rhel
        elif self.os == "centos":
            vmfile = self.vmfile_centos
    
        ##############
        #GET oneadmin password encoded in SHA1
        ##############
        p = Popen('oneuser list', stdout=PIPE, shell=True)
        p1 = Popen('grep oneadmin', stdin=p.stdout, stdout=PIPE, shell=True)
        p2 = Popen('cut -d\" \" -f13', stdin=p1.stdout, shell=True, stdout=PIPE)
        oneadminpass = p2.stdout.read().strip()
        
    
        # ---Start xmlrpc client to opennebula server-------------
        server = xmlrpclib.ServerProxy(self.xmlrpcserver)
        oneauth = "oneadmin:" + oneadminpass
        ###########
        #BOOT VM##
        ##########
        output = self.boot_VM(server, oneauth, vmfile)
        vmaddr = output[0]
        vmID = output[1]
        #####
    
        self.logger.info("The VM deployed is in " + vmaddr)
    
        self.logger.info("Mount scratch directory in the VM")
        cmd = "ssh -q " + self.rootId + "@" + vmaddr
        cmdmount = " mount -t nfs " + self.addrnfs + ":" + self.tempdirserver + " " + self.tempdir
        self.logger.info(cmd + cmdmount)
        stat = os.system(cmd + cmdmount)
    
    
        if (stat == 0):
            self.logger.info("Sending IMGenerateScript.py to the VM")
            cmdscp = "scp -q " + self.serverdir + '/IMGenerateScript.py  ' + self.rootId + "@" + vmaddr + ":/root/"
            self.logger.info(cmdscp)
            stat = os.system(cmdscp)
            if (stat != 0):
                self.logger.error("Error sending IMGenerateScript.py to the VM. Exit status " + str(stat))
    
    
            options += "-a " + self.arch + " -o " + self.os + " -v " + self.version + " -u " + self.user + " -t " + self.tempdir
    
            if type(self.givenname) is not NoneType:
                options += " -n " + self.givenname
            if type(self.desc) is not NoneType:
                options += " -e " + self.desc
            if type(self.auth) is not NoneType:
                options += " -l " + self.auth
            if type(self.software) is not NoneType:
                options += " -s " + self.software
    
            options += " -c " + self.http_server + " -b " + self.bcfg2_url + " -p " + self.bcfg2_port
      
            cmdexec = " -q '/root/IMGenerateScript.py " + options + " '"
    
            self.logger.info(cmdexec)
    
            uid = self._rExec(self.rootId, cmdexec, vmaddr)
    
            status = uid[0].strip() #it contains error or filename
            if status == "error":
                print uid
            else:
                out = os.system("tar cfz " + self.tempdirserver + "/" + status + ".tgz -C " + self.tempdirserver + " " + status + ".manifest.xml " + status + ".img")
                if out == 0:
                    os.system("rm -f " + self.tempdirserver + "" + status + ".manifest.xml " + self.tempdirserver + "" + status + ".img")
    
                print tempdirserver + "" + status + ".tgz"
    
            self.logger.info("Umount scratch directory in the VM")
            cmd = "ssh -q " + self.rootId + "@" + vmaddr
            cmdmount = " umount " + self.tempdir
            stat = os.system(cmd + cmdmount)
    
        #destroy VM
        server.one.vm.action(oneauth, "finalize", vmID)
    
    def boot_VM(self, server, oneauth, vmfile):
        """
        It will boot a VM using XMLRPC API for OpenNebula
        
        from lib/ruby/OpenNebula/VirtualMachine.rb
        index start in 0
        
        VM_STATE=%w{INIT PENDING HOLD ACTIVE STOPPED SUSPENDED DONE FAILED}
        LCM_STATE=%w{LCM_INIT PROLOG BOOT RUNNING MIGRATE SAVE_STOP SAVE_SUSPEND
            SAVE_MIGRATE PROLOG_MIGRATE PROLOG_RESUME EPILOG_STOP EPILOG
            SHUTDOWN CANCEL FAILURE CLEANUP UNKNOWN}
        """
        vmaddr = ""
        fail = False
    
    
        #-----read template into string -------------------------
        #s=open('./share/examples/ubuntu_context.one','r').read()
        s = open(vmfile, 'r').read()
        #self.logger.debug("Vm template:\n"+s)
    
        #-----Start VM-------------------------------------------
        vm = server.one.vm.allocate(oneauth, s)
    
        if vm[0]:
            self.logger.debug("VM ID:\n" + str(vm[1]))
    
            #monitor VM
            booted = False
            while not booted:
                #-------Get Info about VM -------------------------------
                vminfo = server.one.vm.info(oneauth, vm[1])
                #print  vminfo[1]
                manifest = parseString(vminfo[1])
    
                #VM_status (init=0, pend=1, act=3, fail=7)
                vm_status = manifest.getElementsByTagName('STATE')[0].firstChild.nodeValue.strip()
    
                if vm_status == "3":
                    #LCM_status (prol=1,boot=2,runn=3, fail=14, unk=16)
                    lcm_status = manifest.getElementsByTagName('LCM_STATE')[0].firstChild.nodeValue.strip()
    
                    if lcm_status == "3":
                        booted = True
                elif vm_status == "7":
                    self.logger.error("Fail to deploy VM " + str(vm[1]))
                    booted = True
                    fail = True
                    vmaddr = "fail"
                else:
                    time.sleep(2)
    
            if not fail:
                #get IP
                nics = manifest.getElementsByTagName('NIC')
    
                for i in range(len(nics)):
                    if(nics[i].childNodes[0].firstChild.nodeValue.strip() == self.bridge):
                        vmaddr = nics[i].childNodes[1].firstChild.nodeValue.strip()
    
                self.logger.debug("IP of the VM " + str(vm[1]) + " is " + str(vmaddr))
    
                access = False
                while not access:
                    cmd = "ssh -q root@" + vmaddr + " uname"
                    p = Popen(cmd, shell=True, stdout=PIPE)
                    status = os.waitpid(p.pid, 0)[1]
                    #print status
                    if status == 0:
                        access = True
                        self.logger.debug("The VM " + str(vm[1]) + " with ip " + str(vmaddr) + "is accessible")
                    else:
                        time.sleep(2)
        else:
            vmaddr = "fail"
    
        return [vmaddr, vm[1]]
    
    ############################################################
    # _rExec
    ############################################################
    def _rExec(self, userId, cmdexec, vmaddr):
    
        #TODO: do we want to use the .format statement from python to make code more readable?
        #Set up random string    
        random.seed()
        randid = str(random.getrandbits(32))
    
        cmdssh = "ssh " + userId + "@" + vmaddr
        tmpFile = "/tmp/" + str(time.time()) + str(randid)
        #print tmpFile
        cmdexec = cmdexec + " > " + tmpFile
        cmd = cmdssh + cmdexec
    
        self.logger.info(str(cmd))
    
        stat = os.system(cmd)
        if (str(stat) != "0"):
            #print stat
            self.logger.info(str(stat))
        f = open(tmpFile, "r")
        outputs = f.readlines()
        f.close()
        os.system("rm -f " + tmpFile)
        #output = ""
        #for line in outputs:
        #    output += line.strip()
        #print outputs
        return outputs


if __name__ == "__main__":
    main()
#END
