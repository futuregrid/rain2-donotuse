"""
utility class for static methods
"""

from random import randrange


################
#BACKEND CONFIG
################
"""
#MongoDB config
__backend__="mongodb"
__address__="localhost:23000"
__fgirimgstoremongo__="/tmp/"
"""
#Mysql config
__backend__= "mysql"
__address__= "localhost"
__fgirimgstoremysql__="/srv/irstore/"

############################################
#DIR WHERE THE SERVER SOFTWARE IS INSTALLED
############################################
__fgserverdir__="/home/javi/imagerepo/ImageRepo/"
#__fgserverdir__="/N/u/fuwang/fgir/"

##############################
#Mysql CONFIG
##############################
#File with the MySQL password
__mysqlcfg__=__fgserverdir__+".mysql.cnf"
__iradmin__="IRUser"

def getFgserverdir():
    return __fgserverdir__

def getMysqlcfg():
    return __mysqlcfg__

def getMysqluser():
    return __iradmin__

def getFgirimgstore():
    if (__backend__=="mongodb"):
        return __fgirimgstoremongo__
    elif (__backend__=="mysql"):
        return __fgirimgstoremysql__
      

def getBackend():
    return __backend__
def getAddress():
    return __address__

def getImgId():
    imgId = str(randrange(9999999999999))
    return imgId
    
def auth(userId, cred):
    return True
