#!/usr/bin/env python
"""
It generates the images for different OS
"""
__author__ = 'Javier Diaz, Andrew Younge'
__version__ = '0.9'

from optparse import OptionParser
from types import *
import re
import logging
import logging.handlers
import glob
import random
import os
import sys
import socket
from subprocess import *
import time
import re
#from xml.dom.ext import *
from xml.dom.minidom import Document, parse

#This enable some extra config for the mini-cluster.
#it will be removed as soon as we code the ubuntu part in deployserverxcat
TEST_MODE = True

logger=None
def main():
    global tempdir
    global namedir #this == name is to clean up when something fails
    global http_server
    global bcfg2_url
    global bcfg2_port
    #Set up logging
    log_filename = 'fg-image-generate.log'
    
    logger = logging.getLogger("GenerateScript")
    logger.setLevel(logging.DEBUG)    
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False
    

    #Set up random string    
    random.seed()
    randid = str(random.getrandbits(32))

    parser = OptionParser()

    #Default params
    base_os = ""
    spacer = "-"
    latest_ubuntu = "lucid"
    latest_debian = "lenny"
    latest_rhel = "5.5"
    latest_centos = "5.6"
    latest_fedora = "13"
    #kernel = "2.6.27.21-0.1-xen"

    #ubuntu-distro = ['lucid', 'karmic', 'jaunty']
    #debian-distro = ['squeeze', 'lenny', 'etch']
    #rhel-distro = ['5.5', '5.4', '4.8']
    #fedora-distro = ['14','12']



    logger.info('Starting image generator...')

    #Check if we have root privs 
    if os.getuid() != 0:
        logger.error("Sorry, you need to run with root privileges")
        sys.exit(1)

    #help is auto-generated
    parser.add_option("-o", "--os", dest = "os", help = "specify destination Operating System")
    parser.add_option("-v", "--version", dest = "version", help = "Operating System version")
    parser.add_option("-a", "--arch", dest = "arch", help = "Destination hardware architecture")
    parser.add_option("-s", "--software", dest = "software", help = "Software stack to be automatically installed")
    parser.add_option("-d", "--debug", action = "store_true", dest = "debug", help = "Enable debugging")
    parser.add_option("-u", "--user", dest = "user", help = "FutureGrid username")
    parser.add_option("-n", "--name", dest = "givenname", help = "Desired recognizable name of the image")
    parser.add_option("-e", "--description", dest = "desc", help = "Short description of the image and its purpose")
    parser.add_option("-t", "--tempdir", dest = "tempdir", help = "directory to be use in to generate the image")
    parser.add_option("-c", "--httpserver", dest = "httpserver", help = "httpserver to download config files")
    parser.add_option("-b", "--bcfg2url", dest = "bcfg2url", help = "address where our IMBcfg2GroupManagerServer is listening")
    parser.add_option("-p", "--bcfg2port", dest = "bcfg2port", help = "port where our IMBcfg2GroupManagerServer is listening")
    

    (ops, args) = parser.parse_args()


    #Turn debugging off
    #if not ops.debug:
    #    logging.basicConfig(level = logging.INFO)
        #ch.setLevel(logging.INFO)

    if type(ops.httpserver) is not NoneType:
        http_server=ops.httpserver
    else:
        logger.error("You need to provide the http server that contains files needed to create images")
        sys.exit(1)
    if type(ops.bcfg2url) is not NoneType:
        bcfg2_url=ops.bcfg2url
    else:
        logger.error("You need to provide the address of the machine where IMBcfg2GroupManagerServer.py is listening")
        sys.exit(1)
    if type(ops.bcfg2port) is not NoneType:
        bcfg2_port=int(ops.bcfg2port)
    else:
        logger.error("You need to provide the port of the machine where IMBcfg2GroupManagerServer.py is listening")
        sys.exit(1)
    
    if type(ops.tempdir) is not NoneType:
        tempdir = ops.tempdir
        if(tempdir[len(tempdir) - 1:] != "/"):
            tempdir += "/"
    else:
        tempdir = "/tmp/"

    #the if-else is not needed, but can be useful to execute this script alone
    #user = ops.user
    if type(ops.user) is not NoneType:
        user = ops.user
    else:
        user = "default"

    logger.debug('FG User: ' + user)

    namedir = user + '' + randid

    arch = ops.arch
    """Already controlled...delete..    
    arch = "x86_64" #Default to 64-bit
    
    #Parse arch command line arg
    if type(ops.arch) is not NoneType:
        if ops.arch == "i386" or ops.arch == "i686":
            arch = "i386"
        elif ops.arch == "amd64" or ops.arch == "x86_64":
            arch = "x86_64"
        else:    
            parser.error("Incorrect architecture type specified (i386|x86_64)")
            sys.exit(1)
    """
    logger.debug('Selected Architecture: ' + arch)

    #Parse Software stack list
    if ops.software != "None":

        #Assume its comma seperated, so parse
        packages = re.split('[, ]', ops.software)
        #packages = ops.software.split(', ')
        packs = ' '.join(packages)
        logger.debug('Selected software packages: ' + packs)
    else:
        packs = 'wget'

    # Build the image
    #OS and Version already parsed in client side, just assign it
    version = ops.version
    if ops.os == "ubuntu":
        base_os = base_os + "ubuntu" + spacer

        logger.info('Building Ubuntu ' + version + ' image')

        create_base_os = True
        config_ldap = True

        img = buildUbuntu(namedir, version, arch, packs, tempdir, create_base_os, config_ldap)

    elif ops.os == "debian":
        base_os = base_os + "debian" + spacer
    elif ops.os == "rhel":
        base_os = base_os + "rhel" + spacer
    elif ops.os == "centos":
        base_os = base_os + "centos" + spacer

        logger.info('Building Centos ' + version + ' image')
        create_base_os = True
        config_ldap = True

        img = buildCentos(namedir, version, arch, packs, tempdir, create_base_os, config_ldap)

    elif ops.os == "fedora":
        base_os = base_os + "fedora" + spacer

   # logger.info('Generated image is available at '+tempdir+' ' + img + '.img.  Please be aware that this FutureGrid image is packaged without a kernel and fstab and is not built for any deployment type.  To deploy the new image, use the fg-image-deploy command.')

    if type(ops.givenname) is NoneType:
        ops.givenname = img

    if type(ops.desc) is NoneType:
        ops.desc = " "

    manifest(user, img, ops.os, version, arch, packs, ops.givenname, ops.desc, tempdir)

    print img
    # Cleanup
    #TODO: verify everything is unmounted, delete temporary folder

