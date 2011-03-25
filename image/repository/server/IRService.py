#!/usr/bin/env python

"""
Service interface in the server side.

For the current impelmentation this is just a dummy one, and only serves to
maintain the proposed deployed code structure. In the later phase this will
be replaced by a WS implementation
"""

"""
TODO: move isAdmin,isPublic,ExistsandOwner control from IRDataAccess... to here

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

sys.path.append(os.getcwd())

try:
    from futuregrid.utils import fgLog #This should the the final one
#To execute IRClient for tests
except:
    sys.path.append(os.path.dirname(__file__)+"/../../../") #Directory where fg.py is
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
        
    def uploadValidator(self, userId, size):
        return self.userStore.uploadValidator(userId, size)
    
    def userAdd(self, userId, username):
        user=IRUser(username)
        return self.userStore.userAdd(userId, user)
    
    def userDel(self, userId, userIdtoDel):
        return self.userStore.userDel(userId, userIdtoDel)
    
    def userList(self, userId):
        return self.userStore.queryStore(userId, None)
    
    def setUserRole(self, userId, userIdtoModify, role):
        if (role in IRUser.Role):
            return self.userStore.setRole(userId, userIdtoModify, role)
        else:
            self._log.error("Role "+role+" is not valid")
            print "Role not valid. Valid roles are "+str(IRUser.Role)
            return False
          
    def setUserQuota(self, userId, userIdtoModify, quota):        
        return self.userStore.setQuota(userId, userIdtoModify, quota)
        
    def setUserStatus(self, userId, userIdtoModify, status):
        if (status in IRUser.Status):
            return self.userStore.setUserStatus(userId, userIdtoModify, status)
        else:
            self._log.error("Status "+status+" is not valid")
            print "Status not valid. Status available: "+str(IRUser.Status)
            return False
    
    def auth(self, userId):
        # to be implemented when integrating with the security framework
        return IRUtil.auth(userId, None)

    def query(self, userId, queryString):
        return self.metaStore.getItems(queryString)

    def get(self, userId, option, imgId):
        if (option == "img"):
            return self.imgStore.getItem(imgId, userId)
        elif (option == "uri"):
            return self.imgStore.getItemUri(imgId, userId)

    def put(self, userId, imgId, imgFile, attributeString, size):
        """
        Register the file in the database
        
        return imgId or 0 if something fails
        """  
        
        status=False      
        fileLocation = self._fgirimgstore + imgId
        if(os.path.isfile(fileLocation)):
            if (size > 0 ):
                #parse attribute string and construct image metadata
                aMeta = self._createImgMeta(userId, imgId, attributeString,False)
    
                #print "meta data created:"
                #print aMeta        
                                
                #put image item in the image store        
                aImg = ImgEntry(imgId, aMeta, fileLocation, size)                
                status=self.imgStore.addItem(aImg)
                                
                #put metadata into the image meta store
                if(IRUtil.getBackend()!="mongodb"):                
                    #with MongoDB I put the metadata with the ImgEntry            
                    status=self.metaStore.addItem(aMeta)
                
                #Add size to user
                status=self.userStore.updateDiskUsed(userId,size)
                
            else:
                self._log.error("File size must be higher than 0")
            
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
        size=[0] #Size is output parameter in the first call. 
        status=self.imgStore.removeItem(userId, imgId, size) 
        if(status):
            status=self.userStore.updateDiskUsed(userId, -(size[0]))
        return status
    
    def histImg(self,userId, imgId):
        return self.imgStore.histImg(imgId)
    
    def printHistImg(self,imgs):
        output={}
        output ['head'] = "    Image Id \t\t     Created Date \t Last Access \t    #Access \n"
        output ['head']=string.expandtabs(output ['head'],8)
        stradd=""
        for i in range(len(output['head'])):
            stradd+="-"    
        output ['head']+=stradd

        if(imgs!=None):
            for key in imgs.keys():
                spaces=""
                num=24-len(imgs[key]._imgId)
                if (num>0):                                                  
                    for i in range(num):
                        spaces+=" "
                        
                output[key]=imgs[key]._imgId+spaces+"  "+str(imgs[key]._createdDate)+"  "+ \
                        str(imgs[key]._lastAccess)+"    "+str(imgs[key]._accessCount)+"\n"
        
        return output
    
    def histuser(self,userId,userIdtoSearch):        
        output={}
        output ['head'] = "    User Id \t\t     Last Login \t   #Owned Images \n"
        output ['head']=string.expandtabs(output ['head'],8)
        stradd=""
        for i in range(len(output['head'])):
            stradd+="-"    
        output ['head']+=stradd
        
        user=self.userStore.queryStore(userIdtoSearch)                
                                
        
        
        
    
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
        -m/--modify imgId attributeString: update information
        -r/--remove imgId: remove an image from the repository
        -i/--histimg imgId: get usage info of an image
        -u/--histuser userId: get usage info of a user
        --getBackend: provide the back-end configuration in the server side
        --useradd <userId> : add user 
        --userdel <userId> : remove user
        --userlist : list of users
        --setquota <userId> <quota> :modify user quota
        --setrole  <userId> <role> : modify user role
        --setUserStatus <userId> <status> :modify user status
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
                                 "modify",
                                 "useradd",
                                 "userdel",
                                 "userlist",
                                 "setUserQuota",
                                 "setUserRole",
                                 "setUserStatus"
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
            print service.put(os.popen('whoami', 'r').read().strip(), args[0], args[1], args[2], int(args[3]))
            
            #print service.put(os.popen('whoami', 'r').read().strip(), "id536785449", "/home/jav/tst3.iso","vmtype=kvm|imgtype=Nimbus|os=RHEL5|arch=i386|owner=tstuser1|description=this is a test description|tag=tsttag1, tsttag2|permission=private" )
            #print service.put(os.popen('whoami', 'r').read().strip(), "id536785449", "ttylinux1.img", "vmType=kvm|imgType=opennebula|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
        elif o in ("-r", "--remove"):
            print service.remove(os.popen('whoami', 'r').read().strip(),args[0])
            #print service.remove(os.popen('whoami', 'r').read().strip(), "4d4b0b8a577d700d2b000000")
        elif o in ("-i", "--histimg"):
            imgs=service.histImg(os.popen('whoami', 'r').read().strip(),args[0])                 
                                   
            print service.printHistImg(imgs)

        elif o in ("-u", "--histuser"):
            print "in user usage"
        elif o in ("--uploadValidator"):
            print service.uploadValidator(os.popen('whoami', 'r').read().strip(), int(args[0]))
            #print service.uploadValidator("javi", 0)
        elif o in ("--getuid"):
            print IRUtil.getImgId()
        elif o in ("--getBackend"):
            print service._backend
            print service._fgirimgstore
        elif o in ("-m", "--modify"):
            print service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            #print service.updateItem(os.popen('whoami', 'r').read().strip(), "4d681d65577d703439000000", "vmtype=vmware|os=windows")
            
#This commands only can be used by users with Admin Role.
        elif o in ("--useradd"):  #args[0] is the username. It MUST be the same that the system user
            print service.userAdd(os.popen('whoami', 'r').read().strip(), args[0])
            
        elif o in ("--userdel"):
            print service.userDel(os.popen('whoami', 'r').read().strip(), args[0])
            
        elif o in ("--userlist"):
            print service.userList(os.popen('whoami', 'r').read().strip())
           
        elif o in ("--setUserQuota"):
            print service.setUserQuota(os.popen('whoami', 'r').read().strip(), args[0], int(args[1]))
            
        elif o in ("--setUserRole"):
            print service.setUserRole(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            
        elif o in ("--setUserStatus"):
            print service.setUserStatus(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            
        else:
            assert False, "unhandled option"

if __name__ == "__main__":
    main()
