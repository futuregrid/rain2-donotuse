#!/usr/bin/python
# Description: Command line front end for image generator
#
# Author: Andrew J. Younge and Javier Diaz
#



from optparse import OptionParser
import sys
import os
from types import *
import socket
from subprocess import * 
import logging
import logging.handlers
from xml.dom.minidom import Document,parse


#Eventually need to move these to a config file
xcat_port = 56789
moab_port = 56790
base_url = "http://fg-gravel3.futuregrid.iu.edu/"

#Default Kernels to use for each deployment
default_xcat_kernel = '2.6.18-164.el5'
default_xcat_kernel_ubuntu = '2.6.35-22-generic'
default_euca_kernel = '2.6.27.21-0.1-xen'

log_filename = 'fg-image-deploy.log'

TEST_MODE=False

class ImageDeploy(object):
    ############################################################
    # __init__
    ############################################################
    def __init__(self, kernel, user,nasaddr, shareddirserver, logger):
        super(ImageDeploy, self).__init__()
        
        self.tempdir="/tmp/"  #root of the temporal directory to mount the image.Subdirectories are created inside
        self.kernel=kernel
        self.user=user      
        self.nasaddr=nasaddr
        self.shareddirserver=shareddirserver  #directory 
        self.logger=logger
        
        self.manifestname=""
        self.imagefile=""
        self.extractdir="./"
        
        #from manifest
        self.name=""
        self.givenname=""
        self.operatingsystem=""
        self.version=""
        self.arch=""
    
        
    
    #if type(os.getenv('FG_USER')) is not NoneType:
    #    user = os.getenv('FG_USER')
    #elif type(ops.user) is not NoneType:
    #   user = ops.user
    #TODO: authenticate user via promting for CERT or password to auth against LDAP 

    
    def handle_image(self, image):
        
        nameimg=""
                
        urlparts=image.split("/")
        self.logger.debug(str(urlparts))
        if len(urlparts) == 1:
            nameimg=urlparts[0].split(".")[0]
        elif len(urlparts) == 2:
            nameimg=urlparts[1].split(".")[0]
            if (urlparts!="."):
                self.extractdir=urlparts[0]+"/"
        else:
            nameimg=urlparts[len(urlparts)-1].split(".")[0]
            self.extractdir=""
            for i in range(len(urlparts)-1):
                self.extractdir+=urlparts[i]+"/"
            
        self.logger.debug("name img "+nameimg)
        self.logger.debug("extract dir "+self.extractdir)
        
        self.logger.info('untar file with image and manifest')
        stat=os.system("tar xvfz "+image+" -C "+self.extractdir)
        
        if (stat!=0):
            print "Error: the files were not extracted"
            sys.exit(1)
        
        
        self.tempdir+=nameimg+"/"
        
        self.manifestname=nameimg+".manifest.xml"
        
        manifestfile = open(self.extractdir+"/"+self.manifestname, 'r')
        manifest = parse(manifestfile)

        
        self.imagefile = nameimg+'.img'
        self.logger.info('Using image: '+self.imagefile)    
        
        self.name = manifest.getElementsByTagName('name')[0].firstChild.nodeValue.strip()
        self.givenname = manifest.getElementsByTagName('givenname')
        self.operatingsystem = manifest.getElementsByTagName('os')[0].firstChild.nodeValue.strip()
        self.version = manifest.getElementsByTagName('version')[0].firstChild.nodeValue.strip()
        self.arch = manifest.getElementsByTagName('arch')[0].firstChild.nodeValue.strip()
        #kernel = manifest.getElementsByTagName('kernel')[0].firstChild.nodeValue.strip()

        self.logger.debug(self.name + " "+ self.operatingsystem+ " " + self.version +" "+ self.arch)

    
    def euca_method(self):
        if isinstance(self.kernel,NoneType):
            self.kernel = default_euca_kernel
            
        #Mount the root image for final edits and compressing
        self.logger.info('Mounting image...')
        cmd = 'mkdir -p '+self.tempdir+''+ self.name
        self.runCmd(cmd)
        cmd = 'sudo mount -o loop ' + self.imagefile + ' '+self.tempdir+''+ self.name
        self.runCmd(cmd)

        #TODO: Pick kernel and ramdisk from available eki and eri

        #hardcoded for now
        eki = 'eki-78EF12D2'
        eri = 'eri-5BB61255'
 

        #Inject the kernel
        self.logger.info('Retrieving kernel '+kernel)
        self.runCmd('sudo wget '+base_url+'kernel/'+self.kernel+'.modules.tar.gz -O '+self.tempdir+''+self.kernel+'.modules.tar.gz')
        self.runCmd('sudo tar xfz '+self.tempdir+''+self.kernel+'.modules.tar.gz --directory '+self.tempdir+''+self.name+'/lib/modules/')
        self.logger.info('Injected kernel '+kernel)


        # Setup fstab
        fstab = '''
# Default Ubuntu fstab
 /dev/sda1       /             ext3     defaults,errors=remount-ro 0 0
 /dev/sda3    swap          swap     defaults              0 0
 proc            /proc         proc     defaults                   0 0
 devpts          /dev/pts      devpts   gid=5,mode=620             0 0
 '''

        f= open(self.tempdir+'/fstab', 'w')
        f.write(fstab)
        f.close()
        os.system('sudo mv -f '+self.tempdir+'/fstab '+self.tempdir+'rootimg/etc/fstab')
        self.logger.info('Injected fstab')

        #Done making changes to root fs
        self.runCmd('sudo umount '+self.tempdir+''+self.name)
        
        print 'Name-User: ' +self.name + '-'+ self.user

