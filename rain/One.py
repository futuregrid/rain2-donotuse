#!/usr/bin/env python
"""
Server that manage the image generation by provisioning VM and interacting with IMGenerateScript
"""
__author__ = 'Javier Diaz'
__version__ = '0.9'

from types import *
import re
import logging
import logging.handlers
import random
import os
import sys
import socket, ssl
from multiprocessing import Process

from subprocess import *
#from xml.dom.ext import *
from xml.dom.minidom import Document, parseString
import xmlrpclib
import time
import argparse


class OpenNebulaTest(object):

    def __init__(self):
        super(OpenNebulaTest, self).__init__()

        #*********************
        #Static Configuration.
        #*********************        
        #this is to login in the VM. This MUST be root because IMGenerateScript needs this access.
        self.rootId = 'root'
        self.vmfile_centos = "/srv/cloud/one/test_opennebula/centos.one"             
        self.xmlrpcserver = "http://localhost:2633/RPC2"
        self.bridge = "br0:jv"


        
        self.oneauth = "oneadmin:0a73ae90642f781274eeb13a301bbed786d673fb"
        
        self.log_filename = "./opennebulatest.log"
        self.logLevel = logging.DEBUG    
        self.logger = self.setup_logger()

    
    def setup_logger(self):
        #Setup logging
        logger = logging.getLogger("OpenNebulaTest")
        logger.setLevel(self.logLevel)    
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler = logging.FileHandler(self.log_filename)
        handler.setLevel(self.logLevel)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False #Do not propagate to others
        
        return logger    
   
      
    def start(self, n):
        #this runs in a different proccess
        
        start_all = time.time()
        
        self.logger = logging.getLogger("OpenNebulaTest." + str(os.getpid()))
        
        self.logger.info('Starting')
        #it will have the IP of the VM  

        
        #channel.write("OK")
        #print "---Auth works---"            
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
        start = time.time()
        
        output = self.boot_VM(server, vmfile, n)
        
        end = time.time()
        self.logger.info('TIME walltime boot VM:' + str(end - start))
        
        end_all = time.time()
        self.logger.info('TIME walltime image generate:' + str(end_all - start_all))
        
    
    
    
    def boot_VM(self, server, vmfile,n):
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
        
        s = open(os.path.expanduser(vmfile), 'r').read()
        #self.logger.debug("Vm template:\n"+s)
    
    
        vm = []
        
        #-----Start VMs-------------------------------------------
        ok=0
        vmaddr = []
        for i in range(n):
            vm.append(server.one.vm.allocate(self.oneauth, s))
            if vm[i][0]:
                self.logger.debug("VM ID: " + str(vm[i][1]))      
                vminfo = server.one.vm.info(self.oneauth, vm[i][1])                
                manifest = parseString(vminfo[1])
                nics = manifest.getElementsByTagName('NIC')                
                for j in range(len(nics)):
                    if(nics[j].childNodes[0].firstChild.nodeValue.strip() == self.bridge):
                        vmaddr.append(nics[j].childNodes[1].firstChild.nodeValue.strip())
                        ok+=1
                           
        if ok == n:
            self.logger.debug("All is ok")
        
            #wait all running
            maxretry = 240 #time that the VM has to change from penn to runn
            retry = 0
            fail = False
            
            allrunning = False
            while not allrunning and retry < maxretry and not fail:  #eventually the VM has to boot or fail
                    running = 0                                        
                    for i in range(n):
                        try:
                            #-------Get Info about VM -------------------------------
                            vminfo = server.one.vm.info(self.oneauth, vm[i][1])
                            #print  vminfo[1]
                            manifest = parseString(vminfo[1])                
                            #VM_status (init=0, pend=1, act=3, fail=7)
                            vm_status = manifest.getElementsByTagName('STATE')[0].firstChild.nodeValue.strip()
                            print vm_status
                            if vm_status == "3": #running
                                #LCM_status (prol=1,boot=2,runn=3, fail=14, unk=16)                                
                                lcm_status = manifest.getElementsByTagName('LCM_STATE')[0].firstChild.nodeValue.strip()
                
                                if lcm_status == "3": #if vm_status is 3, this will be 3 too.
                                    running += 1
                            elif vm_status == "7": #fail
                                self.logger.error("Fail to deploy VM " + str(vm[1]))                                
                                fail = True                                
                            elif vm_status == "6": #done
                                self.logger.error("The status of the VM " + str(vm[1]) + " is DONE")                                
                                fail = True                                
                        except:
                            pass
                    print "------------------"
                    if (running == n):
                        allrunning = True
                        retry+=1
                    else:
                        time.sleep(5)
                    if retry >= maxretry:
                        self.logger.error("The VMs did not change to runn status. Please verify that the status of the OpenNebula hosts "
                                          "or increase the wait time in the configuration file (max_wait) \n")                        
                        fail = True
                    
            if not fail:                
                for i in range(n):
                    if vmaddr[i].strip() != "":
                        self.logger.debug("IP of the VM " + str(vm[i][1]) + " is " + str(vmaddr[i]))
            
                        access = False
                        maxretry = 240  #this says that we wait 20 minutes maximum to allow the VM get online. 
                        #this also prevent to get here forever if the ssh key was not injected propertly.
                        retry = 0
                        self.logger.debug("Waiting to have access to VM")
                        while not access and retry < maxretry:
                            cmd = "ssh -q -oBatchMode=yes root@" + vmaddr + " uname"
                            p = Popen(cmd, shell=True, stdout=PIPE)
                            status = os.waitpid(p.pid, 0)[1]
                            #print status
                            if status == 0:
                                access = True
                                self.logger.debug("The VM " + str(vm[1]) + " with ip " + str(vmaddr) + "is accessible")
                            else:
                                retry += 1
                                time.sleep(5)
                        if retry >= maxretry:
                            self.logger.error("Could not get access to the VM " + str(vm[1]) + " with ip " + str(vmaddr) + "\n" 
                                              "Please verify the OpenNebula templates to make sure that the public ssh key to be injected is accessible to the oneadmin user. \n"
                                              "Also verify that the VM has ssh server and is active on boot.")

                    else:
                        self.logger.error("Could not determine the IP of the VM " + str(vm[1]) + " for the bridge " + self.bridge)
                        fail=True
                        break
                if fail:
                    self.logger.error("Some VM failed to get IP")
                    self.logger.info("Destroy VMs")
                    for i in range(n):
                        try:                    
                            server.one.vm.action(self.oneauth, "finalize", vm[i][1])
                        except:
                            self.logger.error("Error destroying VM: "+vm[i][1])
            else:
                self.logger.error("Some VM failed")
                self.logger.info("Destroy VMs")
                for i in range(n):
                    try:                    
                        server.one.vm.action(self.oneauth, "finalize", vm[i][1])
                    except:
                        self.logger.error("Error destroying VM: "+vm[i][1])
        else:
            self.logger.error("Error to create VMs")
            self.logger.info("Destroy VMs")
            for i in range(n):
                try:                    
                    server.one.vm.action(self.oneauth, "finalize", vm[i][1])
                except:
                    self.logger.error("Error destroying VM: "+vm[i][1])
    
        return [vmaddr, vm[1]]
    
    def errormsg(self, channel, msg):
        self.logger.error(msg)
        try:    
            channel.write(msg)                
            channel.shutdown(socket.SHUT_RDWR)
            channel.close()
        except:
            self.logger.debug("In errormsg: " + str(sys.exc_info()))
        self.logger.info("Image Generation DONE")
    
def main():
       
    parser = argparse.ArgumentParser(prog="One", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="One Help ")    
    parser.add_argument('-n', '--number', dest='n', required=True, metavar='n', help='Number of Instances')
    
    
    args = parser.parse_args()

    
    
    imgtest = OpenNebulaTest()
    
    imgtest.start(int(args.n))            
        

if __name__ == "__main__":
    main()
#END
