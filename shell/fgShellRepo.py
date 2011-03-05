#!/usr/bin/python
"""
FutureGrid Command Line Interface

Image Repository
"""
import os
import cmd
import readline
import sys
from futuregrid.shell import fgShellUtils
from futuregrid.image.repository.client.IRServiceProxy import IRServiceProxy
from futuregrid.image.repository.client import IRTypes
import logging
from futuregrid.utils import fgLog


class fgShellRepo(cmd.Cmd):
    
    def __init__(self):
        self._service = IRServiceProxy()
    
    def do_repotest(self,args):
        """Test Help"""
        print "This is a test"
       
    def do_repolist(self, args):
        
        #args=self.getArgs(args)        
        
        ok=False         
        
        if (args.strip()==""):
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), "*")
            ok=True
        else:
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), args)
            ok=True
        #else:
        #    self.help_repolist()
        
        if(ok):
            try:
                imgs = eval(imgsList[0])
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]                
            except:
                print "do_repo_list: Error:"+str(sys.exc_info()[0])+"\n"                
                self._log.error("do_repo_list: Error interpreting the list of images from Image Repository"+str(sys.exc_info()[0]))
             
            
    def help_repolist(self):
        print  "Image Repository list command: Get list of images that meet the criteria \n"+  \
                "                              It takes one optional argument [queryString] \n"+ \
                "                              If not argument provided it get all \n"+ \
                "   queryString can be: * ; * where field=XX, field2=YY; \n"+ \
                "                       field1,field2 where field3=XX \n"
                
    def do_repomodify(self, args):       
        args=self.getArgs(args)                
        if (len(args)==2):
            status=self._service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], args[1])
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
               "\"vmtype=xen|imgtype=opennebula|os=linux|arch=x86_64|description=my image|tag=tag1,tag2|permission=public|imgStatus=available\" \n"+\
                "Some attributes are controlled: \n"+ \
                "     vmtype= "+str(IRTypes.ImgMeta.VmType)+"\n"\
                "     imgtype= "+str(IRTypes.ImgMeta.ImgType)+"\n"\
                "     imgStatus= "+str(IRTypes.ImgMeta.ImgStatus)+"\n"\
                "     Permission= "+str(IRTypes.ImgMeta.Permission)
    
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
                           
    def do_repoget(self, args): 
        args=self.getArgs(args)                
        if (len(args)==2):
            print self._service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
            
        else:
            self.help_repoget()        
            
    def help_repoget(self):
        print  "Image Repository get command: Get an image or only the URI by id. \n"+ \
               "                              It has two arguments <img OR uri> <imgId>"
    
    def do_repoput(self, args):
        args=self.getArgs(args)            
        print args
        second=""
        if(len(args)>1):
            for i in range(1,len(args)):
                second+=args[i]+" "
                    
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
        if(ok):
            if(status==0):
                print "The image has NOT been uploaded. Please, verify that the file exists and the metadata string is valid"
            elif(status==-1):
                print "The image has NOT been uploaded"
                print "The User does not exist"
            else:
                print "image has been uploaded and registered with id " + str(status)
        
        
    def help_repoput(self):
        print  "The Image Repository put command has two arguments <imgId> [attributeString] \
                \n If no attributeString provided some default values are assigned \n"+ \
                "Example of all values of attributeString (you do not need to provide all of them) \n" \
                "\"vmtype=xen|imgtype=opennebula|os=linux|arch=x86_64|description=my image|tag=tag1,tag2|permission=public|imgStatus=available\" \n"+\
                "Some attributes are controlled: \n"+ \
                "     vmtype= "+str(IRTypes.ImgMeta.VmType)+"\n"\
                "     imgtype= "+str(IRTypes.ImgMeta.ImgType)+"\n"\
                "     imgStatus= "+str(IRTypes.ImgMeta.ImgStatus)+"\n"\
                "     Permission= "+str(IRTypes.ImgMeta.Permission)


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
        
    