#END MAIN

def buildUbuntu(name, version, arch, pkgs, tempdir, base_os, ldap):

    output = ""
    namedir = name

    ubuntuLog = logging.getLogger('GenerateScript.ubuntu')


    if not base_os:
        ubuntuLog.info('Retrieving Image: ubuntu-' + version + '-' + arch + '-base.img')
        #Download base image from repository
        runCmd('wget ' + http_server + 'base_os/ubuntu-' + version + '-' + arch + '-base.img -O ' + tempdir + ' ' + name + '.img')
    elif base_os:
        ubuntuLog.info('Generation Image: centos-' + version + '-' + arch + '-base.img')

        #to create base_os    
        ubuntuLog.info('Creating Disk for the image')
        runCmd('dd if=/dev/zero of=' + tempdir + '' + name + '.img bs=1024k seek=1496 count=0')
        runCmd('mke2fs -F -j ' + tempdir + '' + name + '.img')


    #Mount the new image
    ubuntuLog.info('Mounting new image')
    runCmd('mkdir ' + tempdir + '' + name)
    runCmd('mount -o loop ' + tempdir + '' + name + '.img ' + tempdir + '' + name)
    #ubuntuLog.info('Mounted image')


    if base_os:

        #to create base_os
        #centosLog.info('Modifying repositories to match the version requested')
        ubuntuLog.info('Installing base OS')
        #runCmd('yum --installroot='+tempdir+''+name+' -y groupinstall Core')
        runCmd('debootstrap --include=grub,language-pack-en,openssh-server --components=main,universe,multiverse ' + version + ' ' + tempdir + '' + name)

        ubuntuLog.info('Copying configuration files')

