#!/usr/bin/python
# Description: Command line front end for image generator
#
# Author: Andrew J. Younge & Javier Diaz
#

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
#from xml.dom.ext import *
from xml.dom.minidom import Document, parse

#This enable some extra config for the mini-cluster
TEST_MODE=True

#global vars
base_url = "http://fg-gravel3.futuregrid.iu.edu/"
bcfg2_url = 'fg-gravel3.futuregrid.iu.edu'
bcfg2_port = 45678
namedir = "" #this == name is to clean up when something fails

def main():    
    #Set up logging
    log_filename = 'fg-image-generate.log'
    #logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",datefmt='%a, %d %b %Y %H:%M:%S',filemode='w',filename=log_filename,level=logging.DEBUG)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    #ch = logging.StreamHandler()
    #ch.setLevel(logging.DEBUG)
    #ch.setFormatter(formatter)
    #logger.addHandler(ch)
    
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



    logging.info('Starting image generator...')

    #Check if we have root privs 
    if os.getuid() != 0:
        print "Sorry, you need to run with root privileges"
        sys.exit(1)
    
    #help is auto-generated
    parser.add_option("-o", "--os", dest="os", help="specify destination Operating System")
    parser.add_option("-v", "--version", dest="version", help="Operating System version")
    parser.add_option("-a", "--arch", dest="arch", help="Destination hardware architecture")
    parser.add_option("-l", "--auth", dest="auth", help="Authentication mechanism")
    parser.add_option("-s", "--software", dest="software", help="Software stack to be automatically installed")
    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debugging")
    parser.add_option("-u", "--user", dest="user", help="FutureGrid username")
    parser.add_option("-n", "--name", dest="givenname", help="Desired recognizable name of the image")
    parser.add_option("-e", "--description", dest="desc", help="Short description of the image and its purpose")
    parser.add_option("-t", "--tempdir", dest="tempdir", help="directory to be use in to generate the image")
            
    (ops, args) = parser.parse_args()
    
    
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)
        #ch.setLevel(logging.INFO)
    
    global tempdir
    
    if type(ops.tempdir) is not NoneType: 
        tempdir=ops.tempdir
    else:
        tempdir="/tmp/"
    
    #the if-else is not needed, but can be useful to execute this script alone
    #user = ops.user
    if type(ops.user) is not NoneType:
        user = ops.user
    else:        
        user = "default"
    
    #if type(os.getenv('FG_USER')) is not NoneType:
    #    user = os.getenv('FG_USER')
    #elif type(ops.user) is not NoneType:
    #    user = ops.user
    #else:
        #user = "default"
    #TODO: authenticate user via promting for CERT or password to auth against LDAP db
    
    logging.debug('FG User: ' + user)
    
    arch=ops.arch
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
    logging.debug('Selected Architecture: ' + arch)
    
    #Parse Software stack list
    if type(ops.software) is not NoneType:
    
        #Assume its comma seperated, so parse
        packages = re.split('[, ]', ops.software)
        #packages = ops.software.split(', ')
        packs = ' '.join(packages)
        logging.debug('Selected software packages: ' + packs)
    else:
        packs = 'wget' 
    
    """at this level we are already authenticated...delete..
    #TODO: Authorization mechanism TBD
    if type(ops.auth) is not NoneType:
        auth = ""
    """
    
    # Build the image
    #OS and Version already parsed in client side, just assign it
    version=ops.version
    if ops.os == "ubuntu":
        base_os = base_os + "ubuntu" + spacer    
        
        logging.info('Building Ubuntu ' + version + ' image')
        
        create_base_os=True
        config_ldap=True 
        
        img = buildUbuntu(user + '-' + randid, version, arch, packs, tempdir, create_base_os, config_ldap)
    
    elif ops.os == "debian":
        base_os = base_os + "debian" + spacer
    elif ops.os == "rhel":
        base_os = base_os + "rhel" + spacer
    elif ops.os == "centos":
        base_os = base_os + "centos" + spacer
                
        logging.info('Building Centos ' + version + ' image')        
        create_base_os=True
        config_ldap=True       
        
        img = buildCentos(user + '-' + randid, version, arch, packs,tempdir, create_base_os, config_ldap)
        
    elif ops.os == "fedora":
        base_os = base_os + "fedora" + spacer    
    
    logging.info('Generated image is available at '+tempdir+' ' + img + '.img.  Please be aware that this FutureGrid image is packaged without a kernel and fstab and is not built for any deployment type.  To deploy the new image, use the fg-image-deploy command.')
    
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

    output=""

    ubuntuLog = logging.getLogger('ubuntu')


    if not base_os:
        ubuntuLog.info('Retrieving Image: ubuntu-' + version + '-' + arch + '-base.img')
        #Download base image from repository
        runCmd('wget ' + base_url + 'base_os/ubuntu-' + version + '-' + arch + '-base.img -O '+tempdir+' '+ name + '.img')
    elif base_os:
        ubuntuLog.info('Generation Image: centos-' + version + '-' + arch + '-base.img')
     
        #to create base_os    
        ubuntuLog.info('Creating Disk for the image')        
        runCmd('dd if=/dev/zero of='+tempdir+''+name+'.img bs=1024k seek=1496 count=0')
        runCmd('mke2fs -F -j '+tempdir+''+name+'.img')
    
    
    #Mount the new image
    ubuntuLog.info('Mounting new image')
    runCmd('mkdir '+tempdir+''+name)
    runCmd('mount -o loop '+tempdir+''+name + '.img '+tempdir+''+name)
    ubuntuLog.info('Mounted image')

    
    if base_os:
                
        #to create base_os
        #centosLog.info('Modifying repositories to match the version requested')
        ubuntuLog.info('Installing base OS')
        runCmd('yum --installroot='+tempdir+''+name+' -y groupinstall Core')
        runCmd('debootstrap --include=grub,language-pack-en,openssh-server --components=main,universe,multiverse '+version+' '+tempdir+''+name)

        ubuntuLog.info('Copying configuration files')
        
