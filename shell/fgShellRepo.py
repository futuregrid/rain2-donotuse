#!/usr/bin/python
"""
FutureGrid Command Line Interface

Image Repository
"""
import os
#import cmd
import readline
import sys
from futuregrid.shell import fgShellUtils
from futuregrid.image.repository.client.IRServiceProxy import IRServiceProxy
from futuregrid.image.repository.client import IRTypes
import logging
from futuregrid.utils import fgLog
from cmd2 import Cmd
from cmd2 import options
from cmd2 import make_option
import textwrap


class fgShellRepo(Cmd):

    ############################################################
    #
    ############################################################
    def __init__(self):
        self._service = IRServiceProxy()

    ############################################################
    # test
    ############################################################
    """
    @options([make_option('-q', '--quick', help='Make things fast'),
              make_option('-s', '--slow', type=int, help='Make things slow')]) 
    def do_repotest(self, args, opts):        
        arg = ''.join(args)      
        print opts.quick
        print opts.slow
        self._log.error("SHElll test in fgshell repo")
    """
    ############################################################
    # hist img
    ############################################################
    
    def do_repohistimg(self, args):        
        args = self.getArgs(args)
        
        if(len(args) == 1):
            imgsList = self._service.histImg(os.popen('whoami', 'r').read().strip(), args[0])
        else:
            imgsList = self._service.histImg(os.popen('whoami', 'r').read().strip(), "None")
        
        try:
            imgs = eval(imgsList[0])            
            print imgs['head']
            for key in imgs.keys():
                if key != 'head':
                    print imgs[key]     
        except:
            print "do_repohistimg: Error:" + str(sys.exc_info()[0]) + "\n"                
            self._log.error("do_repohistimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
       
    def help_repohistimg(self):
        msg = "Image Repository histimg command: Return information about the " + \
        " image historical usage. \n"
        self.print_man("histimg [imgId]", msg)
    
    def do_repohistuser(self, args):        
        args = self.getArgs(args)
        
        if(len(args) == 1):
            userList = self._service.histUser(os.popen('whoami', 'r').read().strip(), args[0])
        else:
            userList = self._service.histUser(os.popen('whoami', 'r').read().strip(), "None")
        
        try:
            #print userList
            users = eval(userList[0])            
            print users['head']            
            for key in users.keys():
                if key != 'head':
                    print users[key]     
        except:
            print "do_repohistuser: Error:" + str(sys.exc_info()[0]) + "\n"                
            self._log.error("do_repohistuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
       
    def help_repohistuser(self):
        msg = "Image Repository histuser command: Return information about the " + \
        "user historical usage."
        self.print_man("histuser [userId]", msg)
    ############################################################
    # user add
    ############################################################
    
    def do_repouseradd(self, args):
        args = self.getArgs(args)                
        if (len(args) == 1):
            status = self._service.userAdd(os.popen('whoami', 'r').read().strip(), args[0])                
            if(status == "True"):
                print "User created successfully."
                print "Remember that you still need to activate this user (see setuserstatus command)\n"
            else:
                print "The user has not been created. \n" + \
                      "Please verify that you are admin and that the username does not exist \n"
        else:
            self.help_repouseradd()
            
    def help_repouseradd(self):
        msg = "Image Repository useradd command: Add new user (only Admin user " + \
        "can execut it). \n"
        self.print_man("useradd <userId>", msg)
               
    ############################################################
    # user del
    ############################################################
    
    def do_repouserdel(self, args):
        args = self.getArgs(args)         
        if (len(args) == 1):
            status = self._service.userDel(os.popen('whoami', 'r').read().strip(), args[0])                
            if(status == "True"):
                print "User deleted successfully."                
            else:
                print "The user has not been deleted. \n" + \
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_repouserdel()
    
    def help_repouserdel(self):
        msg = "Image Repository userdel command: Remove a user (only Admin user" + \
        "can execut it). \n"
        self.print_man("userdel <userId>", msg)
        
        

    ############################################################
    # userlist
    ############################################################
    
    def do_repouserlist(self, args):        
        #args=self.getArgs(args)      
        ok = False         
        
        userList = self._service.userList(os.popen('whoami', 'r').read().strip())
      
        if(userList[0].strip() != "None"):
            try:
                imgs = eval(userList[0])
                print str(len(imgs)) + " users found"
                for key in imgs.keys():
                    print imgs[key]               
            except:
                print "do_repouserlist: Error:" + str(sys.exc_info()[0]) + "\n"                
                self._log.error("do_repouserlist: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
        else:
            print "No list of images returned. \n" + \
                  "Please verify that you are admin \n"  
            
    def help_repouserlist(self):
        msg = "Image Repository userlist command: Get list of users \n"
        self.print_man("userlist", msg)
                

    ############################################################
    # setuserquota
    ############################################################
    
    def do_reposetuserquota(self, args):
        args = self.getArgs(args)         
        if (len(args) == 2):
            status = self._service.setUserQuota(os.popen('whoami', 'r').read().strip(), args[0], args[1])                
            if(status == "True"):
                print "User quota changed successfully."                
            else:
                print "The user quota has not been changed. \n" + \
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_reposetuserquota()
    
    def help_reposetuserquota(self):
        msg = "Image Repository setuserquota command: Establish disk space " + \
        "available for users (this is given in bytes). Quota argument allow math expressions like 4*1024"
        self.print_man("userquota <userId> <quota in bytes>", msg)
    ############################################################
    # userrole
    ############################################################
    
    def do_reposetuserrole(self, args):
        args = self.getArgs(args)         
        if (len(args) == 2):
            status = self._service.setUserRole(os.popen('whoami', 'r').read().strip(), args[0], args[1])                
            if(status == "True"):
                print "User role has been changed successfully."                
            else:
                print "The user role has not been changed. " + status + "\n"\
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_reposetuserrole()
    
    def help_reposetuserrole(self):
        msg = "Image Repository setuserrole command: Change role of a particular " + \
        "user. Available roles: " + str(IRTypes.IRUser.Role) + "\n"               
        self.print_man("setuserrole <userId> <role>", msg)
    ############################################################
    # userstatus
    ############################################################
    
    def do_reposetuserstatus(self, args):
        args = self.getArgs(args)         
        if (len(args) == 2):
            status = self._service.setUserStatus(os.popen('whoami', 'r').read().strip(), args[0], args[1])                
            if(status == "True"):
                print "User role has been changed successfully."                
            else:
                print "The user status has not been changed. " + status + "\n"\
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_reposetuserstatus()
    
    def help_reposetuserstatus(self):
        msg = "Image Repository setuserstatus command: Change status of a " + \
        "particular user. Available status: " + str(IRTypes.IRUser.Status)
        self.print_man("setuserstatus <userId> <status>", msg)
    ############################################################
    # list
    ############################################################
            
    def do_repolist(self, args):        
        #args=self.getArgs(args)      
        ok = False         
        
        if (args.strip() == ""):
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), "*")            
        else:
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), args)
        #else:
        #    self.help_repolist()
        
        if(imgsList[0].strip() != "None"):
            try:
                imgs = eval(imgsList[0])
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]                
            except:
                print "do_repolist: Error:" + str(sys.exc_info()[0]) + "\n"                
                self._log.error("do_repolist: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
        else:
            print "No list of images returned"   
            
    def help_repolist(self):
        msg = "Image Repository list command: Get list of images that meet the " + \
        "criteria. If not argument provided it get all images. queryString can " + \
        "be: * ; * where field=XX, field2=YY; field1,field2 where field3=XX \n"
        self.print_man("list [queryString] ", msg)
    ############################################################
    # modify
    ############################################################
                
    def do_repomodify(self, args):       
        args = self.getArgs(args)
        second = ""
        if(len(args) > 1):
            for i in range(1, len(args)):
                second += args[i] + " "
        second = second.replace("&", "|")
                  
        if (len(args) >= 2):
            status = self._service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], second)
            if(status == "True"):
                print "The metadata of img " + args[0] + " has been updated"
            else:
                print "Error in the update. Please verify that you are the owner or that you introduced the correct arguments"
        else:
            self.help_repomodify()        
            
    def help_repomodify(self):
        msg = "Image Repository modify command: Modify image metadata. Example " + \
        "of all values of attributeString (you do not need to provide all of " + \
        "them): vmtype=xen & imgtype=opennebula & os=linux & arch=x86_64 & " + \
        "description=my image & tag=tag1,tag2 & permission=public & " + \
        "imgStatus=available. Some attributes are controlled:"        
        self.print_man("modify <imgId> <Metadata>", msg)
        
        first = True
        for line in textwrap.wrap("vmtype= " + str(IRTypes.ImgMeta.VmType), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
        first = True
        for line in textwrap.wrap("imgtype= " + str(IRTypes.ImgMeta.ImgType), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
        first = True
        for line in textwrap.wrap("imgStatus= " + str(IRTypes.ImgMeta.ImgStatus), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
        first = True
        for line in textwrap.wrap("Permission= " + str(IRTypes.ImgMeta.Permission), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
              
              
    ############################################################
    # permission
    ############################################################
    
    def do_reposetpermission(self, args):       
        args = self.getArgs(args)                
        if (len(args) == 2):            
            status = self._service.setPermission(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            if(status == "True"):
                print "Permission of img " + args[0] + " updated"
            else:
                print "The permission have not been changed. " + status
        else:
            self.help_reposetpermission()        
            
    def help_reposetpermission(self):
        msg = "Image Repository setPermission command: Change image permission." + \
            " Permission= " + str(IRTypes.ImgMeta.Permission)
        self.print_man("setpermission  <imgId> <permission>", msg)

    ############################################################
    # get
    ############################################################
                           
    def do_repoget(self, args): 
        args = self.getArgs(args)   
                     
        if (len(args) == 2):
            imgstatus = self._service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            
            if imgstatus:
                print imgstatus
            else:
                print "Cannot get access to the image with imgId = " + args[1]
        else:
            self.help_repoget()        
            
    def help_repoget(self):
        msg = "Image Repository get command: Get an image or only the URI by id. \n"
        self.print_man("get <img OR uri> <imgId>", msg)

    ############################################################
    # put
    ############################################################
    
    def do_repoput(self, args):       
        
        args = self.getArgs(args)            
        
        second = ""
        if(len(args) > 1):
            for i in range(1, len(args)):
                second += args[i] + " "
        
        second = second.replace("&", "|")          
            
        status = 0
        ok = False
        if (len(args) > 1):                
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, args[0], second)
            ok = True
        elif (len(args) == 1):
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, args[0], "")
            ok = True
        else:
            self.help_repoput()
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
        #print "image has been uploaded and registered with id " + str(id1)
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
        #print status        
        if(ok):
            if(status == "0"):
                print "The image has NOT been uploaded. Please, verify that the file exists and the metadata string is valid"
            elif(status == "-1"):
                print "The image has NOT been uploaded"
                print "The User does not exist"
            elif(status == "-2"):
                print "The image has NOT been uploaded"
                print "The User is not active"
            elif(status == "-3"):
                print "The image has NOT been uploaded"
                print "The file exceed the quota"
            else:
                print "image has been uploaded and registered with id " + str(status)
        
        
    def help_repoput(self):
        msg = "Image Repository put command: Upload a new image and its " + \
            "metadata as an attributeString. If no attributeString provided some default values are " + \
            "assigned. Example of all values of attributeString (you do not need to " + \
            "provide all of them): vmtype=xen & imgtype=opennebula & os=linux & " + \
            "arch=x86_64 & description=my image & tag=tag1,tag2 & permission=public & " + \
            "imgStatus=available. Some attributes are controlled:"
        self.print_man("put <imgFile> [attributeString]", msg)
        
        first = True
        for line in textwrap.wrap("vmtype= " + str(IRTypes.ImgMeta.VmType), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
        first = True
        for line in textwrap.wrap("imgtype= " + str(IRTypes.ImgMeta.ImgType), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
        first = True
        for line in textwrap.wrap("imgStatus= " + str(IRTypes.ImgMeta.ImgStatus), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)
        first = True
        for line in textwrap.wrap("Permission= " + str(IRTypes.ImgMeta.Permission), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)


    ############################################################
    # remove
    ############################################################
    def do_reporemove(self, args):        
        args = self.getArgs(args)                 
        if (len(args) == 1):
            if (self._service.remove(os.popen('whoami', 'r').read().strip(), args[0]) == "True"):
                print "The image with imgId=" + args[0] + " has been removed"
            else:
                print "The image with imgId=" + args[0] + " has NOT been removed. Please verify the imgId and if you are the image owner"
        else:
            self.help_reporemove() 
            
    def help_reporemove(self):
        msg = "The Image Repository remove command: Remove a image from the repository."
        self.print_man("remove <imgId>", msg)
    
