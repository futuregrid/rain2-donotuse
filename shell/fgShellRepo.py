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
            
    def do_repo_get(self, args):
        """Get an image or only the URI by id
           <img OR uri> <imgId> 
        """
        values=args.split(" ")                
        if (len(values)==2):
            print self._service.get(os.popen('whoami', 'r').read().strip(), values[0], values[1])
        else:
            self.help_repo_get()        
            
    def help_repo_get(self):
        print  "The Image Repository get command has two arguments <img OR uri> <imgId>"
    
    def do_repo_put(self, args):
        """Put new image 
           <imgId> [metadataString]
        """
        values=args.split(" ")                
        if (len(values)==2):
            print self._service.get(os.popen('whoami', 'r').read().strip(), values[0], values[1])
        else:
            self.help_repo_get()        
        
        status=0
        ok=False
        if (len(values)==2):                
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, values[0], values[1])
            ok=True
        elif (len(values)==1):
            status = self._service.put(os.popen('whoami', 'r').read().strip(), None, values[0], "")
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
        
        
    def help_repo_put(self):
        print  "The Image Repository get command has two arguments <imgId> [attributeString] \
                \n If no atributeString provided some default values are assigned"

    def do_repo_remove(self):
        if (service.remove(os.popen('whoami', 'r').read().strip(), args[0]) == "True"):
            print "The image with imgId=" + args[0] +" has been removed"
        else:
            print "The image with imgId=" + args[0] +" has NOT been removed. Please verify the imgId and if you are the image owner"
