#!/usr/bin/env python
"""
FutureGrid Command Line Interface

Rain
"""

import os
#import cmd
import readline
import sys
from futuregrid.shell import fgShellUtils
import logging
from futuregrid.utils import fgLog
from cmd2 import Cmd
from cmd2 import options
from cmd2 import make_option
import textwrap


class fgShellRain(Cmd):

    def __init__(self):
        #self._service = rain()
        print "Init Rain"

    def do_rainrun(self, args):
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
                rest = ""
                for j in range(len(newlist)):
                    rest+=" "+newlist[j]
                if rest.strip() != "":
                    rest=rest.strip()
                    sys.argv += [rest]
                #sys.argv += [prefix+'-'+argslist[i]]
                prefix = ''

        parser = argparse.ArgumentParser(prog="RainClient", formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description="FutureGrid Image Deployment Help ")    
        parser.add_argument('-u', '--user', dest='user', required=True, metavar='user', help='FutureGrid User name')
        parser.add_argument('-d', '--debug', dest='debug', action="store_true", help='Print logs in the screen for debug')
        parser.add_argument('-k', '--kernel', dest="kernel", metavar='Kernel version', help="Specify the desired kernel" 
                            "(must be exact version and approved for use within FG). Not yet supported")
        group = parser.add_mutually_exclusive_group()
        group.add_argument('-i', '--deployedimageid', dest='deployedimageid', metavar='ImgId', help='Id of the image in the target infrastructure. This assumes that the image'
                           ' is deployed in the selected infrastructure.')
        group.add_argument('-r', '--imgid', dest='imgid', metavar='ImgId', help='Id of the image stored in the repository')
        group1 = parser.add_mutually_exclusive_group()
        group1.add_argument('-x', '--xcat', dest='xcat', metavar='MachineName', help='Deploy image to xCAT. The argument is the machine name (minicluster, india ...)')
        group1.add_argument('-e', '--euca', dest='euca', nargs='?', metavar='Address:port', help='Deploy the image to Eucalyptus, which is in the specified addr')
        #group1.add_argument('-o', '--opennebula', dest='opennebula', nargs='?', metavar='Address', help='Deploy the image to OpenNebula, which is in the specified addr')
        #group1.add_argument('-n', '--nimbus', dest='nimbus', nargs='?', metavar='Address', help='Deploy the image to Nimbus, which is in the specified addr')
        group1.add_argument('-s', '--openstack', dest='openstack', nargs='?', metavar='Address', help='Deploy the image to OpenStack, which is in the specified addr')
        parser.add_argument('-v', '--varfile', dest='varfile', help='Path of the environment variable files. Currently this is used by Eucalyptus and OpenStack')
        parser.add_argument('-m', '--numberofmachines', dest='machines', default=1, help='Number of machines needed.')
        parser.add_argument('-j', '--jobscript', dest='jobscript', required=True, help='Script to execute on the provisioned images.')
        
        args = parser.parse_args()
        
        used_args = sys.argv[1:]
    
        image_source = "repo"
        image = args.imgid    
        if args.deployedimageid != None:
            image_source = "deployed"
            image = args.deployedimageid
            
        if not os.path.isfile(args.jobscript):
            print 'Not script file found. Please specify an script file using the paramiter -j/--jobscript'            
            sys.exit(1)
        
        
        output = None
        if image_source == "repo":
            self.imgdeploy.setKernel(args.kernel)
            self.imgdeploy.setDebug(args.debug)    
            #XCAT
            if args.xcat != None:
                if args.imgid == None:
                    print "ERROR: You need to specify the id of the image that you want to deploy (-r/--imgid option)."
                    print "The parameter -i/--image cannot be used with this type of deployment"
                    sys.exit(1)
                else:
                    output = self.imgdeploy.xcat_method(args.xcat, args.imgid)
            else:
                ldap = True #we configure ldap to run commands and be able to login from on vm to other
                varfile = ""
                if args.varfile != None:
                    varfile = os.path.expanduser(args.varfile)
                #EUCALYPTUS    
                if ('-e' in used_args or '--euca' in used_args):
                    if not args.getimg:
                        if args.varfile == None:
                            print "ERROR: You need to specify the path of the file with the Eucalyptus environment variables"
                        elif not os.path.isfile(str(os.path.expanduser(varfile))):
                            print "ERROR: Variable files not found. You need to specify the path of the file with the Eucalyptus environment variables"
                        else:    
                            output = self.imgdeploy.iaas_generic(args.euca, image, image_source, "euca", varfile, args.getimg, ldap)        
                    else:    
                        output = self.imgdeploy.iaas_generic(args.euca, image, image_source, "euca", varfile, args.getimg, ldap)
                #OpenNebula
                elif ('-o' in used_args or '--opennebula' in used_args):
                    output = self.imgdeploy.iaas_generic(args.opennebula, image, image_source, "opennebula", varfile, args.getimg, ldap)
                #NIMBUS
                elif ('-n' in used_args or '--nimbus' in used_args):
                    #TODO        
                    print "Nimbus deployment is not implemented yet"
                elif ('-s' in used_args or '--openstack' in used_args):
                    if not args.getimg:
                        if args.varfile == None:
                            print "ERROR: You need to specify the path of the file with the OpenStack environment variables"
                        elif not os.path.isfile(str(os.path.expanduser(varfile))):
                            print "ERROR: Variable files not found. You need to specify the path of the file with the OpenStack environment variables"
                        else:    
                            output = self.imgdeploy.iaas_generic(args.openstack, image, image_source, "openstack", varfile, args.getimg, ldap)
                    else:    
                        output = self.imgdeploy.iaas_generic(args.openstack, image, image_source, "openstack", varfile, args.getimg, ldap)
                else:
                    print "ERROR: You need to specify a deployment target"
        else:
            output = args.deployedimageid
            
        if output != None:
            rain = RainClient(verbose, args.debug)
            target = ""
            if args.xcat != None:            
                output = rain.baremetal(output, args.jobscript, args.machines)
                print output
            else:
                if ('-e' in used_args or '--euca' in used_args):
                    output = rain.euca(output, args.jobscript, args.machines)
                elif ('-o' in used_args or '--opennebula' in used_args):
                    output = rain.opennebula(output, args.jobscript, args.machines)
                elif ('-n' in used_args or '--nimbus' in used_args):
                    output = rain.nimbus(output, args.jobscript, args.machines)
                elif ('-s' in used_args or '--openstack' in used_args):
                    output = rain.openstack(output, args.jobscript, args.machines)
                else:
                    print "ERROR: You need to specify a Rain target (xcat, eucalyptus or openstack)"
            
            
        else:
            print "ERROR: invalid image id."
        
    """
    def do_rainmove(self, args):

        self.help_rainmove()

    def help_rainmove(self):
        msg = "RAIN move command: Move a node between between IaaS clouds to and from HPC. " + \
              "Available destination are: HPC, eucalyptus, nimbus\n "
        self.print_man("move <hostname> <destination>", msg)

    def do_raingroup(self, args):

        self.help_raingroup()

    def help_raingroup(self):
        msg = "RAIN group command: Define a group of nodes and reserve them. \n "
        self.print_man("group <hostname_list> <set_name>", msg)

    def do_raindeploy(self, args):

        self.help_raindeploy()

    def help_raindeploy(self):
        msg = "RAIN deploy command: Deploy an image in a particular set of nodes. " + \
              "The imgId refers to an image stored in the Image Repository or to the specification " + \
              "of an image that need to be generated\n "
        self.print_man("deploy <imgId> <infrastructure>", msg)
    """