##TODO. I think that this should be in deploy-server

        #Bucket folder
        self.runCmd('mkdir -p '+self.tempdir+''+ self.user)

        #Bundle Image
        cmd = 'euca-bundle-image --image '+self.tempdir+'' + self.name +'.img --destination '+self.tempdir+''+self.user+ ' --kernel ' + eki + ' --ramdisk ' + eri
        self.runCmd(cmd)

        #Upload bundled image
        cmd = 'bash -c \" cd '+self.tempdir+'; euca-upload-bundle --bucket ' + self.user + ' --manifest '+self.user+'/'+self.name+'.img.manifest.xml \"'
        os.system(cmd)    

        #Register image
        cmd = 'bash -c \" cd '+self.tempdir+'; euca-register '+self.user+'/'+self.name+'.img.manifest.xml \"'
        os.system(cmd)
    

    def xcat_method(self, xcatmachine, moabmachine):
        
        """
        xcatserver=ops.xcat.lower()
        if (xcatserver == "india" or xcatserver== "india.futuregrid.org" ):
            #load config for india (later will be from a file)
            dest="im1"
            tempdirserver="/media/scratch"
            nasaddr="india.futuregrid.org"
            
        elif (xcatserver == "th1r" or xcatserver== "th1r.tidp.iu.futuregrid.org" ):
            #load config for minicluster (later will be from a file)
            dest="tm1r.tidp.iu.futuregrid.org"
            tempdirserver="/media/scratch"
            nasaddr="th1r.tidp.iu.futuregrid.org"
            
        else:
            self.logger.error("xCAT server not recognized")
            sys.exit(1)
        """
        
                
        self.logger.info("server "+self.nasaddr)
        
        self.logger.info("server dir "+self.shareddirserver)
        
        #Select kernel version
        if isinstance(self.kernel,NoneType):
            if (self.operatingsystem!="ubuntu"):
                self.kernel = default_xcat_kernel
            elif (self.operatingsystem == "ubuntu"):
                self.kernel = default_xcat_kernel_ubuntu                
    
    
        #Mount the root image for final edits and compressing
        self.logger.info('Mounting image...')
        cmd = 'mkdir -p '+self.tempdir+'/rootimg' #to have write access in this directory as normal user. Needed to create files with open
        self.runCmd(cmd)
        cmd = 'sudo mount -o loop '+self.extractdir+'/'+ self.imagefile + ' '+self.tempdir+'/rootimg/'
        self.runCmd(cmd)
        fstab=""
        if (self.operatingsystem!="ubuntu"):
            self.logger.info('Installing torque')
            if(TEST_MODE):
                self.logger.info('Torque for minicluster')
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.5.1_minicluster/torque-2.5.1.tgz'+\
                       ' fg-gravel3.futuregrid.iu.edu/torque/torque-2.5.1_minicluster/var.tgz')   
                self.runCmd('sudo tar xfz torque-2.5.1.tgz -C '+self.tempdir+'/rootimg/usr/local/')
                self.runCmd('sudo tar xfz var.tgz -C '+self.tempdir+'/rootimg/')
                self.runCmd('sudo rm -f var.tgz torque-2.5.1.tgz')
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.5.1_minicluster/pbs_mom -O '+self.tempdir+'/rootimg/etc/init.d/pbs_mom')
                
                self.logger.info('Configuring network')        
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/conf/centos/netsetup_minicluster.tgz')   
                self.runCmd('sudo tar xfz netsetup_minicluster.tgz -C '+self.tempdir+'/rootimg/etc/')
                self.runCmd('sudo chmod +x '+self.tempdir+'/rootimg/etc/netsetup/netsetup.sh')
                self.runCmd('sudo rm -f netsetup_minicluster.tgz')                
                
                os.system('touch ./_hosts')
                os.system('cat '+self.tempdir+'/rootimg/etc/hosts'+' > ./_hosts')            
                f= open('./_hosts', 'a')
                f.write("\n"+"172.29.200.1 t1 tm1"+'\n'+"172.29.200.3 tc1"+'\n'+"149.165.145.35 tc1r.tidp.iu.futuregrid.org tc1r"+'\n'+\
                        "172.29.200.4 tc2"+'\n'+"149.165.145.36 tc2r.tidp.iu.futuregrid.org tc2r"+'\n')        
                f.close()          
                os.system('sudo mv -f ./_hosts '+self.tempdir+'/rootimg/etc/hosts')
                os.system('sudo chown root:root '+self.tempdir+'/rootimg/etc/hosts')
                os.system('sudo chmod 644 '+self.tempdir+'/rootimg/etc/hosts')
                
                self.runCmd('sudo mkdir -p '+self.tempdir+'/rootimg/root/.ssh')
                
                os.system('touch ./_authorized_keys')
                f= open('./_authorized_keys', 'a')
                f.write("ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEA5uo1oo4+/wzKl+4hfaD/cf4MF6WDrWnG8wtufSk4ThOvCfc4a1BiEUZ+O71"
                          "u1qzgbvi0TnA+tc3fS9mU2zrBZeIL1eB2VkK4cjzltIS6pthm8tFUCtS1hHYupnftC/1Hbzo2zJB+nGAfIznmkYATiVvulwl6SudV"
                          "RKM2SUahWsGXh4JkZqt4vAAuBVifFwE3axh3g9nji8wq4ITYjzTWDsogbcwsJNXpF9dkyuDg5xQmEszUsGSug3hA4aVrgs36cnLNG"
                          "5i+zWlwmA31IV+6Yyx1+s6YYp6YG8GNiuL1vZUYrnvfmRbm24eUc7cU4Dz6hBfI2wqjDkCU15HRM0ZV3Q== root@tm1"+'\n')        
                f.close()                 
                os.system('sudo mv ./_authorized_keys '+self.tempdir+'/rootimg/root/.ssh/authorized_keys')
                
                os.system('sudo chown root:root '+self.tempdir+'/rootimg/root/.ssh/authorized_keys')
                os.system('sudo chmod 600 '+self.tempdir+'/rootimg/root/.ssh/authorized_keys')
                
                   
                fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