#Move next 3 to deploy        
        #os.system('echo "search idpm" > '+tempdir+''+name+'/etc/resolv.conf')
        os.system('echo "nameserver 129.79.1.1" >> ' + tempdir + '' + name + '/etc/resolv.conf')
        os.system('echo "nameserver 172.29.202.149" >> ' + tempdir + '' + name + '/etc/resolv.conf')

        os.system('echo "127.0.0.1 localhost.localdomain localhost" > ' + tempdir + '' + name + '/etc/hosts')
        #base_os done

    #Mount proc and pts
    runCmd('mount -t proc proc ' + tempdir + '' + name + '/proc')
    runCmd('mount -t devpts devpts ' + tempdir + '' + name + '/dev/pts')
    ubuntuLog.info('Mounted proc and devpts')

    # Setup package repositories 
    #TODO: Set mirros to IU/FGt
    ubuntuLog.info('Configuring repositories')

    #runCmd('wget ' + http_server + '/conf/ubuntu/' + version + '-sources.list -O ' + tempdir + '' + name + '/etc/apt/sources.list')
    f = open(tempdir + '' + name + '/etc/apt/source.list', 'w')
    f.write('deb http://us.archive.ubuntu.com/ubuntu/ ' + version + ' main restricted \n' 
    'deb-src http://us.archive.ubuntu.com/ubuntu/ ' + version + ' main restricted \n'      
    'deb http://us.archive.ubuntu.com/ubuntu/ ' + version + '-updates main restricted \n' 
    'deb-src http://us.archive.ubuntu.com/ubuntu/ ' + version + '-updates main restricted \n'
    'deb http://us.archive.ubuntu.com/ubuntu/ ' + version + ' universe \n' 
    'deb-src http://us.archive.ubuntu.com/ubuntu/ ' + version + ' universe \n' 
    'deb http://us.archive.ubuntu.com/ubuntu/ ' + version + '-updates universe \n' 
    'deb-src http://us.archive.ubuntu.com/ubuntu/ ' + version + '-updates universe \n'     
    'deb http://us.archive.ubuntu.com/ubuntu/ ' + version + ' multiverse \n' 
    'deb-src http://us.archive.ubuntu.com/ubuntu/ ' + version + ' multiverse \n' 
    'deb http://us.archive.ubuntu.com/ubuntu/ ' + version + '-updates multiverse \n' 
    'deb-src http://us.archive.ubuntu.com/ubuntu/ ' + version + '-updates multiverse ')
    f.close()
    

    #key for bcfg2
    runCmd('chroot ' + tempdir + '' + name + ' apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 98932BEC')
    runCmd('chroot ' + tempdir + '' + name + ' apt-get update')

    #services will install, but not start
    os.system('mkdir -p /usr/sbin')
    os.system('echo "#!/bin/sh" >' + tempdir + '' + name + '/usr/sbin/policy-rc.d')
    os.system('echo "exit 101" >>' + tempdir + '' + name + '/usr/sbin/policy-rc.d')
    os.system('chmod +x ' + tempdir + '' + name + '/usr/sbin/policy-rc.d')


    ubuntuLog.info('Installing some util packages')
    runCmd('chroot ' + tempdir + '' + name + ' apt-get -y install wget nfs-common gcc make libcrypto++8 man curl time')
        


    #Setup networking
    os.system('echo "localhost" > ' + tempdir + '' + name + '/etc/hostname')
    runCmd('hostname localhost')
    
    runCmd('wget ' + http_server + '/conf/ubuntu/interfaces -O ' + tempdir + '' + name + '/etc/network/interfaces')

    ubuntuLog.info('Injected networking configuration')


    #Set apt-get into noninteractive mode
    #runCmd('chroot '+tempdir+' '+name+' DEBIAN_FRONTEND=noninteractive')
    #runCmd('chroot '+tempdir+' '+name+' DEBIAN_PRIORITY=critical')

    # Install BCFG2 client
    #ubuntuLog.info('Installing BCFG2 client')

    ##os.system('chroot '+tempdir+' '+name+' apt-get update')
    #runCmd('chroot ' + tempdir + '' + name + ' apt-get -y install bcfg2')
    ##os.system('chroot '+tempdir+' '+name+' apt-get -y install bcfg2')
    #ubuntuLog.info('Installed BCFG2 client')
    """

    #Configure BCFG2 client
    ubuntuLog.info('Configuring BCFG2')
    runCmd('wget ' + http_server + '/bcfg2/bcfg2.conf -O '+tempdir+''+name + '/etc/bcfg2.conf')
    runCmd('wget ' + http_server + '/bcfg2/bcfg2.ca -O '+tempdir+''+name + '/etc/bcfg2.ca')
    runCmd('wget ' + http_server + '/bcfg2/default -O '+tempdir+''+name + '/etc/default/bcfg2')
    ubuntuLog.info('Injected FG deployment files')

    #Inject group info for Probes
    os.system('echo ' + name + ' > '+tempdir+''+name + '/etc/bcfg2.group')
    ubuntuLog.info('Injected probes hook for unique group')
    
    ubuntuLog.info('Configured BCFG2 client settings')
    """
    #Install packages
    if pkgs != None:
        ubuntuLog.info('Installing user-defined packages')
        runCmd('chroot ' + tempdir + '' + name + ' apt-get -y install ' + pkgs)  #NON_INTERACTIVE
        ubuntuLog.info('Installed user-defined packages')

    #Setup BCFG2 server groups
    #success = push_bcfg2_group(name, pkgs, 'ubuntu', version)
    #if success:
    #    ubuntuLog.info('Setup new BCFG2 group')
    #    #Finished, now clean up
    #    ubuntuLog.info('Genereated Ubuntu image ' + name + ' successfully!')
    #    output = name
    #else:
    #    output = "Error generating bcfg2 group configuration"


    #disable password login via ssh
    os.system('sed -i \'s/PasswordAuthentication yes/PasswordAuthentication no/g\' ' + tempdir + '' + name + '/etc/ssh/sshd_config')
    os.system('echo \"PasswordAuthentication no\" | tee -a ' + tempdir + '' + name + '/etc/ssh/sshd_config > /dev/null')


    output = name

    os.system('rm -f ' + tempdir + '' + name + '/usr/sbin/policy-rc.d')

    cleanup(name)

    return name

