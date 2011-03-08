#!/usr/bin/env python

"""
Service interface in the server side.

For the current impelmentation this is just a dummy one, and only serves to
maintain the proposed deployed code structure. In the later phase this will
be replaced by a WS implementation
"""

__author__ = 'Fugang Wang'
__version__ = '0.1'

import os, sys
import os.path
from getopt import gnu_getopt, GetoptError

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRTypes import IRCredential
import IRUtil
from IRDataAccess import AbstractImgStore
from IRDataAccess import AbstractImgMetaStore
from IRDataAccess import AbstractIRUserStore

if(IRUtil.getBackend()=="mongodb"):
    from IRDataAccessMongo import ImgStoreMongo
    from IRDataAccessMongo import ImgMetaStoreMongo
    from IRDataAccessMongo import IRUserStoreMongo
elif(IRUtil.getBackend()=="mysql"):
    from IRDataAccessMysql import ImgStoreMysql
    from IRDataAccessMysql import ImgMetaStoreMysql
    from IRDataAccessMysql import IRUserStoreMysql
else:
    from IRDataAccess import ImgStoreFS
    from IRDataAccess import ImgMetaStoreFS
    from IRDataAccess import IRUserStoreFS

import string

try:
    from futuregrid.utils import fgLog #This should the the final one
#To execute IRClient for tests
except:
    sys.path.append("/home/javi/imagerepo/ImageRepo/src/futuregrid/") #Directory where fg.py is
    from utils import fgLog


class IRService(object):

    def __init__(self):
        super(IRService, self).__init__()
        
        #Config in IRUtil
        self._backend=IRUtil.getBackend()
        self._address=IRUtil.getAddress()        
        self._fgirimgstore=IRUtil.getFgirimgstore()
        self._fgserverdir=IRUtil.getFgserverdir()
        
        #Setup log        
        self._log=fgLog.fgLog(IRUtil.getLogFile(),IRUtil.getLogLevel(),"Img Repo Server",False)
        
        if (self._backend == "mongodb"): 
            self.metaStore = ImgMetaStoreMongo(self._address,self._fgserverdir,self._log)
            self.imgStore = ImgStoreMongo(self._address,self._fgserverdir,self._log)            
            self.userStore = IRUserStoreMongo(self._address,self._fgserverdir,self._log)
        elif(self._backend == "mysql"):
            self.metaStore = ImgMetaStoreMysql(self._address,self._fgserverdir,self._log)
            self.imgStore = ImgStoreMysql(self._address,self._fgserverdir,self._log)            
            self.userStore = IRUserStoreMysql(self._address,self._fgserverdir,self._log)
        else:
            self.metaStore = ImgMetaStoreFS()
            self.imgStore = ImgStoreFS()            
            self.userStore = IRUserStoreFS()    
        

    def auth(self, userId):
        # to be implemented when integrating with the security framework
        return IRUtil.auth(userId, None)

    def query(self, userId, queryString):
        return self.metaStore.getItems(queryString)

    def get(self, userId, option, imgId):
        if (option == "img"):
            return self.imgStore.getItem(imgId)
        elif (option == "uri"):
            return self.imgStore.getItemUri(imgId)

    def put(self, userId, imgId, imgFile, attributeString):
        """
        Register the file in the database
        
        return imgId or 0 if something fails
        """  
        status=False      
        fileLocation = self._fgirimgstore + imgId
        if(os.path.isfile(fileLocation)):
            #parse attribute string and construct image metadata
            aMeta = self._createImgMeta(userId, imgId, attributeString,False)

            #print "meta data created:"
            #print aMeta        
                            
            #put image item in the image store        
            aImg = ImgEntry(imgId, aMeta, fileLocation)
            status=self.imgStore.addItem(aImg)
            #print status
            #put metadata into the image meta store
            if(IRUtil.getBackend()!="mongodb"):                
                #with MongoDB I put the metadata with the ImgEntry            
                status=self.metaStore.addItem(aMeta)
            #print status
            
        if(status):
            return aImg._imgId
        else:
            return 0
    
    def updateItem(self, userId, imgId, attributeString):
        """
        Update Image Repository
        
        keywords:
        option: img - update only the Image file
                meta - update only the Metadata
                all - update Image file and Metadata
        """
        success=False
        self._log.debug(str(attributeString))
        aMeta = self._createImgMeta(userId, imgId, attributeString,True)
        self._log.debug(str(aMeta))
        success=self.metaStore.updateItem(userId, imgId,aMeta)
                
        return success
        
    def remove(self, userId, imgId):
        return self.imgStore.removeItem(userId, imgId)
    
    def uploadValidator(self, userId, size):
        return self.userStore.uploadValidator(userId, size)
    
    def _createImgMeta(self, userId, imgId, attributeString, update):  ##We assume that values are check in client side
        """
        Create a ImgMeta object from a list of attributes
        
        keywords
        update: if True no default values are added
        """
        args = [''] * 10
        attributes = attributeString.split("|")
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
                            break
                    elif (key == "imgtype"):       
                        value=string.lower(value) 
                        if not (value in ImgMeta.ImgType):
                            print "Wrong value for ImgType, please use: "+str(ImgMeta.ImgType)
                            break
                    elif(key == "permission"):
                        value=string.lower(value)
                        if not (value in ImgMeta.Permission):
                            print "Wrong value for Permission, please use: "+str(ImgMeta.Permission)
                            break
                    elif (key == "imgstatus"):
                        value=string.lower(value)
                        if not (value in ImgMeta.ImgStatus):
                            print "Wrong value for ImgStatus, please use: "+str(ImgMeta.ImgStatus)
                            break
                    args[ImgMeta.metaArgsIdx[key]] = value
        if not update:        
            for x in range(len(args)):
                if args[x] == '':
                    args[x] = ImgMeta.argsDefault[x]
            #if x==4 or x==5 or x==8:
             #   args[x] = "'" + args[x] + "'"
            #print IRService.argsDefault[x], args[x]

        aMeta = ImgMeta(imgId,args[1],args[2],userId,args[4],
                        args[5],args[6],args[7],args[8],args[9])
        #print aMeta
        return aMeta
        