172.29.200.1:/export/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''             
                
                
            else:#Later we should be able to chose the cluster where is deployed
                self.logger.info('Torque for India')    
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/conf/hosts_india -O '+self.tempdir+'/rootimg/etc/hosts')
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.4.8_india/opt.tgz'+\
                       ' fg-gravel3.futuregrid.iu.edu/torque/torque-2.4.8_india/var.tgz')   
                self.runCmd('sudo tar xfz opt.tgz -C '+self.tempdir+'/rootimg/')
                self.runCmd('sudo tar xfz var.tgz -C '+self.tempdir+'/rootimg/')
                self.runCmd('sudo rm -f var.tgz opt.tgz')            
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/torque/torque-2.4.8_india/pbs_mom -O '+self.tempdir+'/rootimg/etc/init.d/pbs_mom')
                
                self.logger.info('Configuring network')
                self.runCmd('sudo mkdir '+self.tempdir+'/rootimg/etc/netsetup/')              
                self.runCmd('sudo wget fg-gravel3.futuregrid.iu.edu/conf/centos/netsetup.sh_india -O '+self.tempdir+'/rootimg/etc/netsetup/netsetup.sh')
                self.runCmd('sudo chmod +x '+self.tempdir+'/rootimg/etc/netsetup/netsetup.sh')             
                self.runCmd('sudo wget ' + base_url + '/conf/centos/ifcfg-eth1 -O '+self.tempdir+'/rootimg/etc/sysconfig/network-scripts/ifcfg-eth1')
                self.runCmd('sudo wget ' + base_url + '/conf/hosts_india -O '+self.tempdir+ '/rootimg/etc/hosts')
                
                self.runCmd('sudo mkdir -p '+self.tempdir+'/rootimg/root/.ssh')
                os.system('touch ./_authorized_keys')
                f= open('./_authorized_keys', 'a')
                f.write("\n"+"ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAsAaCJFcGUXSmA2opcQk/HeuiJu417a69KbuWNjf1UqarP7t0hUpMXQnlc8+yfi"
                          "fI8FpoXtNCai8YEPmpyynqgF9VFSDwTp8use61hBPJn2isZha1JvkuYJX4n3FCHOeDlb2Y7M90DvdYHwhfPDa/jIy8PvFGiFkRLSt1kghY"
                          "xZSleiikl0OxFcjaI8N8EiEZK66HAwOiDHAn2k3oJDBTD69jydJsjExOwlqZoJ4G9ScfY0rpzNnjE9sdxpJMCWcj20y/2T/oeppLmkq7aQtu"
                          "p8JMPptL+kTz5psnjozTNQgLYtYHAcfy66AKELnLuGbOFQdYxnINhX3e0iQCDDI5YQ== jdiaz@india.futuregrid.org"+"\n")        
                f.close()                 
                os.system('sudo mv ./_authorized_keys '+self.tempdir+'/rootimg/root/.ssh/authorized_keys')                
                os.system('sudo chown root:root '+self.tempdir+'/rootimg/root/.ssh/authorized_keys')
                os.system('sudo chmod 600 '+self.tempdir+'/rootimg/root/.ssh/authorized_keys')                
                
                #self.runCmd('sudo chroot '+self.tempdir+'/rootimg/ /sbin/chkconfig --add pbs_mom')
                #self.runCmd('sudo chroot '+self.tempdir+'/rootimg/ /sbin/chkconfig pbs_mom on')       
                
                fstab = '''
# xCAT fstab 
devpts  /dev/pts devpts   gid=5,mode=620 0 0
tmpfs   /dev/shm tmpfs    defaults       0 0
proc    /proc    proc     defaults       0 0
sysfs   /sys     sysfs    defaults       0 0
149.165.146.145:/users /N/u      nfs     rw,rsize=1048576,wsize=1048576,intr,nosuid
'''
            
            self.runCmd('sudo chmod +x '+self.tempdir+'/rootimg/etc/init.d/pbs_mom')
            
            #Modifying rc.local to restart network and start pbs_mom at the end
            os.system('touch ./_rc.local')
            os.system('cat '+self.tempdir+'/rootimg/etc/rc.d/rc.local'+' > ./_rc.local')            
            f= open('./_rc.local', 'a')
            f.write("\n"+"/etc/netsetup/netsetup.sh"+"\n"+"sleep 10"+"\n"+"/etc/init.d/pbs_mom start"+'\n'+'mount -a'+'\n')        
            f.close()          
            os.system('sudo mv -f ./_rc.local '+self.tempdir+'/rootimg/etc/rc.d/rc.local')
            os.system('sudo chown root:root '+self.tempdir+'/rootimg/etc/rc.d/rc.local')
            os.system('sudo chmod 755 '+self.tempdir+'/rootimg/etc/rc.d/rc.local')
                               
            
            f= open(self.tempdir+'/config', 'w')
            f.write("opsys "+ self.operatingsystem + "" + self.name+"\n"+"arch "+ self.arch)        
            f.close()
            
            os.system('sudo mv '+self.tempdir+'/config '+self.tempdir+'/rootimg/var/spool/torque/mom_priv/')
            os.system('sudo chown root:root '+self.tempdir+'/rootimg/var/spool/torque/mom_priv/config')
    
        #Inject the kernel
        self.logger.info('Retrieving kernel '+self.kernel)
        self.runCmd('sudo wget '+base_url+'kernel/'+self.kernel+'.modules.tar.gz -O '+self.tempdir+''+self.kernel+'.modules.tar.gz')
        self.runCmd('sudo tar xfz '+self.tempdir+''+self.kernel+'.modules.tar.gz --directory '+self.tempdir+'/rootimg/lib/modules/')
        self.logger.info('Injected kernel '+self.kernel)
    
    
        #Setup fstab
        f= open(self.tempdir+'/fstab', 'w')
        f.write(fstab)
        f.close()
        os.system('sudo mv -f '+self.tempdir+'/fstab '+self.tempdir+'rootimg/etc/fstab')
        self.logger.info('Injected fstab')
           
        ####################        
        #We are going to send the image and then we copy there the files
        #####################
        #self.logger.info('Compressing image')
        #Its xCAT, so use gzip with cpio compression.
        #cmd = 'sudo bash -c \" cd '+self.tempdir+'; find rootimg/. | cpio -H newc -o | gzip -9 > '+self.tempdir+'/rootimg.gz\"'        
        #os.system(cmd) #use system because of the pipes
    
        #cmd = 'sudo tar cfz '+self.tempdir+'' + name + '.tar.gz --directory '+self.tempdir+' ' + name 
    
        cmd = 'sudo umount '+self.tempdir+'rootimg'
        self.runCmd(cmd)
        
        self.logger.info('Compressing image')
        cmd = ('sudo tar cvfz '+self.extractdir+'/'+self.imagefile+'.tgz -C '+self.extractdir+' '+self.imagefile)
        self.runCmd(cmd)
        
        #Copy the image to the Shared directory.        
        self.logger.info('Uploading image. You may be asked for ssh/paraphrase password')
        cmd = 'scp '+self.extractdir+'/'+self.imagefile+'.tgz '+ self.user + '@' + self.nasaddr + ':'+self.shareddirserver+'/'
        self.logger.info(cmd)
        self.runCmd(cmd)
        
        
        #if name is in tempdir string then del tempdir, else only rootimg
        self.logger.info('sudo rm -rf '+self.tempdir)
        self.logger.info('sudo rm -f '+self.extractdir+'/'+self.imagefile+'.tgz')
        self.runCmd("sudo rm -rf "+self.tempdir)
        self.runCmd("sudo rm -f "+self.extractdir+'/'+self.imagefile+'.tgz')
        
        #remove local img and manifest
        self.runCmd("rm -f "+self.extractdir+'/'+self.manifestname+" "+self.extractdir+'/'+self.imagefile)
    
        #xCAT server                
        self.logger.info('Connecting to xCAT server')
    
        msg = self.name+','+self.operatingsystem+','+self.version+','+self.arch+','+self.kernel+','+self.shareddirserver
        self.logger.debug('Sending message: ' + msg)
    
        #Notify xCAT deployment to finish the job
        xcatServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        xcatServer.connect((xcatmachine, xcat_port))
    
        xcatServer.send(msg)
        #check if the server received all parameters
        ret = xcatServer.recv(1024)
        if ret != 'OK':
            self.logger.error('Incorrect reply from the xCat server:'+ret)            
            sys.exit(1)
    
        #recieve the prefix parameter from xcat server
        moabstring=xcatServer.recv(2048)
        self.logger.debug("String receved from xcat server "+moabstring)
        
        self.logger.info('Connecting to Moab server')
        
        moabstring += ','+self.name+','+self.operatingsystem+','+self.arch
        
        self.logger.debug('Sending message: ' + moabstring)
        
        moabServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        moabServer.connect((moabmachine, moab_port))
        moabServer.send(moabstring)
        ret = moabServer.recv(100)
        if ret != 'OK':
            self.logger.error('Incorrect reply from the Moab server:'+ret)
            sys.exit(1)
        
         
        self.logger.info('Image deployed to xCAT. Please allow a few minutes for xCAT to register the image before attempting to use it.')
    

    def runCmd(self, cmd):
        cmdLog = logging.getLogger('exec')
        cmdLog.debug(cmd)
        p = Popen(cmd.split(' '), stdout=PIPE, stderr=PIPE) 
        std = p.communicate()
        if len(std[0]) > 0: 
            cmdLog.debug('stdout: '+std[0])
        #cmdLog.debug('stderr: '+std[1])
    
        #cmdLog.debug('Ret status: '+str(p.returncode))
        if p.returncode != 0:
            cmdLog.error('Command: '+cmd+' failed, status: '+str(p.returncode)+' --- '+std[1])
            sys.exit(p.returncode)