def buildDebian(name, version, arch, pkgs, tempdir):


    namedir = name
    runCmd('')


def buildRHEL(name, version, arch, pkgs, tempdir):

    namedir = name
    runCmd('')


def buildCentos(name, version, arch, pkgs, tempdir, base_os, ldap):
    
    #actualizar python-hashlib in the centos-5.6 image (the opennebula one) to use centos-6
    
    #we need to remove img file when error
    
    output = ""
    namedir = name

    centosLog = logging.getLogger('GenerateScript.centos')

    if not base_os:
        centosLog.info('Retrieving Image: centos-' + version + '-' + arch + '-base.img')
        #Download base image from repository
        runCmd('wget ' + http_server + 'base_os/centos-' + version + '-' + arch + '-base.img -O ' + tempdir + '' + name + '.img')
    elif base_os:
        centosLog.info('Generation Image: centos-' + version + '-' + arch + '-base.img')

        #to create base_os    
        centosLog.info('Creating Disk for the image')
        runCmd('dd if=/dev/zero of=' + tempdir + '' + name + '.img bs=1024k seek=1496 count=0')
        runCmd('mke2fs -F -j ' + tempdir + '' + name + '.img')

    #Mount the new image
    centosLog.info('Mounting new image')
    runCmd('mkdir ' + tempdir + '' + name)
    runCmd('mount -o loop ' + tempdir + '' + name + '.img ' + tempdir + '' + name)
    #centosLog.info('Mounted image')

    if base_os:
        #to create base_os
        centosLog.info('Create directories image')
        runCmd('mkdir -p ' + tempdir + '' + name + '/var/lib/rpm ' + tempdir + '' + name + '/var/log ' + tempdir + '' + name + '/dev/pts ' + tempdir + '' + name + '/dev/shm')
        runCmd('touch ' + tempdir + '' + name + '/var/log/yum.log')

        #to create base_os
        centosLog.info('Getting appropiate release package')
        if (version == "5"):
            runCmd('wget http://mirror.centos.org/centos/5/os/x86_64/CentOS/centos-release-5-7.el5.centos.x86_64.rpm -O ' + tempdir + 'centos-release.rpm')            
        elif(version == "6"): #the 5.5 is not supported yet
            runCmd('wget http://mirror.centos.org/centos/6.0/os/x86_64/Packages/centos-release-6-0.el6.centos.5.x86_64.rpm -O ' + tempdir + 'centos-release.rpm')            

        runCmd('rpm -ihv --nodeps --root ' + tempdir + '' + name + ' ' + tempdir + 'centos-release.rpm')
        runCmd('rm -f ' + tempdir + 'centos-release.rpm')
        
        #runCmd("yum -y install python-hashlib")
        
        #runCmd("yum clean all")
        """
        centosLog.info('Creating yum.conf with the repositories')
        f = open("./yum.conf","w")        
        f.write(
        "[main]\n"
        "cachedir=/var/cache/yum\n"
        "debuglevel=2\n"
        "logfile=/var/log/yum.log\n"
        "exclude=*-debuginfo\n"
        "gpgcheck=0\n"
        "obsoletes=1\n"
        "pkgpolicy=newest\n"
        "distroverpkg=redhat-release\n"
        "tolerant=1\n"
        "exactarch=1\n"
        "reposdir=/dev/null\n"
        "metadata_expire=1800\n"
        "\n"
        "[base]\n"
        "name=CentOS "+version+" - $basearch - Base\n"            
        #"baseurl=http://vault.centos.org/"+version+"/os/"+arch+"/\n"
        "baseurl=http://mirror.centos.org/centos/"+version+"/os/"+arch+"/\n"
        "enabled=1\n"
        "\n"
        "[updates-released]\n"
        "name=CentOS "+version+" - $basearch - Released Updates\n"
        #"baseurl=http://vault.centos.org/"+version+"/updates/"+arch+"/\n"
        "baseurl=http://mirror.centos.org/centos/"+version+"/updates/"+arch+"/\n"
        "enabled=1\n"
        "\n"
        "[extras]\n"
        "name=CentOS "+version+" Extras $releasever - $basearch\n"
        #"baseurl=http://vault.centos.org/"+version+"/extras/"+arch+"/\n"
        "baseurl=http://mirror.centos.org/centos/"+version+"/extras/"+arch+"/\n"
        "enabled=1 \n")
        
        f.close()
        """
        #to create base_os        
        centosLog.info('Installing base OS')
        runCmd('yum --installroot=' + tempdir + '' + name + ' -y groupinstall Core')
        #runCmd('yum -c ./yum.conf --installroot=' + tempdir + '' + name + ' -y groupinstall Core')

        centosLog.info('Copying configuration files')

