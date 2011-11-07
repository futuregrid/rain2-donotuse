#!/usr/bin/env python
"""
Command line front end for image generator
"""
__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.9'

import argparse
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
import time
from getpass import getpass
import hashlib

from IMClientConf import IMClientConf

sys.path.append(os.getcwd())
try:
    from futuregrid.utils import fgLog #This should the the final one
#To execute IRClient for tests
except:
    sys.path.append(os.path.dirname(__file__) + "/../../") #Directory where fg.py is
    from utils import fgLog

class IMGenerate(object):
    def __init__(self, arch, OS, version, user, software, givenname, desc, getimg, passwd, verbose, printLogStdout):
        super(IMGenerate, self).__init__()
        
        self.arch = arch
        self.OS = OS
        self.version = version
        self.user = user
        self.passwd = passwd
        self.software = software
        self.givenname = givenname
        self.desc = desc
        self.getimg = getimg
        self.verbose = verbose
        self.printLogStdout = printLogStdout
        
        #Load Configuration from file
        self._genConf = IMClientConf()
        self._genConf.load_generationConfig()        
        self.serveraddr = self._genConf.getServeraddr()
        self.gen_port = self._genConf.getGenPort()
        
        self._ca_certs = self._genConf.getCaCertsGen()
        self._certfile = self._genConf.getCertFileGen()
        self._keyfile = self._genConf.getKeyFileGen()
        
        self._log = fgLog.fgLog(self._genConf.getLogFileGen(), self._genConf.getLogLevelGen(), "GenerateClient", printLogStdout)

    def setArch(self, arch):
        self.arch = arch
    def setOs(self, os):
        self.OS = os
    def setVersion(self, version):
        self.version = version
    def setSoftware(self, software):
        self.software = software
    def setGivenname(self, givenname):
        self.givenname = givenname        
    def setDesc(self, desc):
        self.desc = desc
    def setGetimg(self, getimg):
        self.getimg = getimg
    def setDebug(self, printLogStdout):
        self.printLogStdout = printLogStdout

    def generate(self):
        start_all = time.time()
        #generate string with options separated by | character
        output = None
        
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
                "|" + str(self.passwd) + "|ldappassmd5" 
        
        #self._log.debug("string to send: "+options)
        
        #Notify xCAT deployment to finish the job
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            genServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            self._log.debug("Connecting server: " + self.serveraddr + ":" + str(self.gen_port))
            if self.verbose:
                print "Connecting server: " + self.serveraddr + ":" + str(self.gen_port)
            genServer.connect((self.serveraddr, self.gen_port))            
        except ssl.SSLError:
            self._log.error("CANNOT establish SSL connection. EXIT")
            if self.verbose:
                print "ERROR: CANNOT establish SSL connection. EXIT"

        genServer.write(options)
        #check if the server received all parameters
        if self.verbose:
            print "Your image request is in the queue to be processed"
        
        endloop = False
        fail = False
        while not endloop:
            ret = genServer.read(1024)
            if (ret == "OK"):
                if self.verbose:                    
                    print "Your image request is being processed"
                endloop = True
            elif (ret == "TryAuthAgain"):
                if self.verbose:
                    print "Permission denied, please try again. User is " + self.user
                m = hashlib.md5()
                m.update(getpass())
                passwd = m.hexdigest()
                genServer.write(passwd)
                self.passwd = passwd
            else:
                self._log.error(str(ret))
                if self.verbose:
                    print ret
                endloop = True
                fail = True
        if not fail:
            if self.verbose:
                print "Generating the image"
            ret = genServer.read(2048)
            
            if (re.search('^ERROR', ret)):
                self._log.error('The image has not been generated properly. Exit error:' + ret)
                if self.verbose:
                    print "ERROR: The image has not been generated properly. Exit error:" + ret    
            else:
                self._log.debug("Returned string: " + str(ret))
                
                if self.getimg:            
                    output = self._retrieveImg(ret, "./")                    
                    genServer.write('end')
                else:
                    
                    if (re.search('^ERROR', ret)):
                        self._log.error('The image has not been generated properly. Exit error:' + ret)
                        if self.verbose:
                            print "ERROR: The image has not been generated properly. Exit error:" + ret
                    else:
                        output = str(ret)
        
        
        end_all = time.time()
        self._log.info('TIME walltime image generate client: ' + str(end_all - start_all))
        
        #server return addr of the img and metafile compressed in a tgz, imgId or None if error
        return output
    """
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
    
        self._log.debug(str(cmd))
    
        stat = os.system(cmd)
        if (str(stat) != "0"):
            #print stat
            self._log.debug(str(stat))
        f = open(tmpFile, "r")
        outputs = f.readlines()
        f.close()
        os.system("rm -f " + tmpFile)
        #output = ""
        #for line in outputs:
        #    output += line.strip()
        #print outputs
        return outputs
    """
    ############################################################
    # _retrieveImg
    ############################################################
    def _retrieveImg(self, dir, dest):
        imgURI = self.serveraddr + ":" + dir
        imgIds = imgURI.split("/")
        imgId = imgIds[len(imgIds) - 1]
    
        cmdscp = ""
        if self.verbose:            
            cmdscp = "scp " + self.user + "@" + imgURI + " " + dest
        else:#this is the case where another application call it. So no password or passphrase is allowed
            cmdscp = "scp -q -oBatchMode=yes " + self.user + "@" + imgURI + " " + dest
        output = ""
        try:
            if self.verbose:
                print 'Retrieving image. You may be asked for ssh/passphrase password'
            self._log.debug(cmdscp)
            stat = os.system(cmdscp)
            stat = 0
            if (stat == 0):
                output = dest + "/" + imgId
            else:
                self._log.error("Error retrieving the image. Exit status " + str(stat))
                if self.verbose:
                    print "Error retrieving the image. Exit status " + str(stat)
                output = None
                #remove the temporal file
        except os.error:
            self._log.error("Error, The image cannot be retieved" + str(sys.exc_info()))
            if self.verbose:
                print "Error, The image cannot be retieved" + str(sys.exc_info())
            output = None
    
        return output

    
