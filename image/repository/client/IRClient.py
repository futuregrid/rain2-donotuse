#!/usr/bin/env python
"""
FutureGrid Image Repository Command Line Tool

This is a client of the FGIR service
"""

__author__ = 'Javier Diaz, Fugang Wang'
__version__ = '0.9'

import os, sys
import argparse
import textwrap
import hashlib
from getpass import getpass
import re
#TO USER full path in the modules we need to put this file (the main) just outside futuregrid dir.
#THe same apply for the server part where we need to put the main part in other file

#futuregrid.image.repository.client.

from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRServiceProxy import IRServiceProxy



#TODOD: GVL we need to settle on one getopt function. argparse, getopt, .... we should just use one.

# TODO can we make that a shell command and than yous write a wrapper: "fg irclient ... arguments ..."
# This way this command could be a shell script.

############################################################
# usage
############################################################
"""
    print "\n---------------------------------"
    print "FutureGrid Image Repository Help "
    print "---------------------------------\n"
    print '''
    -h/--help: get help information
    -l/--auth: login/authentication
    -q/--list [queryString]: get list of images that meet the criteria
    -a/--setpermission <imgId> <permissionString>: set access permission
    -g/--get <imgId>: get an image
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
    '''
"""
def extra_help():

    string = '''
Notes:

  attributeString, queryString and quotaExpression must be enclosed by " characters 
    
  attributeString example (you do not need to provide all of them): 
    "vmtype=xen & imgtype=opennebula & os=linux & arch=x86_64 & 
    description=my image & tag=tag1,tag2 & permission=public &
    imgStatus=available".
    
  queryString: "*" or "* where field=XX", "field2=YY" or 
    "field1,field2 where field3=XX"

  quotaExpression (in bytes): "4294967296", "2048 * 1024"

  Some argument's values are controlled:
    
    '''
    #message = "\n\n\nvmtype= " + str(ImgMeta.VmType)
    
    first = True
    message = ""
    for line in textwrap.wrap("vmtype= " + str(ImgMeta.VmType), 64):
        if first:
            message += " %s" % (line)
            first = False
        else:
            message += "       %s" % (line)
    first = True
    message += "\n"
    for line in textwrap.wrap("imgtype= " + str(ImgMeta.ImgType), 64):
        if first:
            message += "     %s" % (line)
            first = False
        else:
            message += "\n           %s" % (line)
    first = True
    message += "\n"
    for line in textwrap.wrap("imgStatus= " + str(ImgMeta.ImgStatus), 64):
        if first:
            message += "     %s" % (line)
            first = False
        else:
            message += "\n       %s" % (line)
    first = True
    message += "\n"
    for line in textwrap.wrap("Permission= " + str(ImgMeta.Permission), 64):
        if first:
            message += "     %s" % (line)
            first = False
        else:
            message += "       %s" % (line)
    first = True
    message += "\n"
    for line in textwrap.wrap("User Role= " + str(IRUser.Role), 100):
            if first:
                message += "     %s" % (line)
                first = False
            else:
                message += "\n       %s" % (line)
    first = True
    message += "\n"
    for line in textwrap.wrap("User Status= " + str(IRUser.Status), 100):
        if first:
            message += "     %s" % (line)
            first = False
        else:
            message += "\n       %s" % (line)
    
    return string + message
############################################################
# main
############################################################

