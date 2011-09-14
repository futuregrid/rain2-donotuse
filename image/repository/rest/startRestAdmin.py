#!/usr/bin/env python

## @author Michael Lewis, Fugang Wang, Javier Diaz
# The functions in this class represent the REST interface
# which then delegates the http input values to the Server (IRService) module. 

import ConfigParser
import cherrypy
from cherrypy import _cpserver
from cherrypy import _cpwsgi_server
import os, sys
import cherrypy.lib.sessions
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/../server/')

try:
    from ..server import IRUtil # 3 dir levels up
    from ..server.IRService import IRService
    from ..server.IRTypes import ImgMeta, IRUser
    from ....utils.FGTypes import FGCredential
except:
    sys.path = [os.path.dirname(os.path.abspath(__file__)) + "/../server"] + [os.path.dirname(os.path.abspath(__file__)) + "/../../../utils"] + sys.path
    from IRService import IRService
    from IRServerConf import IRServerConf
    import IRUtil
    from IRTypes import ImgMeta, IRUser
    from FGTypes import FGCredential

from cherrypy.lib.static import serve_file
import textwrap
from random import randrange
import string

localDir = os.path.abspath(os.path.dirname(__file__))

#httpconfig = os.path.join(localDir, 'httpconfig.conf')
#httpsconfig = os.path.join(localDir, 'httpsconfig.conf')
#certificate = os.path.join(localDir, 'server.crt')
#privateKey = os.path.join(localDir, 'server.key')
#adminName = None
#config = None

