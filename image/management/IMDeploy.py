#!/usr/bin/env python
"""
Command line front end for image deployment
"""

__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.9'

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
import time
import boto.ec2
import boto
from random import randrange

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

    def setKernel(self, kernel):
        self.kernel = kernel
    def setDebug(self, printLogStdout):
        self.printLogStdout = printLogStdout
    

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
                self.passwd = passwd
            else:                
                self._log.error(str(ret))
                if self._verbose:
                    print ret
                checkauthstat.append(str(ret))
                endloop = True
                passed = False
        return passed

    #This need to be redo
    def iaas_generic(self, iaas_address, image, image_source, iaas_type, varfile, getimg, ldap, wait):
        start_all = time.time()
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
            
            msg = str(image) + ',' + str(image_source) + ',' + str(iaas_type) + ',' + str(self.kernel) + ',' + str(self.user) + ',' + str(self.passwd) + ",ldappassmd5" + ',' + str(ldap) 
            #self._log.debug('Sending message: ' + msg)
            
            iaasServer.write(msg)
            
            if self.check_auth(iaasServer, checkauthstat):
                start = time.time()
                if self._verbose:
                    print "Customizing image for the selected cloud framework: " + iaas_type
                
                if image_source == "disk":
                    ret = iaasServer.read(2048)
                    cmd = ''
                    status = ''
                    if (self.iaasmachine == "localhost" or self.iaasmachine == "127.0.0.1"):
                        self._log.info('Copying the image to the right directory')
                        cmd = 'cp ' + image + ' ' + ret                        
                        status = self.runCmd(cmd)
                    else:                    
                        self._log.info('Uploading image.')
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
                
                end = time.time()
                self._log.info('TIME customize image in server side for an iaas:' + str(end - start))
                
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
                        
                        start = time.time()
                                                
                        imagebackpath = self._retrieveImg(imgURIinServer, localpath)
                        
                        end = time.time()
                        self._log.info('TIME retrieve image from server side:' + str(end - start))
                        #if we want to introduce retries we need to put next line after checking that the image is actually here
                        iaasServer.write('OK')                        
                        if imagebackpath != None:        
                            #print "self." + iaas_type + "_method(\""+ str(imagebackpath) + "\",\"" + str(kernel) + "\",\"" +\
                            #      str(operatingsystem) + "\",\"" + str(iaas_address) + "\")"   
                            
                            start = time.time()
                            
                            output = eval("self." + iaas_type + "_method(\"" + str(imagebackpath) + "\",\"" + str(kernel) + "\",\"" + 
                                  str(operatingsystem) + "\",\"" + str(iaas_address) + "\",\"" + str(varfile) + "\",\"" + str(getimg) + "\",\"" + str(wait) + "\")")
                            
                            end = time.time()
                            self._log.info('TIME uploading image to cloud framework:' + str(end - start))
                            
                            #wait until image is in available status
                            if wait:
                                self.wait_available(iaas_type, output)                            
                    
                            end_all = time.time()
                            self._log.info('TIME walltime image deploy cloud:' + str(end_all - start_all))
                            
                            if self._verbose:
                                print "Image Deployed successfully"
                            
                            return output
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
    
    
    def openstack_environ(self, varfile, iaas_address):
        nova_key_dir = os.path.dirname(varfile)            
        if nova_key_dir.strip() == "":
            nova_key_dir = "."
        os.environ["NOVA_KEY_DIR"] = nova_key_dir
        
        #read variables
        f = open(varfile, 'r')
        for line in f:
            if re.search("^export ", line):
                line = line.split()[1]                    
                parts = line.split("=")
                #parts[0] is the variable name
                #parts[1] is the value
                parts[0] = parts[0].strip()
                value = ""
                for i in range(1, len(parts)):
                    parts[i] = parts[i].strip()
                    parts[i] = os.path.expanduser(os.path.expandvars(parts[i]))                    
                    value += parts[i] + "="
                value = value.rstrip("=")
                value = value.strip('"')
                value = value.strip("'") 
                os.environ[parts[0]] = value
        f.close()
        if iaas_address != "None":
            ec2_url = "http://" + iaas_address + "/services/Cloud"
            s3_url = "http://" + iaas_address + ":3333"
        else:
            ec2_url = os.getenv("EC2_URL")
            s3_url = os.getenv("S3_URL")
        
        path = "/services/Cloud"
        region = "nova"
          
        return ec2_url, s3_url, path, region
        
    def euca_environ(self, varfile, iaas_address):
        euca_key_dir = os.path.dirname(varfile)            
        if euca_key_dir.strip() == "":
            euca_key_dir = "."
        os.environ["EUCA_KEY_DIR"] = euca_key_dir
                    
        #read variables
        f = open(varfile, 'r')
        for line in f:
            if re.search("^export ", line):
                line = line.split()[1]                    
                parts = line.split("=")
                #parts[0] is the variable name
                #parts[1] is the value
                parts[0] = parts[0].strip()
                value = ""
                for i in range(1, len(parts)):
                    parts[i] = parts[i].strip()
                    parts[i] = os.path.expanduser(os.path.expandvars(parts[i]))                    
                    value += parts[i] + "="
                value = value.rstrip("=")
                value = value.strip('"')
                value = value.strip("'") 
                os.environ[parts[0]] = value
        f.close()
            
        if iaas_address != "None":
            ec2_url = "http://" + iaas_address + "/services/Eucalyptus"
            s3_url = "http://" + iaas_address + "/services/Walrus"
        else:
            ec2_url = os.getenv("EC2_URL")
            s3_url = os.getenv("S3_URL")
        
        path = "/services/Eucalyptus"
        region = "eucalyptus"
        
        return ec2_url, s3_url, path, region
      
    def cloudlist(self, iaas_address, iaas_type, varfile):
        ec2_url = ""
        s3_url = ""   
        path = ""
        region = ""     
        if iaas_type == "openstack":
            ec2_url, s3_url, path, region = self.openstack_environ(varfile, iaas_address)                    
        elif iaas_type == "euca":
            ec2_url, s3_url, path, region = self.euca_environ(varfile, iaas_address)
            
        endpoint = ec2_url.lstrip("http://").split(":")[0]
        
        self._log.debug("Getting Region")
        region = None        
        try:  
            region = boto.ec2.regioninfo.RegionInfo(name=region, endpoint=endpoint)
        except:
            msg = "ERROR: getting region information " + str(sys.exc_info())
            self._log.error(msg)                        
            return msg
        
        self._log.debug("Connecting EC2")
        connection = None        
        try:
            connection = boto.connect_ec2(str(os.getenv("EC2_ACCESS_KEY")), str(os.getenv("EC2_SECRET_KEY")), is_secure=False, region=region, port=8773, path=path)
        except:
            msg = "ERROR:connecting to EC2 interface. " + str(sys.exc_info())
            self._log.error(msg)                        
            return msg
        
        self._log.debug("Getting Image List")
        images = None
        try:
            images = connection.get_all_images()     
            #print images
        except:
            msg = "ERROR: getting image list " + str(sys.exc_info())
            self._log.error(msg)            
            return msg
        imagelist = []
        for i in images:
            imagelist.append(str(i).split(":")[1] + "  -  " + str(i.location) + " - " + str(i.status))
        
        return imagelist
        
            
    def euca_method(self, imagebackpath, kernel, operatingsystem, iaas_address, varfile, getimg, wait):
        #TODO: Pick kernel and ramdisk from available eki and eri

        #hardcoded for now
        eki = 'eki-78EF12D2'
        eri = 'eri-5BB61255'
        path = ""
        region = ""
        imageId = None
        if not eval(getimg):            
            ec2_url, s3_url, path, region = self.euca_environ(varfile, iaas_address)
            
            filename = os.path.split(imagebackpath)[1].strip()    
            print filename

            tempdir = "/tmp/" + str(randrange(999999999999999999999999)) + str(time.time()) + "/"
            os.system("mkdir -p " + tempdir)
