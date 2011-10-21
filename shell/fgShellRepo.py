#!/usr/bin/env python
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
import argparse
import re

class fgShellRepo(Cmd):

    ############################################################
    #
    ############################################################
    def __init__(self):
        print "Init Repo"
        verbose = True        
        printLogStdout = False
        self._service = IRServiceProxy(verbose, printLogStdout)
        

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

        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return

        if(len(args) == 1):
            imgsList = self._service.histImg(self.user, self.passwd, self.user, args[0])
        else:
            imgsList = self._service.histImg(self.user, self.passwd, self.user, "None")

        try:
            imgs = eval(imgsList)            
            for key in imgs.keys():                                
                print imgs[key]
        except:
            print "Server replied: " + str(imgsList)
            print "histimg: Error:" + str(sys.exc_info()) + "\n"
            self._log.error("do_repohistimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))

    def help_repohistimg(self):
        msg = "Image Repository histimg command: Return information about the " + \
        " image historical usage. \n"
        self.print_man("histimg [imgId]", msg)

    def do_repohistuser(self, args):
        args = self.getArgs(args)

        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return

        if(len(args) == 1):
            userList = self._service.histUser(self.user, self.passwd, self.user, args[0])
        else:
            userList = self._service.histUser(self.user, self.passwd, self.user, "None")

        if userList == 'None':
            print "ERROR: Not user found"
        else:            
            try:
                users = eval(userList)            
                for key in users.keys():                
                    print users[key]
            except:
                print "Server replied: " + str(userList)
                print "histuser: Error:" + str(sys.exc_info()) + "\n"
                self._log.error("do_repohistuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()))

    def help_repohistuser(self):
        msg = "Image Repository histuser command: Return information about the " + \
        "user historical usage."
        self.print_man("histuser [userId]", msg)
        
     
    ###################
    #user
    ###################    
    def do_repouser(self, args):        
        argslist = args.split("-")[1:]        

        prefix = ''
        sys.argv=['']        
        for i in range(len(argslist)):
            if argslist[i] == "":
                prefix = '-'
            else:
                newlist = argslist[i].split(" ")
                sys.argv += [prefix+'-'+newlist[0]]
                newlist = newlist [1:]                
                if len(newlist) > 0:                    
                    sys.argv += newlist          
                #sys.argv += [prefix+'-'+argslist[i]]
                prefix = ''

        parser = argparse.ArgumentParser(prog="repouser", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="User command ")            
        group1 = parser.add_mutually_exclusive_group()
        group1.add_argument('-a', '--add', dest='usertoAdd', metavar='userId', help='Add new user to the Image Repository')
        group1.add_argument('-d', '--del', dest='usertoDel', metavar='userId', help='Delete an user to the Image Repository')        
        group1.add_argument('-l', '--list', dest='list', action="store_true", help='List users from Image Repository')        
        group1.add_argument('-m', '--modify', dest='modify', nargs=3, metavar=('userId', 'quota/role/status', 'value'), help='Modify quota, role or status of an user')
                  
        args = parser.parse_args()
        
        used_args = sys.argv[1:]
        
        if len(used_args) == 0:
            parser.print_help()
            return
                
        if ('-a' in used_args or '--add' in used_args):
            self.repouseradd(args.usertoAdd)
        if ('-d' in used_args or '--del' in used_args):
            self.repouserdel(args.usertoDel)
        if ('-l' in used_args or '--list' in used_args):
            self.repouserlist("")
        if ('-m' in used_args or '--modify' in used_args):
            if args.modify[1].strip() == "quota":
                print args.modify[0]
                print args.modify[2]
                self.reposetuserquota(args.modify[0],args.modify[2])
            elif args.modify[1].strip() == "role":
                if not args.modify[2] in IRTypes.IRUser.Role:
                    print "ERROR: third positional parameter must be one of these: " + str(IRTypes.IRUser.Role)
                else:
                    self.reposetuserrole(args.modify[0],args.modify[2])
            elif args.modify[1].strip() == "status":
                if not args.modify[2] in IRTypes.IRUser.Status:
                    print "ERROR: third positional parameter must be one of these: " + str(IRTypes.IRUser.Status)
                else:
                    self.reposetuserstatus(args.modify[0],args.modify[2])
            else:
                print "ERROR: second positional parameter must be quota, role or status"
            
    
    def help_repouser(self):
        msg = "Repo user command: Manage Image Repository Users "              
        self.print_man("user ", msg)
        eval("self.do_repouser(\"-h\")")
    ############################################################
    # user add
    ############################################################

    def repouseradd(self, args):
        '''Image Repository useradd command: Add new user (only Admin
        user can execut it).'''

        args = self.getArgs(args)
        if (len(args) == 1):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            status = self._service.userAdd(self.user, self.passwd, self.user, args[0])
            if(status == "True"):
                print "User created successfully."
                print "Remember that you still need to activate this user (see setuserstatus command)\n"
            else:
                print "The user has not been created. \n" + \
                      "Please verify that you are admin and that the username does not exist \n"
        else:
            self.help_repouseradd()

    ############################################################
    # user del
    ############################################################

    def repouserdel(self, args):
        '''Image Repository userdel command: Remove a user (only Admin
        user can execut it).'''

        args = self.getArgs(args)
        if (len(args) == 1):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            status = self._service.userDel(self.user, self.passwd, self.user, args[0])
            if(status == "True"):
                print "User deleted successfully."
            else:
                print "The user has not been deleted. \n" + \
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_repouserdel()

    ############################################################
    # userlist
    ############################################################

    def repouserlist(self, args):
        '''Image Repository userlist command: Get list of users'''
        
        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return

        userList = self._service.userList(self.user, self.passwd, self.user)

        if(userList.strip() != "None"):
            try:
                imgs = eval(userList)
                print str(len(imgs)) + " users found"
                for key in imgs.keys():
                    print imgs[key]
            except:
                print "Server replied: " + str(userList)
                print "do_repouserlist: Error:" + str(sys.exc_info()[0]) + "\n"
                self._log.error("do_repouserlist: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
        else:
            print "No list of user returned. \n" + \
                  "Please verify that you are admin \n"

    ############################################################
    # setuserquota
    ############################################################

    def reposetuserquota(self, userId, value):
        '''Image Repository setuserquota command: Establish disk space
        available for users (this is given in bytes). Quota argument
        allow math expressions like 4*1024'''

        
        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return
        status = self._service.setUserQuota(self.user, self.passwd, self.user, userId, value)
        if(status == "True"):
            print "User quota changed successfully."
        else:
            print "The user quota has not been changed. \n" + \
                  "Please verify that you are admin and that the username exists \n"

    ############################################################
    # userrole
    ############################################################

    def reposetuserrole(self, userId, value):        
        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return
        status = self._service.setUserRole(self.user, self.passwd, self.user, userId, value)
        if(status == "True"):
            print "User role has been changed successfully."
        else:
            print "The user role has not been changed. " + status + "\n"\
                  "Please verify that you are admin and that the username exists \n"

    ############################################################
    # userstatus
    ############################################################

    def reposetuserstatus(self, userId, value):        
        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return
        status = self._service.setUserStatus(self.user, self.passwd, self.user, userId, value)
        if(status == "True"):
            print "User status has been changed successfully."
        else:
            print "The user status has not been changed. " + status + "\n"\
                  "Please verify that you are admin and that the username exists \n"
        
    ############################################################
    # list
    ############################################################

    def do_repolist(self, args):
        '''Image Repository list command: Get list of images that meet
        the criteria. If not argument provided it get all
        images. queryString can "be: * ; * where field=XX, field2=YY;
        field1,field2 where field3=XX'''
   
        #connect with the server
        if not self._service.connection():
            print "ERROR: Connection with the server failed"
            return
        
        if (args.strip() == ""):
            imgsList = self._service.query(self.user, self.passwd, self.user, "*")
        else:
            imgsList = self._service.query(self.user, self.passwd, self.user, args)


        if(imgsList != None):
            try:                
                imgs = eval(imgsList)
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]
            except:
                print "Server replied: " + str(imgsList)
                print "list: Error:" + str(sys.exc_info()) + "\n"
                self._service._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()))
        else:
            print "No list of images returned"
       

    def help_repolist(self):
        '''Help message for the repouserlist command'''
        self.print_man("list [queryString] ", self.do_repolist.__doc__)

    ############################################################
    # modify
    ############################################################

    def do_repomodify(self, args):
        args = self.getArgs(args)
        second = ""
        if(len(args) > 1):
            for i in range(1, len(args)):
                second += args[i] + " "
        #second = second.replace("&", "|")

        if (len(args) >= 2):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            
            status = self._service.updateItem(self.user, self.passwd, self.user, args[0], second)
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
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            status = self._service.setPermission(self.user, self.passwd, self.user, args[0], args[1])
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
        '''Image Repository get command: Get an image or only the URI by id.'''
        args = self.getArgs(args)
        
        if (len(args) == 1):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            
            imgstatus = self._service.get(self.user, self.passwd, self.user, "img", args[0], "./")

            if imgstatus:
                print "The image " + args[0] + " is located in " +imgstatus
            else:
                print "Cannot get access to the image with imgId = " + args[0]
        else:
            self.help_repoget()

    def help_repoget(self):
        '''Help message for the repoget command'''
        self.print_man("get <imgId>", self.do_repoget.__doc__)

    ############################################################
    # put
    ############################################################

    def do_repoput(self, args):

        args = self.getArgs(args)

        second = ""
        if(len(args) > 1):
            for i in range(1, len(args)):
                second += args[i] + " "

        #second = second.replace("&", "|")

        status = ""
        ok = False
        if (len(args) > 1):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            status = self._service.put(self.user, self.passwd, self.user, args[0], second)
            ok = True
        elif (len(args) == 1):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            status = self._service.put(self.user, self.passwd, self.user, args[0], "")
            ok = True
        else:
            self.help_repoput()
     
        if(ok):
            if (re.search('^ERROR', status)):
                print 'The image has not been uploaded. Exit error: ' + status
            else:
                print "The image has been uploaded and registered with id " + str(status)


    def help_repoput(self):
        msg = "Image Repository put command: Upload a new image and its " + \
            "metadata as an attributeString. If no attributeString provided some default values are " + \
            "assigned. Example of all values of attributeString (you do not need to " + \
            "provide all of them): vmtype=xen & imgtype=opennebula & os=linux & " + \
            "arch=x86_64 & description=my image & tag=tag1,tag2 & permission=public & " + \
            "imgStatus=available. Some attributes are controlled:"
        self.print_man("put <imgFile> [attributeString]", msg)

        self.type_print ("vmtype= ", IRTypes.ImgMeta.VmType)
        self.type_print ("imgtype= ", IRTypes.ImgMeta.ImgType)
        self.type_print ("imgStatus= ",IRTypes.ImgMeta.ImgStatus)
        self.type_print ("Permission=" ,IRTypes.ImgMeta.Permission)

    def type_print (self, label, irtype):
        first = True
        for line in textwrap.wrap(label + str(irtype), 64):
            if first:
                print "    %s" % (line)
                first = False
            else:
                print "      %s" % (line)


    ############################################################
    # remove
    ############################################################
    def do_reporemove(self, args):
        '''The Image Repository remove command: Remove a image from
        the repository.'''
        args = self.getArgs(args)
        if (len(args) == 1):
            #connect with the server
            if not self._service.connection():
                print "ERROR: Connection with the server failed"
                return
            if (self._service.remove(self.user, self.passwd, self.user, args[0]) == "True"):
                print "The image with imgId=" + args[0] + " has been removed"
            else:
                print "The image with imgId=" + args[0] + " has NOT been removed. Please verify the imgId and if you are the image owner"
        else:
            self.help_reporemove()

    def help_reporemove(self):
        '''Help message for the repremove command'''
        self.print_man("remove <imgId>", self.do_reporemove.__doc__)