#Move next 3 to deploy        
        os.system('echo "search idpm" > ' + tempdir + '' + name + '/etc/resolv.conf')
        os.system('echo "nameserver 129.79.1.1" >> ' + tempdir + '' + name + '/etc/resolv.conf')
        os.system('echo "nameserver 172.29.202.149" >> ' + tempdir + '' + name + '/etc/resolv.conf')

        runCmd('cp /etc/sysconfig/network ' + tempdir + '' + name + '/etc/sysconfig/')

        os.system('echo "127.0.0.1 localhost.localdomain localhost" > ' + tempdir + '' + name + '/etc/hosts')
        #base_os done


    #Mount proc and pts
    runCmd('mount -t proc proc '+tempdir+''+name + '/proc')
    runCmd('mount -t devpts devpts '+tempdir+''+name + '/dev/pts')
    centosLog.info('Mounted proc and devpts')

    centosLog.info('Installing some util packages')
    #if not os.path.isfile(tempdir + '' + name +"/proc/cpuinfo"):
    #    os.system("touch "+ tempdir + '' + name +"/proc/cpuinfo")
    #runCmd('chroot ' + tempdir + '' + name + ' yum clean all')
    if (re.search("^5",version)):
        runCmd('chroot ' + tempdir + '' + name + ' rpm -ivh http://download.fedora.redhat.com/pub/epel/5/'+arch+'/epel-release-5-4.noarch.rpm')        
    elif (re.search("^6",version)):
        runCmd('chroot ' + tempdir + '' + name + ' rpm -ivh http://download.fedora.redhat.com/pub/epel/6/'+arch+'/epel-release-6-5.noarch.rpm')
        runCmd('chroot ' + tempdir + '' + name + ' yum -y install plymouth') 

    runCmd('chroot ' + tempdir + '' + name + ' yum -y install wget nfs-utils gcc make man curl time')
   

    #Setup networking

    runCmd('wget ' + http_server + '/conf/centos/ifcfg-eth0 -O ' + tempdir + '' + name + '/etc/sysconfig/network-scripts/ifcfg-eth0')

    centosLog.info('Injected generic networking configuration')


    # Setup package repositories 
    #TODO: Set mirros to IU/FGt

    #centosLog.info('Configuring repositories')    


    # Install BCFG2 client

    #centosLog.info('Installing BCFG2 client')    
    """"    
    runCmd('chroot '+tempdir+''+name + ' yum -y install bcfg2')
    #os.system('chroot '+tempdir+' '+name+' apt-get -y install bcfg2')
    centosLog.info('Installed BCFG2 client')

    
    #Configure BCFG2 client
    centosLog.info('Configuring BCFG2')
    runCmd('wget ' + http_server + '/bcfg2/bcfg2.conf -O '+tempdir+''+name + '/etc/bcfg2.conf')
    runCmd('wget ' + http_server + '/bcfg2/bcfg2.ca -O '+tempdir+''+name + '/etc/bcfg2.ca')
    runCmd('wget ' + http_server + '/bcfg2/default -O '+tempdir+''+name + '/etc/default/bcfg2')
    centosLog.info('Injected FG deployment files')

    #Inject group info for Probes
    os.system('echo ' + name + ' > '+tempdir+''+name + '/etc/bcfg2.group')
    centosLog.info('Injected probes hook for unique group')
    
    centosLog.info('Configured BCFG2 client settings')
    """
    #Install packages
    if pkgs != None:
        centosLog.info('Installing user-defined packages')
        runCmd('chroot ' + tempdir + '' + name + ' yum -y install ' + pkgs)
        centosLog.info('Installed user-defined packages')

    #Setup BCFG2 server groups
    #success = push_bcfg2_group(name, pkgs, 'centos', version)
    #if success:
    #    centosLog.info('Setup new BCFG2 group')
    #    #Finished, now clean up
    #    centosLog.info('Genereated centos image ' + name + ' successfully!')
    #    output = name
    #else:
    #    output = "Error generating bcfg2 group configuration"

    #disable password login via ssh
    os.system('sed -i \'s/PasswordAuthentication yes/PasswordAuthentication no/g\' ' + tempdir + '' + name + '/etc/ssh/sshd_config')
    os.system('echo \"PasswordAuthentication no\" | tee -a ' + tempdir + '' + name + '/etc/ssh/sshd_config > /dev/null')

    #create /etc/shadow file
    #runCmd('chroot ' + tempdir + '' + name + ' pwconv')

    output = name

    cleanup(name)

    return output



