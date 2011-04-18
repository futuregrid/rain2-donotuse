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


class fgShellRepo(Cmd):

    ############################################################
    #
    ############################################################
    def __init__(self):
        self._service = IRServiceProxy()

    ############################################################
    # test
    ############################################################
   
    @options([make_option('-q','--quick', help='Make things fast'),
              make_option('-s','--slow', type=int, help='Make things slow')]) 
    def do_repotest(self, args, opts):
        """Test Help"""
        arg = ''.join(args)      
        print opts.quick
        print opts.slow
        self._log.error("SHElll test in fgshell repo")

    ############################################################
    # hist img
    ############################################################
    
    def do_repohistimg(self, args):        
        args=self.getArgs(args)
        
        if(len(args)==1):
            imgsList=self._service.histImg(os.popen('whoami', 'r').read().strip(), args[0])
        else:
            imgsList=self._service.histImg(os.popen('whoami', 'r').read().strip(), "None")
        
        try:
            imgs = eval(imgsList[0])            
            print imgs['head']
            for key in imgs.keys():
                if key != 'head':
                    print imgs[key]     
        except:
            print "do_repohistimg: Error:"+str(sys.exc_info()[0])+"\n"                
            self._log.error("do_repohistimg: Error interpreting the list of images from Image Repository"+str(sys.exc_info()[0]))
       
    def help_repohistimg(self):
        print  "Image Repository histimg command: Return information about the image historical usage. \n "+ \
               "                                  It has one optional argument [imgId]\n"
    
    def do_repohistuser(self, args):        
        args=self.getArgs(args)
        
        if(len(args)==1):
            userList=self._service.histUser(os.popen('whoami', 'r').read().strip(), args[0])
        else:
            userList=self._service.histUser(os.popen('whoami', 'r').read().strip(), "None")
        
        try:
            #print userList
            users = eval(userList[0])            
            print users['head']            
            for key in users.keys():
                if key != 'head':
                    print users[key]     
        except:
            print "do_repohistuser: Error:"+str(sys.exc_info()[0])+"\n"                
            self._log.error("do_repohistuser: Error interpreting the list of users from Image Repository"+str(sys.exc_info()[0]))
       
    def help_repohistuser(self):
        print  "Image Repository histuser command: Return information about the user historical usage. \n "+ \
               "                                  It has one optional argument [userId]\n"
    ############################################################
    # user add
    ############################################################
    
    def do_repouseradd(self, args):
        args=self.getArgs(args)                
        if (len(args)==1):
            status=self._service.userAdd(os.popen('whoami', 'r').read().strip(), args[0])                
            if(status=="True"):
                print "User created successfully."
                print "Remember that you still need to activate this user (see setuserstatus command)\n"
            else:
                print "The user has not been created. \n"+\
                      "Please verify that you are admin and that the username does not exist \n"
        else:
            self.help_repouseradd()
            
    def help_repouseradd(self):

        msg = '''\
              Image Repository useradd command: Add new user (only Admin
              user can execut it) It has one arguments <userId> (userId must be the
              username in the system.)'''
        self.print_man("user add", msg)               

    ############################################################
    # user del
    ############################################################
    
    def do_repouserdel(self, args):
        args=self.getArgs(args)         
        if (len(args)==1):
            status=self._service.userDel(os.popen('whoami', 'r').read().strip(), args[0])                
            if(status=="True"):
                print "User deleted successfully."                
            else:
                print "The user has not been deleted. \n"+\
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_repouserdel()
    
    def help_repouserdel(self):
        msg = "Image Repository userdel command: Remove a user (only Admin user can execut it) \n"+ \
               "                                  It has one arguments <userId> \n"
        self.print_man("userdel", msg)

    ############################################################
    # userlist
    ############################################################
    
    def do_repouserlist(self, args):        
        #args=self.getArgs(args)      
        ok=False         
        
        userList=self._service.userList(os.popen('whoami', 'r').read().strip())
      
        if(userList[0].strip()!="None"):
            try:
                imgs = eval(userList[0])
                print str(len(imgs)) + " users found"
                for key in imgs.keys():
                    print imgs[key]               
            except:
                print "do_repouserlist: Error:"+str(sys.exc_info()[0])+"\n"                
                self._log.error("do_repouserlist: Error interpreting the list of users from Image Repository"+str(sys.exc_info()[0]))
        else:
            print "No list of images returned. \n" +\
                  "Please verify that you are admin \n"  
            
    def help_repouserlist(self):
        print  "Image Repository userlist command: Get list of users \n"
                

    ############################################################
    #
    ############################################################
    
    def do_reposetuserquota(self, args):
        args=self.getArgs(args)         
        if (len(args)==2):
            status=self._service.setUserQuota(os.popen('whoami', 'r').read().strip(), args[0], args[1])                
            if(status=="True"):
                print "User quota changed successfully."                
            else:
                print "The user quota has not been changed. \n"+\
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_reposetuserquota()
    
    def help_reposetuserquota(self):
        print  "Image Repository setuserquota command: Establish disk space available for users (this is given in bytes) \n"+ \
               "                                  It has one arguments <userId> <quota in bytes> (Math expressions like 4*1024 also works)\n"

    ############################################################
    # userrole
    ############################################################
    
    def do_reposetuserrole(self, args):
        args=self.getArgs(args)         
        if (len(args)==2):
            status=self._service.setUserRole(os.popen('whoami', 'r').read().strip(), args[0], args[1])                
            if(status=="True"):
                print "User role has been changed successfully."                
            else:
                print "The user role has not been changed. "+status +"\n"\
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_reposetuserrole()
    
    def help_reposetuserrole(self):
        print  "Image Repository setuserrole command: Change role of a particular user \n"+ \
               "                                  It has one arguments <userId> <role>\n" +\
               "                                  Available roles: "+str(IRTypes.IRUser.Role)+"\n"

    ############################################################
    # userstatus
    ############################################################
    
    def do_reposetuserstatus(self, args):
        args=self.getArgs(args)         
        if (len(args)==2):
            status=self._service.setUserStatus(os.popen('whoami', 'r').read().strip(), args[0], args[1])                
            if(status=="True"):
                print "User role has been changed successfully."                
            else:
                print "The user status has not been changed. "+status +"\n"\
                      "Please verify that you are admin and that the username exists \n"
        else:
            self.help_reposetuserstatus()
    
    def help_reposetuserstatus(self):
        print  "Image Repository setuserstatus command: Change status of a particular user \n"+ \
               "                                  It has one arguments <userId> <status>\n" +\
               "                                  Available status: "+str(IRTypes.IRUser.Status)+"\n"

    ############################################################
    # list
    ############################################################
            
    def do_repolist(self, args):        
        #args=self.getArgs(args)      
        ok=False         
        
        if (args.strip()==""):
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), "*")            
        else:
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), args)
        #else:
        #    self.help_repolist()
        
        if(imgsList[0].strip()!="None"):
            try:
                imgs = eval(imgsList[0])
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]                
            except:
                print "do_repolist: Error:"+str(sys.exc_info()[0])+"\n"                
                self._log.error("do_repolist: Error interpreting the list of images from Image Repository"+str(sys.exc_info()[0]))
        else:
            print "No list of images returned"   
            
    def help_repolist(self):
        print  "Image Repository list command: Get list of images that meet the criteria \n"+  \
                "                              It takes one optional argument [queryString] \n"+ \
                "                              If not argument provided it get all \n"+ \
                "   queryString can be: * ; * where field=XX, field2=YY; \n"+ \
                "                       field1,field2 where field3=XX \n"

    ############################################################
    # modify
    ############################################################
                
    def do_repomodify(self, args):       
        args=self.getArgs(args)
        second=""
        if(len(args)>1):
            for i in range(1,len(args)):
                second+=args[i]+" "
        second=second.replace("&","|")
                  
        if (len(args)>=2):
            status=self._service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], second)
            if(status=="True"):
                print "The metadata of img "+args[0]+" has been updated"
            else:
                print "Error in the update. Please verify that you are the owner or that you introduced the correct arguments"
        else:
            self.help_repomodify()        
            
    def help_repomodify(self):
        print  "Image Repository modify command: Modify image metadata. \n"+ \
               "                              It has two arguments <imgId> <Metadata> \n"+\
               "Example of all values of attributeString (you do not need to provide all of them) \n" \
               "vmtype=xen & imgtype=opennebula & os=linux & arch=x86_64 & description=my image & tag=tag1,tag2 & permission=public & imgStatus=available \n"+\
                "Some attributes are controlled: \n"+ \
                "     vmtype= "+str(IRTypes.ImgMeta.VmType)+"\n"\
                "     imgtype= "+str(IRTypes.ImgMeta.ImgType)+"\n"\
                "     imgStatus= "+str(IRTypes.ImgMeta.ImgStatus)+"\n"\
                "     Permission= "+str(IRTypes.ImgMeta.Permission)

    ############################################################
    # permission
    ############################################################
    
    def do_reposetpermission(self, args):       
        args=self.getArgs(args)                
        if (len(args)==2):            
            status=self._service.setPermission(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            if(status=="True"):
                print "Permission of img "+args[0]+" updated"
            else:
                print "The permission have not been changed. "+status
        else:
            self.help_reposetpermission()        
            
    def help_reposetpermission(self):
        print  "Image Repository setPermission command: Change image permission. \n"+ \
               "                              It has two arguments <imgId> <permission> \n"+ \
               "                              Permission= "+str(IRTypes.ImgMeta.Permission)

    ############################################################
    # get
    ############################################################
                           
    def do_repoget(self, args): 
        args=self.getArgs(args)   
                     
        if (len(args)==2):
            imgstatus=self._service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            
            if imgstatus:
                print imgstatus
            else:
                print "Cannot get access to the image with imgId = " + args[1]
        else:
            self.help_repoget()        
            
    def help_repoget(self):
        print  "Image Repository get command: Get an image or only the URI by id. \n"+ \
               "                              It has two arguments <img OR uri> <imgId>"

    ############################################################
    # put
    ############################################################
    
    def do_repoput(self, args):       
        
        args=self.getArgs(args)            
        
        second=""
        if(len(args)>1):
            for i in range(1,len(args)):
                second+=args[i]+" "
        
        second=second.replace("&","|")          
            
        status=0
        ok=False
        if (len(args)>1):                
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, args[0], second)
            ok=True
        elif (len(args)==1):
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, args[0], "")
            ok=True
        else:
            self.help_repoput()
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
        #print "image has been uploaded and registered with id " + str(id1)
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
        #print status        
        if(ok):
            if(status=="0"):
                print "The image has NOT been uploaded. Please, verify that the file exists and the metadata string is valid"
            elif(status=="-1"):
                print "The image has NOT been uploaded"
                print "The User does not exist"
            elif(status=="-2"):
                print "The image has NOT been uploaded"
                print "The User is not active"
            elif(status=="-3"):
                print "The image has NOT been uploaded"
                print "The file exceed the quota"
            else:
                print "image has been uploaded and registered with id " + str(status)
        
        
    def help_repoput(self):
        print  "The Image Repository put command has two arguments <imgId> [attributeString] \
                \n If no attributeString provided some default values are assigned \n"+ \
                "Example of all values of attributeString (you do not need to provide all of them) \n" \
                "vmtype=xen & imgtype=opennebula & os=linux & arch=x86_64 & description=my image & tag=tag1,tag2 & permission=public & imgStatus=available \n"+\
                "Some attributes are controlled: \n"+ \
                "     vmtype= "+str(IRTypes.ImgMeta.VmType)+"\n"\
                "     imgtype= "+str(IRTypes.ImgMeta.ImgType)+"\n"\
                "     imgStatus= "+str(IRTypes.ImgMeta.ImgStatus)+"\n"\
                "     Permission= "+str(IRTypes.ImgMeta.Permission)

    ############################################################
    # remove
    ############################################################


    def do_reporemove(self,args):
        """The Image Repository remove command has two arguments <imgId>"""
        args=self.getArgs(args)                 
        if (len(args)==1):
            if (self._service.remove(os.popen('whoami', 'r').read().strip(), args[0]) == "True"):
                print "The image with imgId=" + args[0] +" has been removed"
            else:
                print "The image with imgId=" + args[0] +" has NOT been removed. Please verify the imgId and if you are the image owner"
        else:
            self.help_reporemove() 
            
    def help_reporemove(self):
        print  "The Image Repository remove command has one arguments <imgId>"
        
    
