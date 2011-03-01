#!/usr/bin/env python
"""
FutureGrid Image Repository Command Line Tool

This is a client of the FGIR service
"""

__author__ = 'Fugang Wang'
__version__ = '0.1'

import os, sys
from getopt import gnu_getopt, GetoptError

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRTypes import IRCredential
from IRServiceProxy import IRServiceProxy

def usage():
    print "options:"
    print '''
        -h/--help: get help information
        -l/--auth: login/authentication
        -q/--list [queryString]: get list of images that meet the criteria
        -a/--setPermission <imgId> <permissionString>: set access permission
        -g/--get <img/uri> <imgId>: get a image or only the URI by id
        -p/--put <imgFile> <attributeString>: upload/register an image
        -m/--modify <imgId> <attributeString>: update Metadata   
        -r/--remove <imgId>: remove an image from the repository
        -i/--histimg <imgId>: get usage info of an image
        -u/--histuser <userId>: get usage info of a user
          '''

def main():
    try:
        opts, args = gnu_getopt(sys.argv[1:],
                                "hlqagprium",  
                                ["help",        
                                 "auth",
                                 "list",
                                 "setPermission",
                                 "get",
                                 "put",
                                 "remove",
                                 "histimg",
                                 "histuser",
                                 "modify"
                                 ])

    except GetoptError, err:
        print "%s" % err
        print
        usage()
        sys.exit(2)
    if (len(opts)==0):
        usage()
    else:
        service = IRServiceProxy()

        for o, v in opts:
            if o in ("-h", "--help"):
                usage()
            elif o in ("-l", "--auth"):
                print "in auth"
                #username = os.popen('whoami', 'r').read().strip()
                #service.auth(username)
                print service.auth("fuwang")
            elif o in ("-q", "--list"):
                if (len(args)==0):
                    imgsList = service.query(os.popen('whoami', 'r').read().strip(), "*")
                else:
                    imgsList = service.query(os.popen('whoami', 'r').read().strip(), args[0])
                #dict wrapped into a list, convert it first
                #print imgsList
                imgs = eval(imgsList[0])
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]
                #service.query("tstuser2", "imgId=fakeid4950877")
            elif o in ("-a", "--setPermission"):
                status=service.setPermission(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                if(status=="True"):
                    print "Permission of img "+args[0]+" updated"
                else:
                    print "The permission have not been changed. "+status
            elif o in ("-g", "--get"):                               
                img1 = service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                #img2 = service.get(os.popen('whoami', 'r').read().strip(), option, id2)
                if img1:
                    print img1
                else:
                    print "The image with imgId= " + args[1] +" has not been found"
    
                #if img2:
                #    print img2
                #else:
                #    print "not found for imgId=" + id2
    
            elif o in ("-p", "--put"):
                status=0
                if (len(args)==2):                
                    status = service.put(os.popen('whoami', 'r').read().strip(), None, args[0], args[1])
                elif (len(args)==1):
                    status = service.put(os.popen('whoami', 'r').read().strip(), None, args[0], "")
                #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
                #print "image has been uploaded and registered with id " + str(id1)
                #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
                                
                if(status==0):
                    print "the image has NOT been uploaded"
                elif(status==-1):
                    print "the image has NOT been uploaded"
                    print "The User does not exist"
                else:
                    print "image has been uploaded and registered with id " + str(status)
                
                    
            elif o in ("-r", "--remove"):
                if (service.remove(os.popen('whoami', 'r').read().strip(), args[0]) == "True"):
                    print "The image with imgId=" + args[0] +" has been removed"
                else:
                    print "The image with imgId=" + args[0] +" has NOT been removed. Please verify the imgId and if you are the image owner"
            elif o in ("-i", "--histimg"):
                print "in image usage"
            elif o in ("-u", "--histuser"):
                print "in user usage"
            elif o in ("-m", "--modify"): 
                if (len(args)==2):
                    success=service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                    #success=service.updateItem(os.popen('whoami', 'r').read().strip(), "4d66c1f9577d70165f000000", "vmType=kvm|imgType=Opennebula|os=Windows|arch=x86_64| owner=tstuser2| description=another test| tag=tsttagT, tsttagY")
                    
                    if (success=="True"):
                        print "The item was successfully updated"
                    else:
                        print "Error in the update. Please verify that you are the owner or that you introduced the correct arguments"
                else:
                    usage()
            else:
                assert False, "unhandled option"

if __name__ == "__main__":
    main()

