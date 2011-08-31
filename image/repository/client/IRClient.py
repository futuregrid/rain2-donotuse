#!/usr/bin/env python
"""
FutureGrid Image Repository Command Line Tool

This is a client of the FGIR service
"""

__author__ = 'Fugang Wang'
__version__ = '0.1'

import os, sys
from getopt import gnu_getopt, GetoptError

#TO USER full path in the modules we need to put this file (the main) just outside futuregrid dir.
#THe same apply for the server part where we need to put the main part in other file

#futuregrid.image.repository.client.

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRServiceProxy import IRServiceProxy
import textwrap


#TODOD: GVL we need to settle on one getopt function. argparse, getopt, .... we should just use one.

# TODO can we make that a shell command and than yous write a wrapper: "fg irclient ... arguments ..."
# This way this command could be a shell script.

############################################################
# usage
############################################################

def usage():

    print "\n---------------------------------"
    print "FutureGrid Image Repository Help "
    print "---------------------------------\n"
    print '''
    -h/--help: get help information
    -l/--auth: login/authentication
    -q/--list [queryString]: get list of images that meet the criteria
    -a/--setpermission <imgId> <permissionString>: set access permission
    -g/--get <img/uri> <imgId>: get an image or only the URI
    -p/--put <imgFile> [attributeString]: upload/register an image
    -m/--modify <imgId> <attributeString>: update Metadata   
    -r/--remove <imgId>: remove an image        
    --useradd <userId>: add user 
    --userdel <userId>: remove user
    --userlist: list of users
    --setuserquota <userId> <quota>: modify user quota
    --setuserrole  <userId> <role>: modify user role
    --setuserstatus <userId> <status>: modify user status
    -i/--histimg [imgId]: get usage info of an image
    -u/--histuser <userId>: get usage info of a user
          
          
Notes:
    
    attributeString example (you do not need to provide all of them): 
        vmtype=xen | imgtype=opennebula | os=linux | arch=x86_64 | 
        description=my image | tag=tag1,tag2 | permission=public | 
        imgStatus=available.
    
    queryString: * or * where field=XX, field2=YY or 
         field1,field2 where field3=XX
    
    Some argument's values are controlled:'''


    first = True
    message = ""
    for line in textwrap.wrap("vmtype= " + str(ImgMeta.VmType), 64):
        if first:
            print "         %s" % (line)
            first = False
        else:
            print "           %s" % (line)
    first = True
    for line in textwrap.wrap("imgtype= " + str(ImgMeta.ImgType), 64):
        if first:
            print "         %s" % (line)
            first = False
        else:
            print "               %s" % (line)
    first = True
    for line in textwrap.wrap("imgStatus= " + str(ImgMeta.ImgStatus), 64):
        if first:
            print "         %s" % (line)
            first = False
        else:
            print "           %s" % (line)
    first = True
    for line in textwrap.wrap("Permission= " + str(ImgMeta.Permission), 64):
        if first:
            print "         %s" % (line)
            first = False
        else:
            print "           %s" % (line)
    for line in textwrap.wrap("User Role= " + str(IRUser.Role), 100):
            if first:
                message += "         %s" % (line)
                first = False
            else:
                message += "           %s" % (line)
    for line in textwrap.wrap("User Status= " + str(IRUser.Status), 100):
        if first:
            message += "         %s" % (line)
            first = False
        else:
            message += "           %s" % (line)

############################################################
# main
############################################################