#Move next 3 to deploy        
        os.system('echo "search idpm" > '+tempdir+''+name+'/etc/resolv.conf')
        os.system('echo "nameserver 129.79.1.1" >> '+tempdir+''+name+'/etc/resolv.conf')
        os.system('echo "nameserver 172.29.202.149" >> '+tempdir+''+name+'/etc/resolv.conf')
        
        os.system('echo "127.0.0.1 localhost.localdomain localhost" > '+tempdir+''+name+'/etc/hosts')    
        #base_os done

    #Mount proc and pts
    runCmd('mount -t proc proc '+tempdir+''+name + '/proc')
    runCmd('mount -t devpts devpts '+tempdir+''+name + '/dev/pts')
    ubuntuLog.info('Mounted proc and devpts')

    ubuntuLog.info('Installing some util packages')
    runCmd('chroot '+tempdir+''+name+' apt-get -y install wget nfs-common gcc make')


#NOT FINISH. look into ldap part

#Move ldap to deploy    
    if (ldap):
        #this is for LDAP auth and mount home dirs. Later, we may control if we install this or not.
        ubuntuLog.info('Installing LDAP packages')
        runCmd('chroot '+tempdir+''+name+' apt-get --force-yes -y install ldap-utils libpam-ldap libnss-ldap nss-updatedb libnss-db')
        
        ubuntuLog.info('Configuring LDAP access')        
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/nsswitch.conf -O '+tempdir+''+name+'/etc/nsswitch.conf')
        runCmd('mkdir -p '+tempdir+''+name+'/etc/ldap/cacerts '+tempdir+''+name+'/N/u')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/cacerts/12d3b66a.0 -O '+tempdir+''+name+'/etc/ldap/cacerts/12d3b66a.0')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/cacerts/cacert.pem -O '+tempdir+''+name+'/etc/ldap/cacerts/cacert.pem')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/sshd -O '+tempdir+''+name+'/usr/sbin/sshd')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/ldap.conf -O '+tempdir+''+name+'/etc/ldap.conf')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/openldap/ldap.conf -O '+tempdir+''+name+'/etc/ldap/ldap.conf')

    #Setup networking
    os.system('echo localhost > '+tempdir+''+name + '/etc/hostname')
    runCmd('hostname localhost')
    

    if(TEST_MODE):
        #this eth1 is just for miniclusetr. comment this and uncomment the next one for india
        runCmd('wget ' + base_url + '/conf/ubuntu/interfaces_minicluster_tc2 -O '+tempdir+''+name + '/etc/network/interfaces')
        #runCmd('wget ' + base_url + '/conf/ubuntu/interfaces_minicluster_tc1 -O '+tempdir+''+name + '/etc/network/interfaces')
        os.system('echo "172.29.200.1 t1 tm1" >> '+tempdir+''+name+'/etc/hosts')
        os.system('echo "172.29.200.3 tc1" >> '+tempdir+''+name+'/etc/hosts')
        os.system('echo "149.165.145.35 tc1r.tidp.iu.futuregrid.org tc1r" >> '+tempdir+''+name+'/etc/hosts')
        os.system('echo "172.29.200.4 tc2" >> '+tempdir+''+name+'/etc/hosts')        
        os.system('echo "149.165.145.36 tc2r.tidp.iu.futuregrid.org tc2r" >> '+tempdir+''+name+'/etc/hosts')
        runCmd('mkdir -p '+tempdir+''+name+'/root/.ssh')
        os.system('echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAu0D0UbGs7FIjQVQVuARc4MF9XoCEXraQv4j0yhIS2EoTcdamYvHrSE6t+X'+\
                  'OD9DzwZeAFlcd8yJH5g1wivpsuBo7AO89Fy4WfVwSGJGJZDzfu7s850wytVbSpZNoFJUb372su9OrMcFhi3M7khdjWkurs5'+\
                  'giCivJQnlC+ubExwfcC5NeZUMpkSk1pquuVama4URfh9RQlB0q8t3sksAv1z6IygKKcWwIpFlKrEFtinU1Es+1JmWogq87we'+\
                  'SFJm8M9BX/JXQnf38GaoBmgGxlnHyP10X9Jw56P2eocXtH8HChI45PGgMYnpcQVmnz5Va5xhseEWdPr2tdiBmL4fag2UQ== root@tm1" >> '+tempdir+''+name+'/root/.ssh/authorized_keys')
        os.system('chmod 600 '+tempdir+''+name+'/root/.ssh/authorized_keys')

    else:    
        runCmd('wget ' + base_url + '/conf/ubuntu/interfaces -O '+tempdir+''+name + '/etc/network/interfaces')
        
    ubuntuLog.info('Injected networking configuration')

    # Setup package repositories 
    #TODO: Set mirros to IU/FGt
    ubuntuLog.info('Configuring repositories')
    
    runCmd('wget ' + base_url + '/conf/ubuntu/' + version + '-sources.list -O '+tempdir+''+name + '/etc/apt/sources.list')
    runCmd('chroot '+tempdir+''+name + ' apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 98932BEC')

    #Set apt-get into noninteractive mode
    #runCmd('chroot '+tempdir+' '+name+' DEBIAN_FRONTEND=noninteractive')
    #runCmd('chroot '+tempdir+' '+name+' DEBIAN_PRIORITY=critical')

    # Install BCFG2 client
    ubuntuLog.info('Installing BCFG2 client')
    runCmd('chroot '+tempdir+''+name + ' apt-get update')
    #os.system('chroot '+tempdir+' '+name+' apt-get update')
    runCmd('chroot '+tempdir+''+name + ' apt-get -y install bcfg2')
    #os.system('chroot '+tempdir+' '+name+' apt-get -y install bcfg2')
    ubuntuLog.info('Installed BCFG2 client')


    #Configure BCFG2 client
    ubuntuLog.info('Configuring BCFG2')
    runCmd('wget ' + base_url + '/bcfg2/bcfg2.conf -O '+tempdir+''+name + '/etc/bcfg2.conf')
    runCmd('wget ' + base_url + '/bcfg2/bcfg2.ca -O '+tempdir+''+name + '/etc/bcfg2.ca')
    runCmd('wget ' + base_url + '/bcfg2/default -O '+tempdir+''+name + '/etc/default/bcfg2')
    ubuntuLog.info('Injected FG deployment files')

    #Inject group info for Probes
    os.system('echo ' + name + ' > '+tempdir+''+name + '/etc/bcfg2.group')
    ubuntuLog.info('Injected probes hook for unique group')
    
    ubuntuLog.info('Configured BCFG2 client settings')
    
    #Install packages
    if pkgs != None:
        ubuntuLog.info('Installing user-defined packages')
        runCmd('chroot '+tempdir+''+name + ' apt-get -y install ' + pkgs)
        ubuntuLog.info('Installed user-defined packages')

    #Setup BCFG2 server groups
    success=push_bcfg2_group(name, pkgs, 'ubuntu', version)
    if success: 
        ubuntuLog.info('Setup new BCFG2 group')
        #Finished, now clean up
        ubuntuLog.info('Genereated Ubuntu image ' + name + ' successfully!')
        output=name
    else:
        output="Error generating bcfg2 group configuration"

    cleanup(name)

    return name

