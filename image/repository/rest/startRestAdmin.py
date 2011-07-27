#!/usr/bin/env python
"""
@author Michael Lewis
"""
import ConfigParser
import cherrypy
from cherrypy import _cpserver
from cherrypy import _cpwsgi_server
import os, sys
import cherrypy.lib.sessions
sys.path.append(os.path.dirname( os.path.realpath( __file__ ) )+'/../server/')
from IRService import IRService
from IRTypes import ImgMeta
from cherrypy.lib.static import serve_file
import textwrap
from random import randrange
import string

localDir = os.path.abspath(os.path.dirname(__file__))

httpconfig = os.path.join(localDir, 'httpconfig.conf')
httpsconfig = os.path.join(localDir, 'httpsconfig.conf')
certificate = os.path.join(localDir, 'server.crt')
privateKey = os.path.join(localDir, 'server.key')
adminName = None
config = None


class AdminRestService(object):
    
    writeMethodsExposed = True

    def __init__(self):
        super(AdminRestService, self).__init__()
        self.service=IRService()
        self.msg = None

    def results(self) :
        # adds the ending html tags and possible footer here                                      
        self.msg += "<br> <br> <a href = \"index\"> Return to the main page </a> "
        self.msg += "</body> </html>"
        return self.msg
    results.exposed = True

    def setMessage(self, message) :
        if self.msg == None :
            self.msg = "<html> <body> %s " % message
        else :
            self.msg += message
        return

    def index(self) :
        self.msg = None
        message = "<b> User Commands </b><br> "
        message +=  "<a href=\"help\"> Get help information </a> <br>"
        message +=  "<a href=\"list\"> Get list of images that meet the criteria </a> <br>"
        message +=  "<a href=\"setPermission\">  Set access permission </a> <br>"
        message +=  "<a href=\"get\"> Retrieve image or URI </a> <br>"
        message +=  "<a href=\"put\"> Upload/register an image </a> <br>"
        message +=  "<a href=\"modify\"> Modify an image </a> <br>"
        message +=  "<a href=\"remove\">  Remove an image from the repository </a> <br>"
        message +=  "<a href=\"histimg\"> Usage info of an image </a> <br>"
        message +=  "<a href=\"histuser\">  Usage info of a user </a> <br>"
        message +=  "<a href=\"useradd\"> Add user </a> <br>"
        message +=  "<a href=\"userdel\"> Remove user </a> <br>"
        message +=  "<a href=\"userlist\"> List of users </a> <br>"
        message +=  "<a href=\"setquota\"> Modify user quota </a> <br>"
        message +=  "<a href=\"setrole\"> Modify user role </a> <br>"
        message +=  "<a href=\"setUserStatus\"> Modify user status </a> <br>"
        self.setMessage(message)
        raise cherrypy.HTTPRedirect("results")
    index.exposed = True;

    def help (self) :
        self.msg = None
        """
        message =  " help: get help information. <br>"
        message += " list queryString: get list of images that meet the criteria<br>"
        message += " setPermission imgId permissionString: set access permission<br>"
        message += " get img/uri imgId: get a image or only the URI by id<br>"
        message += " put imgFile attributeString: upload/register an image<br>"
        message += " modify imgId attributeString: update information<br>"
        message += " remove imgId: remove an image from the repository<br>"
        message += " histimg imgId: get usage info of an image <br>"
        message += " histuser userId: get usage info of a user <br>"
        message += " useradd <userId> : add user <br>"
        message += " userdel <userId> : remove user <br>"
        message += " userlist : list of users <br>"
        message += " setquota <userId> <quota> :modify user quota <br>"
        message += " setrole  <userId> <role> : modify user role <br>"
        message += " setUserStatus <userId> <status> :modify user status"
        """
        message = "\n------------------------------------------------------------------<br>"
        message += "FutureGrid Image Repository Help <br>"
        message += "------------------------------------------------------------------<br>"
        message += '''        
        <b>help:</b> get help information<br>
        <b>auth:</b> login/authentication<br>
        <b>list</b> [queryString]: get list of images that meet the criteria<br>
        <b>setPermission</b> &lt;imgId> <permissionString>: set access permission<br>
        <b>get</b> &lt;img/uri&gt &lt;imgId&gt: get an image or only the URI<br>
        <b>put</b> &lt;imgFile&gt [attributeString]: upload/register an image<br>
        <b>modify</b> &lt;imgId&gt &lt;attributeString&gt: update Metadata   <br>
        <b>remove</b> &lt;imgId&gt: remove an image        <br>
        <b>histimg</b> [imgId]: get usage info of an image<br>
        <br>
        <b>Commands only for Admins</b> <br>
        <b>useradd</b> &lt;userId&gt: add user <br>
        <b>userdel</b> &lt;userId&gt: remove user<br>
        <b>userlist</b>: list of users<br>
        <b>setuserquota</b> &lt;userId&gt &lt;quota>: modify user quota<br>
        <b>setuserrole</b>  &lt;userId&gt &lt;role>: modify user role<br>
        <b>setuserstatus</b> &lt;userId&gt &lt;status>: modify user status<br>        
        <b>histuser</b> &lt;userId&gt: get usage info of a user<br>
              <br>
              <br>
    Notes:<br>
        <br>
        <b>attributeString</b> example (you do not need to provide all of them): <br>
            vmtype=xen | imgtype=opennebula | os=linux | arch=x86_64 | <br>
            description=my image | tag=tag1,tag2 | permission=public | <br>
            imgStatus=available.<br>
        <br>
        <b>queryString</b>: * or * where field=XX, field2=YY or <br>
             field1,field2 where field3=XX<br>
        <br>
        Some argument's values are controlled:<br>'''
        
        
        first = True
        for line in textwrap.wrap("<b>vmtype</b>= " + str(ImgMeta.VmType), 100):
            if first:
                message += "         %s<br>" % (line)
                first = False
            else:
                message += "           %s<br>" % (line)
        first = True
        for line in textwrap.wrap("<b>imgtype</b>= " + str(ImgMeta.ImgType), 100):
            if first:
                message += "         %s<br>" % (line)
                first = False
            else:
                message += "               %s<br>" % (line)
        first = True
        for line in textwrap.wrap("<b>imgStatus</b>= " + str(ImgMeta.ImgStatus), 100):
            if first:
                message += "         %s<br>" % (line)
                first = False
            else:
                message += "           %s<br>" % (line)
        first = True
        for line in textwrap.wrap("<b>Permission</b>= " + str(ImgMeta.Permission), 100):
            if first:
                message += "         %s<br>" % (line)
                first = False
            else:
                message += "           %s<br>" % (line)
        
        self.setMessage(message)
        raise cherrypy.HTTPRedirect("results")
    help.exposed = True;


    def actionList (self, queryString) :
        
        if (len(queryString) == 0):
            imgsList = self.service.query(adminName, "*")
        else:
            imgsList = self.service.query(adminName, queryString)

        if(len(imgsList) > 0):
            try:
                    self.msg = str(imgsList)
            except:
                self.msg = "list: Error:" + str(sys.exc_info()[0]) + "</br>"
                self._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
        else:
            self.msg = "No list of images returned"
        raise cherrypy.HTTPRedirect("results")
    actionList.exposed = True

    def list (self) :
        self.msg = """ <form method=get action=actionList>                                                                                                      Query string: <input type=string name=queryString> <br>                                                                                        <input type=submit> </form> """
        return self.msg;
    list.exposed = True

    def actionSetPermission (self, imgId = None, permissionString = None) :
        self.msg = None
        if (len(permissionString) > 0):
            
            status = self.service.updateItem(adminName, imgId, permissionString)
            if(status == True):
                self.setMessage("Permission of img " + imgId + " updated")
            else:
                self.setMessage("The permission has not been changed.")
        else :
            self.setMessage("Permission string length not set")

        raise cherrypy.HTTPRedirect("results")
    actionSetPermission.exposed = True;

    def setPermission (self):
      message = """ <form method=get action=actionSetPermission>
        Image Id: <input type=string name=imgId> <br>                                                                                 
        Permission string: <input type=string name=permissionString> <br>                                                              
        <input type=submit> </form> """
      return message
    setPermission.exposed = True;


    def actionGet(self, option, imgId):
        self.msg = None
        if(len(imgId) > 0 and len(option) > 0):
            
            filepath = self.service.get(adminName, option, imgId)
            if (filepath != None):
                if (len(imgId) > 0 ) :
                    self.setMessage("Downloading img to %s " % filepath.__str__())
                else :
                    self.setMessage("URL:  %s " % filepath.__str__())
            else:
                self.setMessage("Cannot get access to the image with imgId = "+imgId)
                raise cherrypy.HTTPRedirect("results")
        else :
            self.setMessage("The image Id or option is empty! Please input both the image Id and option")
            raise cherrypy.HTTPRedirect("results")

        serve_file(filepath, "application/x-download", "attachment")
        raise cherrypy.HTTPRedirect("results")

    actionGet.exposed = True

    def get (self):
        return """                                                                                                                                           <html><body>                                                                                                                                      <form method=get action=actionGet>                                                                                                                    Image Id: <input type=string name=imgId> <br>                                                                                                     Option ('img' or 'uri'): <input type=string name=option> <br>                                                                                     <input type=submit>
                                       </form> 
                         </body></html>
       """
    get.exposed = True;

    def actionPut (self, userId = None, imageFileName = None, attributeString = None) :
        # retrieve the data                                                                                                                       
        size = 0
        self.fromSite = "actionPut"
        self.msg = None
        
        while 1:
            data = imageFileName.file.read(1024 * 8) # Read blocks of 8KB at a time                                                               
            size += len(data)
            if not data: break
        
        
        
        #check metadata
        correct=self.checkMeta(attributeString)
        if correct:
            #check quota
            isPermitted = self.service.uploadValidator(userId, size)
                  
            
            if (isPermitted == True):
                imgId=self.getImgId() #this is needed when we are not using mongodb as image storage backend
                imageId = self.service.put(adminName, imgId, imageFileName,attributeString,size)
                
                self.msg = "Image %s successfully uploaded." % imageFileName.filename
                self.msg += " Image size %s " % size
                self.msg += "<br> The image ID is %s " % imageId
            elif (isPermitted.strip() == "NoUser"):
                self.msg = "the image has NOT been uploaded<br>"
                self.msg = "The User does not exist"                        
            elif (isPermitted.strip() == "NoActive"):
                self.msg = "The image has NOT been uploaded<br>"
                self.msg = "The User is not active"
            else:
                self.msg = "The image has NOT been uploaded"
                self.msg = "The file exceed the quota"
        else:
            self.msg = "The image has NOT been uploaded. Please, verify that the metadata string is valid"        
        raise cherrypy.HTTPRedirect("results")
    actionPut.exposed = True

    def put (self) :
       return """                                                                                                                                             <html><body>                                                                                                                                      <form method=post action=actionPut enctype="multipart/form-data">                                                                                     Upload a file: <input type=file name=imageFileName><br>                                                                                           User Id: <input type=string name=userId> <br>                                                                                                     attributeString: <input type=string name=attributeString> <br>                                                                                    <input type=submit>                                                                                                                           </form>                                                                                                </body></html>      
        """
    put.exposed = True;


    def getImgId(self):
        imgId = str(randrange(999999999999999999999999))
        return imgId

    ############################################################
    # checkMeta
    ############################################################
    def checkMeta(self, attributeString):        
        attributes = attributeString.split("|")
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
                            print "Wrong value for VmType, please use: " + str(ImgMeta.VmType)
                            correct = False
                            break
                    elif (key == "imgtype"):       
                        value = string.lower(value) 
                        if not (value in ImgMeta.ImgType):
                            print "Wrong value for ImgType, please use: " + str(ImgMeta.ImgType)
                            correct = False
                            break
                    elif(key == "permission"):
                        value = string.lower(value)
                        if not (value in ImgMeta.Permission):
                            print "Wrong value for Permission, please use: " + str(ImgMeta.Permission)
                            correct = False
                            break
                    elif (key == "imgstatus"):
                        value = string.lower(value)
                        if not (value in ImgMeta.ImgStatus):
                            print "Wrong value for ImgStatus, please use: " + str(ImgMeta.ImgStatus)
                            correct = False
                            break                
                
        return correct

    def actionModify (self, imgId = None, attributeString = None):
        fname = sys._getframe().f_code.co_name
        self.msg = None
        if(len(imgId) > 0):
            
            success = self.service.updateItem(adminName, imgId, attributeString)
        if (success):
            self.msg = "The image %s was successfully updated" % imgId
            self.msg += " User name: < %s > " % adminName
        else:
            self.msg = "Error in the update.<br>Please verify that you are the owner or that you introduced the correct arguments"
        raise cherrypy.HTTPRedirect("results")
    actionModify.exposed = writeMethodsExposed;

    def modify (self, imgId = None, attributeString = None):
        self.msg = """ <form method=get action=actionModify>                                                                                                      Image Id: <input type=string name=imgId> <br>                                                                                                     Atribute String: <input type=string name=attributeString> <br>                                                                                   <input type=submit> </form> """
        return self.msg;
    modify.exposed = writeMethodsExposed;


    def actionRemove (self, imgId = None):
        fname = sys._getframe().f_code.co_name
        
        status = self.service.remove(adminName, imgId)
        self.msg = None
        if (status == True):
            self.msg = "The image with imgId=" + imgId + " has been removed"
        else:
            self.msg = "The image with imgId=" + imgId + " has NOT been removed.</br>Please verify the imgId and if you are the image owner"
        raise cherrypy.HTTPRedirect("results")
    actionRemove.exposed = True;

    def remove (self):
        self.msg = """ <form method=get action=actionRemove>                                                                                                      Image Id: <input type=string name=imgId> <br>                                                                                                     <input type=submit> </form> """
        return self.msg
    remove.exposed = True

    def actionHistImage (self, imgId):
        
        fname = sys._getframe().f_code.co_name
        self.msg = None
        if(len(imgId) > 0):
            imgsList = self.service.histImg(adminName, imgId)
        else:
            imgsList = self.service.histImg(adminName, "None")

        try:
            imgs = self.service.printHistImg(imgsList)
            self.msg = imgs['head']
            for key in imgs.keys():
                if key != 'head':
                    self.msg = self.msg + imgs[key] + "\n"
        except:
            self.msg = "histimg: Error:" + str(sys.exc_info()[0]) + "\n"
            self._log.error("histimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
        raise cherrypy.HTTPRedirect("results")
    actionHistImage.exposed = True;

    def histimg (self):
        self.msg = """ <form method=get action=actionHistImage>                                                                                                   Image Id: <input type=string name=imgId> <br>                                                                                                     <input type=submit> </form> """
        return self.msg;
    histimg.exposed = True;



    def actionHistUser (self, userId):
        fname = sys._getframe().f_code.co_name
        
        self.msg = None
        if (len(userId) > 0):
            userList = self.service.histUser(adminName, userId)
        else:
            userList = self.service.histUser(adminName, "None")

        try:
            users = userList
            self.msg = users['head']
            self.msg = "<br>"
            for key in users.keys():
                if key != 'head':
                    self.msg = self.msg + users[key]
        except:
            self.msg = "histuser: Error:" + str(sys.exc_info()[0]) + "\n"
            self._log.error("histuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
        raise cherrypy.HTTPRedirect("results")
    actionHistUser.exposed = True;

    def histuser (self) :
        self.msg = """ <form method=get action=actionHistUser>                                                                                                     User Id: <input type=string name=userId> <br>                                                                                                     <input type=submit> </form> """
        return self.msg
    histuser.exposed = True;


    def actionUserAdd (self, userId):
        
        status = self.service.userAdd(adminName, userId)
        if(status):
            self.msg = "User created successfully.</br>"
            self.msg = self.msg + "Remember that you still need to activate this user (see setuserstatus command)</br>"
        else:
            self.msg = "The user has not been created.</br>"
            self.msg = self.msg + "Please verify that you are admin and that the username does not exist </br>"
        raise cherrypy.HTTPRedirect("results")
    actionUserAdd.exposed = True

    def useradd (self, userId = None) :
        self.msg = """ <form method=get action=actionUserAdd>                                                                                       Add User Id: <input type=string name=userId> <br>                                                                                   <input type=submit> </form> """
        return self.msg
    useradd.exposed = True;


    def actionUserDel(self,userId = None) :
        
        status = self.service.userDel(adminName,userId)
        self.msg = None
        if(status == True):
            self.msg = "User deleted successfully."
        else:
            self.msg = "The user has not been deleted.</br>"
            self.msg = self.msg + "Please verify that you are admin and that the username exists \n"
        raise cherrypy.HTTPRedirect("results")
    actionUserDel.exposed = True

    def userdel (self, userId = None) :
        self.msg = """ <form method=get action=actionUserDel>                                                                                       User Id: <input type=string name=userId> <br>                                                                                       <input type=submit> </form> """
        return self.msg
    userdel.exposed = True

    def userlist(self):
        fname = sys._getframe().f_code.co_name
        
        self.msg = None

        if (adminName != None) :
            usersList = self.service.userList(adminName)
            if (len(usersList) > 0):
                try:
                    self.msg = "<br>" + str(len(usersList)) + " users found </br>"
                    self.msg = self.msg + "<br> UserId Cred fsCap fsUsed lastLogin status role ownedImgs </br>"
                    for user in usersList.items():
                        self.msg = self.msg + "<br>" + str(user[1])[1:len(str(user[1]))-1]
                        self.msg = self.msg + "</br>"
                except:
                    self.msg = "userlist: Error:" + str(sys.exc_info()[0]) + "\n"
                    self.msg = self.msg + "userlist: Error interpreting the list of users from Image Repository\
" + str(sys.exc_info()[0])
            else:
                self.msg =  "No list of users returned. \n" + \
                        "Please verify that you are admin \n"
        else :
            self.msg = "<br> Error admin name is not set" 

        raise cherrypy.HTTPRedirect("results")
    userlist.exposed = True;

    def actionQuota (self,userId, quota) :
        
        status = self.service.setUserQuota(adminName,userId,quota)
        if(status == True):
            self.msg = "Quota changed successfully."
        else:
            self.msg = "The user quota has not been changed.</br>"
            self.msg = self.msg + "Please verify that you are admin and that the username exists"
        return self.msg
    actionQuota.exposed = True

    def setquota (self) :
        self.msg = """ <form method=get action=actionQuota>                                                                                     User Id: <input type=string name=userId> <br>                                                                                       Quota : <input type=string name=quota> <br>                                                                                         <input type=submit> </form> """
        return self.msg
    setquota.exposed = True;

    def actionUserRole (self,userId, role) :
        
        # User name based on admin file
        status = self.service.setUserRole(adminName,userId, role) 
        
        self.msg = None
        if (status == True):
            self.msg = "Role changed successfully."
        else:
            self.msg =  "The user role has not been changed </br>"
            self.msg = self.msg + "Please verify that you are admin and that the username exists"
        raise cherrypy.HTTPRedirect("results")
    actionUserRole.exposed = True


    def setrole (self) :
        fname = sys._getframe().f_code.co_name
        self.msg = """ <form method=post action=actionUserRole>
                User To Modify : <input type=string name=userId> <br>
                Role : <input type=string name=role> <br>
                <input type=submit> </form> """
        return self.msg;
    setrole.exposed = True;


    def actionUserStatus (self,userId, status) :
        
        status = self.service.setUserStatus(adminName,userId,status)
        self.msg = None
        if(status == True):
            self.msg = "Status changed successfully."
        else:
            self.msg = "The user status has not been changed.</br>"
            self.msg = self.msg + "Please verify that you are admin and that the username exists \n"
        raise cherrypy.HTTPRedirect("results")
    actionUserStatus.exposed = True

    def setuserstatus (self) :
        fname = sys._getframe().f_code.co_name

        self.msg = """ <form method=post action=actionUserStatus>                                                                                   User Id: <input type=string name=userId> <br>                                                                                       Status : <input type=string name=status> <br>                                                                                       <input type=submit> </form> """
        return self.msg;
    setuserstatus.exposed = True;



def configSectionMap(section) :
    dict1 = {}
    options = cherrypy.config.options(section)
    dict1[option] = cherrypy.config.get(section,option)
    for options in options :
        try:
            dict1[option] = cherrypy.config.get(section,option)
            if dict1[option] == -1 :
                print("Skip: %s " % option)
        except:
            print("Exeption on %s " % option)
            dict1[option] = None
    return dict1

if __name__ == '__main__':

    # Site configuration
    cherrypy.config.update(httpsconfig)
    cherrypy.tree.mount(AdminRestService(),'/adminRest',config='adminConfig.conf')
    ip = cherrypy.config.get("server.socket_host")
    port = cherrypy.config.get("server.socket_port")
    cherrypy.config.update('adminConfig.conf')
    adminName = cherrypy.config.get("admin_name")
    print("Admin name: %s" % adminName) 
#    adminName = cherrypy.config.get("Admin")['username']
#    adminName = configSectionMap("Admin")['username']



    secure_server = _cpwsgi_server.CPWSGIServer()
    secure_server.bind_addr = (ip, port)
    secure_server.ssl_certificate = certificate
    secure_server.ssl_private_key = privateKey

    adapter = _cpserver.ServerAdapter(cherrypy.engine, secure_server, secure_server.bind_addr)
    adapter.subscribe()
    cherrypy.quickstart(AdminRestService(), config=httpconfig)
 

else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(AdminRestService, config=configurationFile)
