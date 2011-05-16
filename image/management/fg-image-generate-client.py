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
    
    ##configuration
    serveraddr = "fg-gravel6.futuregrid.iu.edu"     
    serverdir="/srv/cloud/one/fg-management/"   
    ####
    
    options=''
    
    #Set up logging
    log_filename = 'fg-image-generate-client.log'
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

    logging.info('Image generator client...')

        
    #help is auto-generated
    parser.add_option("-o", "--os", dest="OS", help="specify destination Operating System")
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
    userId='oneadmin'
    
    try:
        user = os.environ['FG_USER']
    except KeyError:
        if type(ops.user) is not NoneType:
            user = ops.user
        else:
            logging.info("FG_USER is not defined, we are using default user name")
            user = "default"
    
    
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)
        #ch.setLevel(logging.INFO)
    
    #TODO: authenticate user via promting for CERT or password to auth against LDAP db
    
    arch = "x86_64" #Default to 64-bit
    
    #Parse arch command line arg
    if type(ops.arch) is not NoneType:
        if ops.arch == "i386" or ops.arch == "i686":
            arch = "i386"
        elif ops.arch == "amd64" or ops.arch == "x86_64":
            arch = "x86_64"
        else:    
            parser.error("Incorrect architecture type specified (i386|x86_64)")
            sys.exit(1)
    
    logging.debug('Selected Architecture: ' + arch)
    
    
    #TODO: Authorization mechanism TBD
    if type(ops.auth) is not NoneType:
        auth = ""
    
    # Build the image
    version=""
    #Parse OS and version command line args
    OS=""
    if ops.OS == "Ubuntu" or ops.OS == "ubuntu":     
        OS="ubuntu"   
        if type(ops.version) is NoneType:
            version = latest_ubuntu
        elif ops.version == "10.04" or ops.version == "lucid":
            version = "lucid"
        elif ops.version == "9.10" or ops.version == "karmic":
            version = "karmic"                    
    elif ops.OS == "Debian" or ops.OS == "debian":
        OS="debian"
        version = latest_debian
    elif ops.OS == "Redhat" or ops.OS == "redhat" or ops.OS == "rhel":
        OS="rhel"
        version = latest_rhel
    elif ops.OS == "CentOS" or ops.OS == "CentOS" or ops.OS == "centos":
        OS="centos"                
        if type(ops.version) is NoneType:
            version = latest_centos
        #later control supported versions
        else: 
            version = latest_centos  
    elif ops.OS == "Fedora" or ops.OS == "fedora":
        OS="fedora"
        version = latest_fedora
    else:
        parser.error("Incorrect OS type specified")
        sys.exit(1)
        
    

    #generate string with options in the previous ifs
    
    options+="-a "+ops.arch+" -o "+ops.OS+" -v "+version+" -u "+user
    
    
    if type(ops.givenname) is not NoneType:
        options+=" -n "+ops.givenname
    if type(ops.desc) is not NoneType:
        options+=" -e "+ops.desc
    if type(ops.auth) is not NoneType:
        options+" -l "+ops.auth    
    if type(ops.software) is not NoneType:
        options+" -s "+ops.software
    
    cmdexec = " '" + serverdir + "fg-image-generate-server.py "+options+" '"
    
    logging.info("Generating the image")
    
    uid = _rExec(userId, cmdexec, logging, serveraddr)
    
    status = uid[0].strip()#it contains error or filename
    
    logging.info("Status: "+str(status))
    
    if status=="error":
        print "The image has not been generated properly. Exit error:"+uid[1]
    else:
        _retrieveImg(userId, status, logging, serveraddr)
    
    #server return addr of the img and metafeile compressed in a tgz or None
    #get tgz 
    #delete remote files

############################################################
# _rExec
############################################################
def _rExec(userId, cmdexec, logging, serveraddr):        
            
    #TODO: do we want to use the .format statement from python to make code more readable?
    #Set up random string    
    random.seed()
    randid = str(random.getrandbits(32))
          
    cmdssh = "ssh " + userId + "@" + serveraddr
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
    
############################################################
# _retrieveImg
############################################################
def _retrieveImg(userId, dir, logging, serveraddr):
    imgURI=serveraddr+":"+dir
    imgIds=imgURI.split("/")
    imgId=imgIds[len(imgIds)-1]
        
    cmdscp = "scp " + userId + "@" + imgURI + " ."    
    output = ""
    try:
        logging.info("Retrieving the image")
        logging.info(cmdscp)
        stat = os.system(cmdscp)
        stat=0
        if (stat == 0):
            output = "The image " + imgId + " is located in " + os.popen('pwd', 'r').read().strip() + "/" + imgId            
            cmdrm = " rm -f " + dir
            logging.info("Post processing")
            logging.info(cmdrm)
            _rExec(userId, cmdrm, logging, serveraddr)
        else:
            logging.error("Error retrieving the image. Exit status " + str(stat))
            #remove the temporal file
    except os.error:
        logging.error("Error, The image cannot be retieved" + str(sys.exc_info()))
        output = None
    
    return output

if __name__ == "__main__":
    main()   
    
    
    
    