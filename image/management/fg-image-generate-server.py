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
from xml.dom.minidom import Document, parse
from time import time


def main():    
    
    
    #the ips should be given by the method that deploy the VM on demand.
    vmaddr_centos = "192.168.1.23"
    vmaddr_rhel= ""
    vmaddr_ubuntu= ""
    vmaddr_debian= ""
    vmaddr=""
    ####
    
    ######################
    #Server configuration
    ######################
    vmdir="/root/"
    serverdir="/srv/cloud/one/fg-management"
    
    addrnfs="192.168.1.6"  #ip of the machine that shares the directory tempserver
    tempdirserver="/srv/scratch" #name of the shared dir in the server
    tempdir="/media/"  #name of the shared dir in the VM
    ####
    
    options=''
    
    #Set up logging
    log_filename = 'fg-image-generate-server.log'
    #logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt='%a, %d %b %Y %H:%M:%S',filemode='w',filename=log_filename,level=logging.DEBUG)
    logger = logging.getLogger()
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
    logging.info('Image generator server...')
        
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
    userId='root'
    
    #this is the user name
    user = ops.user
    
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)        
        #ch.setLevel(logging.INFO)
    
    #TODO: authenticate user via promting for CERT or password to auth against LDAP db
    
        
#TODO. METHOD THAT BOOT A VM, inject the public key of the user in the root user AND GIVE ME THE IP
#Here we have to call other method that boot an image with the OS required and give me the ip
    
    if ops.os == "ubuntu":        
        vmaddr=vmaddr_ubuntu
    elif ops.os == "debian":
        vmaddr=vmaddr_debian
    elif ops.os == "rhel":
        vmaddr=vmaddr_rhel
    elif ops.os == "centos":
        vmaddr=vmaddr_centos
    
    
    logging.info("The VM deployed is in "+vmaddr)
    
    logging.info("Mount scratch directory in the VM")
    cmdmount="mount -t nfs "+addrnfs+":"+tempdirserver+" "+tempdir
    uid = _rExec(userId, cmdmount, logging, vmaddr)
    
    logging.info("Sending fg-image-generate.py to the VM")
    cmdscp = "scp "+serverdir+'/fg-image-generate.py  ' + userId + "@" + vmaddr + ":"+vmdir
    looging.info(cmdscp)
    stat = os.system(cmdscp)
    if (stat != 0):
        looging.error("Error sending fg-image-generate.py to the VM. Exit status " + str(stat))
        
                
    options+="-a "+ops.arch+" -o "+ops.os+" -v "+ops.version+" -u "+user+" -t "+tempdir
    
    if type(ops.givenname) is not NoneType:
        options+=" -n "+ops.givenname
    if type(ops.desc) is not NoneType:
        options+=" -e "+ops.desc
    if type(ops.auth) is not NoneType:
        options+" -l "+ops.auth
    if type(ops.software) is not NoneType:
        options+" -s "+ops.software
    
    cmdexec = " '" + vmdir + "fg-image-generate.py "+options
    
    print cmdexec
    
    uid = _rExec(userId, cmdexec, logging, vmaddr)
    
    status = uid[0].strip() #it contains error or filename
    if status=="error":
        print uid
    else:         
        out=os.system("tar cfz "+tempdirserver+""+status+".tgz -C "+tempdirserver+" "+status+".manifest.xml "+status+".img")
        if out == 0:
            os.system("rm -f "+tempdirserver+""+status+".manifest.xml "+tempdirserver+""+status+".img")
            
        print tempdirserver+""+status+".tgz"
        
    
    

############################################################
# _rExec
############################################################
def _rExec(userId, cmdexec, logging, vmaddr):        
            
    #TODO: do we want to use the .format statement from python to make code more readable?
    #Set up random string    
    random.seed()
    randid = str(random.getrandbits(32))
          
    cmdssh = "ssh " + userId + "@" + vmaddr
    tmpFile = "/tmp/" + str(time()) + str(randid)
    #print tmpFile
    cmdexec = cmdexec + " > " + tmpFile
    cmd = cmdssh + cmdexec
    
    logging.info(str(cmd))
    
    stat = os.system(cmd)
    if (str(stat) != "0"):
        #print stat
        logging.info(str(stat))
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