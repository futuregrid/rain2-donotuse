"""
utility class for static methods
"""

from random import randrange
import logging
import sys, os
################
#BACKEND CONFIG
################
"""
#MongoDB config
__backend__ = "mongodb"
__address__ = "localhost:23000"
__fgirimgstore__ = "/tmp/"
"""
"""
#Mysql config
__backend__= "mysql"
__address__= "localhost"
__fgirimgstore__="/srv/irstore/"
"""
"""
#Swift-Mysql
__backend__= "swiftmysql"
__address__= "localhost"  #MysqlAddress
__addressS__= "192.168.1.2" #Swift proxy address
__fgirimgstore__="/tmp/"
"""
"""
#Swift-Mongo
__backend__= "swiftmongo"
__address__="localhost:23000"  #Mongos address
__addressS__= "192.168.1.2"#Swift proxy address
__fgirimgstore__="/tmp/"
"""
"""
#Cumulus-Mysql
__backend__= "cumulusmysql"
__address__="localhost"  #Mongos address
__addressS__= "192.168.1.2"#cumulus address
__fgirimgstore__="/tmp/"
"""

#Cumulus-Mongo
__backend__= "cumulusmongo"
__address__="localhost:23000"  #Mongos address
__addressS__= "192.168.1.2"#cumulus address
__fgirimgstore__="/tmp/"



############################################
#DIR WHERE THE SERVER SOFTWARE IS INSTALLED (Only used to store the log and in Mysql to keep the pass)
############################################
__fgserverdir__ = "/opt/futuregrid/futuregrid/"
#__fgserverdir__="/N/u/fuwang/fgir/"

##############################
#Mysql CONFIG
##############################
#File with the MySQL password
__mysqlcfg__ = __fgserverdir__ + "/var/.mysql.cnf"
__iradmin__ = "IRUser"

########################
#Log Options
########################
##At the end, it should be in /var/log or a var directory in the Futuregrid software
__logfile__ = __fgserverdir__ + "/var/reposerver.log"  
__logLevel__ = logging.DEBUG


############################################################
# getFgserverdir
############################################################
def getFgserverdir():
    return __fgserverdir__

############################################################
# getMysqlcfg
############################################################
def getMysqlcfg():
    return __mysqlcfg__

############################################################
# getMysqluser
############################################################
def getMysqluser():
    return __iradmin__


############################################################
# getFgirimgstore
############################################################
def getFgirimgstore():
    return __fgirimgstore__

############################################################
# getLogFile
############################################################
def getLogFile():
    return __logfile__

############################################################
# getLogLevel
############################################################
def getLogLevel():
    return __logLevel__


############################################################
# getBackend
############################################################
def getBackend():
    return __backend__

############################################################
# getAddress
############################################################
def getAddress():
    return __address__


############################################################
# getAddressS
############################################################
def getAddressS():
    return __addressS__


############################################################
# getImgId
############################################################
def getImgId():
    imgId = str(randrange(999999999999999999999999))
    return imgId
    

############################################################
# auth
############################################################
def auth(userId, cred):
    return True