#GENERATE RANDOM NUMBER
#CREATE DIRECTORY IN TMP
#ADD -d PARAMETER TO EUCA_GBUNDLE AND RANDOM NUMBER TO EUCA_UPLOAD_BUNDLE
#DELETE DIRECTORY
    
            #Bundle Image
            #cmd = 'euca-bundle-image --image ' + imagebackpath + ' --kernel ' + eki + ' --ramdisk ' + eri
            cmd = "euca-bundle-image --cert " + str(os.getenv("EC2_CERT")) + " --privatekey " + str(os.getenv("EC2_PRIVATE_KEY")) + \
                  " --user " + str(os.getenv("EC2_USER_ID")) + " --ec2cert " + str(os.getenv("EUCALYPTUS_CERT")) + " --url " + str(ec2_url) + \
                  " -a " + str(os.getenv("EC2_ACCESS_KEY")) + " -s " + str(os.getenv("EC2_SECRET_KEY")) + \
                  " --image " + str(imagebackpath) + " --kernel " + str(eki) + " --ramdisk " + str(eri) + " --destination " + tempdir
            print cmd
            self._log.debug(cmd)
            stat = os.system(cmd)
            if stat != 0:
                msg = "ERROR: in euca-bundle-image. " + str(sys.exc_info())
                self._log.error(msg)
                return msg
            
            #Upload bundled image
            #cmd = 'euca-upload-bundle --bucket ' + self.user + ' --manifest ' + '/tmp/' + filename + '.manifest.xml'
            cmd = "euca-upload-bundle -a " + os.getenv("EC2_ACCESS_KEY") + " -s " + os.getenv("EC2_SECRET_KEY") + \
                " --url " + s3_url + " --ec2cert " + os.getenv("EUCALYPTUS_CERT") + " --bucket " + self.user + " --manifest " + \
                tempdir + filename + ".manifest.xml"
            print cmd      
            self._log.debug(cmd)  
            stat = os.system(cmd)
            if stat != 0:
                msg = "ERROR: in euca-bundle-image. " + str(sys.exc_info())
                self._log.error(msg)
                return msg
    
            #Register image
            #cmd = 'euca-register ' + self.user + '/' + filename + '.manifest.xml'
            cmd = "euca-register -a " + os.getenv("EC2_ACCESS_KEY") + " -s " + os.getenv("EC2_SECRET_KEY") + \
                " --url " + ec2_url + " " + self.user + '/' + filename + '.manifest.xml'        
            print cmd
            self._log.debug(cmd)
            #stat = os.system(cmd) #execute this with Popen to get the output
            p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
            std = p.communicate()
            stat = 0
            if len(std[0]) > 0:
                self._log.debug('stdout: ' + std[0])
                self._log.debug('stderr: ' + std[1])
                print std[0]
                imageId = std[0].split("IMAGE")[1].strip()
            if p.returncode != 0:
                self._log.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
                stat = 1
            
            os.system("rm -rf " + tempdir)
            
            cmd = "rm -f " + imagebackpath
            if stat == 0:
                print cmd
                self._log.debug(cmd)
                os.system(cmd)
                
                print "Your image has been registered on Eucalyptus with the id printed in the previous line (IMAGE  id) \n" + \
                  "To launch a VM you can use euca-run-instances -k keyfile -n <#instances> id  \n" + \
                  "Remember to load you Eucalyptus environment before you run the instance (source eucarc) \n " + \
                  "More information is provided in https://portal.futuregrid.org/tutorials/eucalyptus \n"                
            else:
                print "An error occured when uploading image to Eucalyptus. Your image is located in " + str(imagebackpath) + " so you can upload it manually \n" + \
                "The kernel and ramdisk to use are " + eki + " and " + eri + " respectively \n" + \
                "Remember to load you Eucalyptus environment before you run the instance (source eucarc) \n" + \
                "More information is provided in https://portal.futuregrid.org/tutorials/eucalyptus \n"
                           
              
            return imageId              
        else:            
            print "Your Eucalyptus image is located in " + str(imagebackpath) + " \n" + \
            "The kernel and ramdisk to use are " + eki + " and " + eri + " respectively \n" + \
            "Remember to load you Eucalyptus environment before you run the instance (source eucarc) \n" + \
            "More information is provided in https://portal.futuregrid.org/tutorials/eucalyptus \n"
            return None
                       
        
    def openstack_method(self, imagebackpath, kernel, operatingsystem, iaas_address, varfile, getimg, wait):
        #TODO: Pick kernel and ramdisk from available eki and eri

        #hardcoded for now
        eki = 'aki-00000026'
        eri = 'ari-00000027'
        imageId = None
        path = ""
        region = ""
        if not eval(getimg):            
            ec2_url, s3_url, path, region = self.openstack_environ(varfile, iaas_address)
                        
            filename = os.path.split(imagebackpath)[1].strip()
    
            print filename
            
            tempdir = "/tmp/" + str(randrange(999999999999999999999999)) + str(time.time()) + "/"
            os.system("mkdir -p " + tempdir)
    
            #Bundle Image
            #cmd = 'euca-bundle-image --image ' + imagebackpath + ' --kernel ' + eki + ' --ramdisk ' + eri
            cmd = "euca-bundle-image --cert " + os.path.expanduser(os.path.expandvars(os.getenv("EC2_CERT"))) + " --privatekey " + os.path.expanduser(os.path.expandvars(os.getenv("EC2_PRIVATE_KEY"))) + \
                  " --user " + str(os.getenv("EC2_USER_ID")) + " --ec2cert " + str(os.getenv("EUCALYPTUS_CERT")) + " --url " + str(ec2_url) + \
                  " -a " + str(os.getenv("EC2_ACCESS_KEY")) + " -s " + str(os.getenv("EC2_SECRET_KEY")) + \
                  " --image " + str(imagebackpath) + " --kernel " + str(eki) + " --ramdisk " + str(eri) + " --destination " + tempdir
            print cmd
            self._log.debug(cmd)
            stat = os.system(cmd)
            if stat != 0:
                msg = "ERROR: in euca-bundle-image. " + str(sys.exc_info())
                self._log.error(msg)
                return msg
            #Upload bundled image
            #cmd = 'euca-upload-bundle --bucket ' + self.user + ' --manifest ' + '/tmp/' + filename + '.manifest.xml'
            cmd = "euca-upload-bundle -a " + os.getenv("EC2_ACCESS_KEY") + " -s " + os.getenv("EC2_SECRET_KEY") + \
                " --url " + s3_url + " --ec2cert " + os.getenv("EUCALYPTUS_CERT") + " --bucket " + self.user + " --manifest " + \
                tempdir + filename + ".manifest.xml"
            print cmd      
            self._log.debug(cmd)  
            stat = os.system(cmd)
            if stat != 0:
                msg = "ERROR: in euca-upload-image. " + str(sys.exc_info())
                self._log.error(msg)
                return msg
            
            #Register image
            #cmd = 'euca-register ' + self.user + '/' + filename + '.manifest.xml'
            cmd = "euca-register -a " + os.getenv("EC2_ACCESS_KEY") + " -s " + os.getenv("EC2_SECRET_KEY") + \
                " --url " + ec2_url + " " + self.user + '/' + filename + '.manifest.xml'    
            print cmd
            self._log.debug(cmd)
            #stat = os.system(cmd) #execute this with Popen to get the output
            
            p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
            std = p.communicate()
            stat = 0
            if len(std[0]) > 0:
                self._log.debug('stdout: ' + std[0])
                self._log.debug('stderr: ' + std[1])
                print std[0]
                try:
                    imageId = std[0].split("IMAGE")[1].strip()
                except:
                    self._log.error("Trying to get imageId. " + str(sys.exc_info()))
                    stat = 1
            if p.returncode != 0:
                self._log.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
                stat = 1
            
            os.system("rm -rf " + tempdir)
                
            cmd = "rm -f " + imagebackpath            
            if stat == 0:
                print cmd
                self._log.debug(cmd)
                os.system(cmd)
            
                print "Your image has been registered on OpenStack with the id " + imageId + " \n" + \
                      "To launch a VM you can use euca-run-instances -k keyfile -n <#instances> id \n" + \
                      "Remember to load you OpenStack environment before you run the instance (source novarc) \n " + \
                      "More information is provided in https://portal.futuregrid.org/tutorials/oss " + \
                      " and in https://portal.futuregrid.org/tutorials/eucalyptus\n"                
            else:
                print "An error occured when uploading image to OpenStack. Your image is located in " + str(imagebackpath) + " so you can upload it manually \n" + \
                "The kernel and ramdisk to use are " + eki + " and " + eri + " respectively \n" + \
                "Remember to load you Eucalyptus environment before you run the instance (source eucarc) \n" + \
                "More information is provided in https://portal.futuregrid.org/tutorials/oss " + \
                " and in https://portal.futuregrid.org/tutorials/eucalyptus\n"
            
            return imageId
        else:
            print "Your OpenStack image is located in " + str(imagebackpath) + " \n" + \
            "The kernel and ramdisk to use are " + eki + " and " + eri + " respectively \n" + \
            "Remember to load you OpenStack environment before you run the instance (source novarc) \n" + \
            "More information is provided in https://portal.futuregrid.org/tutorials/oss " + \
            " and in https://portal.futuregrid.org/tutorials/eucalyptus\n"
            return None
    
    def wait_available(self, iaas_name, imageId):
                #Verify that the image is in available status
        start = time.time()
        available = False
        retry = 0
        fails = 0
        max_retry = 100 #wait around 15 minutes. plus the time it takes to execute the command, that in openstack can be several seconds 
        max_fails = 5
        stat = 0
        if self._verbose:
            print "Verify that the requested image is in available status or wait until it is available"
        cmd = "euca-describe-images --access-key " + os.getenv("EC2_ACCESS_KEY") + " --secret-key " + os.getenv("EC2_SECRET_KEY") + \
                " --url " + os.getenv("EC2_URL") + " " + imageId 
        cmd1 = ""
        if iaas_name == "euca":
            cmd1 = "awk {print $5}"
        elif iaas_name == "openstack":
            cmd1 = "awk {print $4}"
            
        self._log.debug(cmd)
        while not available and retry < max_retry and fails < max_fails:
            p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
            p1 = Popen(cmd1.split(' ', 1), stdin=p.stdout, stdout=PIPE, stderr=PIPE)
            std = p1.communicate()
            stat = 0
            if len(std[0]) > 0:
                self._log.debug('stdout: ' + std[0])
            if p1.returncode != 0:
                self._log.error('Command: ' + cmd + ' failed, status: ' + str(p1.returncode) + ' --- ' + std[1])
                stat = 1
            if stat == 1:
                fails+=1
            elif std[0].strip() == "available":
                available = True
            else:
                retry +=1
                time.sleep(10)
        if stat == 1:
            msg = "ERROR: checking image status"
            self._log.error(msg)            
            return msg
        elif not available:
            msg = "ERROR: Timeout, image is not in available status"
            self._log.error(msg)            
            return msg
        
        end = time.time()
        self._log.info('TIME Image available:' + str(end - start))
    
    def opennebula_method(self, imagebackpath, kernel, operatingsystem, iaas_address, varfile, getimg, wait):
        
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
        
        print "The file " + filename + "_template.one is an example of the template that it is needed to launch a VM \n" + \
        "You need to modify the kernel and initrd path to indiacte their location in your particular system\n" + \
        "To see the availabe networks you can use onevnet list\n" + \
        "To launch a VM you can use onevm create " + filename + "_template.one \n" 
        
        #create template to upload image to opennebula repository
        
        #create script to boot image and tell user how to use it
   

    def xcat_method(self, xcat, image):
        start_all = time.time()
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

                if image == "list":                    
                    xcatimagelist = xcatServer.read(4096)
                    self._log.debug("Getting xCAT image list:" + xcatimagelist)
                    xcatimagelist = xcatimagelist.split(",")
                    moabstring = 'list,list,list,list,list'           
                else:
                    if self._verbose:
                        print "Customizing and deploying image on xCAT"
                    
                    ret = xcatServer.read(1024)
                    #check if the server did all right
                    if ret != 'OK':
                        self._log.error('Incorrect reply from the xCat server: ' + str(ret))
                        if self._verbose:
                            print 'Incorrect reply from the xCat server: ' + str(ret)
                        return
                    #recieve the prefix parameter from xcat server
                    moabstring = xcatServer.read(2048)
                    self._log.debug("String received from xcat server " + moabstring)
                    params = moabstring.split(',')
                    imagename = params[0] + '' + params[2] + '' + params[1]                    	    
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
        
        if self._verbose:
            print 'Connecting to Moab server'
        
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
            
            if image == "list":                                
                moabimageslist = moabServer.read(4096)
                self._log.debug("Getting Moab image list:" + moabimageslist)
                moabimageslist = moabimageslist.split(",")                
                setmoab = set(moabimageslist)
                setxcat = set(xcatimagelist)
                setand = setmoab & setxcat                
                imagename = list(setand)
            else:
                ret = moabServer.read(100)
                if ret != 'OK':
                    self._log.error('Incorrect reply from the Moab server:' + str(ret))
                    if self._verbose:
                        print 'Incorrect reply from the Moab server:' + str(ret)
                    return
                if self._verbose:
                    print 'Your image has been deployed in xCAT as ' + imagename + '.\n Please allow a few minutes for xCAT to register the image before attempting to use it.'
                    print 'To run a job in a machine using your image you can execute the next command: qsub -l os=<imagename> <scriptfile>'
                    print 'To check the status of the job you can use checkjob and showq commands'                    
            #return image deployed or list of images
            end_all = time.time()
            self._log.info('TIME walltime image deploy xcat/moab: ' + str(end_all - start_all))
            return imagename  
        
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
            self._log.debug('Retrieving image')
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
    group.add_argument('-l', '--list', dest='list', action="store_true", help='List of Id of the images deployed in xCAT/Moab or in the Cloud Frameworks')
    group1 = parser.add_mutually_exclusive_group()
    group1.add_argument('-x', '--xcat', dest='xcat', metavar='MachineName', help='Deploy image to xCAT. The argument is the machine name (minicluster, india ...)')
    group1.add_argument('-e', '--euca', dest='euca', nargs='?', metavar='Address:port', help='Deploy the image to Eucalyptus, which is in the specified addr')
    group1.add_argument('-o', '--opennebula', dest='opennebula', nargs='?', metavar='Address', help='Deploy the image to OpenNebula, which is in the specified addr')
    group1.add_argument('-n', '--nimbus', dest='nimbus', nargs='?', metavar='Address', help='Deploy the image to Nimbus, which is in the specified addr')
    group1.add_argument('-s', '--openstack', dest='openstack', nargs='?', metavar='Address', help='Deploy the image to OpenStack, which is in the specified addr')
    parser.add_argument('-v', '--varfile', dest='varfile', help='Path of the environment variable files. Currently this is used by Eucalyptus and OpenStack')
    parser.add_argument('-g', '--getimg', dest='getimg', action="store_true", help='Customize the image for a particular cloud framework but does not register it. So the user gets the image file.')
    parser.add_argument('-p', '--ldap', dest='ldap', action="store_true", help='Configure ldap in the VM.')
    parser.add_argument('-w', '--wait', dest='wait', action="store_true", help='Wait until the image is available. Currently this is used by Eucalyptus and OpenStack')
    
    args = parser.parse_args()
    

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
        if args.imgid != None:
            imgdeploy.xcat_method(args.xcat, args.imgid)
        elif args.list:
            hpcimagelist = imgdeploy.xcat_method(args.xcat, "list")
            print "The list of available images on xCAT/Moab is:"
            for i in hpcimagelist:
                print "  "+ i
            print "You can get more details by querying the image repository using IRClient.py -q command and the query string: \"* where tag=imagename\". \n" +\
                "NOTE: To query the repository you need to remove the OS from the image name (centos,ubuntu,debian,rhel...). " + \
                  "The real name starts with the username."
        else:            
            print "ERROR: You need to specify the id of the image that you want to deploy (-r/--imgid option) or the -q/--list option to list the deployed images"
            print "The parameter -i/--image cannot be used with this type of deployment"
            sys.exit(1)
    else:
        ldap = False 
        varfile = ""
        if args.varfile != None:
            varfile = os.path.expandvars(os.path.expanduser(args.varfile))
        #EUCALYPTUS    
        if ('-e' in used_args or '--euca' in used_args):
            if not args.getimg:
                if varfile == "":
                    print "ERROR: You need to specify the path of the file with the Eucalyptus environment variables"
                elif not os.path.isfile(varfile):
                    print "ERROR: Variable files not found. You need to specify the path of the file with the Eucalyptus environment variables"
                elif args.list:
                    output = imgdeploy.cloudlist(str(args.euca),"euca", varfile)                    
                    if output != None:
                        if not isinstance(output, list):
                            print output
                        else:
                            print "The list of available images on Eucalyptus is:"                        
                            for i in output:                       
                                print i
                            print "You can get more details by querying the image repository using IRClient.py -q command and the query string: \"* where tag=imagename\". \n" +\
                    "NOTE: To query the repository you need to remove the OS from the image name (centos,ubuntu,debian,rhel...). " + \
                      "The real name starts with the username and ends before .img.manifest.xml" 
                else:
                    output = imgdeploy.iaas_generic(args.euca, image, image_source, "euca", varfile, args.getimg, ldap, args.wait)
                    if output != None:
                        if re.search("^ERROR", output):
                            print output       
            elif args.list:
                output = imgdeploy.cloudlist(str(args.euca),"euca", varfile)                
                if output != None:
                    if not isinstance(output, list):
                        print output
                    else:
                        print "The list of available images on Eucalyptus is:"                        
                        for i in output:                       
                            print i    
                        print "You can get more details by querying the image repository using IRClient.py -q command and the query string: \"* where tag=imagename\". \n" +\
                    "NOTE: To query the repository you need to remove the OS from the image name (centos,ubuntu,debian,rhel...). " + \
                      "The real name starts with the username and ends before .img.manifest.xml" 
            else:
                output = imgdeploy.iaas_generic(args.euca, image, image_source, "euca", varfile, args.getimg, ldap, args.wait)
                if output != None:
                    if re.search("^ERROR", output):
                        print output
        #OpenNebula
        elif ('-o' in used_args or '--opennebula' in used_args):
            output = imgdeploy.iaas_generic(args.opennebula, image, image_source, "opennebula", varfile, args.getimg, ldap, args.wait)
        #NIMBUS
        elif ('-n' in used_args or '--nimbus' in used_args):
            #TODO        
            print "Nimbus deployment is not implemented yet"
        elif ('-s' in used_args or '--openstack' in used_args):
            if not args.getimg:
                if varfile == "":
                    print "ERROR: You need to specify the path of the file with the OpenStack environment variables"
                elif not os.path.isfile(varfile):
                    print "ERROR: Variable files not found. You need to specify the path of the file with the OpenStack environment variables"
                elif args.list:
                    output = imgdeploy.cloudlist(str(args.openstack),"openstack", varfile)                    
                    if output != None:
                        if not isinstance(output, list):
                            print output
                        else:
                            print "The list of available images on OpenStack is:"
                            for i in output:                       
                                print i 
                            print "You can get more details by querying the image repository using IRClient.py -q command and the query string: \"* where tag=imagename\". \n" +\
                "NOTE: To query the repository you need to remove the OS from the image name (centos,ubuntu,debian,rhel...). " + \
                  "The real name starts with the username and ends before .img.manifest.xml"
                else:    
                    output = imgdeploy.iaas_generic(args.openstack, image, image_source, "openstack", varfile, args.getimg, ldap, args.wait)
                    if output != None:
                        if re.search("^ERROR", output):
                            print output
            elif args.list:
                output = imgdeploy.cloudlist(str(args.openstack),"openstack", varfile)                
                if output != None:
                    if not isinstance(output, list):
                        print output
                    else:
                        print "The list of available images on OpenStack is:"
                        for i in output:                       
                            print i  
                        print "You can get more details by querying the image repository using IRClient.py -q command and the query string: \"* where tag=imagename\". \n" +\
                    "NOTE: To query the repository you need to remove the OS from the image name (centos,ubuntu,debian,rhel...). " + \
                      "The real name starts with the username and ends before .img.manifest.xml"
            else:    
                output = imgdeploy.iaas_generic(args.openstack, image, image_source, "openstack", varfile, args.getimg, ldap, args.wait)
                if output != None:
                    if re.search("^ERROR", output):
                        print output
        else:
            print "ERROR: You need to specify a deployment target"
    

if __name__ == "__main__":
    main()
#END

