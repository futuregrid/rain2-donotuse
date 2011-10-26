#!/usr/bin/env python
"""
Client of the FG RAIN
"""
__author__ = 'Javier Diaz'
__version__ = '0.1'

import argparse
from types import *
import re
import logging
import logging.handlers
import glob
import random
import os
import sys
import socket, ssl
from subprocess import *
from getpass import getpass
import hashlib
import time

from RainClientConf import RainClientConf
sys.path.append(os.getcwd())
try:
    from futuregrid.image.management import IMDeploy 
    from futuregrid.utils import fgLog
except:
    sys.path.append(os.path.dirname(__file__) + "/../") #Directory where fg.py is
    from image.management import IMDeploy
    from utils import fgLog

class RainClient(object):

    #(Now we assume that the server is where the images are stored. We may want to change that)    
    ############################################################
    # __init__
    ############################################################
    def __init__(self, verbose, printLogStdout):
        super(RainClient, self).__init__()
        
        
        self.verbose = verbose
        self.printLogStdout = printLogStdout
        
        self._rainConf = RainClientConf()
        self._log = fgLog.fgLog(self._rainConf.getLogFile(), self._rainConf.getLogLevel(), "RainClient", printLogStdout)
        self.refresh = self._rainConf.getRefresh()
        
    def baremetal(self, imageidonsystem, jobscript, machines):
        #1.in the case of qsub wait until job is done. then we read the output file and the error one to print it out to the user.
        std = []
        f = open(jobscript, 'r')
        #PBS -e stderr.txt
        #PBS -o stdout.txt
        stdoutfound = False
        stderrfound = False        
        stdout = ""
        stderr = ""        
        for i in f:
            if re.search('^#PBS -e', i):
                stderrfound = True
                stderr = os.path.expandvars(os.path.expanduser(i.split()[2]))                    
            elif re.search('^#PBS -o', i):
                stdoutfound = True
                stdout = os.path.expandvars(os.path.expanduser(i.split()[2]))            
            elif not re.search('^#', i):
                break                      
            if stderrfound and stdoutfound:
                break
        f.close()
        
        #execute qsub
        cmd = "qsub "
        if machines > 1:
            cmd += "-l nodes=" + str(machines)
        if imageidonsystem != None:
            cmd += " -l os=" + imageidonsystem
        cmd += " " + jobscript
        
        self._log.debug(cmd)
        
        p_qsub = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
        std_qsub = p_qsub.communicate()
        if p_qsub.returncode != 0:
            self._log.debug(std_qsub[1])
            if self.verbose:
                print std_qsub[1]
            return "ERROR in qsub: " + std_qsub[1]
        else:
            jobid = std_qsub[0]
        
        if stdoutfound == False:
            stdout = "jobscript.o" + jobid
        if stderrfound == False:
            stderr = "jobscript.e" + jobid
                    
        #execute checkjob checking Status until complete or fail
        cmd = "checkjob " + jobid
        alive = True
        status = 0
        state = ""
        lines = []
        while alive:            
            p = Popen(cmd.split(), stdout=PIPE, stderr=PIPE)
            std = p.communicate()
            lines = std[0].split('\n')
            if p.returncode != 0:
                self._log.debug(std[1])
                if self.verbose:
                    print std[1]                
                status = 1
                alive = False
            else:
                for i in lines:
                    if re.search("^State:", i.strip()):                        
                        state = i.strip().split(":")[1].strip()
                        print state
                        break
                if state == "Completed":
                    alive = False
                else:
                    time.sleep(self.refresh)
        completion = ""
        for i in lines:
            if re.search("^Completion Code:", i.strip()):                        
                completion = i.strip()                    
                break
        
        if self.verbose:
            print completion
            print "The output of the job is in the file: " + stdout
            print "The error output of the job is in the file: " + stderr                
        
        #read exit file and print it
            
    #2. in the case of euca-run-instance, wait until the vms are booted, execute the job inside, wait until done.
    def euca(self, imageidonsystem, jobscript, machines):
        print "in eucalyptus method.end"
    def opennebula(self, imageidonsystem, jobscript, machines):
        print "in opennebula method.end"
    def nimbus(self, imageidonsystem, jobscript, machines):
        print "in nimbus method.end"
    def openstack(self, imageidonsystem, jobscript, machines):
        print "in openstack method.end"
        
    """
    def runCmd(self, cmd, std):        
        self._log.debug(cmd)
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE)
        std = p.communicate()
        status = 0
        if len(std[0]) > 0:
            self._log.debug('stdout: ' + std[0])
            self._log.debug('stderr: ' + std[1])
        if p.returncode != 0:
            cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
            status = 1
            #sys.exit(p.returncode)
        return status
    """
#TODO: in the case of cloud deployment, we need to configure ldap to allow users to login and run parallel jobs. For that we need to modify the deployment iaas to include the code that does that.
def main():
 
    user = ""

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

    #print args
    

    print 'Starting Rain...'
    
    verbose = True #to activate the print
    
    print "Please insert the password for the user " + args.user + ""
    m = hashlib.md5()
    m.update(getpass())
    passwd = m.hexdigest()

    #TODO: if Kernel is provided we need to verify that it is supported. 
    
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
        imgdeploy = IMDeploy(args.kernel, args.user, passwd, verbose, args.debug)    
        #XCAT
        if args.xcat != None:
            if args.imgid == None:
                print "ERROR: You need to specify the id of the image that you want to deploy (-r/--imgid option)."
                print "The parameter -i/--image cannot be used with this type of deployment"
                sys.exit(1)
            else:
                output = imgdeploy.xcat_method(args.xcat, args.imgid)
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
                        output = imgdeploy.iaas_generic(args.euca, image, image_source, "euca", varfile, args.getimg, ldap)        
                else:    
                    output = imgdeploy.iaas_generic(args.euca, image, image_source, "euca", varfile, args.getimg, ldap)
            #OpenNebula
            elif ('-o' in used_args or '--opennebula' in used_args):
                output = imgdeploy.iaas_generic(args.opennebula, image, image_source, "opennebula", varfile, args.getimg, ldap)
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
                        output = imgdeploy.iaas_generic(args.openstack, image, image_source, "openstack", varfile, args.getimg, ldap)
                else:    
                    output = imgdeploy.iaas_generic(args.openstack, image, image_source, "openstack", varfile, args.getimg, ldap)
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
    #call rain with the command
    

if __name__ == "__main__":
    main()
#END
