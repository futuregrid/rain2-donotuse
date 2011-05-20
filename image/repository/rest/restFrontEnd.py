"""
@author Michael Lewis

"""

import cherrypy
import os, sys
#sys.path.append('/opt/futuregrid/futuregrid/image/repository/server')
sys.path.append('/opt/cherryPyRest/rest/server')
from IRService import IRService
from cherrypy.lib.static import serve_file

inSession = False

class RepositoryService:
    """
    This class is a simple Web service interface to the FutureGrid
    repository. The repository is documented in more detail in the
    following paper:

    * TBD

    """
    writeMethodsExposed = True;

    def actionGetSession(self,userName) :
        # validate session information here
        return "actionGetSession"
    actionGetSession.exposed = True
    
    def index(self) :
        if (inSession == False) :
            msg = "<html> <body> <p> Future Grid Rest Service API </p>"
            msg += """<form method=get action=actionGetSession>"""
            msg += "username: <input type=string name=userName><br> "
            msg += "password: <input type=string name=password><br> "
            msg += "<input type=submit> </form> </body></html> "
        else :
            msg = "<b> User Commands </b><br> "
            msg +=  " /help: get help information. <br>"
            msg += " /auth: login/authentication <br>"
            msg += " /list queryString: get list of images that meet the criteria<br>"
            msg += " /setPermission imgId permissionString: set access permission<br>"
            msg += " /get img/uri imgId: get a image or only the URI by id<br>"
            msg += " /put imgFile attributeString: upload/register an image<br>"
            msg += " /modify imgId attributeString: update information<br>"
            msg += " /remove imgId: remove an image from the repository<br>"
            msg += " /histimg imgId: get usage info of an image <br>"
            msg += " /histuser userId: get usage info of a user <br>"
            msg += " /getBackend: provide the back-end configuration in the server side <br>"
            msg += " /useradd <userId> : add user <br>" 
            msg += " /userdel <userId> : remove user <br>"
            msg += " /userlist : list of users <br>"
            msg += " /setquota <userId> <quota> :modify user quota <br>"
            msg += " /setrole  <userId> <role> : modify user role <br>"
            msg += " /setUserStatus <userId> <status> :modify user status"
        return msg;
    index.exposed = True;


    def help (self) : 
        msg =  " /help: get help information. <br>"
        msg += " /auth: login/authentication <br>"
        msg += " /list queryString: get list of images that meet the criteria<br>"
        msg += " /setPermission imgId permissionString: set access permission<br>"
        msg += " /get img/uri imgId: get a image or only the URI by id<br>"
        msg += " /put imgFile attributeString: upload/register an image<br>"
        msg += " /modify imgId attributeString: update information<br>"
        msg += " /remove imgId: remove an image from the repository<br>"
        msg += " /histimg imgId: get usage info of an image <br>"
        msg += " /histuser userId: get usage info of a user <br>"
        msg += " /getBackend: provide the back-end configuration in the server side <br>"
        msg += " /useradd <userId> : add user <br>" 
        msg += " /userdel <userId> : remove user <br>"
        msg += " /userlist : list of users <br>"
        msg += " /setquota <userId> <quota> :modify user quota <br>"
        msg += " /setrole  <userId> <role> : modify user role <br>"
        msg += " /setUserStatus <userId> <status> :modify user status"
        return msg;
    help.exposed = True;
    
    def auth(self):
        fname = sys._getframe().f_code.co_name
        service = IRService()
        username = os.popen('whoami', 'r').read().strip()
        msg = service.auth(username)
        #msg = service.auth("fuwang")
        return msg;
    auth.exposed = True;

    def userlist(self):
        fname = sys._getframe().f_code.co_name
        service = IRService()
        usersList = service.userList(os.popen('whoami', 'r').read().strip())

        if(len(usersList) > 0):
            try:
                msg = "<br>" + str(len(usersList)) + " users found </br>"
                msg = msg + "<br> UserId Cred fsCap fsUsed lastLogin status role ownedImgs </br>"
                for user in usersList.items():
                    msg = msg + "<br>" + str(user[1])[1:len(str(user[1]))-1]
                msg = msg + "</br>"
            except:
                msg = "userlist: Error:" + str(sys.exc_info()[0]) + "\n"                
                msg = msg + "userlist: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0])
            else:
                    print "No list of images returned. \n" + \
                          "Please verify that you are admin \n" 
        return msg;
    userlist.exposed = True;
    
    def actionHistUser (self, userIdto):
        fname = sys._getframe().f_code.co_name
        service = IRService()
        
        if(len(userIdto) > 0):
            userList = service.histUser(os.popen('whoami', 'r').read().strip(), userIdto)
        else:
            userList = service.histUser(os.popen('whoami', 'r').read().strip(), "None")
                                
        try:
            users = userList            
            msg = users['head']    
            for key in users.keys():
                if key != 'head':
                    msg = msg + users[key]     
        except:
            msg = "histuser: Error:" + str(sys.exc_info()[0]) + "\n"                
            self._log.error("histuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
        return msg;
    actionHistUser.exposed = True;

    def histuser (self) :
        msg = """ <form method=get action=actionHistUser>
                User Id: <input type=string name=userIdto> <br>
                <input type=submit> </form> """
        return msg;
    histuser.exposed = True;
    
    def actionUserAdd (self, userId):
        service = IRService()
        status = service.userAdd(os.popen('whoami', 'r').read().strip(), userId)
        if(status):
            msg = "User created successfully.</br>"
            msg = msg + "Remember that you still need to activate this user (see setuserstatus command)</br>"
        else:
            msg = "The user has not been created.</br>"
            msg = msg + "Please verify that you are admin and that the username does not exist </br>"
        return msg
    actionUserAdd.exposed = True

    def useradd (self, userId = None) :
        msg = """ <form method=get action=actionUserAdd>
                Add User Id: <input type=string name=userId> <br>
                <input type=submit> </form> """
        return msg
    useradd.exposed = True;
    
    def actionUserDel(self,userId = None) :
        service = IRService()
        status = service.userDel(os.popen('whoami', 'r').read().strip(),userId)
        if(status == True):
            msg = "User deleted successfully."                
        else:
            msg = "The user has not been deleted.</br>"
            msg = msg + "Please verify that you are admin and that the username exists \n"
        return msg
    actionUserDel.exposed = True

    def userdel (self, userId = None) :
      msg = """ <form method=get action=actionUserDel>
                User Id: <input type=string name=userId> <br>
                <input type=submit> </form> """
      return msg;
    userdel.exposed = True
    
    def actionUserQuota (self,userId, quota) :
        service = IRService()
        status = service.setUserQuota(os.popen('whoami', 'r').read(),userId,quota)
        if(status == True):
            msg = "Quota changed successfully."
        else:
            msg = "The user quota has not been changed.</br>"
            msg = msg + "Please verify that you are admin and that the username exists"
        return msg
    actionUserQuota.exposed = True

    def setUserQuota (self) :
        msg = """ <form method=get action=actionUserQuota>
                User Id: <input type=string name=userId> <br>
                Quota : <input type=string name=quota> <br>
                <input type=submit> </form> """
        return msg
    setUserQuota.exposed = True;    
    
    def actionUserRole (self,userId, role) :
        service = IRService()
        status = service.setUserRole(os.popen('whoami', 'r').read().strip(),userId, role)
        if(status == True):
            msg = "Role changed successfully."
        else:
            msg =  "The user role has not been changed </br>"
            msg = msg + "Please verify that you are admin and that the username exists"
        return msg
    actionUserRole.exposed = True

    def setuserrole (self) :
        fname = sys._getframe().f_code.co_name
        msg = """ <form method=post action=actionUserRole>
                User Id: <input type=string name=userId> <br>
                Role : <input type=string name=role> <br>
                <input type=submit> </form> """
        return msg;
    setuserrole.exposed = True;
    
    def actionUserStatus (self,userId, status) :
        service = IRService()
        status = service.setUserStatus(os.popen('whoami', 'r').read().strip(),userId,status)
        if(status == True):
            msg = "Status changed successfully."
        else:
            msg = "The user status has not been changed.</br>"
            msg = msg + "Please verify that you are admin and that the username exists \n"        
        return msg
    actionUserRole.exposed = True

    def setuserstatus (self) :
        fname = sys._getframe().f_code.co_name
        msg = """ <form method=post action=actionUserStatus>
                User Id: <input type=string name=userId> <br>
                Status : <input type=string name=status> <br>
                <input type=submit> </form> """
        return msg;
    setuserstatus.exposed = True;

    def actionHistImage (self, imgId):
        service = IRService()
        fname = sys._getframe().f_code.co_name
        if(len(imgId) > 0):
            imgsList = service.histImg(os.popen('whoami', 'r').read().strip(), imgId)
        else:
            imgsList = service.histImg(os.popen('whoami', 'r').read().strip(), "None")

        try:
            imgs = service.printHistImg(imgsList)
            msg = imgs['head']
            for key in imgs.keys():
                if key != 'head':
                    msg = msg + imgs[key] + "\n"     
        except:
            msg = "histimg: Error:" + str(sys.exc_info()[0]) + "\n"                
            self._log.error("histimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
        return msg;
    actionHistImage.exposed = True;
    
    def histimage (self):
      msg = """ <form method=get action=actionHistImage>
                Image Id: <input type=string name=imgId> <br>
                <input type=submit> </form> """
      return msg;
    histimage.exposed = True;
    
    def actionList (self, queryString) :
        service = IRService()
        if (len(queryString) == 0):
            imgsList = service.query(os.popen('whoami', 'r').read().strip(), "*")
        else:
            imgsList = service.query(os.popen('whoami', 'r').read().strip(), queryString)
                
        if(len(imgsList) > 0):
            try:
                    msg = str(imgsList)
            except:
                msg = "list: Error:" + str(sys.exc_info()[0]) + "</br>"                
                self._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
        else:
            msg = "No list of images returned"   
        return msg
    actionList.exposed = True

    def list (self) :
        msg = """ <form method=get action=actionList>
                Query string: <input type=string name=queryString> <br>
                <input type=submit> </form> """
        return msg;
    list.exposed = True
    
    def actionSetPermission (self, imgId = None, permissionString = None) :
        if (len(permissionString) > 0):
            service = IRService()
            status = service.updateItem(os.popen('whoami', 'r').read().strip(), imgId, permissionString)
            if(status == True):
                msg = "Permission of img " + imgId + " updated"
            else:
                msg = "The permission have not been changed."
        return msg;
    actionSetPermission.exposed = True;
    
    def setpermission (self):
      msg = """ <form method=get action=actionSetPermission>
                Image Id: <input type=string name=imgId> <br>
                Permission string: <input type=string name=permissionString> <br>
                <input type=submit> </form> """
      return msg;
    setpermission.exposed = True;
    
    def actionGet(self, option, imgId):
       if(len(imgId) > 0 and len(option) > 0):
           service = IRService()
           filepath = service.get(os.popen('whoami', 'r').read().strip(), option, imgId)
       else:
           msg = "The image Id or option is empty! Please input both the image Id and option"
       return serve_file(filepath, "application/x-download", "attachment")
    actionGet.exposed = True

    def get (self):
        return """
           <html><body>
           <form method=get action=actionGet>
               Image Id: <input type=string name=imgId> <br>
               Option ('img' or 'uri'): <input type=string name=option> <br>
               <input type=submit>
           </form>
           </body></html>
       """
    get.exposed = True;

    def actionPut(self, userId = None, imageFileName = None, attributeString = None) :
        # retrieve the data
        size = 0
        while 1:
            data = imageFileName.file.read(1024 * 8) # Read blocks of 8KB at a time
            size += len(data)
            if not data: break
    
            
        service = IRService()
        print type(imageFileName)
        imageId = service.put(os.popen('whoami', 'r').read().strip(), userId,imageFileName,attributeString,size)
        return 
    actionPut.exposed = True;

    def put (self) :
       return """
            <html><body>
            <form method=post action=actionPut enctype="multipart/form-data">
                Upload a file: <input type=file name=imageFileName><br>
                User Id: <input type=string name=userId> <br>
                attributeString: <input type=string name=attributeString> <br>
                <input type=submit>
            </form>
            </body></html>
        """
    put.exposed = True;

    def actionRemove (self, imgId = None):
        fname = sys._getframe().f_code.co_name
        service = IRService()
        status = service.remove(os.popen('whoami', 'r').read().strip(), imgId)
        if (status == True):
            msg = "The image with imgId=" + imgId + " has been removed"
        else:
            msg = "The image with imgId=" + imgId + " has NOT been removed.</br>Please verify the imgId and if you are the image owner"
        return msg;
    actionRemove.exposed = True;
    
    def remove (self):
        msg = """ <form method=get action=actionRemove>
                Image Id: <input type=string name=imgId> <br>
                <input type=submit> </form> """
        return msg
    remove.exposed = True
    
    def actionModify (self, imgId = None, attributeString = None):
        fname = sys._getframe().f_code.co_name
        if(len(imgId) > 0):
            service = IRService()
            success = service.updateItem(os.popen('whoami', 'r').read().strip(), imgId, attributeString)
            #success=service.updateItem(os.popen('whoami', 'r').read().strip(), "4d66c1f9577d70165f000000", "vmType=kvm|imgType=Opennebula|os=Windows|arch=x86_64| owner=tstuser2| description=another test| tag=tsttagT, tsttagY")
        if (success):
            msg = "The item was successfully updated"
        else:
            msg = "Error in the update.<br>Please verify that you are the owner or that you introduced the correct arguments"
        return msg;
    actionModify.exposed = writeMethodsExposed;

    def modify (self, imgId = None, attributeString = None):
        msg = """ <form method=get action=actionModify>
                Image Id: <input type=string name=imgId> <br>
                Atribute String: <input type=string name=attributeString> <br>
                <input type=submit> </form> """
        return msg;
    modify.exposed = writeMethodsExposed;
    

    def search (self, queryString = None):
        fname = sys._getframe().f_code.co_name
        service = IRService()
        if (len(queryString) == 0):
            imgsList = service.query(os.popen('whoami', 'r').read().strip(), "*")
        else:
            imgsList = service.query(os.popen('whoami', 'r').read().strip(), queryString)
        #dict wrapped into a list, convert it first
        #print imgsList
                
        if(imgsList[0].strip() != "None"):
            try:
                imgs = eval(imgsList[0])
                msg = str(len(imgs)) + " items found"
                for key in imgs.keys():
                            msg = msg + imgs[key] + "\n"                
            except:
                msg = "list: Error:" + str(sys.exc_info()[0]) + "\n"                
                self._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
            else:
                msg = "No list of images returned"   
        return msg;
    search.exposed = True;

##methods we do not want to expose
#
# adding a user
# deleting a user
# status of a user

#Questions: how about:                               
#setuserquota
#setuserrole
#setpermission
# ?????
#



    ## not all is yet defined, this is just a skeleton



import os.path
configurationFile = os.path.join(os.path.dirname(__file__), 'repository.conf')

if __name__ == '__main__':
    cherrypy.quickstart(RepositoryService(), config=configurationFile)
else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(RepositoryService(), config=configurationFile)
