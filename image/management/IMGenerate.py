#!/usr/bin/env python
"""
Command line front end for image generator
"""
__author__ = 'Javier Diaz, Andrew Younge'
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
import socket, ssl
from subprocess import *
#from xml.dom.ext import *
#from xml.dom.minidom import Document, parse
from time import time
from getpass import getpass
import hashlib

from IMClientConf import IMClientConf

class IMGenerate(object):
    def __init__(self, arch, OS, version, user, software, givenname, desc, logger, getimg, passwd):
        super(IMGenerate, self).__init__()
        
        self.arch = arch
        self.OS = OS
        self.version = version
        self.user = user
        self.passwd = passwd
        self.software = software
        self.givenname = givenname
        self.desc = desc
        self.logger = logger
        self.getimg = getimg
        
        #Load Configuration from file
        self._genConf = IMClientConf()
        self._genConf.load_generationConfig()        
        self.serveraddr = self._genConf.getServeraddr()
        self.gen_port = self._genConf.getGenPort()
        
        self._ca_certs = self._genConf.getCaCertsGen()
        self._certfile = self._genConf.getCertFileGen()
        self._keyfile = self._genConf.getKeyFileGen()

    def generate(self):
        #generate string with options separated by | character
        
        #params[0] is user
        #params[1] is operating system
        #params[2] is version
        #params[3] is arch
        #params[4] is software
        #params[5] is givenname
        #params[6] is the description
        #params[7] is to retrieve the image or to upload in the repo (true or false, respectively)
        #params[8] is the user password
        #params[9] is the type of password
        
        
        
        options = str(self.user) + "|" + str(self.OS) + "|" + str(self.version) + "|" + str(self.arch) + "|" + \
                str(self.software) + "|" + str(self.givenname) + "|" + str(self.desc) + "|" + str(self.getimg) + \
                "|ldappassmd5|" + str(self.passwd) 
        
        self.logger.debug("string to send: "+options)
        
        print "Generating the image"
        
        #Notify xCAT deployment to finish the job
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            genServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED)
            self.logger.debug("Connecting server: "+ self.serveraddr +":"+str(self.gen_port))
            genServer.connect((self.serveraddr, self.gen_port))            
        except ssl.SSLError:
            self.logger.error("CANNOT establish SSL connection. EXIT")

        genServer.write(options)
        #check if the server received all parameters
        print "Your image request is in the queue to be processed"
        
        endloop = False
        while not endloop:
            ret = genServer.read(1024)
            if (ret == "OK"):
                print "Your image request is being processed"
                endloop = True
            elif (ret == "TryAuthAgain"):
                print "Permission denied, please try again. User is "+self.user
                m = hashlib.md5()
                m.update(getpass())
                passwd = m.hexdigest()
                genServer.write(passwd)
            else:
                print ret
                endloop = True
                
        ret = genServer.read(2048)
        
        if (re.search('^ERROR', ret)):
            self.logger.error('The image has not been generated properly. Exit error:' + ret)    
        else:
            self.logger.debug("Returned string: " + str(ret))
            
            if self.getimg:            
                output = self._retrieveImg(ret)
                if output != None:  
                    print output
                genServer.write('end')
            else:
                
                if (re.search('^ERROR', ret)):
                    self.logger.error('The image has not been generated properly. Exit error:' + ret)
                else:
                    print "Your image has be uploaded in the repository with ID="+str(ret)
                    
            
            print '\n The image and the manifest generated are packaged in a tgz file.'+\
                  '\n Please be aware that this FutureGrid image does not have kernel and fstab. Thus, '+\
                  'it is not built for any deployment type. To deploy the new image, use the IMDeploy command.'
            #server return addr of the img and metafile compressed in a tgz or None
        

    ############################################################
    # _rExec
    ############################################################
    def _rExec(self, cmdexec):
    
        #TODO: do we want to use the .format statement from python to make code more readable?
        #Set up random string    
        random.seed()
        randid = str(random.getrandbits(32))
        
        cmdssh = "ssh " + self.serveraddr
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
    
        cmdscp = "scp " + self.user + "@" + imgURI + " ."
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
    default_ubuntu = "maverick"
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
    parser.add_option("-o", "--os", dest="OS", help="specify destination Operating System")
    parser.add_option("-v", "--version", dest="version", help="Operating System version")
    parser.add_option("-a", "--arch", dest="arch", help="Destination hardware architecture")
#    parser.add_option("-l", "--auth", dest="auth", help="Authentication mechanism")
    parser.add_option("-s", "--software", dest="software", help="Software stack to be automatically installed")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debugging")
    parser.add_option("-u", "--user", dest="user", help="FutureGrid username.")
    parser.add_option("-n", "--name", dest="givenname", help="Desired recognizable name of the image")
    parser.add_option("-e", "--description", dest="desc", help="Short description of the image and its purpose")
    parser.add_option("-g", "--getimg", dest="getimg", default=False, action="store_true", help="Short description of the image and its purpose")

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
            logger.debug("you need to specify you user name. It can be donw using the FG_USER variable or the option -u/--user")
            sys.exit(1)

    print "Please insert the password for the user "+ops.user+""
    m = hashlib.md5()
    m.update(getpass())
    passwd = m.hexdigest()

    #Turn debugging off
    if not ops.debug:
        ch.setLevel(logging.INFO)

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

    # Build the image
    version = ""
    #Parse OS and version command line args
    OS = ""
    if ops.OS == "Ubuntu" or ops.OS == "ubuntu":
        OS = "ubuntu"
        if type(ops.version) is NoneType:
            version = default_ubuntu
        elif ops.version == "9.10" or ops.version == "karmic":
            version = "karmic"
        elif ops.version == "10.04" or ops.version == "lucid":
            version = "lucid"
        elif ops.version == "10.10" or ops.version == "maverick":
            version = "maverick"
        elif ops.version == "11.04" or ops.version == "natty":
            version = "natty"
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
    
    imgen = IMGenerate(arch, OS, version, user, ops.software, ops.givenname, ops.desc, logger, ops.getimg, passwd)
    imgen.generate()
    



if __name__ == "__main__":
    main()