def buildFedora(name, version, arch, pkgs, tempdir):

    runCmd('')


def runCmd(cmd):
    cmdLog = logging.getLogger('GenerateScript.exec')
    cmdLog.debug(cmd)

    #os.system(cmd)
    #Use subprocess to properly direct output to log
    #p = subprocess.Popen(cmd, shell=True)
    p = Popen(cmd.split(' '), stdout = PIPE, stderr = PIPE)
    std = p.communicate()
    if len(std[0]) > 0:
        cmdLog.debug('stdout: ' + std[0])
    #cmdLog.debug('stderr: '+std[1])

    #cmdLog.debug('Ret status: '+str(p.returncode))
    if p.returncode != 0:
        cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])        
        cleanup(namedir)        
        cmd = "rm -f " + tempdir + '' + namedir + ".img"
        cmdLog.debug('Executing: ' + cmd)
        os.system(cmd)
        print "error"
        print str(p.returncode) + '---' + std[1]
        sys.exit(p.returncode)



def cleanup(name):
    #Cleanup
    cleanupLog = logging.getLogger('GenerateScript.cleanup')
    if (name.strip() != ""):
        os.system('umount ' + tempdir + '' + name + '/proc')
        os.system('umount ' + tempdir + '' + name + '/dev/pts')

        cmd = 'umount ' + tempdir + '' + name
        cleanupLog.debug('Executing: ' + cmd)
        stat = os.system(cmd)

        if (stat == 0):
            cmd = "rm -rf " + tempdir + '' + name
            cleanupLog.debug('Executing: ' + cmd)
            os.system(cmd)
    else:
        cleanupLog.error("error in clean up")

    cleanupLog.debug('Cleaned up mount points')
    time.sleep(10)

