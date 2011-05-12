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
    serveraddr = "fg-gravel6.futuregrid.iu.edu"     
    serverdir="/srv/cloud/one/fg-management"   
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
    user='oneadmin'
    
    
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)
        ch.setLevel(logging.INFO)
    
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
    
    #Parse Software stack list
    if type(ops.software) is not NoneType:
        packs = ops.software
        logging.debug('Selected software packages: ' + str(acks))
    else:
        packs = 'wget' 
    
    #TODO: Authorization mechanism TBD
    if type(ops.auth) is not NoneType:
        auth = ""
    
    # Build the image
    #Parse OS and version command line args
    if (ops.os == "Ubuntu" or ops.os == "ubuntu" or         
       ops.os == "Debian" or ops.os == "debian" or     
       ops.os == "Redhat" or ops.os == "redhat" or ops.os == "rhel" or
       ops.os == "CentOS" or ops.os == "Centos" or ops.os == "centos" or       
       ops.os == "Fedora" or ops.os == "fedora"):
       pass 
    else:
        parser.error("Incorrect OS type specified")
        sys.exit(1)

    #generate string with options in the previous ifs
    
    options+="-a "+ops.arch+" -s "+packs+" -o "+ops.os
    
    cmdexec = " '" + serverdir + "fg-image-generate-server.py "+options
    
    uid = self._rExec(userId, cmdexec, logging, serveraddr)
    
    #call server with options
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
def _retrieveImg(userId, imgURI, logging):
    imgIds=imgURI.split("/")
    imgId=imgIds[len(imgIds-1)]
    
    cmdscp = "scp " + userId + "@" + imgURI + " ."    
    output = ""
    try:
        logging.info("Retrieving the image")
        logging.info(cmdscp)
        stat = os.system(cmdscp)
        if (stat == 0):
            output = "The image " + imgId + " is located in " + os.popen('pwd', 'r').read().strip() + "/" + imgId            
            cmdrm = " rm -rf " + (imgURI).split(".")[0]+"*"
            logging.info("Post processing")
            logging.info(cmdrm)
            #_rExec(userId, cmdrm)
        else:
            logging.error("Error retrieving the image. Exit status " + str(stat))
            #remove the temporal file
    except os.error:
        logging.error("Error, The image cannot be retieved" + str(sys.exc_info()))
        output = None
    
    return output

if __name__ == "__main__":
    main()   
    
    
    
    