def main():
    
    #Set up logging (later this will use the logs from futuregrid.utils)
    
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    debugLevel=logging.INFO
    imgmanif=""
    type="" 
    user=""   
    
    parser = OptionParser()

    logger.info('Starting image deployer...')        
    
    parser.add_option('-i', '--image', dest='image', help='Name of tgz file that contains manifest and img')

    parser.add_option('-s', '--nasaddr', dest='nasaddr', help='Address to upload the image file. Login machine')
    parser.add_option("-t", "--tempdir", dest="shareddirserver", help="shared dir to upload the image")
    parser.add_option('-m', '--moab', dest='moab', help='Address of the machine that has Moab. (localhost if not specified)')
    
    parser.add_option('-x', '--xcat', dest='xcat', help='Deploy image to xCAT, which is in the specified addr. Management machine')
    parser.add_option('-e', '--euca', dest='euca', help='Deploy the image to Eucalyptus, which is in the specified addr')
    parser.add_option('-n', '--nimbus', dest='nimbus', help='Deploy the image to Nimbus, which is in the specified addr')

    parser.add_option("-u", "--user", dest="user", help="FutureGrid username")

    parser.add_option("-d", "--debug", action="store_true", dest="debug", help="Enable debug logs")
    parser.add_option("-k", "--kernel", dest="kernel", help="Specify the desired kernel (must be exact version and approved for use within FG")

    (ops, args) = parser.parse_args()
    
    if (len(sys.argv) == 1):
        parser.print_help()
        sys.exit(1)
    
