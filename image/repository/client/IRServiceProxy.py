#/usr/bin/env python
"""
Service proxy in the client side.

Before the SOA is implemented, this contains the concrete functional access
that supposed to reside in the service side. When the web service is used,
this will serve as a proxy that talks to the service in the server side.
"""

__author__ = 'Javier Diaz, Fugang Wang'
__version__ = '0.9'

import os
from time import time
import string
import sys
from random import randrange
import socket,ssl
import hashlib
from getpass import getpass
import re
#futuregrid.image.repository.client.

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRClientConf import IRClientConf

sys.path.append(os.getcwd())
try:
    from futuregrid.utils import fgLog #This should the the final one
#To execute IRClient for tests
except:
    sys.path.append(os.path.dirname(__file__) + "/../../../") #Directory where fg.py is
    from utils import fgLog


class IRServiceProxy(object):

    #(Now we assume that the server is where the images are stored. We may want to change that)    
    ############################################################
    # __init__
    ############################################################
    def __init__(self, verbose, printLogStdout):
        super(IRServiceProxy, self).__init__()

        #Load Config
        self._conf = IRClientConf()
        #self._backend = self._conf.getBackend()
        #self._fgirimgstore = self._conf.getFgirimgstore()
        self._port = self._conf.getPort()
        self._serveraddr = self._conf.getServeraddr()
        self.verbose = verbose
        
        self._ca_certs = self._conf.getCaCerts()
        self._certfile = self._conf.getCertFile()
        self._keyfile = self._conf.getKeyFile()
        
        self._connIrServer = None
        
        self.passwdtype = "ldappassmd5"
        #Setup log
        self._log = fgLog.fgLog(self._conf.getLogFile(), self._conf.getLogLevel(), "Img Repo Client", printLogStdout)
        

    def connection(self):
        connected = False
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self._connIrServer = ssl.wrap_socket(s,
                                        ca_certs=self._ca_certs,
                                        certfile=self._certfile,
                                        keyfile=self._keyfile,
                                        cert_reqs=ssl.CERT_REQUIRED,
                                        ssl_version=ssl.PROTOCOL_TLSv1)
            self._log.debug("Connecting server: " + self._serveraddr + ":" + str(self._port))
            self._connIrServer.connect((self._serveraddr, self._port))   
            connected = True         
        except ssl.SSLError:
            self._log.error("CANNOT establish SSL connection. EXIT")
        except socket.error:
            self._log.error("Error with the socket connection")
        except:
            if self.verbose:
                print "Error CANNOT establish connection with the server"
            self._log.error("ERROR: exception not controlled" + str(sys.exc_info()))
            
        
        return connected
        #irServer.write(options) #to be done in each method
    def disconnect(self):
        try:
            self._connIrServer.shutdown(socket.SHUT_RDWR)
            self._connIrServer.close()
        except:            
            self._log.debug("In disconnect:" + str(sys.exc_info()))
          
    def check_auth(self, userId, checkauthstat):
        endloop = False
        passed = False
        while not endloop:
            ret = self._connIrServer.read(1024)
            if (ret == "OK"):
                if self.verbose:
                    print "Authentication OK"
                self._log.debug("Authentication OK")
                endloop = True
                passed = True
            elif (ret == "TryAuthAgain"):
                msg = "Permission denied, please try again. User is " + userId                    
                self._log.error(msg)
                if self.verbose:
                    print msg                            
                m = hashlib.md5()
                m.update(getpass())
                passwd = m.hexdigest()
                self._connIrServer.write(passwd)
            else:                
                self._log.error(str(ret))
                if self.verbose:
                    print ret
                checkauthstat.append(str(ret))
                endloop = True
                passed = False
        return passed
        
    ############################################################
    # query
    ############################################################
    def query(self, userId, passwd, userIdB, queryString):   
        """
        userId: user that authenticate against the repository.
        password: password of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|list|" + userIdB + "|" + queryString
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(32768)            
            if output == "None":
                output = None
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output
            
    ############################################################
    # get
    ############################################################
    def get(self, userId, passwd, userIdB, option, imgId, dest):
        """
        userId: user that authenticate against the repository.
        password: password of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """  
        checkauthstat = []      
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|get|" + userIdB + "|" + option + "|" + imgId
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read()
            if not output == 'None':
                output = self._serveraddr + ":" + output
                if (option == "img"):
                    output = self._retrieveImg(userId, imgId, output, dest)
                    if output != None:
                        self._connIrServer.write('OK')
                    else:#this should be used to retry retrieveImg
                        self._connIrServer.write('Fail')
            else:
                output = None
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
                
        return output
    
    ############################################################
    # put
    ############################################################
    def put(self, userId, passwd, userIdB, imgFile, attributeString):
        """
        userId: user that authenticate against the repository.
        password: password of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        
        output:
        0 is general error
        """
        status = "0"
        if (self.checkMeta(attributeString) and os.path.isfile(imgFile)):
            
            status = "0"
            output = ""
            checkauthstat = []
            
            size = os.path.getsize(imgFile)
            extension = os.path.splitext(imgFile)[1].strip() 
                        
            if self.verbose:
                print "Checking quota and Generating an ImgId"
            msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|put|" + userIdB + "|" + str(size) + "|" + extension +\
                 "|" + attributeString
            self._connIrServer.write(msg)
            
            authstatus = self.check_auth(userId, checkauthstat)
            self._log.debug("Auth in server status "+str(authstatus))
            if authstatus:
                #wait for "OK,tempdir,imgId" or error status                
                output = self._connIrServer.read(2048)
                self._log.debug("after auth, repo server answer: "+str(output))
                #print output
                if not (re.search('^ERROR', output)):
                    output = output.split(',')                    
                    imgStore = output[0] 
                    imgId = output[1]
                    fileLocation = imgStore + imgId
                    self._log.info("Uploading the image")
                    if self.verbose:
                        print 'Uploading image. You may be asked for ssh/passphrase password'
                        cmd = 'scp ' + imgFile + " " + \
                            self._serveraddr + ":" + fileLocation
                    else:#this is the case where another application call it. So no password or passphrase is allowed
                        cmd = 'scp -q -oBatchMode=yes ' + imgFile + " " + \
                            self._serveraddr + ":" + fileLocation
                    stat = os.system(cmd)
                    if (str(stat) != "0"):
                        self._log.error(str(stat))
                        self._connIrServer.write("Fail")
                    else:
                        if self.verbose:
                            print "Registering the image"                            
                        msg = fileLocation
                        self._connIrServer.write(msg)
                        #wait for final output
                        status = self._connIrServer.read(2048)
                        if status == "0":    
                            status = "ERROR: uploading image to the repository. File does not exists or metadata string is invalid"
                else:
                    status = output
            else:
                self._log.error("ERROR:auth failed "+str(checkauthstat[0]))
                status = checkauthstat[0]
        else:
            status = "ERROR: uploading image to the repository. File does not exists or metadata string is invalid"
        return status
        
    ############################################################
    # updateItem
    ############################################################
    def updateItem(self, userId, passwd, userIdB, imgId, attributeString):
        """
        userId: user that authenticate against the repository.
        password: password of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        success = "False"
        if (self.checkMeta(attributeString)):       
            msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|modify|" + userIdB + "|" + imgId + "|" + attributeString
            self._connIrServer.write(msg)
            if self.check_auth(userId, checkauthstat):
                #wait for output
                output = self._connIrServer.read(2048)
            else:
                self._log.error(str(checkauthstat[0]))
                if self.verbose:
                    print checkauthstat[0]
            
        return output
    
    ############################################################
    # remove
    ############################################################
    def remove(self, userId, passwd, userIdB, imgId):
        """
        userId: user that authenticate against the repository.
        passwd: password of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|remove|" + userIdB + "|" + imgId
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(2048)
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output
    
            
    ############################################################
    # setPermission
    ############################################################
    def setPermission(self, userId, passwd, userIdB, imgId, permission):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []        
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|setPermission|" + userIdB + "|" + imgId + "|" + permission
        if(permission in ImgMeta.Permission):
            self._connIrServer.write(msg)
            if self.check_auth(userId, checkauthstat):
                #wait for output
                output = self._connIrServer.read(2048)
            else:
                self._log.error(str(checkauthstat[0]))
                if self.verbose:
                    print checkauthstat[0]
        else:
            output = "Available options: " + str(ImgMeta.Permission)
                
        return output
    
    ############################################################
    # userAdd
    ############################################################
    def userAdd(self, userId, passwd, userIdB, userIdtoAdd):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|useradd|" + userIdB + "|" + userIdtoAdd
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(2048)
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output
        
    ############################################################
    # userDel
    ############################################################
    def userDel(self, userId, passwd, userIdB, userIdtoDel):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|userdel|" + userIdB + "|" + userIdtoDel
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(2048)
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output

    ############################################################
    # userList
    ############################################################
    def userList(self, userId, passwd, userIdB):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|userlist|" + userIdB 
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(32768)
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output

    ############################################################
    # setUserQuota    
    ############################################################
    def setUserQuota(self, userId, passwd, userIdB, userIdtoModify, quota):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        try:
            quotanum = str(eval(quota))
            msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|setUserQuota|" + userIdB + "|" + userIdtoModify + "|" + quotanum
            self._connIrServer.write(msg)
            if self.check_auth(userId, checkauthstat):
                #wait for output
                output = self._connIrServer.read(2048)
            else:
                self._log.error(str(checkauthstat[0]))
                if self.verbose:
                    print checkauthstat[0]
        except:
            if self.verbose:
                print "ERROR: evaluating the quota. It must be a number or a mathematical operation enclosed in \"\" characters"        
            
        return output


    ############################################################
    # setUserRole
    ############################################################
    def setUserRole(self, userId, passwd, userIdB, userIdtoModify, role):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []        
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|setUserRole|" + userIdB + "|" + userIdtoModify + "|" + role
        if(role in IRUser.Role):
            self._connIrServer.write(msg)
            if self.check_auth(userId, checkauthstat):
                #wait for output
                output = self._connIrServer.read(2048)
            else:
                self._log.error(str(checkauthstat[0]))
                if self.verbose:
                    print checkauthstat[0]
        else:
            output = "Available options: " + str(IRUser.Role)
                
        return output
        
        
    ############################################################
    # setUserStatus
    ############################################################
    def setUserStatus(self, userId, passwd, userIdB, userIdtoModify, status):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []        
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|setUserStatus|" + userIdB + "|" + userIdtoModify + "|" + status
        if(status in IRUser.Status):
            self._connIrServer.write(msg)
            if self.check_auth(userId, checkauthstat):
                #wait for output
                output = self._connIrServer.read(2048)
            else:
                self._log.error(str(checkauthstat[0]))
                if self.verbose:
                    print checkauthstat[0]
        else:
            output = "Available options: " + str(IRUser.Status)
                
        return output
        

    ############################################################
    # histImg
    ############################################################
    def histImg(self, userId, passwd, userIdB, imgId):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|histimg|" + userIdB + "|" + imgId
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(32768)
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output

    ############################################################
    # histUser
    ############################################################
    def histUser(self, userId, passwd, userIdB, userIdtoSearch):
        """
        userId: user that authenticate against the repository.
        passwd: passwd of the previous user
        userIdB: user that execute the command in the repository.         
        
        Typically, userId and userIdB are the same user. However, they are different when the repo 
        is used by a service like IMGenerateServer or IMDeployServer, because these services interact 
        with the repo in behalf of other users.
        """
        checkauthstat = []
        output = None
        msg = userId + "|" + str(passwd) + "|" + self.passwdtype + "|histuser|" + userIdB + "|" + userIdtoSearch
        self._connIrServer.write(msg)
        if self.check_auth(userId, checkauthstat):
            #wait for output
            output = self._connIrServer.read(32768)
        else:
            self._log.error(str(checkauthstat[0]))
            if self.verbose:
                print checkauthstat[0]
            
        return output
    
    ############################################################
    # checkMeta
    ############################################################
    def checkMeta(self, attributeString):
        attributes = attributeString.split("&")
        correct = True
        for item in attributes:
            attribute = item.strip()
            #print attribute
            tmp = attribute.split("=")
            if (len(tmp) == 2):
                key = string.lower(tmp[0])
                value = tmp[1]
                if key in ImgMeta.metaArgsIdx.keys():
                    if (key == "vmtype"):
                        value = string.lower(value)
                        if not (value in ImgMeta.VmType):
                            self._log.error("Wrong value for VmType, please use: " + str(ImgMeta.VmType))
                            if self.verbose:
                                print "Wrong value for VmType, please use: " + str(ImgMeta.VmType)
                            correct = False
                            break
                    elif (key == "imgtype"):
                        value = string.lower(value)
                        if not (value in ImgMeta.ImgType):
                            self._log.error("Wrong value for ImgType, please use: " + str(ImgMeta.ImgType))
                            if self.verbose:
                                print "Wrong value for ImgType, please use: " + str(ImgMeta.ImgType)
                            correct = False
                            break
                    elif(key == "permission"):
                        value = string.lower(value)
                        if not (value in ImgMeta.Permission):
                            self._log.error("Wrong value for Permission, please use: " + str(ImgMeta.Permission))
                            if self.verbose:
                                print "Wrong value for Permission, please use: " + str(ImgMeta.Permission)
                            correct = False
                            break
                    elif (key == "imgstatus"):
                        value = string.lower(value)
                        if not (value in ImgMeta.ImgStatus):
                            self._log.error("Wrong value for ImgStatus, please use: " + str(ImgMeta.ImgStatus))
                            if self.verbose:
                                print "Wrong value for ImgStatus, please use: " + str(ImgMeta.ImgStatus)
                            correct = False
                            break
                else:
                    self._log.warning("Wrong attribute: "+key)
                    if self.verbose:
                        print "WARNING: Attribute "+key+" is invalid. It will be ignored."
        return correct
    """
    ############################################################
    # _rExec
    ############################################################
    def _rExec(self, userId, cmdexec):

        #TODO: do we want to use the .format statement from python to make code more readable?

        #cmdssh = "ssh " + userId + "@" + self._serveraddr
        cmdssh = "ssh " + self._serveraddr
        tmpFile = "/tmp/" + str(time()) #+ str(self.randomId())
        #print tmpFile
        cmdexec = cmdexec + " > " + tmpFile
        cmd = cmdssh + cmdexec
        #print cmd
        stat = os.system(cmd)
        if (str(stat) != "0"):
            self._log.error(str(stat))
            if self.verbose:
                print stat
        f = open(tmpFile, "r")
        outputs = f.readlines()
        #print outputs
        f.close()
        os.system("rm -rf " + tmpFile)
        #output = ""
        #for line in outputs:
        #    output += line.strip()
        #print outputs
        return outputs
    """
    ############################################################
    # _retrieveImg
    ############################################################
    def _retrieveImg(self, userId, imgId, imgURI, dest):
        
        extension = os.path.splitext(imgURI)[1]
        extension = string.split(extension, "_")[0]
        
        fulldestpath = dest + "/" + imgId + "" + extension
                
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
                
    
        if self.verbose:
            #cmdscp = "scp " + userId + "@" + imgURI + " " + fulldestpath
            cmdscp = "scp " + imgURI + " " + fulldestpath
        else:
            #cmdscp = "scp -q " + userId + "@" + imgURI + " " + fulldestpath
            cmdscp = "scp -q -oBatchMode=yes " + imgURI + " " + fulldestpath
        #print cmdscp
        output = ""
        try:
            self._log.debug('Retrieving image. You may be asked for ssh/passphrase password')
            if self.verbose:
                print 'Retrieving image. You may be asked for ssh/passphrase password'
            stat = os.system(cmdscp)
            if (stat == 0):
                output = fulldestpath                
            else:
                self._log.error("Error retrieving the image. Exit status " + str(stat))
                if self.verbose:
                    print "Error retrieving the image. Exit status " + str(stat)
                #remove the temporal file
        except os.error:
            self._log("Error, The image cannot be retieved" + str(sys.exc_info()))
            if self.verbose:
                print "Error, The image cannot be retieved" + str(sys.exc_info())
            output = None

        return output
     
    #def randomId(self):
    #    Id = str(randrange(999999999999999999999999))
    #    return Id
