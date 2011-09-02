#!/usr/bin/env python
"""
Image repository server

For the current implementation this is just a dummy one, and only serves to
maintain the proposed deployed code structure. In the later phase this will
be replaced by a WS implementation
"""
__author__ = 'Fugang Wang, Javier Diaz'
__version__ = '0.1'

import os, sys
import string
from multiprocessing import Process

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRServerConf import IRServerConf
from IRService import IRService

try:
    from ....utils.FGTypes import FGTypes, fgLog
    from ....utils import FGAuths
except:
    sys.path.append(os.getcwd())
    sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../../")    
    from utils.FGTypes import FGCredential
    from utils import FGAuth
    


class IRServer(object):

    ############################################################
    # __init__
    ############################################################
    def __init__(self):
        super(IRServer, self).__init__()

        self.numparams = 5

        self._service = IRService()
        self._log = self.service.getLog()
        self._repoconf = self.service.getRepoConf()

        self.port = self._repoconf.getPort()
        self.proc_max = self._repoconf.getProcMax()
        self.refresh_status = self._repoconf.getRefreshStatus()       
        self._authorizedUsers = self._repoconf.getAuthorizedUsers()    
        
        
        
    def start(self):
        self._log.info('Starting Server on port ' + str(self.port))
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.port))
        sock.listen(1) #Maximum of system unaccepted connections. Maximum value depend of the system (usually 5) 
                
        proc_list = []
        total_count = 0
        while True:        
            if len(proc_list) == self.proc_max:
                full = True
                while full:
                    for i in range(len(proc_list) - 1, -1, -1):
                        #self._log.debug(str(proc_list[i]))
                        if not proc_list[i].is_alive():
                            #print "dead"                        
                            proc_list.pop(i)
                            full = False
                    if full:
                        time.sleep(self.refresh_status)
            
            total_count += 1
            #channel, details = sock.accept()
            newsocket, fromaddr = sock.accept()
            connstream = 0
            try:
                connstream = ssl.wrap_socket(newsocket,
                              server_side=True,
                              ca_certs=self._ca_certs,
                              cert_reqs=ssl.CERT_REQUIRED,
                              certfile=self._certfile,
                              keyfile=self._keyfile,
                              ssl_version=ssl.PROTOCOL_TLSv1)
                #print connstream                                
                proc_list.append(Process(target=self.repo, args=(connstream)))            
                proc_list[len(proc_list) - 1].start()
            except ssl.SSLError:
                self._log.error("Unsuccessful connection attempt from: " + repr(fromaddr))
            except socket.error:
                self._log.error("Error with the socket connection")
            except:
                self._log.error("Uncontrolled Error: " + str(sys.exc_info()))
                if type(connstream) is ssl.SSLSocket: 
                    connstream.shutdown(socket.SHUT_RDWR)
                    connstream.close()
                     
    def auth(self, userCred):
        return FGAuth.auth(self.user, userCred)        
      
    
    def repo(self, connstream):
        self._log = logging.getLogger("ImageRepoServer." + str(os.getpid()))
        
        self._log.info('Processing an image generation request')
        #it will have the IP of the VM
        vmaddr = ""        
        options = ''    
        vmID = 0
        
        #receive the message
        data = channel.read(2048)
        
        self._log.debug("received data: " + data)
        
        params = data.split('|')

        #params[0] is user  
        #params[1] is the user password
        #params[2] is the type of password
        #params[3] is the command
        #params[4] is the options separated by commas
        
        self.user = params[0].strip()
        passwd = params[1].strip()
        passwdtype = params[2].strip()
        command = params[3].strip()
        options = params[4].strip()
        
        #optionlist[0] is the user
        #optionlist[1-5] depend of command 
        optionlist = options.split(",")            
        for i in range(len(optionlist)):
            optionlist[i]=optionlist[i].strip()

        if len(params) != self.numparams:
            msg = "ERROR: incorrect message"
            self.errormsg(channel, msg)
            #break
            sys.exit(1)
        
        if not self.user in self._authorizedUsers:
            if not (self.user == optionlist[0]):
                msg = "Error. your are not authorized to use another user name"    
                self.errormsg(channel, msg)
                sys.exit(1)
        
        retry = 0
        maxretry = 3
        endloop = False
        while (not endloop):
            userCred = FGCredential(passwd, passwdtype)
            if self.auth(userCred):
                channel.write("OK")
                endloop = True
            else:
                if self.user in self._authorizedUsers: #because this is users are services that cannot retry.
                    endloop = True
                else:
                    channel.write("TryAuthAgain")
                    retry += 1
                    if retry < maxretry:
                        passwd = channel.read(2048)
                    else:
                        msg = "ERROR: authentication failed"
                        endloop = True
                        self.errormsg(channel, msg)
                        sys.exit(1)

        if (command == "list"):            
            if (len(optionlist) != 2):
                #user, query string
                self._service.query(optionlist[0], optionlist[1])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "setPermission"):
            #user, imgid, query
            if (len(optionlist) != 3):                
                self._service.updateItem(optionlist[0], optionlist[1], optionlist[2])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "get"):
            #user, img/uri, imgid
            if (len(optionlist) != 3):
                self._service.get(optionlist[0], optionlist[1], optionlist[2])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "put"):
            #user, imgId, imgFile(uri), attributeString, size, extension
            if (len(optionlist) != 6):
                self._service.put(optionlist[0], optionlist[1], optionlist[2], optionlist[3], long(optionlist[4]), optionlist[5])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "remove"):
            #user, imgid
            if (len(optionlist) != 2):
                self._service.remove(optionlist[0], optionlist[1])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "histimg"):
            #userId, imgId
            if (len(optionlist) != 2):
                self._service.histImg(optionlist[0], optionlist[1])                
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "histuser"):
            #userId, userId
            if (len(optionlist) != 2):
                self._service.histUser(optionlist[0], optionlist[1])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "uploadValidator"):
            #user, size of the img to upload
            if (len(optionlist) != 2):
                self._service.uploadValidator(optionlist[0], long(optionlist[1]))
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "genImgId"):
            if (len(optionlist) != 1):
                self._service.genImgId()
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "getBackend"):
            if (len(optionlist) != 1):
                self._service.getBackend()
                self._service.getImgStore()
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "modify"):
            #userid, imgid, attributestring
            if (len(optionlist) != 3):
                self._service.updateItem(optionlist[0], optionlist[1], optionlist[2])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "useradd"):
            #userid, useridtoadd
            if (len(optionlist) != 2):
                self._service.userAdd(optionlist[0], optionlist[1])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "userdel"):
            #userid, useridtodel
            if (len(optionlist) != 2):
                self._service.userDel(optionlist[0], optionlist[1])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "userlist"):
            #userid
            if (len(optionlist) != 1):
                self._service.userList(optionlist[0])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "setUserQuota"):
            #userid, useridtomodify, quota in bytes
            if (len(optionlist) != 3):
                self._service.setUserQuota(optionlist[0], optionlist[1], long(optionlist[2]))
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "setUserRole"):
            #userid, useridtomodify, role
            if (len(optionlist) != 3):
                self._service.setUserRole(optionlist[0], optionlist[1], optionlist[2])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        elif (command == "setUserStatus"):
            if (len(optionlist) != 3):
                self._service.setUserStatus(optionlist[0], optionlist[1], optionlist[2])
            else:
                msg = "Invalid Number of Parameters"
                self.errormsg(channel, msg)
        else:
            msg = "Invalid Command: "+ command
            self.errormsg(channel, msg)
        
    def errormsg(self, channel, msg):
        self._log.error(msg)        
        channel.write(msg)                
        channel.shutdown(socket.SHUT_RDWR)
        channel.close()
        self._log.info("Image Repository Request DONE")
        
def main():
    
    server = IRServer()
    server.start()
    
if __name__ == "__main__":
    main()
