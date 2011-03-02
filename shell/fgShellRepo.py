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
import logging
from futuregrid.utils import fgLog


class fgShellRepo(cmd.Cmd):
    
    def __init__(self):
        self._service = IRServiceProxy()
    
    def do_repolist(self, args):
        
        args=self.getArgs(args)        
        
        ok=False         
        
        if (len(args)==0):
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), "*")
            ok=True
        elif (len(values)==1):
            imgsList = self._service.query(os.popen('whoami', 'r').read().strip(), args[0])
            ok=True
        else:
            self.help_repo_get()
        
        if(ok):
            try:
                imgs = eval(imgsList[0])
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]
            except:
                print "do_repo_list: Error:", sys.exc_info()[0]                
                fgLog.error("do_repo_list: Error interpreting the list of images from Image Repository"+str(sys.exc_info()[0]))
             
            
    def help_repolist(self):
        print  "Image Repository list command: \n"+ \
                "    Get list of images that meet the criteria \n"+  \
                "    It takes one optional argument [queryString] \n"+ \
                "    If not argument provided it get all \n"+ \
                "    queryString can be: * ; * where field=XX, field2=YY; field1, field2; "+ \
                "    field1,field2 where field3=XX; field4=YY \n"
                
    def do_repoget(self, args):
        """Get an image or only the URI by id
           <img OR uri> <imgId> 
        """
        args=self.getArgs(args)                
        if (len(args)==2):
            print self._service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
        else:
            self.help_repo_get()        
            
    def help_repoget(self):
        print  "The Image Repository get command has two arguments <img OR uri> <imgId>"
    
    def do_repoput(self, args):
        """Put new image 
           <imgId> [metadataString]
        """
        args=self.getArgs(args)             
        if (len(values)==2):
            print self._service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
        else:
            self.help_repo_get()        
        
        status=0
        ok=False
        if (len(values)==2):                
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, args[0], args[1])
            ok=True
        elif (len(values)==1):
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, args[0], "")
            ok=True
        else:
            self.help_repo_put()
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
        #print "image has been uploaded and registered with id " + str(id1)
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
        if(ok):
            if(status==0):
                print "the image has NOT been uploaded"
            elif(status==-1):
                print "the image has NOT been uploaded"
                print "The User does not exist"
            else:
                print "image has been uploaded and registered with id " + str(status)
        
        
    def help_repoput(self):
        print  "The Image Repository get command has two arguments <imgId> [attributeString] \
                \n If no atributeString provided some default values are assigned"

    def do_reporemove(self,args):
        """The Image Repository remove command has two arguments <imgId>"""
        args=self.getArgs(args)                 
        if (len(args)==1):
            if (self._service.remove(os.popen('whoami', 'r').read().strip(), args[0]) == "True"):
                print "The image with imgId=" + args[0] +" has been removed"
            else:
                print "The image with imgId=" + args[0] +" has NOT been removed. Please verify the imgId and if you are the image owner"
        else:
            self.help_repo_remove() 
            
    def help_reporemove(self):
        print  "The Image Repository remove command has one arguments <imgId>"
        
    
