#!/usr/bin/env python
"""
Command line front end for image deployment
"""

__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.1'

import argparse
import sys
import os
from types import *
import socket, ssl
from subprocess import *
import logging
from xml.dom.minidom import Document, parse
import re
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
    
class IMDeploy(object):
    ############################################################
    # __init__
    ############################################################
    def __init__(self, kernel, user, passwd, verbose, printLogStdout):
        super(IMDeploy, self).__init__()

        
        self.kernel = kernel
        self.user = user
        self.passwd = passwd
        self._verbose = verbose
        self.printLogStdout = printLogStdout
        
        self.machine = ""  #(india or minicluster or ...)
        self.loginmachine = ""
        self.shareddirserver = "" 
        
        #Load Configuration from file
        self._deployConf = IMClientConf()
        self._deployConf.load_deployConfig()        
        self._xcat_port = self._deployConf.getXcatPort()
        self._moab_port = self._deployConf.getMoabPort()
        self._http_server = self._deployConf.getHttpServer()        
        self._ca_certs = self._deployConf.getCaCertsDep()
        self._certfile = self._deployConf.getCertFileDep()
        self._keyfile = self._deployConf.getKeyFileDep()

        self.iaasmachine = self._deployConf.getIaasServerAddr()
        self._iaas_port = self._deployConf.getIaasPort()
        
        self._log = fgLog.fgLog(self._deployConf.getLogFileDeploy(), self._deployConf.getLogLevelDeploy(), "DeployClient", printLogStdout)
        
        self.tempdir = "" #DEPRECATED

    def check_auth(self, socket_conn, checkauthstat):
        endloop = False
        passed = False
        while not endloop:
            ret = socket_conn.read(1024)
            if (ret == "OK"):
                if self._verbose:
                    print "Authentication OK"
                self._log.debug("Authentication OK")
                endloop = True
                passed = True
            elif (ret == "TryAuthAgain"):
                msg = "Permission denied, please try again. User is " + self.user                    
                self._log.error(msg)
                if self._verbose:
                    print msg                            
                m = hashlib.md5()
                m.update(getpass())
                passwd = m.hexdigest()
                socket_conn.write(passwd)
            else:                
                self._log.error(str(ret))
                if self._verbose:
                    print ret
                checkauthstat.append(str(ret))
                endloop = True
                passed = False
        return passed

    #This need to be redo
    def iaas_generic(self, iaas_address, image, image_source, iaas_type):
        checkauthstat = []     
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            iaasServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            iaasServer.connect((self.iaasmachine, self._iaas_port))
            
            msg = str(image) + ',' + str(image_source) + ',' + str(iaas_type) + ',' + str(self.kernel) + ',' + str(self.user) + ',' + str(self.passwd) + ",ldappassmd5" 
            #self._log.debug('Sending message: ' + msg)
            
            iaasServer.write(msg)
            
            if self.check_auth(iaasServer, checkauthstat):
                
                if image_source == "disk":
                    ret = iaasServer.read(2048)
                    cmd = ''
                    status = ''
                    if (self.iaasmachine == "localhost" or self.iaasmachine == "127.0.0.1"):
                        self._log.info('Copying the image to the right directory')
                        cmd = 'cp ' + image + ' ' + ret                        
                        status = self.runCmd(cmd)
                    else:                    
                        self._log.info('Uploading image. You may be asked for ssh/passphrase password')
                        if self._verbose:
                            print 'Uploading image. You may be asked for ssh/passphrase password'
                            cmd = 'scp ' + image + ' ' + self.user + '@' + self.iaasmachine + ':' + ret
                        else:#this is the case where another application call it. So no password or passphrase is allowed              
                            cmd = 'scp -q -oBatchMode=yes ' + image + ' ' + self.user + '@' + self.iaasmachine + ':' + ret
                        status = self.runCmd(cmd)
                    
                    if status == 0:
                        iaasServer.write('OK,' + os.path.split(image)[1].strip())
                    else:                    
                        iaasServer.write('ERROR from client, ')
                        self._log.error("ERROR sending image to server via scp. EXIT.")
                        if self._verbose:
                            print "ERROR sending image to server via scp. EXIT."
                        return                        
                                         
                #print msg
                ret = iaasServer.read(1024)
                if (re.search('^ERROR', ret)):
                    self._log.error('The image has not been generated properly. Exit error:' + ret)
                    if self._verbose:
                        print "ERROR: The image has not been generated properly. Exit error:" + ret    
                else:                           
                    results = ret.split(",")
                    if len(results) == 3:
                        imgURIinServer = results[0].strip()
                        kernel = results[1].strip()
                        operatingsystem = results[2].strip()
                        #imagebackpath = retrieve   
                        localpath = "./"
                        imagebackpath = self._retrieveImg(imgURIinServer, localpath)
                        #if we want to introduce retries we need to put next line after checking that the image is actually here
                        iaasServer.write('OK')                        
                        if imagebackpath != None:        
                            #print "self." + iaas_type + "_method(\""+ str(imagebackpath) + "\",\"" + str(kernel) + "\",\"" +\
                            #      str(operatingsystem) + "\",\"" + str(iaas_address) + "\")"   
                            eval("self." + iaas_type + "_method(\"" + str(imagebackpath) + "\",\"" + str(kernel) + "\",\"" + 
                                  str(operatingsystem) + "\",\"" + str(iaas_address) + "\")")
                        else:
                            self._log.error("CANNOT retrieve the image from server. EXIT.")
                            if self._verbose:
                                print "ERROR: CANNOT retrieve the image from server. EXIT."
                    else:
                        self._log.error("Incorrect reply from server. EXIT.")
                        if self._verbose:
                            print "ERROR: Incorrect reply from server. EXIT."
                    
                
            else:       
                self._log.error(str(checkauthstat[0]))
                if self._verbose:
                    print checkauthstat[0]
                return
                            
        except ssl.SSLError:
            self._log.error("CANNOT establish SSL connection. EXIT")
            if self._verbose:
                print "ERROR: CANNOT establish SSL connection."
        
                
    def euca_method(self, imagebackpath, kernel, operatingsystem, iaas_address):
        #TODO: Pick kernel and ramdisk from available eki and eri

        #hardcoded for now
        eki = 'eki-78EF12D2'
        eri = 'eri-5BB61255'

        #CONTACT IMDeployServerIaaS to customize image ...

        if iaas_address != "None":
            ec2_url = "http://" + iaas_address + "/services/Eucalyptus"
            s3_url = "http://" + iaas_address + "/services/Walrus"
        else:
            ec2_url = os.getenv("EC2_URL")
            s3_url = os.getenv("S3_URL")
        
        filename = os.path.split(imagebackpath)[1].strip()

        print filename

        #Bundle Image
        #cmd = 'euca-bundle-image --image ' + imagebackpath + ' --kernel ' + eki + ' --ramdisk ' + eri
        cmd = "euca-bundle-image --cert " + str(os.getenv("EC2_CERT")) + " --privatekey " + str(os.getenv("EC2_PRIVATE_KEY")) + \
              " --user " + str(os.getenv("EC2_USER_ID")) + " --ec2cert " + str(os.getenv("EUCALYPTUS_CERT")) + " --url " + str(ec2_url) + \
              " -a " + str(os.getenv("EC2_ACCESS_KEY")) + " -s " + str(os.getenv("EC2_SECRET_KEY")) + \
              " --image " + str(imagebackpath) + " --kernel " + str(eki) + " --ramdisk " + str(eri)
        print cmd
        self._log.debug(cmd)
        os.system(cmd)

        #Upload bundled image
        #cmd = 'euca-upload-bundle --bucket ' + self.user + ' --manifest ' + '/tmp/' + filename + '.manifest.xml'
        cmd = "euca-upload-bundle -a " + os.getenv("EC2_ACCESS_KEY") + " -s " + os.getenv("EC2_SECRET_KEY") + \
            " --url " + s3_url + " --ec2cert " + os.getenv("EUCALYPTUS_CERT") + " --bucket " + self.user + " --manifest " + \
            "/tmp/" + filename + ".manifest.xml"
        print cmd      
        self._log.debug(cmd)  
        os.system(cmd)

        #Register image
        #cmd = 'euca-register ' + self.user + '/' + filename + '.manifest.xml'
        cmd = "euca-register -a " + os.getenv("EC2_ACCESS_KEY") + " -s " + os.getenv("EC2_SECRET_KEY") + \
            " --url " + ec2_url + " " + self.user + '/' + filename + '.manifest.xml'        
        print cmd
        self._log.debug(cmd)
        os.system(cmd)
        
        cmd = "rm -f " + imagebackpath
        print cmd
        self._log.debug(cmd)
        os.system(cmd)
        
        print "Your images has been registered on Eucalyptus with the id printed in the previous line (IMAGE  id) \n" +\
              "To launch a VM you can use euca-run-instances -k keyfile -n <#instances> id \n" +\
              "More information is provided in https://portal.futuregrid.org/tutorials/eucalyptus \n"              
        

    def opennebula_method(self, imagebackpath, kernel, operatingsystem, iaas_address):
        
        filename = os.path.split(imagebackpath)[1].strip()

        print filename
        
        name = operatingsystem + "-" + filename.split(".")[0] + "-" + self.user
        print name
        
        f = open(filename + ".one", 'w')
        f.write("NAME          = \"" + name + "\" \n" 
        "PATH          = " + imagebackpath + " \n"
        "PUBLIC        = NO \n")
        f.close()
        
        self._log.debug("Authenticating against OpenNebula")
        if self._verbose:
            print "Authenticating against OpenNebula"
        cmd = "oneauth login " + self.user
        #oneuser in OpenNebula 3.0
        print cmd
        #os.system(cmd)
        
        self._log.debug("Uploading image to OpenNebula")
        if self._verbose:
            print "Uploading image to OpenNebula"
        cmd = "oneimage register " + filename + ".one"
        print cmd
        #os.system(cmd)
        
        cmd = "rm -f " + filename + ".one"
        print cmd
        #os.system(cmd)
        
        f = open(filename + "_template.one", 'w')     
        #On OpenNebula 3.0 NETWORK_ID and IMAGE_ID  
        if (operatingsystem == "centos"):                        
            f.write("#--------------------------------------- \n"
                    "# VM definition example \n"
                    "#--------------------------------------- \n"            
                    "NAME = \"" + name + "\" \n"
                    "\n"
                    "CPU    = 0.5\n"
                    "MEMORY = 2048\n"
                    "\n"
                    "OS = [ \n"
                    "  arch=\"x86_64\", \n"
                    "  kernel=\"/srv/cloud/images/testmyimg/centos_ker_ini/vmlinuz-" + kernel + "\", \n"
                    "  initrd=\"/srv/cloud/images/testmyimg/centos_ker_ini/initrd-" + kernel + ".img\", \n"
                    "  root=\"hda\" \n"
                    "  ] \n"
                    " \n"
                    "DISK = [ \n"
                    "  image   = \"" + name + "\",\n"
                    "  target   = \"hda\",\n"
                    "  readonly = \"no\"]\n"
                    "\n"
                    "NIC = [ NETWORK=\"Virt LAN\"]\n"
                    "NIC = [ NETWORK=\"Large LAN\"]\n"
                    "\n"                    
                    "FEATURES=[ acpi=\"no\" ]\n"
                    "\n"
                    "CONTEXT = [\n"
                    "   files = \"/srv/cloud/images/centos/init.sh /tmp/id_rsa.pub\",\n"
                    "   target = \"hdc\",\n"
                    "   root_pubkey = \"id_rsa.pub\"\n"
                    "]\n"
                    "\n"                    
                    "GRAPHICS = [\n"
                    "  type    = \"vnc\",\n"
                    "  listen  = \"127.0.0.1\"\n"
                    "  ]\n")
                
        elif (operatingsystem == "ubuntu"):
            f.write("#--------------------------------------- \n"
                    "# VM definition example \n"
                    "#--------------------------------------- \n"            
                    "NAME = \"" + name + "\" \n"
                    "\n"
                    "CPU    = 0.5\n"
                    "MEMORY = 2048\n"
                    "\n"
                    "OS = [ \n"
                    "  arch=\"x86_64\", \n"
                    "  kernel=\"/srv/cloud/images/testmyimg/ubuntu_ker_ini/vmlinuz-" + kernel + "\", \n"
                    "  initrd=\"/srv/cloud/images/testmyimg/ubuntu_ker_ini/initrd.img-" + kernel + "\", \n"
                    "  root=\"sda\" \n"
                    "  ] \n"
                    " \n"
                    "DISK = [ \n"
                    "  image   = \"" + name + "\",\n"
                    "  target  = \"hda\",\n"
                    "  bus     = \"ide\",\n"
                    "  readonly = \"no\"]\n"
                    "\n"
                    "NIC = [ NETWORK=\"Virt LAN\"]\n"
                    "NIC = [ NETWORK=\"Large LAN\"]\n"
                    "\n"                    
                    "FEATURES=[ acpi=\"no\" ]\n"
                    "\n"
                    "CONTEXT = [\n"
                    "   files = \"/srv/cloud/images/ubuntu/init.sh /tmp/id_rsa.pub\",\n"
                    "   target = \"hdc\",\n"
                    "   root_pubkey = \"id_rsa.pub\"\n"
                    "]\n"
                    "\n"                    
                    "GRAPHICS = [\n"
                    "  type    = \"vnc\",\n"
                    "  listen  = \"127.0.0.1\"\n"
                    "  ]\n")
        
        f.close()
        
        print "The file " + filename + "_template.one is an example of the template that it is needed to launch a VM \n" +\
        "You need to modify the kernel and initrd path to indiacte their location in your particular system\n" +\
        "To see the availabe networks you can use onevnet list\n" +\
        "To launch a VM you can use onevm create " + filename + "_template.one \n" 
        
        #create template to upload image to opennebula repository
        
        #create script to boot image and tell user how to use it
   

    def xcat_method(self, xcat, image):
        checkauthstat = []
        #Load Machines configuration
        xcat = xcat.lower()
        if (xcat == "india" or xcat == "india.futuregrid.org"):
            self.machine = "india"
        elif (xcat == "minicluster" or xcat == "tm1r" or xcat == "tm1r.tidp.iu.futuregrid.org"):
            self.machine = "minicluster"
        else:
            self._log.error("Machine name not recognized")
            if self._verbose:
                print "ERROR: Machine name not recognized"
            sys.exit(1)
        
        self._deployConf.load_machineConfig(self.machine)
        self.loginmachine = self._deployConf.getLoginMachine()
        self.xcatmachine = self._deployConf.getXcatMachine()
        self.moabmachine = self._deployConf.getMoabMachine()        
        
        self._log.debug("login machine " + self.loginmachine)
        self._log.debug("xcat machine " + self.xcatmachine)
        self._log.debug("moab machine " + self.moabmachine)        
        #################
        
        """
        urlparts = image.split("/")
        self._log.debug(str(urlparts))
        if len(urlparts) == 1:
            nameimg = urlparts[0].split(".")[0]
        elif len(urlparts) == 2:
            nameimg = urlparts[1].split(".")[0]
        else:
            nameimg = urlparts[len(urlparts) - 1].split(".")[0]

        
        #REMOVE THIS. WE ONLY ALLOW DEPLOY IMAGES FROM REPOSITORY
        #NOW IT IS NOT NEEDED THE SHAREDDIRSERVER.
        
        #Copy the image to the Shared directory.
        if (self.loginmachine == "localhost" or self.loginmachine == "127.0.0.1"):
            self._log.info('Copying the image to the right directory')
            cmd = 'cp ' + image + ' ' + self.shareddirserver + '/' + nameimg + '.tgz'
            self._log.info(cmd)
            self.runCmd(cmd)
        else:                    
            self._log.info('Uploading image. You may be asked for ssh/passphrase password')
            cmd = 'scp ' + image + ' ' + self.user + '@' + self.loginmachine + ':' + self.shareddirserver + '/' + nameimg + '.tgz'
            self._log.info(cmd)
            self.runCmd(cmd)
        """
        
        #xCAT server                
        if self._verbose:
            print 'Connecting to xCAT server'

        #msg = self.name + ',' + self.operatingsystem + ',' + self.version + ',' + self.arch + ',' + self.kernel + ',' + self.shareddirserver + ',' + self.machine
        
        #self.shareddirserver + '/' + nameimg + '.tgz, '
        moabstring = ""
        #Notify xCAT deployment to finish the job
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            xcatServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            xcatServer.connect((self.xcatmachine, self._xcat_port))
            
            msg = str(image) + ',' + str(self.kernel) + ',' + self.machine + ',' + str(self.user) + ',' + str(self.passwd) + ",ldappassmd5" 
            #self._log.debug('Sending message: ' + msg)
            
            xcatServer.write(msg)
            """           
            endloop = False
            fail = False
            while not endloop:
                ret = xcatServer.read(1024)
                if (ret == "OK"):
                    if self._verbose:                        
                        print "Your image request is being processed"
                    endloop = True
                elif (ret == "TryAuthAgain"):
                    if self._verbose:
                        print "Permission denied, please try again. User is "+self.user
                    m = hashlib.md5()
                    m.update(getpass())
                    passwd = m.hexdigest()
                    xcatServer.write(passwd)
                else:
                    self._log.error(str(ret))
                    if self._verbose:
                        print ret
                    endloop = True
                    fail = True
            """
            if self.check_auth(xcatServer, checkauthstat):            
                #print msg
                ret = xcatServer.read(1024)
                #check if the server received all parameters
                if ret != 'OK':
                    self._log.error('Incorrect reply from the xCat server:' + str(ret))
                    if self._verbose:
                        print 'Incorrect reply from the xCat server:' + str(ret)
                    sys.exit(1)
                #recieve the prefix parameter from xcat server
                moabstring = xcatServer.read(2048)
                self._log.debug("String received from xcat server " + moabstring)
                params = moabstring.split(',')
                imagename = params[0] + '' + params[2] + '' + params[1]
                if self._verbose:
                    print 'Connecting to Moab server'	    
                moabstring += ',' + self.machine
            else:
                self._log.error(str(checkauthstat[0]))
                if self._verbose:
                    print checkauthstat[0]
                return
        
                    
        except ssl.SSLError:
            self._log.error("CANNOT establish SSL connection. EXIT")
            if self._verbose:
                print "ERROR: CANNOT establish SSL connection."
        
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            moabServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            moabServer.connect((self.moabmachine, self._moab_port))
            
            self._log.debug('Sending message: ' + moabstring)
            moabServer.write(moabstring)
            ret = moabServer.read(100)
            if ret != 'OK':
                self._log.error('Incorrect reply from the Moab server:' + str(ret))
                if self._verbose:
                    print 'Incorrect reply from the Moab server:' + str(ret)
                sys.exit(1)
            if self._verbose:
                print 'Your image has been deployed in xCAT as ' + imagename + '. Please allow a few minutes for xCAT to register the image before attempting to use it.'
        except ssl.SSLError:
            self._log.error("CANNOT establish SSL connection. EXIT")
            if self._verbose:
                print "ERROR: CANNOT establish SSL connection. EXIT"

    ############################################################
    # _retrieveImg
    ############################################################
    def _retrieveImg(self, imgURI, dest):
        
        filename = os.path.split(imgURI)[1]        
        
        fulldestpath = dest + "/" + filename
                
        if os.path.isfile(fulldestpath):
            exists = True
            i = 0       
            while (exists):            
                aux = fulldestpath + "_" + i.__str__()
                if os.path.isfile(aux):
                    i += 1
                else:
                    exists = False
                    fulldestpath = aux
                
    
        if self._verbose:
            cmdscp = "scp " + self.iaasmachine + ":" + imgURI + " " + fulldestpath
        else: #this is the case where another application call it. So no password or passphrase is allowed
            cmdscp = "scp -q -oBatchMode=yes " + self.iaasmachine + ":" + imgURI + " " + fulldestpath
        #print cmdscp
        output = ""
        try:
            if self._verbose:
                print 'Retrieving image. You may be asked for ssh/passphrase password'
            stat = os.system(cmdscp)
            if (stat == 0):
                output = fulldestpath                
            else:
                self._log.error("Error retrieving the image. Exit status " + str(stat))
                if self._verbose:
                    print "Error retrieving the image. Exit status " + str(stat)
                #remove the temporal file
        except os.error:
            self._log("Error, The image cannot be retieved" + str(sys.exc_info()))
            if self._verbose:
                print "Error, The image cannot be retieved" + str(sys.exc_info())
            output = None

        return output


    def runCmd(self, cmd):        
        cmdLog = logging.getLogger('DeployClient.exec')
        cmdLog.debug(cmd)
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
        std = p.communicate()
        status = 0
        if len(std[0]) > 0:
            cmdLog.debug('stdout: ' + std[0])
            cmdLog.debug('stderr: ' + std[1])
        if p.returncode != 0:
            cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
            status = 1
            #sys.exit(p.returncode)
        return status


