#!/usr/bin/env python
"""
Class to read Image Management Server configuration
"""

import os
import ConfigParser
import string
import sys
import logging

configFileName = "fg-server.conf"

class IMServerConf(object):

    ############################################################
    # init
    ############################################################

    def __init__(self):
        super(IMServerConf, self).__init__()

        self._fgpath = ""
        try:
            self._fgpath = os.environ['FG_PATH']
        except KeyError:
            self._fgpath = os.path.dirname(__file__) + "/../../"

        ##DEFAULT VALUES##
        self._localpath = "~/.fg/"

        self._configfile = os.path.expanduser(self._localpath) + "/" + configFileName
        #print self._configfile
        if not os.path.isfile(self._configfile):
            self._configfile = os.path.expanduser(self._fgpath) + "/etc/" + configFileName
            #print self._configfile
            if not os.path.isfile(self._configfile):
                self._configfile = os.path.expanduser(os.path.dirname(__file__)) + "/" + configFileName
                #print self._configfile

                if not os.path.isfile(self._configfile):   
                    print "ERROR: configuration file "+configFileName+" not found"
                    sys.exit(1)
        
        #image generation server
        self._gen_port = 0
        self._proc_max = 0
        self._refresh_status = 0
        self._wait_max = 3600
        self._vmfile_centos = {}
        self._vmfile_rhel = ""
        self._vmfile_ubuntu ="" 
        self._vmfile_debian = ""
        self._xmlrpcserver = ""
        self._bridge = ""
        self._serverdir = ""
        self._addrnfs = ""
        self._tempdirserver_gen = ""
        self._tempdir_gen = ""
        self._http_server_gen = ""
        self._bcfg2_url = ""
        self._bcfg2_port = 0
        self._oneuser = ""
        self._onepass = ""
        self._log_gen = ""
        self._logLevel_gen=""
        self._ca_certs_gen = ""
        self._certfile_gen = ""
        self._keyfile_gen = ""

        #image server xcat
        self._xcat_port = 0
        self._xcatNetbootImgPath = ''
        self._http_server = ""
        self._log_xcat = ""
        self._logLevel_xcat = ""
        self._test_xcat = ""
        self._default_xcat_kernel_centos = {}
        self._default_xcat_kernel_ubuntu = {}
        self._tempdir_xcat = ""
        self._ca_certs_xcat = ""
        self._certfile_xcat = ""
        self._keyfile_xcat = ""
        self._max_diskusage = 0

        #image server moab
        self._moab_port = 0
        self._moabInstallPath = ""
        self._log_moab = ""
        #self._timeToRestartMoab = 0
        self._logLevel_moab = ""
        self._ca_certs_moab = ""
        self._certfile_moab = ""
        self._keyfile_moab = ""
        
        #image server iaas
        self._iaas_port = 0
        self._tempdir_iaas = ""   
        self._proc_max_iaas = "" 
        self._refresh_status_iaas = 0
        self._http_server_iaas = ""    
        self._log_iaas = ""
        self._logLevel_iaas = ""   
        self._ca_certs_iaas = ""
        self._certfile_iaas = ""
        self._keyfile_iaas = ""
        self._default_euca_kernel = ""
        self._default_nimbus_kernel = ""
        self._default_openstack_kernel = ""
        self._default_opennebula_kernel = ""

        
        self._logLevel_default = "DEBUG"
        self._logType = ["DEBUG", "INFO", "WARNING", "ERROR"]
        
        self._config = ConfigParser.ConfigParser()
        self._config.read(self._configfile)

    ############################################################
    # getConfigFile
    ############################################################
    def getConfigFile(self):
        return self._configfile
    
    #image generation server
    def getGenPort(self):
        return self._gen_port
    def getProcMax(self):
        return self._proc_max
    def getRefreshStatus(self):
        return self._refresh_status
    def getWaitMax(self):
        return self._wait_max
    def getVmFileCentos(self):
        return self._vmfile_centos
    def getVmFileRhel(self):
        return self._vmfile_rhel
    def getVmFileUbuntu(self):
        return self._vmfile_ubuntu
    def getVmFileDebian(self): 
        return self._vmfile_debian
    def getXmlRpcServer(self):
        return self._xmlrpcserver
    def getBridge(self):
        return self._bridge
    def getServerDir(self):
        return self._serverdir
    def getAddrNfs(self):
        return self._addrnfs
    def getTempDirServerGen(self):
        return self._tempdirserver_gen
    def getTempDirGen(self):
        return self._tempdir_gen
    def getHttpServerGen(self):
        return self._http_server_gen
    def getBcfg2Url(self):
        return self._bcfg2_url
    def getBcgf2Port(self):
        return self._bcfg2_port
    def getOneUser(self):
        return self._oneuser
    def getOnePass(self):
        return self._onepass
    def getLogGen(self):
        return self._log_gen
    def getLogLevelGen(self):
        return self._logLevel_gen
    def getCaCertsGen(self):
        return self._ca_certs_gen
    def getCertFileGen(self): 
        return self._certfile_gen
    def getKeyFileGen(self): 
        return self._keyfile_gen
    
    #image server xcat    
    def getXcatPort(self):
        return self._xcat_port    
    def getXcatNetbootImgPath(self):
        return self._xcatNetbootImgPath
    def getHttpServer(self):
        return self._http_server
    def getLogXcat(self):
        return self._log_xcat
    def getLogLevelXcat(self):
        return self._logLevel_xcat
    def getTestXcat(self):
        return self._test_xcat
    def getDXKernelCentos(self):
        return self._default_xcat_kernel_centos
    def getDXKernelUbuntu(self):
        return self._default_xcat_kernel_ubuntu
    def getTempDirXcat(self):
        return self._tempdir_xcat
    def getCaCertsXcat(self):
        return self._ca_certs_xcat
    def getCertFileXcat(self): 
        return self._certfile_xcat
    def getKeyFileXcat(self): 
        return self._keyfile_xcat 
    def getMaxDiskUsage(self):
        return self._max_diskusage
    
    #image server moab    
    def getMoabPort(self):
        return self._moab_port
    def getMoabInstallPath(self):
        return self._moabInstallPath
    def getLogMoab(self):
        return self._log_moab
    #def getTimeToRestartMoab(self):
        #return self._timeToRestartMoab
    def getLogLevelMoab(self):
        return self._logLevel_moab
    def getCaCertsMoab(self):
        return self._ca_certs_moab
    def getCertFileMoab(self):
        return self._certfile_moab
    def getKeyFileMoab(self):
        return self._keyfile_moab
            
    #image server IaaS    
    def getIaasPort(self):
        return self._iaas_port
    def getTempDirIaas(self):
        return self._tempdir_iaas
    def getProcMaxIaas(self):
        return self._proc_max_iaas
    def getRefreshStatusIaas(self):
        return self._refresh_status_iaas
    def getHttpServerIaas(self):
        return self._http_server_iaas
    def getLogIaas(self):
        return self._log_iaas
    def getLogLevelIaas(self):
        return self._logLevel_iaas
    def getCaCertsIaas(self):
        return self._ca_certs_iaas
    def getCertFileIaas(self):
        return self._certfile_iaas
    def getKeyFileIaas(self):
        return self._keyfile_iaas
    def getDefaultEucaKernel(self):
        return self._default_euca_kernel
    def getDefaultNimbusKernel(self):
        return self._default_nimbus_kernel
    def getDefaultOpenstackKernel(self):
        return self._default_openstack_kernel
    def getDefaultOpennebulaKernel(self):
        return self._default_opennebula_kernel
    
    ############################################################
    # load_generateServerConfig
    ############################################################
    def load_generateServerConfig(self):        
        section = "GenerateServer"
        try:
            self._gen_port = int(self._config.get(section, 'port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No port option found in section " + section + " file " + self._configfile
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)
        try:
            self._proc_max = int(self._config.get(section, 'proc_max', 0))
        except ConfigParser.NoOptionError:
            print "Error: No proc_max option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._refresh_status = int(self._config.get(section, 'refresh', 0))
        except ConfigParser.NoOptionError:
            print "Error: No refresh option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._wait_max = int(self._config.get(section, 'wait_max', 0))
        except ConfigParser.NoOptionError:
            print "Error: No wait_max option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:            
            centos_temp = os.path.expanduser(self._config.get(section, 'vmfile_centos', 0))
            centos_temp1 = centos_temp.split(",")
            for i in range(len(centos_temp1)):      
                self._vmfile_centos[centos_temp1[i].split(":")[0].strip()]=centos_temp1[i].split(":")[1].strip()            
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_centos option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._vmfile_rhel = os.path.expanduser(self._config.get(section, 'vmfile_rhel', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_rhel option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._vmfile_ubuntu = os.path.expanduser(self._config.get(section, 'vmfile_ubuntu', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_ubuntu option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._vmfile_debian = os.path.expanduser(self._config.get(section, 'vmfile_debian', 0))
        except ConfigParser.NoOptionError:
            print "Error: No vmfile_debian option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._xmlrpcserver = self._config.get(section, 'xmlrpcserver', 0)
        except ConfigParser.NoOptionError:
            print "Error: No xmlrpcserver option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._bridge = self._config.get(section, 'bridge', 0)
        except ConfigParser.NoOptionError:
            print "Error: No bridge option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._serverdir = os.path.expanduser(self._config.get(section, 'serverdir', 0))
        except ConfigParser.NoOptionError:
            self._serverdir=None
        try:
            self._addrnfs = self._config.get(section, 'addrnfs', 0)
        except ConfigParser.NoOptionError:
            print "Error: No addrnfs option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._tempdirserver_gen = os.path.expanduser(self._config.get(section, 'tempdirserver', 0))
        except ConfigParser.NoOptionError:
            print "Error: No tempdirserver option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._tempdir_gen = os.path.expanduser(self._config.get(section, 'tempdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No tempdir option found in section " + section + " file " + self._configfile
            sys.exit(1)            
        try:
            self._http_server_gen = self._config.get(section, 'http_server', 0)
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._bcfg2_url = self._config.get(section, 'bcfg2_url', 0)
        except ConfigParser.NoOptionError:
            print "Error: No bcfg2_url option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._bcfg2_port = int(self._config.get(section, 'bcfg2_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No bcfg2_port option found in section " + section + " file " + self._configfile
            sys.exit(1) 
        try:
            self._oneuser = self._config.get(section, 'oneuser', 0)
        except ConfigParser.NoOptionError:
            print "Error: No oneuser option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._onepass = self._config.get(section, 'onepass', 0)
        except ConfigParser.NoOptionError:
            print "Error: No onepass option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._log_gen = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self._logLevel_gen = eval("logging." + tempLevel)
        
        try:
            self._ca_certs_gen = os.path.expanduser(self._config.get(section, 'ca_cert', 0))
        except ConfigParser.NoOptionError:
            print "Error: No ca_cert option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._ca_certs_gen):
            print "Error: ca_cert file not found in "  + self._ca_certs_gen 
            sys.exit(1)
        try:
            self._certfile_gen = os.path.expanduser(self._config.get(section, 'certfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No certfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._certfile_gen):
            print "Error: certfile file not found in "  + self._certfile_gen 
            sys.exit(1)
        try:
            self._keyfile_gen = os.path.expanduser(self._config.get(section, 'keyfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No keyfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._keyfile_gen):
            print "Error: keyfile file not found in "  + self._keyfile_gen 
            sys.exit(1)
        
    ############################################################
    # load_deployServerXcatConfig
    ############################################################
    def load_deployServerXcatConfig(self):        
        section = "DeployServerXcat"
        try:
            self._xcat_port = int(self._config.get(section, 'xcat_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No xcat_port option found in section " + section + " file " + self._configfile
            sys.exit(1)
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)
        try:
            self._xcatNetbootImgPath = os.path.expanduser(self._config.get(section, 'xcatNetbootImgPath', 0))
        except ConfigParser.NoOptionError:
            print "Error: No xcatNetbootImgPath option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._http_server = self._config.get(section, 'http_server', 0)
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._log_xcat = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self._logLevel_xcat = eval("logging." + tempLevel)
        try:
             aux = string.lower(self._config.get(section, 'test_mode', 0))
             if aux == "true":
                 self._test_xcat=True
             else:
                 self._test_xcat=False
        except ConfigParser.NoOptionError:
            self._test_xcat=False
        try:
            centos_temp = os.path.expanduser(self._config.get(section, 'default_xcat_kernel_centos', 0))
            centos_temp1 = centos_temp.split(",")
            for i in range(len(centos_temp1)):      
                self._default_xcat_kernel_centos[centos_temp1[i].split(":")[0].strip()]=centos_temp1[i].split(":")[1].strip()            
        except ConfigParser.NoOptionError:
            print "Error: No default_xcat_kernel_centos option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:            
            ubuntu_temp = os.path.expanduser(self._config.get(section, 'default_xcat_kernel_ubuntu', 0))
            ubuntu_temp1 = ubuntu_temp.split(",")
            for i in range(len(ubuntu_temp1)):      
                self._default_xcat_kernel_ubuntu[ubuntu_temp1[i].split(":")[0].strip()]=ubuntu_temp1[i].split(":")[1].strip()            
        except ConfigParser.NoOptionError:
            print "Error: No default_xcat_kernel_ubuntu option found in section " + section + " file " + self._configfile
            sys.exit(1)    
        try:
            self._tempdir_xcat = os.path.expanduser(self._config.get(section, 'tempdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No tempdir option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            self._ca_certs_xcat = os.path.expanduser(self._config.get(section, 'ca_cert', 0))
        except ConfigParser.NoOptionError:
            print "Error: No ca_cert option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._ca_certs_xcat):
            print "Error: ca_cert file not found in "  + self._ca_certs_xcat 
            sys.exit(1)
        try:
            self._certfile_xcat = os.path.expanduser(self._config.get(section, 'certfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No certfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._certfile_xcat):
            print "Error: keyfile file not found in "  + self._certfile_xcat 
            sys.exit(1)
        try:
            self._keyfile_xcat = os.path.expanduser(self._config.get(section, 'keyfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No keyfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._keyfile_xcat):
            print "Error: keyfile file not found in "  + self._keyfile_xcat 
            sys.exit(1)
        try:
            self._max_diskusage = int(self._config.get(section, 'max_diskusage', 0))
        except ConfigParser.NoOptionError:
            print "Error: No max_diskusage option found in section " + section + " file " + self._configfile
            sys.exit(1)  


    ############################################################
    # load_deployServerMoab
    ############################################################
    def load_deployServerMoabConfig(self):
        section = "DeployServerMoab"
        try:
            self._moab_port = int(self._config.get(section, 'moab_port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No moab_port option found in section " + section + " file " + self._configfile
            sys.exit(1)  
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)              
        try:
            self._moabInstallPath = os.path.expanduser(self._config.get(section, 'moabInstallPath', 0))
        except ConfigParser.NoOptionError:
            print "Error: No moabInstallPath option found in section " + section + " file " + self._configfile
            sys.exit(1)
        """
        try:
            self._timeToRestartMoab = int(self._config.get(section, 'timeToRestartMoab', 0))
        except ConfigParser.NoOptionError:
            print "Error: No timeToRestartMoab option found in section " + section
            sys.exit(1) 
        """
        try:
            self._log_moab = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self._logLevel_moab = eval("logging." + tempLevel)
        try:
            self._ca_certs_moab = os.path.expanduser(self._config.get(section, 'ca_cert', 0))
        except ConfigParser.NoOptionError:
            print "Error: No ca_cert option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._ca_certs_moab):
            print "Error: ca_cert file not found in "  + self._ca_certs_moab 
            sys.exit(1)
        try:
            self._certfile_moab = os.path.expanduser(self._config.get(section, 'certfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No certfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._certfile_moab):
            print "Error: certfile file not found in "  + self._certfile_moab 
            sys.exit(1)
        try:
            self._keyfile_moab = os.path.expanduser(self._config.get(section, 'keyfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No keyfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._keyfile_moab):
            print "Error: keyfile file not found in "  + self._keyfile_moab 
            sys.exit(1)

    ############################################################
    # load_deployServerIaas
    ############################################################
    def load_deployServerIaasConfig(self):
        section = "DeployServerIaas"
        try:
            self._iaas_port = int(self._config.get(section, 'port', 0))
        except ConfigParser.NoOptionError:
            print "Error: No port option found in section " + section + " file " + self._configfile
            sys.exit(1)  
        except ConfigParser.NoSectionError:
            print "Error: no section "+section+" found in the "+self._configfile+" config file"
            sys.exit(1)
        try:
            self._proc_max_iaas = int(self._config.get(section, 'proc_max', 0))
        except ConfigParser.NoOptionError:
            print "Error: No proc_max option found in section " + section + " file " + self._configfile
            sys.exit(1)     
        try:
            self._refresh_status_iaas = int(self._config.get(section, 'refresh', 0))
        except ConfigParser.NoOptionError:
            print "Error: No refresh option found in section " + section + " file " + self._configfile
            sys.exit(1)     
        try:
            self._tempdir_iaas = os.path.expanduser(self._config.get(section, 'tempdir', 0))
        except ConfigParser.NoOptionError:
            print "Error: No tempdir option found in section " + section + " file " + self._configfile
            sys.exit(1)            
        try:
            self._http_server_iaas = self._config.get(section, 'http_server', 0)
        except ConfigParser.NoOptionError:
            print "Error: No http_server option found in section " + section + " file " + self._configfile
            sys.exit(1)        
        try:
            self._default_euca_kernel = self._config.get(section, 'default_euca_kernel', 0)
        except ConfigParser.NoOptionError:
            print "Error: No default_euca_kernel option found in section " + section + " file " + self._configfile
            sys.exit(1)        
        try:
            self._default_nimbus_kernel = self._config.get(section, 'default_nimbus_kernel', 0)
        except ConfigParser.NoOptionError:
            print "Error: No default_nimbus_kernel option found in section " + section + " file " + self._configfile
            sys.exit(1)        
        try:
            self._default_openstack_kernel = self._config.get(section, 'default_openstack_kernel', 0)
        except ConfigParser.NoOptionError:
            print "Error: No default_openstack_kernel option found in section " + section + " file " + self._configfile
            sys.exit(1)        
        try:
            self._default_opennebula_kernel = self._config.get(section, 'default_opennebula_kernel', 0)
        except ConfigParser.NoOptionError:
            print "Error: No default_opennebula_kernel option found in section " + section + " file " + self._configfile
            sys.exit(1)                
        try:
            self._log_iaas = os.path.expanduser(self._config.get(section, 'log', 0))
        except ConfigParser.NoOptionError:
            print "Error: No log option found in section " + section + " file " + self._configfile
            sys.exit(1)
        try:
            tempLevel = string.upper(self._config.get(section, 'log_level', 0))
        except ConfigParser.NoOptionError:
            tempLevel = self._logLevel_default
        if not (tempLevel in self._logType):
            print "Log level " + tempLevel + " not supported. Using the default one " + self._logLevel_default
            tempLevel = self._logLevel_default
        self._logLevel_iaas = eval("logging." + tempLevel)
        try:
            self._ca_certs_iaas = os.path.expanduser(self._config.get(section, 'ca_cert', 0))
        except ConfigParser.NoOptionError:
            print "Error: No ca_cert option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._ca_certs_iaas):
            print "Error: ca_cert file not found in "  + self._ca_certs_iaas 
            sys.exit(1)
        try:
            self._certfile_iaas = os.path.expanduser(self._config.get(section, 'certfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No certfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._certfile_iaas):
            print "Error: certfile file not found in "  + self._certfile_iaas 
            sys.exit(1)
        try:
            self._keyfile_iaas = os.path.expanduser(self._config.get(section, 'keyfile', 0))
        except ConfigParser.NoOptionError:
            print "Error: No keyfile option found in section " + section + " file " + self._configfile
            sys.exit(1)
        if not os.path.isfile(self._keyfile_iaas):
            print "Error: keyfile file not found in "  + self._keyfile_iaas 
            sys.exit(1)