def main():    
    parser = argparse.ArgumentParser(prog="IRClient", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="FutureGrid Image Repository Help ",
                                     epilog=textwrap.dedent(extra_help()))
    parser.add_argument('-u', '--user', dest='user', required=True, metavar='user', help='FutureGrid User name')
    parser.add_argument('-d', '--debug', dest='debug', action="store_true", help='Print logs in the screen for debug')
    group = parser.add_mutually_exclusive_group(required=True)    
    group.add_argument('-q', '--list', dest='list', nargs='?', default='', metavar='AttributeString',
                        help='Get list of images that meet the criteria.')
    group.add_argument('-g', '--get', dest='get', metavar='imgId',
                        help='Get an image')
    group.add_argument('-p', '--put', dest='put', nargs='+', metavar=('imgFile', 'AttributeString'), help='Upload/Register an image')
    group.add_argument('-m', '--modify', dest='modify', nargs=2, metavar=('imgId', 'AttributeString'), help='Update image metadata')
    group.add_argument('-r', '--remove', dest='remove', metavar='imgId', help='Delete an image')
    group.add_argument('-s', '--setpermission', dest='setpermission', nargs=2, metavar=('imgId', 'permissionString'),
                       help='Set Access permission')
    group.add_argument('--useradd', dest='useradd', metavar='userId', help='Add a new user to the repository')
    group.add_argument('--userdel', dest='userdel', metavar='userId', help='Delete an user to the repository')
    group.add_argument('--userlist', dest='userlist', action="store_true",  help='List of users')
    group.add_argument('--setuserquota', dest='setuserquota', nargs=2, metavar=('userId', 'quotaExpresion'), help='Modify User Quota')
    group.add_argument('--setuserrole', dest='setuserrole', nargs=2, metavar=('userId', 'role'), help='Modify User Role')
    group.add_argument('--setuserstatus', dest='setuserstatus', nargs=2, metavar=('userId', 'status'), help='Modify User Status')
    group.add_argument('--histimg', dest='histimg', nargs='?', metavar='imgId', default='None', help='Get usage info of an Image')
    group.add_argument('--histuser', dest='histuser', nargs='?', metavar='userId', default='None', help='Get usage info of an User')



    args = parser.parse_args()
    #print args
    if len(sys.argv) == 3:
        print "\nERROR: You need to select and additional option to indicate the operation that you want to do. \n"
        parser.print_help()
    
    verbose = True  #This is to print the logs in the screen
    
    service = IRServiceProxy(verbose, args.debug)
    
    print "Please insert the password for the user " + args.user + ""
    m = hashlib.md5()
    m.update(getpass())
    passwd = m.hexdigest()
    
    used_args = sys.argv[1:]

    print "Your request is in the queue to be processed"

    #connect with the server
    if not service.connection():
        print "ERROR: Connection with the server failed"
        sys.exit(1)

    if ('-q' in used_args or '--list' in used_args):
                
        if (args.list == None):
            imgsList = service.query(args.user, passwd, args.user, "*")
        else:
            imgsList = service.query(args.user, passwd, args.user, args.list)
        #dict wrapped into a list, convert it first        
        #print imgsList        
        if(imgsList != None):
            try:                
                imgs = eval(imgsList)
                print str(len(imgs)) + " items found"
                for key in imgs.keys():
                    print imgs[key]
            except:
                print "Server replied: " + str(imgsList)
                print "list: Error:" + str(sys.exc_info()) + "\n"
                service._log.error("list: Error interpreting the list of images from Image Repository" + str(sys.exc_info()))
        else:
            print "No list of images returned"
                
    elif ('-g' in used_args or '--get' in used_args):        
        #if (args.get[0] == 'img' or args.get[0] == 'uri'):
        img1 = service.get(args.user, passwd, args.user, "img", args.get, "./")                    
        if img1:
            print "The image " + args.get + " is located in " + img1
        else:
            print "Cannot get access to the image with imgId = " + args.get
        #else:
        #    print "Error: First argument of -g/--get must be 'img' or 'uri'"
        

    elif ('-p' in used_args or '--put' in used_args):
        status = ""
        ok = False
        if (len(args.put) == 2):
            status = service.put(args.user, passwd, args.user, args.put[0], args.put[1])
            ok = True
        elif (len(args.put) == 1):
            status = service.put(args.user, passwd, args.user, args.put[0], "")
            ok = True
        else:
            usage()
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst3.iso", "vmtype=vmware")
        #print "image has been uploaded and registered with id " + str(id1)
        #id2 = service.put(os.popen('whoami', 'r').read().strip(), None, "/home/javi/tst2.iso", "vmtype=11|imgType=0|os=UBUNTU|arch=x86_64| owner=tstuser2| description=another test| tag=tsttaga, tsttagb")
        if(ok):            
            if (re.search('^ERROR', status)):
                print 'The image has not been uploaded. Exit error: ' + status
            else:
                print "The image has been uploaded and registered with id " + str(status)
                
    elif ('-m' in used_args or '--modify' in used_args):        
        success = service.updateItem(args.user, passwd, args.user, args.modify[0], args.modify[1])    
        if (success == "True"):
            print "The item was successfully updated"
        else:
            print "Error in the update. Please verify that you are the owner and the attribute string"
        
    elif ('-r' in used_args or '--remove' in used_args):        
        output = service.remove(args.user, passwd, args.user, args.remove)
        if ( output == "True"):
            print "The image with imgId=" + args.remove + " has been removed."
        else:
            print "The image with imgId=" + args.remove + " has NOT been removed. Please verify the imgId and if you are the image owner"
        
    elif('-s' in used_args or '--setpermission' in used_args):        
        status = service.setPermission(args.user, passwd, args.user, args.setpermission[0], args.setpermission[1])
        if(status == "True"):
            print "Permission of img " + args.setpermission[0] + " updated"
        else:
            print "The permission have not been changed. " + status
          
    #This commands only can be used by users with Admin Role.
    elif ('--useradd' in used_args):  #args[0] is the username. It MUST be the same that the system user
        
        status = service.userAdd(args.user, passwd, args.user, args.useradd)
        if(status == "True"):
            print "User created successfully."
            print "Remember that you still need to activate this user (see --setuserstatus command)\n"
        else:
            print "The user has not been created. \n" + \
                  "Please verify that you are admin and that the username does not exist \n"
        

    elif ('--userdel' in used_args):
        
        status = service.userDel(args.user, passwd, args.user, args.userdel)
        if(status == "True"):
            print "User deleted successfully."
        else:
            print "The user has not been deleted. \n" + \
                  "Please verify that you are admin and that the username exists \n"
        
    elif ('--userlist' in used_args):
        userList = service.userList(args.user, passwd, args.user)
        #print userList                
        if(userList.strip() != "None"):
            try:
                imgs = eval(userList)
                print str(len(imgs)) + " users found"
                for key in imgs.keys():
                    print imgs[key]
            except:
                print "Server replied: " + str(userList)
                print "userlist: Error:" + str(sys.exc_info()[0]) + "\n"
                service._log.error("userlist: Error interpreting the list of users from Image Repository" + str(sys.exc_info()[0]))
        else:
            print "No list of images returned. \n" + \
                  "Please verify that you are admin \n"
                  