def main():
 
    user = ""

    parser = argparse.ArgumentParser(prog="IMDeploy", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="FutureGrid Image Deployment Help ")    
    parser.add_argument('-u', '--user', dest='user', required=True, metavar='user', help='FutureGrid User name')
    parser.add_argument('-d', '--debug', dest='debug', action="store_true", help='Print logs in the screen for debug')
    parser.add_argument('-k', '--kernel', dest="kernel", metavar='Kernel version', help="Specify the desired kernel" 
                        "(must be exact version and approved for use within FG). Not yet supported")
    group = parser.add_mutually_exclusive_group(required=True)    
    group.add_argument('-i', '--image', dest='image', metavar='ImgFile', help='tgz file that contains manifest and img')
    group.add_argument('-r', '--imgid', dest='imgid', metavar='ImgId', help='Id of the image stored in the repository')
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-x', '--xcat', dest='xcat', metavar='MachineName', help='Deploy image to xCAT. The argument is the machine name (minicluster, india ...)')
    group1.add_argument('-e', '--euca', dest='euca', nargs='?', metavar='Address:port', help='Deploy the image to Eucalyptus, which is in the specified addr')
    group1.add_argument('-o', '--opennebula', dest='opennebula', nargs='?', metavar='Address', help='Deploy the image to OpenNebula, which is in the specified addr')
    group1.add_argument('-n', '--nimbus', dest='nimbus', nargs='?', metavar='Address', help='Deploy the image to Nimbus, which is in the specified addr')
    group1.add_argument('-s', '--openstack', dest='openstack', nargs='?', metavar='Address', help='Deploy the image to OpenStack, which is in the specified addr')
    
    args = parser.parse_args()

    #print args
    

    print 'Starting image deployer...'
    
    verbose = True #to activate the print
    
    print "Please insert the password for the user " + args.user + ""
    m = hashlib.md5()
    m.update(getpass())
    passwd = m.hexdigest()

    #TODO: if Kernel is provided we need to verify that it is supported. 
    
    imgdeploy = IMDeploy(args.kernel, args.user, passwd, verbose, args.debug)

    used_args = sys.argv[1:]
    
    image_source = "repo"
    image = args.imgid    
    if args.image != None:
        image_source = "disk"
        image = args.image
        if not  os.path.isfile(args.image):            
            print 'ERROR: Image file not found'            
            sys.exit(1)
    #XCAT
    if args.xcat != None:
        if args.imgid == None:
            print "ERROR: You need to specify the id of the image that you want to deploy (-r/--imgid option)."
            print "The parameter -i/--image cannot be used with this type of deployment"
            sys.exit(1)
        else:
            imgdeploy.xcat_method(args.xcat, args.imgid)
    #EUCALYPTUS    
    if ('-e' in used_args or '--euca' in used_args):
        imgdeploy.iaas_generic(args.euca, image, image_source, "euca")        
    #OpenNebula
    elif ('-o' in used_args or '--opennebula' in used_args):
        imgdeploy.iaas_generic(args.opennebula, image, image_source, "opennebula")
    #NIMBUS
    elif ('-n' in used_args or '--nimbus' in used_args):
        #TODO        
        print "Nimbus deployment is not implemented yet"
    elif ('-s' in used_args or '--openstack' in used_args):
        #TODO        
        print "OpenStack deployment is not implemented yet"
    

if __name__ == "__main__":
    main()
#END

