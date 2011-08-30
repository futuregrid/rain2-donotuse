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
from multiprocessing import Process

from subprocess import *
#from xml.dom.ext import *
from xml.dom.minidom import Document, parseString
import xmlrpclib
import time
from IMServerConf import IMServerConf

#Import client repository
sys.path.append(os.getcwd())
sys.path.append(os.path.dirname(__file__) + "/../")
from repository.client.IRServiceProxy import IRServiceProxy

class IMGenerateServer(object):

    def __init__(self):
        super(IMGenerateServer, self).__init__()

        #*********************
        #Static Configuration.
        #*********************        
        #this is to login in the VM. This MUST be root because IMGenerateScript needs this access.
        self.rootId = 'root'
        self.numparams = 9
        
        
        #this is the user that requested the image
        self.user = ""
        self.os = ""
        self.version = ""
        self.arch = ""
        self.auth = ""
        self.software = ""        
        self.givenname = ""
        self.desc = ""
        self.getimg = False
        
        #load configuration
        self._genConf = IMServerConf()
        self._genConf.load_generateServerConfig()
        self.port = self._genConf.getGenPort()
        self.proc_max = self._genConf.getProcMax()
        self.refresh_status = self._genConf.getRefreshStatus()
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
        
        self.oneauth = self._genConf.getOneUser() + ":" + self._genConf.getOnePass()
        
        self.log_filename = self._genConf.getLogGen()
        self.logLevel = self._genConf.getLogLevelGen()
    
        self.logger = self.setup_logger()
                
        self._reposervice = IRServiceProxy()
    
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
    """
    def get_adminpass(self, oneadmin):
        ##############
        #GET oneadmin password encoded in SHA1
        ##############
        p = Popen('oneuser list', stdout=PIPE, shell=True)
        p1 = Popen('grep ' + oneadmin, stdin=p.stdout, stdout=PIPE, shell=True)
        p2 = Popen('cut -d\" \" -f13', stdin=p1.stdout, shell=True, stdout=PIPE)
        oneadminpass = p2.stdout.read().strip()
            
        return oneadmin + ":" + oneadminpass
    """
    def start(self):
        self.logger.info('Starting Server on port ' + str(self.port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.port))
        sock.listen(1) #Maximum of system unaccepted connections. Maximum value depend of the system (usually 5) 
                
        proc_list=[]
        total_count=0
        while True:        
            if len(proc_list)==self.proc_max:
                full=True
                while full:
                    for i in range(len(proc_list)-1,-1,-1):
                        #self.logger.debug(str(proc_list[i]))
                        if not proc_list[i].is_alive():
                            #print "dead"                        
                            proc_list.pop(i)
                            full=False
                    if full:
                        time.sleep(self.refresh_status)
            
            total_count+=1
            channel, details = sock.accept()            
            proc_list.append(Process(target=self.generate, args=(channel,details, total_count)))            
            proc_list[len(proc_list)-1].start()    
      
    def generate(self, channel, details, pid):
        #this runs in a different proccess
        
        self.logger=logging.getLogger("GenerateServer."+str(pid))
        
        self.logger.info('Processing an image generation request')
        #it will have the IP of the VM
        vmaddr = ""        
        options = ''    
        vmID = 0
        
        #receive the message
        data = channel.recv(2048)
        
        self.logger.debug("received data: "+data)
        
        params = data.split('|')

        #params[0] is auth
        #params[1] is user
        #params[2] is operating system
        #params[3] is version
        #params[4] is arch
        #params[5] is software
        #params[6] is givenname
        #params[7] is the description
        #params[8] is to retrieve the image or to upload in the repo (true or false, respectively)

        self.auth = params[0]
        self.user =  params[1]                 
        self.os = params[2]
        self.version = params[3] 
        self.arch = params[4]
        self.software = params[5]        
        self.givenname = params[6]
        self.desc = params[7]
        self.getimg = eval(params[8]) #boolean
        
        if len(params) != self.numparams:
            msg = "ERROR: incorrect message"
            self.errormsg(channel, msg)
            #break
            sys.exit(1)

        
        channel.send("OK")
        

        vmfile = ""
        if self.os == "ubuntu":
            vmfile = self.vmfile_ubuntu
        elif self.os == "debian":
            vmfile = self.vmfile_debian
        elif self.os == "rhel":
            vmfile = self.vmfile_rhel
        elif self.os == "centos":
            vmfile = self.vmfile_centos

        # ---Start xmlrpc client to opennebula server-------------
        try:
            server = xmlrpclib.ServerProxy(self.xmlrpcserver)
        except:
            self.logger.error("Error connection with OpenNebula " + str(sys.exc_info()))
            print "Error connecting with OpenNebula " + str(sys.exc_info())
            sys.exit(1)

        ###########
        #BOOT VM##
        ##########
        output = self.boot_VM(server, vmfile)
        vmaddr = output[0]
        vmID = output[1]
        #####
        if vmaddr != "fail":
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
                    msg="ERROR: sending IMGenerateScript.py to the VM. Exit status " + str(stat)
                    self.errormsg(channel, msg)
                else:
                        
                    options += "-a " + self.arch + " -o " + self.os + " -v " + self.version + " -u " + self.user + " -t " + self.tempdir
            
                    if type(self.givenname) is not NoneType:
                        options += " -n " + self.givenname
                    if type(self.desc) is not NoneType:
                        options += " -e " + self.desc
                    if type(self.auth) is not NoneType:
                        options += " -l " + self.auth
                    if type(self.software) is not NoneType:
                        options += " -s " + self.software
            
                    options += " -c " + self.http_server + " -b " + self.bcfg2_url + " -p " + str(self.bcfg2_port)
              
                    cmdexec = " -q '/root/IMGenerateScript.py " + options + " '"
            
                    self.logger.info(cmdexec)
            
                    uid = self._rExec(self.rootId, cmdexec, vmaddr)
                    
                    self.logger.info("copying fg-image-generate.log to scrach partition "+self.tempdirserver)
                    cmdscp = "scp -q " + self.rootId + "@" + vmaddr + ":/root/fg-image-generate.log "+self.tempdirserver+"/"+str(vmID)+"_gen.log"
                    os.system(cmdscp)
                    
                    status = uid[0].strip() #it contains error or filename
                    if status == "error":
                        msg = "ERROR: "+str(uid)
                        errormsg(channel, msg)
                    else:
                        #stat = 0
                        #while stat != 0 and :
                        self.logger.info("Umount scratch directory in the VM")
                        cmd = "ssh -q " + self.rootId + "@" + vmaddr
                        cmdmount = " umount " + self.tempdir
                        self.logger.debug(cmd + cmdmount)
                        stat = os.system(cmd + cmdmount)
                        self.logger.debug("exit status "+str(stat))
                            #if stat != 0:
                            #    time.sleep(2)
                        
                        #destroy VM
                        self.logger.info("Destroy VM")
                        server.one.vm.action(self.oneauth, "finalize", vmID)
                        
                        self.logger.debug("Generating tgz with image and manifest files")
                        out = os.system("tar cfz " + self.tempdirserver + "/" + status + ".tgz -C " + self.tempdirserver + \
                                        " " + status + ".manifest.xml " + status + ".img")
                        if out == 0:
                            os.system("rm -f " + self.tempdirserver + "" + status + ".manifest.xml " + self.tempdirserver + \
                                      "" + status + ".img")
                        else:
                            msg = "ERROR: generating compressed file with the image and manifest"
                            errormsg(channel, msg)
                            #break
                            sys.exit(1) 
    
                status = 0
                ok = False
                if (len(args) == 2):
                    status = service.put(os.popen('whoami', 'r').read().strip(), None, args[0], args[1])
                    ok = True
                elif (len(args) == 1):
                    status = service.put(os.popen('whoami', 'r').read().strip(), None, args[0], "")
                    ok = True
                else:
                    usage()
                #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
                #print "image has been uploaded and registered with id " + str(id1)
                #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
                if(ok):
                    if(status == "0"):
                        print "the image has NOT been uploaded. Please, verify that the file exists and the metadata string is valid"
                    elif(status == "-1"):
                        print "the image has NOT been uploaded"
                        print "The User does not exist"
                    elif(status == "-2"):
                        print "The image has NOT been uploaded"
                        print "The User is not active"
                    elif(status == "-3"):
                        print "The image has NOT been uploaded"
                        print "The file exceed the quota"
                    else:
                        print "image has been uploaded and registered with id " + str(status)

                        
                        if self.getimg:                            
                            #send back the url where the image is
                            channel.send(self.tempdirserver + "" + status + ".tgz")
                            channel.close()
                        else:                                                        
                            status=""
                            error_repo = False
                            #send back the ID of the image in the repository
                            try:
                                status=self._reposervice.put(self.user, None, self.tempdirserver + "" + status + ".tgz", "os="+\
                                                             self.os+"_"+self.version+"|arch="+self.arch+"|description="+self.desc )
                                if(status == "0"):                                
                                    msg= "ERROR: uploading image to the repository. File does not exists or metadata string is invalid"
                                    error_repo = True
                                elif(status == "-1"):                                
                                    msg= "ERROR: uploading image to the repository. The User does not exist"
                                    error_repo = True
                                elif(status == "-2"):                                
                                    msg= "ERROR: uploading image to the repository. The User is not active"
                                    error_repo = True
                                elif(status == "-3"):
                                    msg= "ERROR: uploading image to the repository. The file exceed the quota"
                                    error_repo = True
                                else:
                                    channel.send(str(status))
                                    channel.close()
                            except:
                                msg= "ERROR: uploading image to the repository. "+str(sys.exc_info())
                                error_repo = True
                                
                            if error_repo:
                                errormsg(channel, msg)
                                os.system("rm -f "+self.tempdirserver + "" + status + ".tgz")                                
                            
            
            #destroy VM
            self.logger.info("Destroy VM")
            server.one.vm.action(self.oneauth, "finalize", vmID)

    
    def errormsg(self, channel, msg):
        self.logger.error(msg)
        channel.send(msg)
        channel.close()
    
    def boot_VM(self, server, vmfile):
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
    
        #print vmfile
        #-----read template into string -------------------------
        #s=open('./share/examples/ubuntu_context.one','r').read()
        s = open(vmfile, 'r').read()
        #self.logger.debug("Vm template:\n"+s)
    
        #-----Start VM-------------------------------------------
        vm = server.one.vm.allocate(self.oneauth, s)
        
        #print self.oneauth
        #print vm
        
        if vm[0]:
            self.logger.debug("VM ID: " + str(vm[1]))
    
            #monitor VM
            booted = False
            while not booted:
                try:
                    #-------Get Info about VM -------------------------------
                    vminfo = server.one.vm.info(self.oneauth, vm[1])
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
                        time.sleep(5)
                except:
                    pass
        
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
                        time.sleep(5)
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
    
def main():
       
    
    imgenserver = IMGenerateServer()
    
    imgenserver.start()            
        

if __name__ == "__main__":
    main()
#END