def buildDebian(name, version, arch, pkgs, tempdir):

    runCmd('')


def buildRHEL(name, version, arch, pkgs, tempdir):

    runCmd('')


def buildCentos(name, version, arch, pkgs, tempdir, base_os, ldap):

    output=""
    namedir=name

    centosLog = logging.getLogger('centos')
    
    if not base_os:
        centosLog.info('Retrieving Image: centos-' + version + '-' + arch + '-base.img')
        #Download base image from repository
        runCmd('wget ' + base_url + 'base_os/centos-' + version + '-' + arch + '-base.img -O '+tempdir+''+name + '.img')
    elif base_os:
        centosLog.info('Generation Image: centos-' + version + '-' + arch + '-base.img')
     
        #to create base_os    
        centosLog.info('Creating Disk for the image')        
        runCmd('dd if=/dev/zero of='+tempdir+''+name+'.img bs=1024k seek=1496 count=0')
        runCmd('mke2fs -F -j '+tempdir+''+name+'.img')
    
    #Mount the new image
    centosLog.info('Mounting new image')
    runCmd('mkdir '+tempdir+''+name)
    runCmd('mount -o loop '+tempdir+''+name + '.img '+tempdir+''+name)
    centosLog.info('Mounted image')

    if base_os:
        #to create base_os
        centosLog.info('Create directories image')
        runCmd('mkdir -p '+tempdir+''+name+'/var/lib/rpm '+tempdir+''+name+'/var/log '+tempdir+''+name+'/dev/pts '+tempdir+''+name+'/dev/shm')
        runCmd('touch '+tempdir+''+name+'/var/log/yum.log')    
    
        #to create base_os
        centosLog.info('Getting appropiate release package')
        if (version == "5.6"):
            runCmd('wget http://mirror.centos.org/centos/5.6/os/x86_64/CentOS/centos-release-5-6.el5.centos.1.x86_64.rpm -O '+tempdir+'centos-release.rpm')
        elif(version == "5.5"): #the 5.5 is not supported yet
            runCmd('wget http://mirror.centos.org/centos/5.5/os/x86_64/CentOS/centos-release-5-5.el5.centos.x86_64.rpm -O '+tempdir+'centos-release.rpm')
        
        runCmd('rpm -ihv --nodeps --root '+tempdir+''+name+' '+tempdir+'centos-release.rpm')
        runCmd('rm -f '+tempdir+'centos-release.rpm')
        #to create base_os
        #centosLog.info('Modifying repositories to match the version requested')
        centosLog.info('Installing base OS')
        runCmd('yum --installroot='+tempdir+''+name+' -y groupinstall Core')
        
        centosLog.info('Copying configuration files')
        
