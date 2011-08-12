#!/usr/bin/env python
"""
Command line front end for image generator
"""
__author__ = 'Javier Diaz, Andrew Young'
__version__ = '0.1'

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
from IMClientConf import IMClientConf

class IMGenerate(object):
    def __init__(self, arch, OS, version, user, auth, software, givenname, desc, logger):
        super(IMGenerate, self).__init__()
        
        self.arch=arch
        self.OS=OS
        self.version=version
        self.user=user
        self.auth=auth
        self.software=software
        self.givenname=givenname
        self.desc=desc
        self.logger=logger
        
        #Load Configuration from file
        self._genConf = IMClientConf()
        self._genConf.load_generationConfig()        
        self.serveraddr = self._genConf.getServeraddr()
        self.serverdir = self._genConf.getServerdir()
        #this user will be changed to the normal userId 
        self.userId = self._genConf.getUser() #user to scp and run VM
        ####

    def generate(self):
        #generate string with options in the previous ifs
        
        options = "-a " + self.arch + " -o " + self.OS + " -v " + self.version + " -u " + self.user
    
    
        if type(self.givenname) is not NoneType:
            options += " -n " + self.givenname
        if type(self.desc) is not NoneType:
            options += " -e " + self.desc
        if type(self.auth) is not NoneType:
            options += " -l " + self.auth
        if type(self.software) is not NoneType:
            options += " -s " + self.software
    
        cmdexec = " '" + self.serverdir + "IMGenerateServer.py " + options + " '"
    
        print "Generating the image"
    
        uid = self._rExec(cmdexec)
    
        status = uid[0].strip() #it contains error or filename
        self.logger.debug("Status: " + str(status))
        
        output=None
        if status == "error":
            print "The image has not been generated properly. Exit error:" + uid[1]
            sys.exit(1)
        else:
            output=self._retrieveImg(status)
    
        #imgIds = status.split("/")
        #imgId = imgIds[len(imgIds) - 1]
    
        if output != None:
        
                print 'Generated image and the manifest are packed in the file ' + status + '.  Please be aware that this FutureGrid ' +\
                'image is packaged without a kernel and fstab and is not built for any deployment type.  To deploy the new ' +\
                'image, use the IMDeploy command.'
        #server return addr of the img and metafeile compressed in a tgz or None
        

    ############################################################
    # _rExec
    ############################################################
    def _rExec(self, cmdexec):
    
        #TODO: do we want to use the .format statement from python to make code more readable?
        #Set up random string    
        random.seed()
        randid = str(random.getrandbits(32))
        
        cmdssh = "ssh " + self.userId + "@" + self.serveraddr
        tmpFile = "/tmp/" + str(time()) + str(randid)
        #print tmpFile
        cmdexec = cmdexec + " > " + tmpFile
        cmd = cmdssh + cmdexec
    
        self.logger.debug(str(cmd))
    
        stat = os.system(cmd)
        if (str(stat) != "0"):
            #print stat
            self.logger.debug(str(stat))
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
    def _retrieveImg(self, dir):
        imgURI = self.serveraddr + ":" + dir
        imgIds = imgURI.split("/")
        imgId = imgIds[len(imgIds) - 1]
    
        cmdscp = "scp " + self.userId + "@" + imgURI + " ."
        output = ""
        try:
            print "Retrieving the image"
            self.logger.debug(cmdscp)
            stat = os.system(cmdscp)
            stat = 0
            if (stat == 0):
                output = "The image " + imgId + " is located in " + os.popen('pwd', 'r').read().strip() + "/" + imgId
                cmdrm = " rm -f " + dir
                print "Post processing"
                self.logger.debug(cmdrm)
                self._rExec(cmdrm)
            else:
                print "Error retrieving the image. Exit status " + str(stat)
                #remove the temporal file
        except os.error:
            print "Error, The image cannot be retieved" + str(sys.exc_info())
            output = None
    
        return output

def main():
    
    

    #Set up logging
    logger = logging.getLogger('GenerateClient')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")    
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    parser = OptionParser()

    #Default params
    base_os = ""
    spacer = "-"
    default_ubuntu = "lucid"
    default_debian = "lenny"
    default_rhel = "5.5"
    default_centos = "5.6"
    default_fedora = "13"
    #kernel = "2.6.27.21-0.1-xen"

    #ubuntu-distro = ['lucid', 'karmic', 'jaunty']
    #debian-distro = ['squeeze', 'lenny', 'etch']
    #rhel-distro = ['5.5', '5.4', '4.8']
    #fedora-distro = ['14','12']

    print 'Image generator client...'

    #help is auto-generated
    parser.add_option("-o", "--os", dest = "OS", help = "specify destination Operating System")
    parser.add_option("-v", "--version", dest = "version", help = "Operating System version")
    parser.add_option("-a", "--arch", dest = "arch", help = "Destination hardware architecture")
    parser.add_option("-l", "--auth", dest = "auth", help = "Authentication mechanism")
    parser.add_option("-s", "--software", dest = "software", help = "Software stack to be automatically installed")
    parser.add_option("-d", "--debug", action = "store_true", dest = "debug", help = "Enable debugging")
    parser.add_option("-u", "--user", dest = "user", help = "FutureGrid username")
    parser.add_option("-n", "--name", dest = "givenname", help = "Desired recognizable name of the image")
    parser.add_option("-e", "--description", dest = "desc", help = "Short description of the image and its purpose")

    (ops, args) = parser.parse_args()

    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit(1)

    try:
        user = os.environ['FG_USER']
    except KeyError:
        if type(ops.user) is not NoneType:
            user = ops.user
        else:
            logger.debug("FG_USER is not defined, we are using default user name")
            user = "default"

    #Turn debugging off
    if not ops.debug:
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

    logger.debug('Selected Architecture: ' + arch)


    #TODO: Authorization mechanism TBD
    if type(ops.auth) is not NoneType:
        auth = ""

    # Build the image
    version = ""
    #Parse OS and version command line args
    OS = ""
    if ops.OS == "Ubuntu" or ops.OS == "ubuntu":
        OS = "ubuntu"
        if type(ops.version) is NoneType:
            version = default_ubuntu
        elif ops.version == "10.04" or ops.version == "lucid":
            version = "lucid"
        elif ops.version == "9.10" or ops.version == "karmic":
            version = "karmic"
    elif ops.OS == "Debian" or ops.OS == "debian":
        OS = "debian"
        version = default_debian
    elif ops.OS == "Redhat" or ops.OS == "redhat" or ops.OS == "rhel":
        OS = "rhel"
        version = default_rhel
    elif ops.OS == "CentOS" or ops.OS == "CentOS" or ops.OS == "centos":
        OS = "centos"
        if type(ops.version) is NoneType:
            version = default_centos
        #later control supported versions
        else:
            version = default_centos
    elif ops.OS == "Fedora" or ops.OS == "fedora":
        OS = "fedora"
        version = default_fedora
    else:
        parser.error("Incorrect OS type specified")
        sys.exit(1)



    imgen = IMGenerate(arch, OS, version, user, ops.auth, ops.software, ops.givenname, ops.desc, logger)
    imgen.generate()
    



if __name__ == "__main__":
    main()




