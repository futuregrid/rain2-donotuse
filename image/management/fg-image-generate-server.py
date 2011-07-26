#!/usr/bin/python
# Description: Command line front end for image generator
#
# Author: Javier Diaz & Andrew J. Younge & Fugang Wang
#

from optparse import OptionParser
from types import *
import re
import logging
import logging.handlers
import glob
import random
import os
import sys
import socket
from subprocess import *
#from xml.dom.ext import *
from xml.dom.minidom import Document, parseString
import xmlrpclib
import time


def main():    
    
    
    #the file of the VM to be deployed in OpenNebula
    vmfile_centos = "/srv/cloud/one/share/examples/centos_context.one"
    vmfile_rhel= ""
    vmfile_ubuntu= "/srv/cloud/one/share/examples/ubuntu_context.one"
    vmfile_debian= ""
    vmfile=""
    
    #
    xmlrpcserver='http://localhost:2633/RPC2'
    #Bridge/interface for VMs
    bridge="br1"
    #it will have the IP of the VM
    vmaddr=""
    ####
    
    ######################
    #Server configuration
    ######################
    vmdir="/root/"
    serverdir="/srv/cloud/one/fg-management"
    
    addrnfs="192.168.1.6"  #ip of the machine that shares the directory tempserver
    tempdirserver="/srv/scratch/" #name of the shared dir in the server
    tempdir="/media/"  #name of the shared dir in the VM
    ####
    
    options=''
    
    #Set up logging
    log_filename = 'fg-image-generate-server.log'
    #logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt='%a, %d %b %Y %H:%M:%S',filemode='w',filename=log_filename,level=logging.DEBUG)
    logger = logging.getLogger("ImgGenSrv")
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)
    #ch.setFormatter(formatter)
    #logger.addHandler(ch)

    logger.info('Image generator server...')
    
    parser = OptionParser()
    
    """
    #Default params
    base_os = ""
    spacer = "-"
    latest_ubuntu = "lucid"
    latest_debian = "lenny"
    latest_rhel = "5.5"
    latest_centos = "5.6"
    latest_fedora = "13"
    #kernel = "2.6.27.21-0.1-xen"
    
    #ubuntu-distro = ['lucid', 'karmic', 'jaunty']
    #debian-distro = ['squeeze', 'lenny', 'etch']
    #rhel-distro = ['5.5', '5.4', '4.8']
    #fedora-distro = ['14','12']
    """
    
        
    #help is auto-generated
    parser.add_option("-o", "--os", dest="os", help="specify destination Operating System")
    parser.add_option("-v", "--version", dest="version", help="Operating System version")
    parser.add_option("-a", "--arch", dest="arch", help="Destination hardware architecture")
    parser.add_option("-l", "--auth", dest="auth", help="Authentication mechanism")
    parser.add_option("-s", "--software", dest="software", help="Software stack to be automatically installed")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debugging")
    parser.add_option("-u", "--user", dest="user", help="FutureGrid username")
    parser.add_option("-n", "--name", dest="givenname", help="Desired recognizable name of the image")
    parser.add_option("-e", "--description", dest="desc", help="Short description of the image and its purpose")
        
    (ops, args) = parser.parse_args()
    
    #this is to log in in the VM 
    userId='root' #this MUST be root
    
    #this is the user name
    user = ops.user
    
    #Turn debugging off
#    if not ops.debug:
#        logger.setLevel(level=logging.INFO)
                
        #ch.setLevel(logging.INFO)
    
    #TODO: authenticate user via promting for CERT or password to auth against LDAP db
    
        
#TODO. METHOD THAT BOOT A VM, inject the public key of the user in the root user AND GIVE ME THE IP
#Here we have to call other method that boot an image with the OS required and give me the ip
    
    if ops.os == "ubuntu":        
        vmfile=vmfile_ubuntu
    elif ops.os == "debian":
        vmfile=vmfile_debian
    elif ops.os == "rhel":
        vmfile=vmfile_rhel
    elif ops.os == "centos":
        vmfile=vmfile_centos
     
    ##############
    #GET oneadmin password encoded in SHA1
    ##############
    p=Popen('oneuser list',stdout=PIPE)
    p1=Popen('grep oneadmin',stdin=p.stdout, stdout=PIPE)
    p2=Popen('cut -d\" \" -f13', stdin=p1.stdout)
    oneadminpass= p2.stdout.read()
    
    logger.debug("password "+str(oneadminpass))
     
    # ---Start xmlrpc client to opennebula server-------------
    server=xmlrpclib.ServerProxy(xmlrpcserver)       
    auth="oneadmin:"+oneadminpass 
    ###########
    #BOOT VM##
    ##########
    output=boot_VM(server, auth,vmfile, bridge, logger)
    vmaddr=output[0]
    vmID=output[1]    
    #####
    
    logger.info("The VM deployed is in "+vmaddr)
    
    logger.info("Mount scratch directory in the VM")
    cmd="ssh -q " + userId + "@" + vmaddr
    cmdmount=" mount -t nfs "+addrnfs+":"+tempdirserver+" "+tempdir
    logger.info(cmd+cmdmount)
    stat=os.system(cmd+cmdmount)
    
    
    if (stat == 0):        
        logger.info("Sending fg-image-generate.py to the VM")
        cmdscp = "scp -q "+serverdir+'/fg-image-generate.py  ' + userId + "@" + vmaddr + ":"+vmdir
        logger.info(cmdscp)
        stat = os.system(cmdscp)
        if (stat != 0):
            logger.error("Error sending fg-image-generate.py to the VM. Exit status " + str(stat))
            
                    
        options+="-a "+ops.arch+" -o "+ops.os+" -v "+ops.version+" -u "+user+" -t "+tempdir
        
        if type(ops.givenname) is not NoneType:
            options+=" -n "+ops.givenname
        if type(ops.desc) is not NoneType:
            options+=" -e "+ops.desc
        if type(ops.auth) is not NoneType:
            options+=" -l "+ops.auth
        if type(ops.software) is not NoneType:
            options+=" -s "+ops.software
        
        cmdexec = " -q '" + vmdir + "fg-image-generate.py "+options+" '"
        
        logger.info(cmdexec)
        
        uid = _rExec(userId, cmdexec, logger, vmaddr)
        
        status = uid[0].strip() #it contains error or filename
        if status=="error":
            print uid
        else:         
            out=os.system("tar cfz "+tempdirserver+"/"+status+".tgz -C "+tempdirserver+" "+status+".manifest.xml "+status+".img")
            if out == 0:
                os.system("rm -f "+tempdirserver+""+status+".manifest.xml "+tempdirserver+""+status+".img")
                
            print tempdirserver+""+status+".tgz"
            
        logger.info("Umount scratch directory in the VM")
        cmd="ssh -q " + userId + "@" + vmaddr
        cmdmount=" umount "+tempdir
        stat=os.system(cmd+cmdmount)
    
    #destroy VM
    server.one.vm.action(auth,"finalize",vmID)