#Move next 3 to deploy        
        os.system('echo "search idpm" > '+tempdir+''+name+'/etc/resolv.conf')
        os.system('echo "nameserver 129.79.1.1" >> '+tempdir+''+name+'/etc/resolv.conf')
        os.system('echo "nameserver 172.29.202.149" >> '+tempdir+''+name+'/etc/resolv.conf')
        
        runCmd('cp /etc/sysconfig/network '+tempdir+''+name+'/etc/sysconfig/')
        
        os.system('echo "127.0.0.1 localhost.localdomain localhost" > '+tempdir+''+name+'/etc/hosts')    
        #base_os done
    
    centosLog.info('Installing some util packages')
    runCmd('chroot '+tempdir+''+name+' yum -y install wget nfs-utils gcc make')
     
#Move ldap to deploy    
    if (ldap):
        #this is for LDAP auth and mount home dirs. Later, we may control if we install this or not.
        centosLog.info('Installing LDAP packages')
        runCmd('chroot '+tempdir+''+name+' yum -y install openldap-clients nss_ldap')
        
        centosLog.info('Configuring LDAP access')        
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/nsswitch.conf -O '+tempdir+''+name+'/etc/nsswitch.conf')
        runCmd('mkdir -p '+tempdir+''+name+'/etc/openldap/cacerts '+tempdir+''+name+'/N/u')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/cacerts/12d3b66a.0 -O '+tempdir+''+name+'/etc/openldap/cacerts/12d3b66a.0')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/cacerts/cacert.pem -O '+tempdir+''+name+'/etc/openldap/cacerts/cacert.pem')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/sshd -O '+tempdir+''+name+'/usr/sbin/sshd')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/ldap.conf -O '+tempdir+''+name+'/etc/ldap.conf')
        runCmd('wget fg-gravel3.futuregrid.iu.edu/ldap/openldap/ldap.conf -O '+tempdir+''+name+'/etc/openldap/ldap.conf')
        os.system('sed -i \'s/enforcing/disabled/g\' '+tempdir+''+name+'/etc/selinux/config')
    
    
    #Mount proc and pts
    #runCmd('mount -t proc proc '+tempdir+''+name + '/proc')
    #runCmd('mount -t devpts devpts '+tempdir+''+name + '/dev/pts')
    #centosLog.info('Mounted proc and devpts')

    #Setup networking
    
    runCmd('wget ' + base_url + '/conf/centos/ifcfg-eth0 -O '+tempdir+''+name + '/etc/sysconfig/network-scripts/ifcfg-eth0')

