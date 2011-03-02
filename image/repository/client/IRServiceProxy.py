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
import string


class IRServiceProxy(object):
    
    #Server location 
    #(Now we assume that the server is where the images are stored. We may want to change that)
    SERVICEENDP = "localhost"   #xray.futuregrid.org"    
    FGIRDIR = "/home/javi/imagerepo/ImageRepo/src/futuregrid/image/repository/server/"  #"/N/u/fuwang/fgir/"
    # TODO: GVL: This is not good, we want a config file where we specify this, the config is to be placed in .futuregrid

    BACKENDS = ["mongodb","mysql"]
    
    
    def __init__(self):
        super(IRServiceProxy, self).__init__()
        self._backend = ""
        self._fgirimgstore = ""
        # GVL: THIS IS NOT GOOD, we want a .futuregrid dir in which the IRconfig is placed
        # We want a util function taht manages location, creation, existence and destruction of the .futuregrid dir
        self._configfile=os.environ['HOME']+"/.IRconfig"
        self._setupBackend()
        
    def _setupBackend (self):  #We can set up manually to avoid two ssh conections each time
        userId = os.popen('whoami', 'r').read().strip()        
        if not os.path.isfile(self._configfile):
            cmdexec = " '" + IRServiceProxy.FGIRDIR + \
                    "IRService.py --getBackend " "'"
        
            print "Requesting Server Config"
            aux=self._rExec(userId, cmdexec)            
            self._backend=aux[0].strip()
            self._fgirimgstore=aux[1].strip()
            try:
                f = open(self._configfile, "w")
                f.write(self._backend+'\n')
                f.write(self._fgirimgstore)
                f.close()
            except(IOError),e:
                print "Unable to open the file", self._configfile, "Ending program.\n", e
        else:
            print "Reading Server Config from "+self._configfile
            try:
                f = open(self._configfile, "r")
                self._backend=f.readline()
                if not (self._backend.strip() in self.BACKENDS):
                    print "Error in local config. Please remove file: "+os.environ['HOME']+"/.IRconfig"
                    exit(0)
                self._fgirimgstore=f.readline()
                f.close()
            except(IOError),e:
                print "Unable to open the file", self._configfile, "Ending program.\n", e
 
    def auth(self, userId):
        # to be implemented when integrating with the security framework
        cmdexec = " '" + IRServiceProxy.FGIRDIR + \
                    "IRService.py --auth " + userId + "'"
        #print cmd
        return self._rExec(userId, cmdexec)
        
    def query(self, userId, queryString):    
        cmdexec = " '" + IRServiceProxy.FGIRDIR + \
                    "IRService.py --list \""+ queryString + "\"'"
        
        return self._rExec(userId, cmdexec)
        
    def get(self, userId, option, imgId):
        cmdexec = " '" + IRServiceProxy.FGIRDIR + \
                    "IRService.py --get " + option + " " + imgId + "'"
        #print cmd
        
        imgURI = self._rExec(userId, cmdexec)[0].strip()
        #print imgURI        
        if not imgURI=='None':
            imgURI = IRServiceProxy.SERVICEENDP + ":" + imgURI
            if (option == "img"):
                imgURI = self._retreiveImg(userId, imgId, imgURI)      
        else:            
            imgURI = None
        
        return imgURI
        
    def put(self, userId, uid, imgFile, attributeString):
        status=0
        if (self.checkMeta(attributeString)):
            cmdexec = " '" + IRServiceProxy.FGIRDIR + \
                    "IRService.py --uploadValidator " +  userId + "'"
                    
                    #TODO ADD size of the image
                   
            isPermitted = self._rExec(userId, cmdexec)
            #print isPermitted[0].strip()      
            if (isPermitted[0].strip()=="NoUser"):
                status=-1            
            elif (isPermitted[0].strip()=="True"):            
                cmdexec = " '" + IRServiceProxy.FGIRDIR + "IRService.py --getuid'"
                uidRet = self._rExec(userId, cmdexec)
                uid = uidRet[0].strip()

                fileLocation = self._fgirimgstore + uid            
                cmd = 'scp ' + imgFile + ' ' + userId +"@" + \
                        IRServiceProxy.SERVICEENDP + ":" + fileLocation
    
                print "uploading file through scp:"
                print cmd
                os.system(cmd)
                
                cmdexec = " '" + IRServiceProxy.FGIRDIR + "IRService.py --put " + \
                             uid + " " + fileLocation + " \"" + attributeString + "\"'"   ##Why do we need to send imgFile???
                #print cmdexec
                uid = self._rExec(userId, cmdexec)
                
                status=uid[0].strip()
                #print status            
            
        return status
    
    def updateItem(self, userId, imgId, attributeString):  
        success="False"  #A string because _rExec return a string ;)
        if (self.checkMeta(attributeString)):
            cmdexec = " '" + IRServiceProxy.FGIRDIR + "IRService.py --modify " +\
                         imgId + " \"" + attributeString + "\"'"
            #print cmdexec
            success = self._rExec(userId, cmdexec)
        
        #print success
        return success[0].strip()
    
    def setPermission(self, userId, imgId, permission):
        success=["False"]
        if(permission in ImgMeta.Permission):
            cmdexec = " '" + IRServiceProxy.FGIRDIR + "IRService.py --modify "+\
                         imgId + " \"permission=" + permission + "\"'"
            #print cmdexec
            success = self._rExec(userId, cmdexec)
        else:
            success=["Available options: "+str(ImgMeta.Permission)]
            
        #print success
        return success[0].strip()
   
    def remove(self, userId, imgId):
        cmdexec = " '" + IRServiceProxy.FGIRDIR + \
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
        """
        could the name of the tmpFile be overwiten???
        I have added /tmp to the file
        """
        #TODO:GVL: we need a util function that generates unique files in /tmp, 
        #probably under a dir for a user, permissions have to be worked out, 
        #just doing time may no be strong enough, you want pid also
        
        #TODO: do we want to use the .format statement from python to make code more readable?
        
        cmdssh = "ssh " + userId + "@" + IRServiceProxy.SERVICEENDP
        tmpFile = "/tmp/"+ str(time())
        cmdexec = cmdexec + " > " + tmpFile
        cmd = cmdssh + cmdexec
        #print cmd
        os.system(cmd)
        f = open(tmpFile, "r")
        outputs = f.readlines()
        f.close()
        os.system("rm -rf " + tmpFile)
        #output = ""
        #for line in outputs:
        #    output += line.strip()
        return outputs

    def _retreiveImg(self, userId, imgId, imgURI):
        cmdscp = "scp " + userId + "@" + imgURI + " ./" + imgId + ".img"
        #print cmdscp
        output=""
        try:
            if (os.system(cmdscp) == 0):
                output = "The image " + imgId + " is located in " + os.popen('pwd', 'r').read().strip() + "/" + imgId + ".img"
                if (self._backend=="mongodb"):
                    cmdrm=" rm -rf " + (imgURI).split(":")[1]
                    self._rExec(userId, cmdrm)
                #remove the temporal file
        except os.error:
            print "Error, The image cannot be retieved"
            output = None
        
        return output