def main():

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

    parser = argparse.ArgumentParser(prog="IMGenerate", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="FutureGrid Image Deployment Help")    
    parser.add_argument('-u', '--user', dest='user', required=True, help='FutureGrid User name')
    parser.add_argument('-d', '--debug', dest='debug', action="store_true", help='Print logs in the screen for debug')
    parser.add_argument("-o", "--os", dest="OS", metavar='OSName', help="specify destination Operating System. Currently only Centos and Ubuntu are supported")
    parser.add_argument("-v", "--version", dest="version", metavar='OSversion', help="Operating System version. In the case of Centos it can be 5 or 6. In the case of Ubuntu karmic(9.10), lucid(10.04), maverick(10.10), natty (11.04)")
    parser.add_argument("-a", "--arch", dest="arch", metavar='arch', help="Destination hardware architecture")
    parser.add_argument("-s", "--software", dest="software", metavar='software', help="Software list to be automatically installed")
    parser.add_argument("-n", "--name", dest="givenname", metavar='givenname', help="Desired recognizable name of the image")
    parser.add_argument("-e", "--description", dest="desc", metavar='description', help="Short description of the image and its purpose")
    parser.add_argument("-g", "--getimg", dest="getimg", default=False, action="store_true", help="Retrieve the image instead of uploading to the image repository")
    
    args = parser.parse_args()

    print 'Image generator client...'
    
    verbose = True

    print "Please insert the password for the user " + args.user + ""
    m = hashlib.md5()
    m.update(getpass())
    passwd = m.hexdigest()
    
    arch = "x86_64" #Default to 64-bit

    #Parse arch command line arg
    if args.arch != None:
        if args.arch == "i386" or args.arch == "i686":
            arch = "i386"
        elif args.arch == "amd64" or args.arch == "x86_64":
            arch = "x86_64"
        else:
            print "ERROR: Incorrect architecture type specified (i386|x86_64)"
            sys.exit(1)

    print 'Selected Architecture: ' + arch

    # Build the image
    version = ""
    #Parse OS and version command line args
    OS = ""
    if args.OS == "Ubuntu" or args.OS == "ubuntu":
        OS = "ubuntu"
        supported_versions = ["karmic", "lucid", "maverick", "natty"]
        if type(args.version) is NoneType:
            version = default_ubuntu
        elif args.version == "9.10" or args.version == "karmic":
            version = "karmic"
        elif args.version == "10.04" or args.version == "lucid":
            version = "lucid"
        elif args.version == "10.10" or args.version == "maverick":
            version = "maverick"
        elif args.version == "11.04" or args.version == "natty":
            version = "natty"
        else:
            print "ERROR: Incorrect OS version specified. Supported OS version for " + OS + " are " + str(supported_versions)
            sys.exit(1)
    #elif args.OS == "Debian" or args.OS == "debian":
    #    OS = "debian"
    #    version = default_debian
    #elif args.OS == "Redhat" or args.OS == "redhat" or args.OS == "rhel":
    #    OS = "rhel"
    #    version = default_rhel
    elif args.OS == "CentOS" or args.OS == "CentOS" or args.OS == "centos":
        OS = "centos"
        supported_versions = ["5", "5.0", "5.1", "5.2", "5.3", "5.4", "5.5", "5.6", "5.7", "6", "6.0"]
        if type(args.version) is NoneType:
            version = default_centos            
        elif str(args.version) in supported_versions:
            if re.search("^5", str(args.version)):
                version = "5"
            elif re.search("^6", str(args.version)):
                version = "6"
        else:
            print "ERROR: Incorrect OS version specified. Supported OS version for " + OS + " are " + str(supported_versions)
            sys.exit(1)
            
    #elif args.OS == "Fedora" or args.OS == "fedora":
    #    OS = "fedora"
    #    version = default_fedora
    else:
        print "ERROR: Incorrect OS type specified. Currently only Centos and Ubuntu are supported"
        sys.exit(1)
        
    
    imgen = IMGenerate(arch, OS, version, args.user, args.software, args.givenname, args.desc, args.getimg, passwd, verbose, args.debug)
    status = imgen.generate()
    
    if status != None:
        if args.getimg:
            print "The image is located in " + str(status)
        else:
            print "Your image has be uploaded in the repository with ID=" + str(status)
        
        print '\n The image and the manifest generated are packaged in a tgz file.' + \
              '\n Please be aware that this FutureGrid image does not have kernel and fstab. Thus, ' + \
              'it is not built for any deployment type. To deploy the new image, use the IMDeploy command.'


if __name__ == "__main__":
    main()