#Move all /etc/hosts and ssh key to deploy     
    if(TEST_MODE):
        #this eth1 is just for miniclusetr. comment this and uncomment the next one for india  
        #runCmd('wget ' + base_url + '/conf/centos/ifcfg-eth1_minicluster_tc1 -O '+tempdir+''+name + '/etc/sysconfig/network-scripts/ifcfg-eth1')
        runCmd('wget ' + base_url + '/conf/centos/ifcfg-eth1_minicluster_tc2 -O '+tempdir+''+name + '/etc/sysconfig/network-scripts/ifcfg-eth1')
        os.system('echo "172.29.200.1 t1 tm1" >> '+tempdir+''+name+'/etc/hosts')
        os.system('echo "172.29.200.3 tc1" >> '+tempdir+''+name+'/etc/hosts')
        os.system('echo "149.165.145.35 tc1r.tidp.iu.futuregrid.org tc1r" >> '+tempdir+''+name+'/etc/hosts')
        os.system('echo "172.29.200.4 tc2" >> '+tempdir+''+name+'/etc/hosts')        
        os.system('echo "149.165.145.36 tc2r.tidp.iu.futuregrid.org tc2r" >> '+tempdir+''+name+'/etc/hosts')
        runCmd('mkdir -p '+tempdir+''+name+'/root/.ssh')
        os.system('echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAu0D0UbGs7FIjQVQVuARc4MF9XoCEXraQv4j0yhIS2EoTcdamYvHrSE6t+X'+\
                  'OD9DzwZeAFlcd8yJH5g1wivpsuBo7AO89Fy4WfVwSGJGJZDzfu7s850wytVbSpZNoFJUb372su9OrMcFhi3M7khdjWkurs5'+\
                  'giCivJQnlC+ubExwfcC5NeZUMpkSk1pquuVama4URfh9RQlB0q8t3sksAv1z6IygKKcWwIpFlKrEFtinU1Es+1JmWogq87we'+\
                  'SFJm8M9BX/JXQnf38GaoBmgGxlnHyP10X9Jw56P2eocXtH8HChI45PGgMYnpcQVmnz5Va5xhseEWdPr2tdiBmL4fag2UQ== root@tm1" >> '+tempdir+''+name+'/root/.ssh/authorized_keys')
        os.system('chmod 600 '+tempdir+''+name+'/root/.ssh/authorized_keys')

    else:    
        runCmd('wget ' + base_url + '/conf/centos/ifcfg-eth1 -O '+tempdir+''+name + '/etc/sysconfig/network-scripts/ifcfg-eth1')
        runCmd('wget ' + base_url + '/conf/hosts_india -O '+tempdir+''+name + '/etc/hosts')
        #temporal
        runCmd('mkdir -p '+tempdir+''+name+'/root/.ssh')
        os.system('echo "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsAaCJFcGUXSmA2opcQk/HeuiJu417a69KbuWNjf1UqarP7t0hUpMXQnlc8+yfi'+\
                  'fI8FpoXtNCai8YEPmpyynqgF9VFSDwTp8use61hBPJn2isZha1JvkuYJX4n3FCHOeDlb2Y7M90DvdYHwhfPDa/jIy8PvFGiFkRLSt1kghY'+\
                  'xZSleiikl0OxFcjaI8N8EiEZK66HAwOiDHAn2k3oJDBTD69jydJsjExOwlqZoJ4G9ScfY0rpzNnjE9sdxpJMCWcj20y/2T/oeppLmkq7aQtu'+\
                  'p8JMPptL+kTz5psnjozTNQgLYtYHAcfy66AKELnLuGbOFQdYxnINhX3e0iQCDDI5YQ== jdiaz@india.futuregrid.org" >> '+tempdir+''+name+'/root/.ssh/authorized_keys')
        os.system('chmod 600 '+tempdir+''+name+'/root/.ssh/authorized_keys')
    #os.system('echo localhost > '+tempdir+''+name + '/etc/hostname')
    #runCmd('hostname localhost')
    centosLog.info('Injected networking configuration')


    # Setup package repositories 
    #TODO: Set mirros to IU/FGt
    
    #centosLog.info('Configuring repositories')    
       
    
    # Install BCFG2 client
    
    centosLog.info('Installing BCFG2 client')
    runCmd('chroot '+tempdir+''+name + ' rpm -ivh http://download.fedora.redhat.com/pub/epel/5/i386/epel-release-5-4.noarch.rpm')
    """"    
    runCmd('chroot '+tempdir+''+name + ' yum -y install bcfg2')
    #os.system('chroot '+tempdir+' '+name+' apt-get -y install bcfg2')
    centosLog.info('Installed BCFG2 client')

    
    #Configure BCFG2 client
    centosLog.info('Configuring BCFG2')
    runCmd('wget ' + base_url + '/bcfg2/bcfg2.conf -O '+tempdir+''+name + '/etc/bcfg2.conf')
    runCmd('wget ' + base_url + '/bcfg2/bcfg2.ca -O '+tempdir+''+name + '/etc/bcfg2.ca')
    runCmd('wget ' + base_url + '/bcfg2/default -O '+tempdir+''+name + '/etc/default/bcfg2')
    centosLog.info('Injected FG deployment files')

    #Inject group info for Probes
    os.system('echo ' + name + ' > '+tempdir+''+name + '/etc/bcfg2.group')
    centosLog.info('Injected probes hook for unique group')
    
    centosLog.info('Configured BCFG2 client settings')
    """    
    #Install packages
    if pkgs != None:
        centosLog.info('Installing user-defined packages')        
        runCmd('chroot '+tempdir+''+name + ' yum -y install ' + pkgs)
        centosLog.info('Installed user-defined packages')

    #Setup BCFG2 server groups
    success=push_bcfg2_group(name, pkgs, 'centos', version)
    if success: 
        centosLog.info('Setup new BCFG2 group')    
        #Finished, now clean up
        centosLog.info('Genereated centos image ' + name + ' successfully!')
        output=name
    else:
        output="Error generating bcfg2 group configuration"

    
    cleanup(name)

    return output