def manifest(user, name, os, version, arch, pkgs, givenname, description, tempdir):

    manifestLog = logging.getLogger('GenerateScript.manifest')

    manifest = Document()

    head = manifest.createElement('manifest')
    manifest.appendChild(head)

    userNode = manifest.createElement('user')
    userVal = manifest.createTextNode(user)
    userNode.appendChild(userVal)
    head.appendChild(userNode)

    imgNameNode = manifest.createElement('name')
    imgNameVal = manifest.createTextNode(name)
    imgNameNode.appendChild(imgNameVal)
    head.appendChild(imgNameNode)

    imgGivenNameNode = manifest.createElement('givenname')
    imgGivenNameVal = manifest.createTextNode(givenname)
    imgGivenNameNode.appendChild(imgGivenNameVal)
    head.appendChild(imgGivenNameNode)

    descNode = manifest.createElement('description')
    descVal = manifest.createTextNode(description)
    descNode.appendChild(descVal)
    head.appendChild(descNode)

    osNode = manifest.createElement('os')
    osNodeVal = manifest.createTextNode(os)
    osNode.appendChild(osNodeVal)
    head.appendChild(osNode)

    versionNode = manifest.createElement('version')
    versionNodeVal = manifest.createTextNode(version)
    versionNode.appendChild(versionNodeVal)
    head.appendChild(versionNode)

    archNode = manifest.createElement('arch')
    archNodeVal = manifest.createTextNode(arch)
    archNode.appendChild(archNodeVal)
    head.appendChild(archNode)

    #kernelNode = manifest.createElement('kernel')
    #kernelNodeVal = manifest.createTextNode(kernel)
    #kernelNode.appendChild(kernelNodeVal)
    #head.appendChild(kernelNode)

    packagesNode = manifest.createElement('packages')
    packages = pkgs.split(' ')
    for p in packages:
        packageNode = manifest.createElement('package')
        packageNodeVal = manifest.createTextNode(p)
        packageNode.appendChild(packageNodeVal)
        packagesNode.appendChild(packageNode)

    head.appendChild(packagesNode)

    filename = '' + tempdir + '' + name + '.manifest.xml'
    file = open(filename, 'w')
    #Document.PrettyPrint(manifest, file)
    #manifest.writexml(file, indent='    ', addindent='    ', newl='\n')

    output = manifest.toprettyxml()
    file.write(output)
    file.close()
    manifestLog.info('Genereated manifest file: ' + filename)

def push_bcfg2_group(name, pkgs, os, version):
    #Push the group information to the BCFG2 server via a socket connection

    bcfg2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bcfg2.connect((bcfg2_url, bcfg2_port))

    success = True

    #Send group name
    bcfg2.send(name)
    ret = bcfg2.recv(100)
    if ret != 'OK':
        logger.error('Incorrect reply from the server:' + ret)
        success = False
    else:
        #Send OS 
        bcfg2.send(os)
        ret = bcfg2.recv(100)
        if ret != 'OK':
            logger.error('Incorrect reply from the server:' + ret)
            success = False
        else:
            #Send OS Version
            bcfg2.send(version)
            ret = bcfg2.recv(100)
            if ret != 'OK':
                logger.error('Incorrect reply from the server:' + ret)
                success = False
            else:
                #Send package information
                bcfg2.send(pkgs)
                ret = bcfg2.recv(100)
                if ret != 'OK':
                    logger.error('Incorrect reply from the server:' + ret)
                    success = False

    return success



if __name__ == "__main__":
    main()
#END