def usage():
    print "options:"
    print '''
        -h/--help: get help information
        -l/--auth: login/authentication
        -q/--list queryString: get list of images that meet the criteria
        -a/--setPermission imgId permissionString: set access permission
        -g/--get img/uri imgId: get a image or only the URI by id
        -p/--put imgFile attributeString: upload/register an image
        -m/--modify img/meta/all imgId attributeString: update information and/or image
        -r/--remove imgId: remove an image from the repository
        -i/--histimg imgId: get usage info of an image
        -u/--histuser userId: get usage info of a user
        --getBackend: provide the back-end configuration in the server side
          '''
          
def main():

    
    try:
        opts, args = gnu_getopt(sys.argv[1:],
                                "hlqagprium",
                                ["help",
                                 "auth",
                                 "list",
                                 "setPermission",
                                 "get",
                                 "put",
                                 "remove",
                                 "histimg",
                                 "histuser",
                                 "uploadValidator",
                                 "getuid",
                                 "getBackend",
                                 "modify"
                                 ])

    except GetoptError, err:
        print "%s" % err
        sys.exit(2)

    service = IRService()
               
    if(len(opts)==0):
        usage()
    
    for o, v in opts:
        #print o, v
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--auth"):
            #username = os.system("whoami")
            #service.auth(username)
            print service.auth("fuwang")
        elif o in ("-q", "--list"):            
            imgs = service.query(os.popen('whoami', 'r').read().strip(), args[0])
            #for key in imgs.keys():
            #    print imgs[key]
            print imgs
            #service.query("tstuser2", "imgId=fakeid4950877")
        elif o in ("-a", "--getPermission"): ##THIS is not used from client side. We call directly updateItem
            print service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], args[1])
        elif o in ("-g", "--get"):
            print service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            #print service.get(os.popen('whoami', 'r').read().strip(), "img", "4d4c2e6e577d70102a000000")
        elif o in ("-p", "--put"):
            print service.put(os.popen('whoami', 'r').read().strip(), args[0], args[1], args[2])
            
            #print service.put(os.popen('whoami', 'r').read().strip(), "id536785449", "/home/jav/tst3.iso","vmtype=kvm|imgtype=Nimbus|os=RHEL5|arch=i386|owner=tstuser1|description=this is a test description|tag=tsttag1, tsttag2|permission=private" )
            #print service.put(os.popen('whoami', 'r').read().strip(), "id536785449", "ttylinux1.img", "vmType=kvm|imgType=opennebula|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
        elif o in ("-r", "--remove"):
            print service.remove(os.popen('whoami', 'r').read().strip(),args[0])
            #print service.remove(os.popen('whoami', 'r').read().strip(), "4d4b0b8a577d700d2b000000")
        elif o in ("-i", "--histimg"):
            print "in image usage"
        elif o in ("-u", "--histuser"):
            print "in user usage"
        elif o in ("--uploadValidator"):
            #print service.uploadValidator(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            print service.uploadValidator("javi", 0)
        elif o in ("--getuid"):
            print IRUtil.getImgId()
        elif o in ("--getBackend"):
            print service._backend
            print service._fgirimgstore
        elif o in ("-m", "--modify"):
            print service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            #print service.updateItem(os.popen('whoami', 'r').read().strip(), "4d681d65577d703439000000", "vmtype=vmware|os=windows")
            
        else:
            assert False, "unhandled option"

if __name__ == "__main__":
    main()