def buildFedora(name, version, arch, pkgs, tempdir):

    runCmd('')


def runCmd(cmd):
    cmdLog = logging.getLogger('exec')
    cmdLog.debug(cmd)
    #os.system(cmd)
    #Use subprocess to properly direct output to log
    #p = subprocess.Popen(cmd, shell=True)
    p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE) 
    std = p.communicate()
    if len(std[0]) > 0: 
        cmdLog.debug('stdout: ' + std[0])
    #cmdLog.debug('stderr: '+std[1])

    #cmdLog.debug('Ret status: '+str(p.returncode))
    if p.returncode != 0:
        cmdLog.error('Command: ' + cmd + ' failed, status: ' + str(p.returncode) + ' --- ' + std[1])
        cleanup(namedir)
        print "error"       
        print "p.returncode"
        sys.exit(p.returncode)



def cleanup(name):
    #Cleanup
    cleanupLog = logging.getLogger('cleanup')

    os.system('umount '+tempdir+''+name + '/proc')
    os.system('umount '+tempdir+''+name + '/dev/pts')
    
    cmd = 'umount '+tempdir+''+name
    cleanupLog.debug('Executing: ' + cmd)
    os.system(cmd)
    os.system("rm -rf "+tempdir+''+name)
     
    cleanupLog.debug('Cleaned up mount points')


