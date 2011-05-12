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



def main():    
    
    ##configuration
    vmaddr = "192.168.1.23" #this should be given by the method that deploy the VM on demand.
    vmdir="/root/"     
    serverdir="/srv/cloud/one/fg-management"
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
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

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
    
    #user = os.popen('whoami', 'r').read().strip()
    user='root'
    
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)
        ch.setLevel(logging.INFO)
    
    #TODO: authenticate user via promting for CERT or password to auth against LDAP db
    
    #arch
    arch = ops.arch
    #Parse Software stack list
    packs=ops.software
    #os is also there
    
    
    #TODO. METHOD THAT BOOT A VM, inject the public key of the user in the root user AND GIVE ME THE IP
    
    
    logging.info("The VM deployed is in "+vmaddr)
    #mount
    logging.info("Mount scratch directory in the VM")
    cmdmount="mount -t nfs 192.168.1.6:/srv/scratch /media"
    uid = self._rExec(userId, cmdexec, logging, vmaddr)
    
    logging.info("Sending fg-image-generate.py to the VM")
    cmdscp = "scp "+serverdir+'/fg-image-generate.py  ' + userId + "@" + vmaddr + ":"+vmdir
    looging.info(cmdscp)
    stat = os.system(cmdscp)
    if (stat != 0):
        looging.error("Error sending fg-image-generate.py to the VM. Exit status " + str(stat))
        
                
    options+="-a "+ops.arch+" -s "+packs+" -o "+ops.os
    
    cmdexec = " '" + vmdir + "fg-image-generate.py "+options
    
    uid = self._rExec(userId, cmdexec, logging, vmaddr)
    
    #call server with options
    #server return addr of the img and metafeile compressed in a tgz or None
    #get tgz 
    #delete remote files

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