def main():
    try:
        opts, args = gnu_getopt(sys.argv[1:],
                                "hlqagprium",
                                ["help",
                                 "auth",
                                 "list",
                                 "setpermission",
                                 "get",
                                 "put",
                                 "remove",
                                 "histimg",
                                 "histuser",
                                 "modify",
                                 "useradd",
                                 "userdel",
                                 "userlist",
                                 "setuserquota",
                                 "setuserrole",
                                 "setuserstatus"
                                 ])

    except GetoptError, err:
        print "%s" % err
        print
        usage()
        sys.exit(2)
    if (len(opts) == 0):
        usage()
    else:
        service = IRServiceProxy(True)

        for o, v in opts:
            if o in ("-h", "--help"):
                usage()
            elif o in ("-l", "--auth"):
                print "in auth"
                #username = os.popen('whoami', 'r').read().strip()
                #service.auth(username)
                print service.auth("fuwang")
            elif o in ("-q", "--list"):
                if (len(args) == 0):
                    imgsList = service.query(os.popen('whoami', 'r').read().strip(), "*")
                else:
                    imgsList = service.query(os.popen('whoami', 'r').read().strip(), args[0])
                #dict wrapped into a list, convert it first
                #print imgsList

                if(imgsList[0].strip() != "None"):
                    try:
                        imgs = eval(imgsList[0])
                        print str(len(imgs)) + " items found"
                        for key in imgs.keys():
                            print imgs[key]
                    except:
                        print "Server replied: "+str(imgsList)
                        print "list: Error:" + str(sys.exc_info()[0]) + "\n"
                        service._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))
                else:
                    print "No list of images returned"

                #service.query("tstuser2", "imgId=fakeid4950877")
            elif o in ("-a", "--setpermission"):
                if (len(args) != 0):
                    status = service.setPermission(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                    if(status == "True"):
                        print "Permission of img " + args[0] + " updated"
                    else:
                        print "The permission have not been changed. " + status
                else:
                    usage()
            elif o in ("-g", "--get"):
                if (len(args) == 2):
                    img1 = service.get(os.popen('whoami', 'r').read().strip(), args[0], args[1], "./")                    
                    if img1:
                        print "The image " + imgId + " is located in " + img1
                    else:
                        print "Cannot get access to the image with imgId = " + args[1]
                else:
                    usage()

            elif o in ("-p", "--put"):
                status = 0
                ok = False
                if (len(args) == 2):
                    status = service.put(os.popen('whoami', 'r').read().strip(), None, args[0], args[1])
                    ok = True
                elif (len(args) == 1):
                    status = service.put(os.popen('whoami', 'r').read().strip(), None, args[0], "")
                    ok = True
                else:
                    usage()
                #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
                #print "image has been uploaded and registered with id " + str(id1)
                #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
                if(ok):
                    if(status == "0"):
                        print "the image has NOT been uploaded. Please, verify that the file exists and the metadata string is valid"
                    elif(status == "-1"):
                        print "the image has NOT been uploaded"
                        print "The User does not exist"
                    elif(status == "-2"):
                        print "The image has NOT been uploaded"
                        print "The User is not active"
                    elif(status == "-3"):
                        print "The image has NOT been uploaded"
                        print "The file exceed the quota"
                    else:
                        print "image has been uploaded and registered with id " + str(status)


            elif o in ("-r", "--remove"):
                if(len(args) == 1):
                    if (service.remove(os.popen('whoami', 'r').read().strip(), args[0]) == "True"):
                        print "The image with imgId=" + args[0] + " has been removed"
                    else:
                        print "The image with imgId=" + args[0] + " has NOT been removed. Please verify the imgId and if you are the image owner"
                else:
                    usage()
            elif o in ("-i", "--histimg"):
                if(len(args) == 1):
                    imgsList = service.histImg(os.popen('whoami', 'r').read().strip(), args[0])
                else:
                    imgsList = service.histImg(os.popen('whoami', 'r').read().strip(), "None")

                imgs = eval(imgsList[0])

                try:
                    imgs = eval(imgsList[0])
                    print imgs['head']
                    for key in imgs.keys():
                        if key != 'head':
                            print imgs[key]
                except:
                    print "Server replied: "+str(imgsList)
                    print "histimg: Error:" + str(sys.exc_info()[0]) + "\n"
                    service._log.error("histimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))


            elif o in ("-u", "--histuser"):
                if(len(args) == 1):
                    imgsList = service.histUser(os.popen('whoami', 'r').read().strip(), args[0])
                else:
                    imgsList = service.histUser(os.popen('whoami', 'r').read().strip(), "None")

                try:
                    users = eval(userList[0])
                    print users['head']
                    for key in users.keys():
                        if key != 'head':
                            print users[key]
                except:
                    print "Server replied: "+str(imgsList)
                    print "histuser: Error:" + str(sys.exc_info()[0]) + "\n"
                    service._log.error("histuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))


            elif o in ("-m", "--modify"):
                if (len(args) == 2):
                    success = service.updateItem(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                    #success=service.updateItem(os.popen('whoami', 'r').read().strip(), "4d66c1f9577d70165f000000", "vmType=kvm|imgType=Opennebula|os=Windows|arch=x86_64| owner=tstuser2| description=another test| tag=tsttagT, tsttagY")

                    if (success == "True"):
                        print "The item was successfully updated"
                    else:
                        print "Error in the update. Please verify that you are the owner or that you introduced the correct arguments"
                else:
                    usage()
            #This commands only can be used by users with Admin Role.
            elif o in ("--useradd"):  #args[0] is the username. It MUST be the same that the system user
                if (len(args) == 1):
                    status = service.userAdd(os.popen('whoami', 'r').read().strip(), args[0])
                    if(status == "True"):
                        print "User created successfully."
                        print "Remember that you still need to activate this user (see setuserstatus command)\n"
                    else:
                        print "The user has not been created. \n" + \
                              "Please verify that you are admin and that the username does not exist \n"
                else:
                    usage()

            elif o in ("--userdel"):
                if (len(args) == 1):
                    status = service.userDel(os.popen('whoami', 'r').read().strip(), args[0])
                    if(status == "True"):
                        print "User deleted successfully."
                    else:
                        print "The user has not been deleted. \n" + \
                              "Please verify that you are admin and that the username exists \n"
                else:
                    usage()

            elif o in ("--userlist"):
                userList = service.userList(os.popen('whoami', 'r').read().strip())
                #print userList                
                if(userList[0].strip() != "None"):
                    try:
                        imgs = eval(userList[0])
                        print str(len(imgs)) + " users found"
                        for key in imgs.keys():
                            print imgs[key]
                    except:
                        print "Server replied: "+str(imgsList)
                        print "userlist: Error:" + str(sys.exc_info()[0]) + "\n"
                        service._log.error("userlist: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
                else:
                    print "No list of images returned. \n" + \
                          "Please verify that you are admin \n"

            elif o in ("--setuserquota"):
                if (len(args) == 2):
                    status = service.setUserQuota(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                    if(status == "True"):
                        print "Quota changed successfully."
                    else:
                        print "The user quota has not been changed. \n" + \
                              "Please verify that you are admin and that the username exists \n"
                else:
                    usage()

            elif o in ("--setuserrole"):
                if (len(args) == 2):
                    status = service.setUserRole(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                    if(status == "True"):
                        print "Role changed successfully."
                    else:
                        print "The user role has not been changed. " + status + "\n"\
                      "Please verify that you are admin and that the username exists \n"
                else:
                    usage()

            elif o in ("--setuserstatus"):
                if (len(args) == 2):
                    status = service.setUserStatus(os.popen('whoami', 'r').read().strip(), args[0], args[1])
                    if(status == "True"):
                        print "Status changed successfully."
                    else:
                        print "The user status has not been changed. " + status + "\n"\
                      "Please verify that you are admin and that the username exists \n"
                else:
                    usage()
            else:
                assert False, "unhandled option"

if __name__ == "__main__":
    main()