#    if(len(args)== 0):
#        parser.print_help()
#        sys.exit(1) 

    #Turn debugging off
    #Turn debugging off
    if not ops.debug:
        logging.basicConfig(level=logging.INFO)
        ch.setLevel(logging.INFO)
    
    #defining FG user
    try:
        user = os.environ['FG_USER']
    except KeyError:
        if not isinstance(ops.user, NoneType):
            user = ops.user
        else:
            parser.error("Please, define FG_USER to indicate your user name or specify it by using the -u option")
            logger.error("User not specified")
            sys.exit(1) 
        
    imgdeploy=ImageDeploy(ops.kernel,user, ops.nasaddr, ops.shareddirserver, logger)
    #Define the type
    
    #Get image destination
    if not isinstance(ops.image,NoneType):
        if(os.path.isfile(ops.image)):
            imgdeploy.handle_image(ops.image)        
    else:
        parser.error('You need to specify a tgz that contains the image and the manifest (-i option)')
        logger.error('Image file not found')
        sys.exit(1)
        
    #EUCALYPTUS
    if not isinstance(ops.euca, NoneType):
        imgdeploy.euca_method()
    #XCAT
    elif not isinstance(ops.xcat, NoneType):
        moab=""
        if isinstance(ops.nasaddr,NoneType):
            print "You need to specify the machine where you are going to upload the image (-s option)"
            print "This is the login machine of the cluster"
            sys.exit(1)
           
        if isinstance(ops.shareddirserver,NoneType):            
            print "You need to specify a directory to upload the image (-t option)"
            print "This is a directory in the login machine that is shared with the xCAT server machine"
            sys.exit(1)
        if isinstance(ops.moab, NoneType):
            moab="localhost"
        else:
            moab=ops.moab
            
        imgdeploy.xcat_method(ops.xcat, moab)
    
    #NIMBUS
    elif not isinstance(ops.nimbus, NoneType):
        #TODO
        roar = 0  
        logger.info("This is not yet implemented")  
    else:
        logger.error('Deployment type not specified')
        parser.error('You need to specify at least one deployment destination type: xcat (-x option), euca (-e option) or nimbus(-n option)')        
        sys.exit(1)
        

if __name__ == "__main__":
    main()
#END

