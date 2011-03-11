"""
Service proxy in the client side.

Before the SOA is implemented, this contains the concrete functional access
that supposed to reside in the service side. When the web service is used,
this will serve as a proxy that talks to the service in the server side.
"""

__author__ = 'Fugang Wang'
__version__ = '0.1'

import os
from time import time

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRTypes import IRCredential
import IRUtil
from IRClientConf import IRClientConf
import string
import sys

try:
    from futuregrid.utils import fgLog #This should the the final one
#To execute IRClient for tests
except:
    sys.path.append(os.path.dirname(__file__)+"/../../../") #Directory where fg.py is
    from utils import fgLog


class IRServiceProxy(object):
    
    #(Now we assume that the server is where the images are stored. We may want to change that)    
    def __init__(self):
        super(IRServiceProxy, self).__init__()
        
        #Load Config
        self._conf=IRClientConf()
        self._backend = self._conf.getBackend()
        self._fgirimgstore = self._conf.getFgirimgstore()
        self._serverdir=self._conf.getServerdir()
        self._serveraddr=self._conf.getServeraddr()

        #Setup log        
        self._log=fgLog.fgLog(self._conf.getLogFile(),self._conf.getLogLevel(),"Img Repo Client", True)
 
    def auth(self, userId):
        # to be implemented when integrating with the security framework
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --auth " + userId + "'"
        #print cmd
        return self._rExec(userId, cmdexec)
    
    def userAdd(self, userId, userIdtoAdd):  
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --useradd "+ userIdtoAdd + "'"
        
        return self._rExec(userId, cmdexec)[0].strip()
    
    def userDel(self, userId, userIdtoDel):  
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --userdel "+ userIdtoDel + "'"
        
        return self._rExec(userId, cmdexec)[0].strip()
    
    def userList(self, userId):
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --userlist "+ userId + "'"
        
        return self._rExec(userId, cmdexec)
    
    def setUserQuota(self, userId, userIdtoModify, quota):  
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --setUserQuota "+ userIdtoModify +" "+str(eval(quota))+"'"
        
        return self._rExec(userId, cmdexec)[0].strip()
    
    def setUserRole(self, userId, userIdtoModify, role):  
        success=["False"]
        if(role in IRUser.Role):
            cmdexec = " '" + self._serverdir + \
                        "IRService.py --setUserRole "+ userIdtoModify +" "+role+"'"
            
            success=self._rExec(userId, cmdexec)
        else:
            success=["Available options: "+str(IRUser.Role)]
             
        return success[0].strip()
    
    
    def setUserStatus(self, userId, userIdtoModify, status):
        success=["False"]
        if(status in IRUser.Status):  
            cmdexec = " '" + self._serverdir + \
                        "IRService.py --setUserStatus "+ userIdtoModify +" "+status+"'"
            
            success=self._rExec(userId, cmdexec)
        else:
            success=["Available options: "+str(IRUser.Status)]
             
        return success[0].strip()
    
    def query(self, userId, queryString):  
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --list \""+ queryString + "\"'"
        
        return self._rExec(userId, cmdexec)
        
    def get(self, userId, option, imgId):
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --get " + option + " " + imgId + "'"
        #print cmdexec
        
        imgURI = self._rExec(userId, cmdexec)[0].strip()
        #print imgURI        
        if not imgURI=='None':
            imgURI = self._serveraddr + ":" + imgURI
            if (option == "img"):
                imgURI = self._retrieveImg(userId, imgId, imgURI)      
        else:            
            imgURI = None
        
        return imgURI
        
    def put(self, userId, uid, imgFile, attributeString):
        """
        0 is general error
        -1 user doesn't exist
        -2 user is not active
        -3 file exceed the quota 
        """
        status="0"
        if (self.checkMeta(attributeString) and os.path.isfile(imgFile)):
            
            size=os.path.getsize(imgFile)
            
            self._log.debug("Checking quota")
            cmdexec = " '" + self._serverdir + \
                    "IRService.py --uploadValidator " +str(size)+"'"
                   
                    
                   
            isPermitted = self._rExec(userId, cmdexec)
            #print isPermitted[0].strip()      
            if (isPermitted[0].strip()=="NoUser"):
                status="-1"
            elif (isPermitted[0].strip()=="NoActive"):
                status="-2"
            elif (isPermitted[0].strip()=="True"):     
                
                """       
                cmdexec = " '" + self._serverdir + "IRService.py --getuid'"
                uidRet = self._rExec(userId, cmdexec)
                uid = uidRet[0].strip()
                """
                uid=IRUtil.getImgId()
                                                
                fileLocation = self._fgirimgstore + uid
                            
                cmd = 'scp ' + imgFile + ' ' + userId +"@" + \
                        self._serveraddr + ":" + fileLocation
                
                print "uploading file through scp:"
                #print cmd
                stat=os.system(cmd)
                if (str(stat)!="0"):
                    print stat
                print "Registering the Image"
                cmdexec = " '" + self._serverdir + "IRService.py --put " + \
                             uid + " " + fileLocation + " \"" + attributeString + "\" "+str(size)+"'"
                #print cmdexec
                uid = self._rExec(userId, cmdexec)
                
                status=uid[0].strip()
                #print status
            else:
                status="-3"        
            
        return status
    
    def updateItem(self, userId, imgId, attributeString):  
        success="False"  #A string because _rExec return a string ;)
        if (self.checkMeta(attributeString)):
            cmdexec = " '" + self._serverdir + "IRService.py --modify " +\
                         imgId + " \"" + attributeString + "\"'"
            #print cmdexec
            success = self._rExec(userId, cmdexec)
        
        #print success
        return success[0].strip()
    
    def setPermission(self, userId, imgId, permission):
        success=["False"]
        if(permission in ImgMeta.Permission):
            cmdexec = " '" + self._serverdir + "IRService.py --modify "+\
                         imgId + " \"permission=" + permission + "\"'"
            #print cmdexec
            success = self._rExec(userId, cmdexec)
        else:
            success=["Available options: "+str(ImgMeta.Permission)]
            
        #print success
        return success[0].strip()
   
    def remove(self, userId, imgId):
        cmdexec = " '" + self._serverdir + \
                    "IRService.py --remove " + " " + imgId + "'"
        #print cmd
        
        deleted = self._rExec(userId, cmdexec)[0].strip()
        #print deleted
        return deleted
    
    def checkMeta(self,attributeString):        
        attributes = attributeString.split("|")
        correct=True
        for item in attributes:
            attribute = item.strip()
            #print attribute
            tmp = attribute.split("=")
            if (len(tmp)==2):
                key = string.lower(tmp[0])            
                value = tmp[1]            
                if key in ImgMeta.metaArgsIdx.keys():
                    if (key == "vmtype"):
                        value=string.lower(value)
                        if not (value in ImgMeta.VmType):
                            print "Wrong value for VmType, please use: "+str(ImgMeta.VmType)
                            correct=False
                            break
                    elif (key == "imgtype"):       
                        value=string.lower(value) 
                        if not (value in ImgMeta.ImgType):
                            print "Wrong value for ImgType, please use: "+str(ImgMeta.ImgType)
                            correct=False
                            break
                    elif(key == "permission"):
                        value=string.lower(value)
                        if not (value in ImgMeta.Permission):
                            print "Wrong value for Permission, please use: "+str(ImgMeta.Permission)
                            correct=False
                            break
                    elif (key == "imgstatus"):
                        value=string.lower(value)
                        if not (value in ImgMeta.ImgStatus):
                            print "Wrong value for ImgStatus, please use: "+str(ImgMeta.ImgStatus)
                            correct=False
                            break                
                
        return correct
        
    def _rExec(self, userId, cmdexec):        
                
        #TODO: do we want to use the .format statement from python to make code more readable?
                
        cmdssh = "ssh " + userId + "@" + self._serveraddr
        tmpFile = "/tmp/"+ str(time())+str(IRUtil.getImgId())
        #print tmpFile
        cmdexec = cmdexec + " > " + tmpFile
        cmd = cmdssh + cmdexec
        #print cmd
        stat=os.system(cmd)
        if (str(stat)!="0"):
            print stat
        f = open(tmpFile, "r")
        outputs = f.readlines()
        f.close()
        os.system("rm -rf " + tmpFile)
        #output = ""
        #for line in outputs:
        #    output += line.strip()
        #print outputs
        return outputs

    def _retrieveImg(self, userId, imgId, imgURI):
        cmdscp = "scp " + userId + "@" + imgURI + " ./" + imgId + ".img"
        #print cmdscp
        output=""
        try:
            print "Retrieving the image"
            stat=os.system(cmdscp)
            if (stat == 0):
                output = "The image " + imgId + " is located in " + os.popen('pwd', 'r').read().strip() + "/" + imgId + ".img"
                if (self._backend=="mongodb"):
                    cmdrm=" rm -rf " + (imgURI).split(":")[1]
                    print "Post processing"
                    self._rExec(userId, cmdrm)
            else:
                self._log.error("Error retrieving the image. Exit status "+str(stat))
                #remove the temporal file
        except os.error:
            self._log("Error, The image cannot be retieved"+str(sys.exc_info()))
            output = None
        
        return output