#LOOK into how to use math ops, maybe we need to put it between ""
    elif ('--setuserquota' in used_args):
        
        status = service.setUserQuota(args.user, passwd, args.user, args.setuserquota[0], args.setuserquota[1])
        if(status == "True"):
            print "Quota changed successfully."
        else:
            print "The user quota has not been changed. \n" + \
                  "Please verify that you are admin and that the username exists \n"
        

    elif ('--setuserrole' in used_args):
        
        status = service.setUserRole(args.user, passwd, args.user, args.setuserrole[0], args.setuserrole[1])
        if(status == "True"):
            print "Role changed successfully."
        else:
            print "The user role has not been changed. " + status + "\n"\
          "Please verify that you are admin and that the username exists \n"
        

    elif ('--setuserstatus' in used_args):
        
        status = service.setUserStatus(args.user, passwd, args.user, args.setuserstatus[0], args.setuserstatus[1])
        if(status == "True"):
            print "Status changed successfully."
        else:
            print "The user status has not been changed. " + status + "\n"\
          "Please verify that you are admin and that the username exists \n"
                
    #these are again for eveyone
    elif ('--histimg' in used_args):
        if( args.histimg != None ):
            imgsList = service.histImg(args.user, passwd, args.user, args.histimg)
        else:
            imgsList = service.histImg(args.user, passwd, args.user, "None")        
        try:
            imgs = eval(imgsList)            
            for key in imgs.keys():                                
                print imgs[key]
        except:
            print "Server replied: " + str(imgsList)
            print "histimg: Error:" + str(sys.exc_info()) + "\n"
            service._log.error("histimg: Error interpreting the list of images from Image Repository" + str(sys.exc_info()[0]))

    elif('--histuser' in used_args):
        if( args.histuser != None):
            userList = service.histUser(args.user, passwd, args.user, args.histuser)
        else:
            userList = service.histUser(args.user, passwd, args.user, "None")
        
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
                service._log.error("histuser: Error interpreting the list of users from Image Repository" + str(sys.exc_info()))



if __name__ == "__main__":
    main()