class AdminRestService(object):

    writeMethodsExposed = True

    ## Constructor call: instantiate IRservice, retrieve logger
    def __init__(self):
        super(AdminRestService, self).__init__()
        self.service = IRService()
        self.msg = ""
        self._log = self.service.getLog()
        self.provider = "ldappass"

    ## Returning the html output from a Rest call
    def results(self) :
        # adds the ending html tags and possible footer here                                      
        self.msg += "<br> <br> <a href = \"index\"> Return to the main page </a> "
        self.msg += "</body> </html>"
        return self.msg
    results.exposed = True

    ## Adding to the HTML output from a REST call
    def setMessage(self, message) :
        if self.msg == None :
            self.msg = "<html> <body> %s " % message
        else :
            self.msg += message
        return

    ## HTML Listing of all the REST functions 
    def index(self) :
        self.msg = ""
        message = "<b> User Commands </b><br> "
        message += "<a href=\"help\"> Get help information </a> <br>"
        message += "<a href=\"list\"> Get list of images that meet the criteria </a> <br>"
        message += "<a href=\"setPermission\">  Set access permission </a> <br>"
        message += "<a href=\"get\"> Retrieve image or URI </a> <br>"
        message += "<a href=\"put\"> Upload/register an image </a> <br>"
        message += "<a href=\"modify\"> Modify an image </a> <br>"
        message += "<a href=\"remove\">  Remove an image from the repository </a> <br>"
        message += "<a href=\"histimg\"> Usage info of an image </a> <br>"
        message += " <br>"
        message += "<b>Commands only for Admins</b> <br>"
        message += "<a href=\"histuser\">  Usage info of a user </a> <br>"
        message += "<a href=\"useradd\"> Add user </a> <br>"
        message += "<a href=\"userdel\"> Remove user </a> <br>"
        message += "<a href=\"userlist\"> List of users </a> <br>"
        message += "<a href=\"setquota\"> Modify user quota </a> <br>"
        message += "<a href=\"setrole\"> Modify user role </a> <br>"
        message += "<a href=\"setuserstatus\"> Modify user status </a> <br>"
        self.setMessage(message)
        raise cherrypy.HTTPRedirect("results")
    index.exposed = True;

    ## Document to the user, what are the REST services and what they do.
    def help (self) :
        self.msg = ""
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
        for line in textwrap.wrap("<b>User Role</b>= " + str(IRUser.Role), 100):
            if first:
                message += "         %s<br>" % (line)
                first = False
            else:
                message += "           %s<br>" % (line)
        for line in textwrap.wrap("<b>User Status</b>= " + str(IRUser.Status), 100):
            if first:
                message += "         %s<br>" % (line)
                first = False
            else:
                message += "           %s<br>" % (line)
        self.setMessage(message)
        raise cherrypy.HTTPRedirect("results")
    help.exposed = True;

    ## Callback function to the list service
    # @param userId user id to represent list
    # @param userCred user password in MD5 digested format
    # @param queryString (not required) string to help narrow down the query 
    def actionList (self, userId, userCred, queryString):
        userId = userId.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            if (len(queryString) == 0):
                imgsList = self.service.query(userId.strip(), "*")
            else:
                imgsList = self.service.query(userId.strip(), queryString.strip())

            if(len(imgsList) > 0):
                try:
                        self.msg = str(imgsList)
                except:
                    self.msg = "list: Error:" + str(sys.exc_info()[0]) + "</br>"
                    self._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
            else:
                self.msg = "No list of images returned"
        else:
            self.msg = "Please specify valid username/password"
        raise cherrypy.HTTPRedirect("results")
    actionList.exposed = True

    ## list service
    def list (self) :
        self.msg = """ <form method=get action=actionList> 
        Username: <input type=string name=userId><br>
        Password: <input type=password name=userCred><br>
        Query string: <input type=string name=queryString> <br> 
        <input type=submit> </form> """
        return self.msg;
    list.exposed = True

    ## Callback function to the set permission service
    # @param userId login/account name of the Rest user to invoke this service
    # @param imgId id of the uploaded Rest image for the specified user.
    # @param userCred user password in MD5 digested format
    # @permissionString permission string
    def actionSetPermission (self, userId, userCred, imgId = None, permissionString = None) :
        self.msg = ""
        userId = userId.strip()
        imgId = imgId.strip()
        permstring = permissionString.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            if (len(permissionString) > 0 and len(imgId) > 0):
                permstring = "permission=" + permissionString
                status = self.service.updateItem(userId, imgId, permstring)
                if(status == True):
                    self.setMessage("Permission of img " + imgId + " updated")
                else:
                    self.setMessage("The permission has not been changed.")
            else :
                self.setMessage("Please verify the input information, you need to include userId, permission and imgId")
    
            raise cherrypy.HTTPRedirect("results")
    actionSetPermission.exposed = True;

    ## Set permission service
    def setPermission (self):
        message = """ <form method=get action=actionSetPermission>
        UserId: <input type=string name=userId> <br>
        Image Id: <input type=string name=imgId> <br>                                                                                 
        Permission string: <input type=string name=permissionString> <br>                                                              
        <input type=submit> </form> """
        return message
    setPermission.exposed = True;

    ## Callback function to the get service. 
    # @param userId login/account name of the Rest user to invoke this service
    # @param userCred user password in MD5 digested format
    # @param option specify exactly 'img' or 'uri' 
    # @param imgId id of the uploaded Rest image for a specified user.
    def actionGet(self, userId, userCred, option, imgId):
        self.msg = ""

        option = option.strip()
        imgId = imgId.strip()
        userId = userId.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            if(len(imgId) > 0 and len(option) > 0):    
                filepath = self.service.get(userId, option, imgId)
                if (filepath != None):
                    if (len(imgId) > 0) :
                        self.setMessage("Downloading img to %s " % filepath.__str__())
                    else :
                        self.setMessage("URL:  %s " % filepath.__str__())
                else:
                    self.setMessage("Cannot get access to the image with imgId = " + imgId)
                    raise cherrypy.HTTPRedirect("results")
            else :
                self.setMessage("The image Id or option is empty! Please input both the image Id and option")
                raise cherrypy.HTTPRedirect("results")
    
            return serve_file(filepath, "application/x-download", "attachment")
        raise cherrypy.HTTPRedirect("results")

    actionGet.exposed = True

    ## get Rest service. Retrieves image
    def get (self):
        return """<html><body><form method=get action=actionGet>
         Username: <input type=string name=userId><br>
         Password: <input type=password name=userCred><br>
         Image Id: <input type=string name=imgId> <br>
         Option ('img' or 'uri'): <input type=string name=option> <br> 
         <input type=submit> </form> </body></html>
       """
    get.exposed = True;

    ## Callback function to the put service
    # @param userId login/account name of the Rest user to invoke this service
    # @param userCred user password in MD5 digested format
    # @param imageFileName request based object file representing the user file name
    # @param attributeString attribute string
    def actionPut (self, userId, userCred, imageFileName = None, attributeString = None):

        # retrieve the data                                                                                                                       
        size = 0
        self.fromSite = "actionPut"
        self.msg = ""
        userId = userId.strip()
        attributeString = attributeString.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            while 1:
                data = imageFileName.file.read(1024 * 8) # Read blocks of 8KB at a time                                                               
                size += len(data)
                if not data: break
    
    
            #check metadata
            correct = self.checkMeta(attributeString)
            if correct:
                #check quota
                isPermitted = self.service.uploadValidator(userId.strip(), size)
    
    
                if (isPermitted == True):
                    imgId = self.service.genImgId() #this is needed when we are not using mongodb as image storage backend
                    if imgId != None:
                        extension = os.path.splitext(imageFileName.filename)[1]
                        imageId = self.service.put(userId, imgId, imageFileName, attributeString, size, extension)
    
                        self.msg = "Image %s successfully uploaded." % imageFileName.filename
                        self.msg += " Image size %s " % size
                        self.msg += " Image extension is %s " % extension
                        self.msg += "<br> The image ID is %s " % imageId
                    else:
                        self.msg += "Error generating the imgId"
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
                self.msg += "The image has NOT been uploaded. Please, verify that the metadata string is valid"
        raise cherrypy.HTTPRedirect("results")
    actionPut.exposed = True

    ## put Rest service. Download an image to the Rest service.
    def put (self) :
        return """<html><body><form method=post action=actionPut enctype="multipart/form-data">
       Upload a file: <input type=file name=imageFileName><br>
       Username: <input type=string name=userId><br>
       Password: <input type=password name=userCred><br>
       attributeString: <input type=string name=attributeString> <br>
       <input type=submit></form></body></html>      
        """
    put.exposed = True;


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
                            self.msg = "Wrong value for VmType, please use: " + str(ImgMeta.VmType) + "<br>"
                            correct = False
                            break
                    elif (key == "imgtype"):
                        value = string.lower(value)
                        if not (value in ImgMeta.ImgType):
                            self.msg = "Wrong value for ImgType, please use: " + str(ImgMeta.ImgType) + "<br>"
                            correct = False
                            break
                    elif(key == "permission"):
                        value = string.lower(value)
                        if not (value in ImgMeta.Permission):
                            self.msg = "Wrong value for Permission, please use: " + str(ImgMeta.Permission) + "<br>"
                            correct = False
                            break
                    elif (key == "imgstatus"):
                        value = string.lower(value)
                        if not (value in ImgMeta.ImgStatus):
                            self.msg = "Wrong value for ImgStatus, please use: " + str(ImgMeta.ImgStatus) + "<br>"
                            correct = False
                            break

        return correct

    ## Callback function to the modify service. Modifies the imageid based on attribute string
    # @param userId login/account name of the Rest user to invoke this service
    # @param userCred user password in MD5 digested format
    # @param imgId id of the uploaded Rest image for the specified user.
    # @param attributeString
    def actionModify (self, userId, userCred, imgId = None, attributeString = None):
        self.msg = ""
        success = False
        userId = userId.strip()
        imgId = imgId.strip()
        attributeString = attributeString.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            if(len(imgId) > 0 and len(attributeString) > 0):
                if self.checkMeta(attributeString):
                    success = self.service.updateItem(userId, imgId, attributeString)
    
            if (success):
                self.msg = "The image %s was successfully updated" % imgId
            else:
                self.msg += "Error in the update.<br>Please verify that you are the owner or that you introduced the correct arguments"
        raise cherrypy.HTTPRedirect("results")
    actionModify.exposed = writeMethodsExposed;

    # modify Rest service
    def modify (self, imgId = None, attributeString = None):
        self.msg = """ <form method=get action=actionModify>
        User Id: <input type=string name=userId> <br>
        Password: <input type=password name=userCred><br>
        Image Id: <input type=string name=imgId> <br>
        Atribute String: <input type=string name=attributeString> <br> 
         <input type=submit> </form> """
        return self.msg;
    modify.exposed = writeMethodsExposed;


    ## Callback function to the remove Rest service
    # @param userId login/account name of the Rest user to invoke this service
    # @param userCred user password in MD5 digested format
    # @param imgId id of the uploaded Rest image for the specified user.
    def actionRemove (self, userId, userCred, imgId = None):
        userId = userId.strip()
        imgId = imgId.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            status = self.service.remove(userId, imgId)
            self.msg = ""
            if (status == True):
                self.msg = "The image with imgId=" + imgId + " has been removed"
            else:
                self.msg = "The image with imgId=" + imgId + " has NOT been removed.</br>Please verify the imgId and if you are the image owner"
        raise cherrypy.HTTPRedirect("results")
    actionRemove.exposed = True;

    ## Remove Rest service.
    # Removes image based on specified image id and user id
    def remove (self):
        self.msg = """ <form method=get action=actionRemove>
        User Id: <input type=string name=userId> <br>
        Password: <input type=password name=userCred><br>
        Image Id: <input type=string name=imgId> <br>
        <input type=submit> </form> """
        return self.msg
    remove.exposed = True

    ## Callback function to the histimage service
    # @param userId login/account name of the Rest user to invoke this service
    # @param userCred user password in MD5 digested format
    # @param imgId id of the uploaded Rest image for the specified user.
    def actionHistImage (self, userId, userCred, imgId):
        self.msg = ""
        userId = userId.strip()
        imgId = imgId.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(userId) > 0 and self.service.auth(userId, userCred, self.provider)):
            if(len(imgId) > 0):
                imgsList = self.service.histImg(userId, imgId)
            else:
                imgsList = self.service.histImg(userId, "None")

            try:
                imgs = self.service.printHistImg(imgsList)
                self.msg = string.replace(imgs['head'], "\n", "<br>")
                self.msg += "<br>"
                for key in imgs.keys():
                    if key != 'head':
                        self.msg = self.msg + imgs[key] + "<br>"
            except:
                self.msg = "histimg: Error:" + str(sys.exc_info()) + "\n"
                self._log.error("histimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
        else:
            self.msg = "Please introduce your userId"
        raise cherrypy.HTTPRedirect("results")
    actionHistImage.exposed = True;

    ## histimg Rest service. 
    def histimg (self):
        self.msg = """ <form method=get action=actionHistImage>
        User Id: <input type=string name=userId> <br>
        Password: <input type=password name=userCred><br>
        Image Id: <input type=string name=imgId> <br>
        <input type=submit> </form> """
        return self.msg;
    histimg.exposed = True;


    ## Callback function to the histuser service
    # @param adminId login/account name of the admin user to invoke this service
    # @param adminCred user password in MD5 digested format
    # @param userCred user password in MD5 digested format
    # @param userIdtoSearch user id that is the subject of the search
    def actionHistUser (self, adminId, adminCred, userIdtoSearch):
        self.msg = ""
        adminId = adminId.strip()
        userIdtoSearch = userIdtoSearch.strip()
        #userCred = IRCredential("ldappass", userCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            if (len(userIdtoSearch) > 0):
                userList = self.service.histUser(adminId, userIdtoSearch)
            else:
                userList = self.service.histUser(adminId, "None")

            try:
                users = userList
                self.msg = string.replace(users['head'], "\n", "<br>")
                self.msg += "<br>"
                for key in users.keys():
                    if key != 'head':
                        self.msg = self.msg + users[key] + "<br>"
            except:
                self.msg = "histuser: Error:" + str(sys.exc_info()) + "<br>"
                self._log.error("histuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
        else:
            self.msg = "Please introduce your userId"

        raise cherrypy.HTTPRedirect("results")
    actionHistUser.exposed = True;

    ## histuser Rest service
    def histuser (self) :
        self.msg = """ <form method=get action=actionHistUser>
        Admin Username: <input type=string name=adminId><br>
        Admin Password: <input type=password name=adminCred><br>
        UserId to Search: <input type=string name=userIdtoSearch> <br>
        <input type=submit> </form> """
        return self.msg
    histuser.exposed = True;


    ## Callback function to the userAdd Rest service
    # @param adminId login/account name of the admin user to invoke this service
    # @param adminCred user password in MD5 digested format
    # @param userCred user password in MD5 digested format
    # @param userIdtoAdd user id that is the subject of the add in the datbase
    def actionUserAdd (self, adminId, adminCred, userIdtoAdd):
        self.msg = ""
        adminId = adminId.strip()
        userIdtoAdd = userIdtoAdd.strip()
        #adminCred = IRCredential("ldappass", adminCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            if (len(userIdtoAdd) > 0):
                status = self.service.userAdd(adminId, userIdtoAdd)
                if(status):
                    self.msg = "User created successfully.</br>"
                    self.msg = self.msg + "Remember that you still need to activate this user (see setuserstatus command)</br>"
                else:
                    self.msg = "The user has not been created.</br>"
                    self.msg = self.msg + "Please verify that you are admin and that the username does not exist </br>"
            else:
                self.msg = "Please introduce your userId and the userId to add"
        raise cherrypy.HTTPRedirect("results")
    actionUserAdd.exposed = True

    ## useradd Rest service.  Adding a new user to the database
    def useradd (self, userId = None) :
        self.msg = """ <form method=get action=actionUserAdd>
        Admin Username: <input type=string name=adminId><br>
        Admin Password: <input type=password name=adminCred><br>
        UserId to Add: <input type=string name=userIdtoAdd> <br>
        <input type=submit> </form> """
        return self.msg
    useradd.exposed = True;

    ## Callback function to the userdel Rest service
    # @param adminId login/account name of the Rest user to invoke this service
    # @param adminCred user password in MD5 digested format
    # @param userIdtoDel user id that is the subject of the delete in the datbase
    def actionUserDel(self, adminId, adminCred, userIdtoDel):
        adminId = adminId.strip()
        userIdtoDel = userIdtoDel.strip()
        #adminCred = IRCredential("ldappass", adminCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            if (len(userIdtoDel) > 0):
                status = self.service.userDel(adminId, userIdtoDel)
                self.msg = ""
                if(status == True):
                    self.msg = "User deleted successfully."
                else:
                    self.msg = "The user has not been deleted.</br>"
                    self.msg = self.msg + "Please verify that you are admin and that the username exists \n"
            else:
                self.msg = "Please introduce your userId and the userId to del"
        raise cherrypy.HTTPRedirect("results")
    actionUserDel.exposed = True

    ## userdel Rest service. Removing a user from the database.
    def userdel (self, userId = None) :
        self.msg = """ <form method=get action=actionUserDel>
        Admin Username: <input type=string name=adminId><br>
        Admin Password: <input type=password name=adminCred><br>
        UserId to Delete: <input type=string name=userIdtoDel> <br>
        <input type=submit> </form> """
        return self.msg
    userdel.exposed = True

    ## Callback function to the userlist Rest service
    # @param adminId login/account name of the Rest user to invoke this service
    # @param adminCred user password in MD5 digested format
    def actionUserList(self, adminId, adminCred):
        self.msg = ""
        adminId = adminId.strip()
        #adminCred = IRCredential("ldappass", adminCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            usersList = self.service.userList(adminId)
            if (usersList != None):
                try:
                    self.msg = "<br>" + str(len(usersList)) + " users found </br>"
                    self.msg = self.msg + "<br> UserId Cred fsCap fsUsed lastLogin status role ownedImgs </br>"
                    for user in usersList.items():
                        self.msg = self.msg + "<br>" + str(user[1])[1:len(str(user[1])) - 1]
                        self.msg = self.msg + "</br>"
                except:
                    self.msg = "userlist: Error:" + str(sys.exc_info()) + "\n"
                    self.msg = self.msg + "userlist: Error interpreting the list of users from Image Repository " + str(sys.exc_info())
            else:
                self.msg = "No list of users returned. \n" + \
                        "Please verify that you are admin \n"
        else :
            self.msg = "<br> Please introduce your userId"

        raise cherrypy.HTTPRedirect("results")
    actionUserList.exposed = True;

    ## userlist Rest service. 
    def userlist (self, userId = None) :
        self.msg = """ <form method=get action=actionUserList>
        Admin Username: <input type=string name=adminId><br>
        Admin Password: <input type=password name=adminCred><br>     
        <input type=submit> </form> """
        return self.msg
    userlist.exposed = True;

    ## Callback function to the setquota Rest service
    # @param adminId login/account name of the admin user to invoke this service
    # @param adminCred user password in MD5 digested format
    # @param userIdtoModify user id where the quota is modified
    # @param quota quota of the specified user
    def actionQuota (self, adminId, adminCred, userIdtoModify, quota) :

        adminId = adminId.strip()
        userIdtoModify = userIdtoModify.strip()
        #adminCred = IRCredential("ldappass", adminCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            try:
                quota = eval(quota)
                if (len(userIdtoModify) > 0):
                    status = self.service.setUserQuota(adminId, userIdtoModify, quota)
                    if(status == True):
                        self.msg = "Quota changed successfully."
                    else:
                        self.msg = "The user quota has not been changed.</br>"
                        self.msg = self.msg + "Please verify that you are admin and that the username exists"
                else:
                    self.msg = "<br> Please introduce your userId, the userId to modify and the quota in bytes (math operation allowed)"
            except:
                self.msg = "<br> The quota must be a number or a valid math function"

        raise cherrypy.HTTPRedirect("results")
        return self.msg
    actionQuota.exposed = True

    # setquota Rest service
    def setquota (self) :
        self.msg = """ <form method=get action=actionQuota>
        Admin Username: <input type=string name=adminId><br>
        Admin Password: <input type=password name=adminCred><br>
        UserId to Modify: <input type=string name=userIdtoModify> <br>
        Quota : <input type=string name=quota> <br>
        <input type=submit> </form> """
        return self.msg
    setquota.exposed = True;

    ## Callback function to Rest service setrole.
    # @param adminId login/account name of the admin user to invoke this service
    # @param adminCred user password in MD5 digested format
    # @param userIdtoModify user id that is the subject of the set role in the datbase
    # @param role
    def actionUserRole (self, adminId, adminCred, userIdtoModify, role) :
        adminId = adminId.strip()
        userIdtoModify = userIdtoModify.strip()
        role = role.strip()
        #adminCred = IRCredential("ldappass", adminCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            if (len(userIdtoModify) > 0 and len(role) > 0):
                # User name based on admin file
                status = self.service.setUserRole(adminId, userIdtoModify, role)
    
                self.msg = ""
                if (status == True):
                    self.msg = "Role changed successfully."
                else:
                    self.msg = "The user role has not been changed </br>"
                    self.msg = self.msg + "Please verify that you are admin and that the username exists"
            else:
                self.msg = "<br> Please introduce your userId, the userId to modify and the role"
        raise cherrypy.HTTPRedirect("results")
    actionUserRole.exposed = True

    ## setrole Rest service
    def setrole (self) :
        self.msg = """ <form method=post action=actionUserRole>
                        Admin Username: <input type=string name=adminId><br>
                        Admin Password: <input type=password name=adminCred><br>
                        UserId to Modify: <input type=string name=userIdtoModify> <br>
                Role : <input type=string name=role> <br>
                <input type=submit> </form> """
        return self.msg;
    setrole.exposed = True;

    ## Callback function to the setuserstatus Rest service.
    # @param adminId login/account name of the admin user to invoke this service
    # @param adminCred user password in MD5 digested format
    # @param userIdtoModfiy user id that is the subject of the delete in the datbase
    # @param status 
    def actionUserStatus (self, adminId, adminCred, userIdtoModify, status) :
        adminId = adminId.strip()
        userIdtoModify = userIdtoModify.strip()
        status = status.strip()
        #adminCred = IRCredential("ldappass", adminCred)
        if (len(adminId) > 0 and self.service.auth(adminId, adminCred, self.provider)):
            if (len(userIdtoModify) > 0 and len(status) > 0):
                status = self.service.setUserStatus(adminId, userIdtoModify, status)
                self.msg = ""
                if(status == True):
                    self.msg = "Status changed successfully."
                else:
                    self.msg = "The user status has not been changed.</br>"
                    self.msg = self.msg + "Please verify that you are admin and that the username exists \n"
            else:
                self.msg = "<br> Please introduce your userId, the userId to modify and the status"
        raise cherrypy.HTTPRedirect("results")
    actionUserStatus.exposed = True

    ## setuserstatus Rest service
    def setuserstatus (self) :
        self.msg = """ <form method=post action=actionUserStatus>
        Admin Username: <input type=string name=adminId><br>
        Admin Password: <input type=password name=adminCred><br>
        UserId to Modify: <input type=string name=userIdtoModify> <br>
        Status : <input type=string name=status> <br>
        <input type=submit> </form> """
        return self.msg;
    setuserstatus.exposed = True;



#def configSectionMap(section) :
#    dict1 = {}
#    options = cherrypy.config.options(section)
#    dict1[option] = cherrypy.config.get(section,option)
#    for options in options :
#        try:
#            dict1[option] = cherrypy.config.get(section,option)
#            if dict1[option] == -1 :
#                print("Skip: %s " % option)
#        except:
#            print("Exeption on %s " % option)
#            dict1[option] = None
#    return dict1

if __name__ == '__main__':

    # Site configuration


    #cherrypy.config.update(httpsconfig)

    #cherrypy.tree.mount(AdminRestService(),"/")#,'/adminRest',config='adminConfig.conf')

    #ip = cherrypy.config.get("server.socket_host")
    #port = cherrypy.config.get("server.socket_port")
    #cherrypy.config.update('adminConfig.conf')
    #adminName = cherrypy.config.get("admin_name")
    #print("Admin name: %s" % adminName) 
#    adminName = cherrypy.config.get("Admin")['username']
#    adminName = configSectionMap("Admin")['username']
    cherrypy.log.error_log.propagate = False
    cherrypy.log.access_log.propagate = False


    #secure_server = _cpwsgi_server.CPWSGIServer()
    #secure_server.bind_addr = (ip, port)
    #secure_server.ssl_certificate = certificate
    #secure_server.ssl_private_key = privateKey

    #adapter = _cpserver.ServerAdapter(cherrypy.engine, secure_server, secure_server.bind_addr)
    #adapter.subscribe()
    
    repoConf = IRServerConf()
    repoConf.loadRepoServerConfig()    
    configFileName =repoConf.getRestConfFile() 
    if not os.path.isfile(configFileName):
        print "Configuration File "+configFileName+" not found"
        sys.exit(1)
    cherrypy.quickstart(AdminRestService(), "/", config = configFileName)


#else:
    # This branch is for the test suite; you can ignore it.
#    cherrypy.tree.mount(AdminRestService, config=configurationFile)