def boot_VM(server, auth, vmfile, bridge, logger):
    """
    It will boot a VM using XMLRPC API for OpenNebula
    
    from lib/ruby/OpenNebula/VirtualMachine.rb
    index start in 0
    
    VM_STATE=%w{INIT PENDING HOLD ACTIVE STOPPED SUSPENDED DONE FAILED}
    LCM_STATE=%w{LCM_INIT PROLOG BOOT RUNNING MIGRATE SAVE_STOP SAVE_SUSPEND
        SAVE_MIGRATE PROLOG_MIGRATE PROLOG_RESUME EPILOG_STOP EPILOG
        SHUTDOWN CANCEL FAILURE CLEANUP UNKNOWN}
    """
    vmaddr=""
    fail=False
    
    
    #-----read template into string -------------------------
    #s=open('./share/examples/ubuntu_context.one','r').read()
    s=open(vmfile,'r').read()
    #logger.debug("Vm template:\n"+s)
    
    #-----Start VM-------------------------------------------
    vm=server.one.vm.allocate(auth,s)
    
    if vm[0]:
        logger.debug("VM ID:\n"+str(vm[1]))
    
        #monitor VM
        booted=False
        while not booted:
            #-------Get Info about VM -------------------------------
            vminfo=server.one.vm.info(auth,vm[1])
            #print  vminfo[1]
            manifest = parseString(vminfo[1])
        
            #VM_status (init=0, pend=1, act=3, fail=7)
            vm_status=manifest.getElementsByTagName('STATE')[0].firstChild.nodeValue.strip()
            
            if vm_status == "3":
                #LCM_status (prol=1,boot=2,runn=3, fail=14, unk=16)
                lcm_status=manifest.getElementsByTagName('LCM_STATE')[0].firstChild.nodeValue.strip()
                
                if lcm_status == "3":
                    booted=True
            elif vm_status == "7":
                logger.error("Fail to deploy VM "+str(vm[1]))
                booted=True
                fail=True
                vmaddr="fail"
            else:
                time.sleep(2)
                
        if not fail:    
            #get IP
            nics=manifest.getElementsByTagName('NIC')
            
            for i in range(len(nics)):
                if( nics[i].childNodes[0].firstChild.nodeValue.strip() == bridge ):
                    vmaddr=nics[i].childNodes[1].firstChild.nodeValue.strip()
            
            logger.debug("IP of the VM "+str(vm[1])+" is "+str(vmaddr))
            
            access=False
            while not access:
                cmd = "ssh -q root@"+vmaddr+" uname"
                p=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
                status=os.waitpid(p.pid,0)[1]
                #print status
                if status == 0:
                    access=True
                    logger.debug("The VM "+str(vm[1])+" with ip "+str(vmaddr)+"is accessible")
                else:
                    time.sleep(2)
    else:
        vmaddr="fail"
    
    return [vmaddr,vm[1]]

############################################################
# _rExec
############################################################
def _rExec(userId, cmdexec, logger, vmaddr):        
            
    #TODO: do we want to use the .format statement from python to make code more readable?
    #Set up random string    
    random.seed()
    randid = str(random.getrandbits(32))
          
    cmdssh = "ssh " + userId + "@" + vmaddr
    tmpFile = "/tmp/" + str(time.time()) + str(randid)
    #print tmpFile
    cmdexec = cmdexec + " > " + tmpFile
    cmd = cmdssh + cmdexec
    
    logger.info(str(cmd))
    
    stat = os.system(cmd)
    if (str(stat) != "0"):
        #print stat
        logger.info(str(stat))
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