def manifest(user, name, os, version, arch, pkgs, givenname, description, tempdir):

    manifestLog = logging.getLogger('manifest')

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

    filename = ''+tempdir+''+name + '.manifest.xml'
    file = open(filename, 'w')
    #Document.PrettyPrint(manifest, file)
    #manifest.writexml(file, indent='    ', addindent='    ', newl='\n')

    output = manifest.toprettyxml()
    file.write(output)
    
    manifestLog.info('Genereated manifest file: ' + filename)
    
def push_bcfg2_group(name, pkgs, os, version):
    #Push the group information to the BCFG2 server via a socket connection

    bcfg2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bcfg2.connect((bcfg2_url, bcfg2_port))
    
    success=True
    
    #Send group name
    bcfg2.send(name)
    ret = bcfg2.recv(100)
    if ret != 'OK':
        logging.error('Incorrect reply from the server:' + ret)
        success=False
    else:
        #Send OS 
        bcfg2.send(os)
        ret = bcfg2.recv(100)
        if ret != 'OK':
            logging.error('Incorrect reply from the server:' + ret)
            success=False
        else:
            #Send OS Version
            bcfg2.send(version)
            ret = bcfg2.recv(100)
            if ret != 'OK':
                logging.error('Incorrect reply from the server:' + ret)
                success=False
            else:
                #Send package information
                bcfg2.send(pkgs)
                ret = bcfg2.recv(100)
                if ret != 'OK':
                    logging.error('Incorrect reply from the server:' + ret)
                    success=False
                    
    return success



if __name__ == "__main__":
    main()
#END




