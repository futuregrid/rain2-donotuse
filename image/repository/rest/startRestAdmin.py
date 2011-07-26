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
from cherrypy.lib.static import serve_file

localDir = os.path.abspath(os.path.dirname(__file__))

httpconfig = os.path.join(localDir, 'httpconfig.conf')
httpsconfig = os.path.join(localDir, 'httpsconfig.conf')
certificate = os.path.join(localDir, 'server.crt')
privateKey = os.path.join(localDir, 'server.key')
adminName = None
config = None


class AdminRestService :
    msg = None
    writeMethodsExposed = True

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
        self.setMessage(message)
        raise cherrypy.HTTPRedirect("results")
    help.exposed = True;


    def actionList (self, queryString) :
        service = IRService()
        if (len(queryString) == 0):
            imgsList = service.query(adminName, "*")
        else:
            imgsList = service.query(adminName, queryString)

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
            service = IRService()
            status = service.updateItem(adminName, imgId, permissionString)
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
            service = IRService()
            filepath = service.get(adminName, option, imgId)
            if (len(imgId) > 0 ) :
                self.setMessage("Downloading img to %s " % filepath.__str__())
            else :
                self.setMessage("URL:  %s " % filepath.__str__())
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
        self.msg = "Uploaded fileName: %s " % imageFileName.__str__()
        while 1:
            data = imageFileName.file.read(1024 * 8) # Read blocks of 8KB at a time                                                               
            size += len(data)
            if not data: break

        self.msg += " Image size %s " % size
        service = IRService()
        print type(imageFileName)
        imageId = service.put(adminName, userId,imageFileName,attributeString,size)
        raise cherrypy.HTTPRedirect("results")
    actionPut.exposed = True

    def put (self) :
       return """                                                                                                                                             <html><body>                                                                                                                                      <form method=post action=actionPut enctype="multipart/form-data">                                                                                     Upload a file: <input type=file name=imageFileName><br>                                                                                           User Id: <input type=string name=userId> <br>                                                                                                     attributeString: <input type=string name=attributeString> <br>                                                                                    <input type=submit>                                                                                                                           </form>                                                                                                </body></html>      
        """
    put.exposed = True;


    def actionModify (self, imgId = None, attributeString = None):
        fname = sys._getframe().f_code.co_name
        self.msg = None
        if(len(imgId) > 0):
            service = IRService()
            success = service.updateItem(adminName, imgId, attributeString)
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
        service = IRService()
        status = service.remove(adminName, imgId)
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
        service = IRService()
        fname = sys._getframe().f_code.co_name
        self.msg = None
        if(len(imgId) > 0):
            imgsList = service.histImg(adminName, imgId)
        else:
            imgsList = service.histImg(adminName, "None")

        try:
            imgs = service.printHistImg(imgsList)
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
        service = IRService()
        self.msg = None
        if (len(userId) > 0):
            userList = service.histUser(adminName, userId)
        else:
            userList = service.histUser(adminName, "None")

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
        service = IRService()
        status = service.userAdd(adminName, userId)
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
        service = IRService()
        status = service.userDel(adminName,userId)
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
        service = IRService()
        self.msg = None

        if (adminName != None) :
            usersList = service.userList(adminName)
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
        service = IRService()
        status = service.setUserQuota(adminName,userId,quota)
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
        service = IRService()
        # User name based on admin file
        status = service.setUserRole(adminName,userId, role) 
        
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
        service = IRService()
        status = service.setUserStatus(adminName,userId,status)
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
