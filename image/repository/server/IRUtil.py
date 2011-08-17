"""
utility class for static methods
"""

from random import randrange
import logging
import sys, os
import ConfigParser
import hashlib
import base64
import binascii
import ldap
import MySQLdb
from IRTypes import IRCredential
from IRServerConf import IRServerConf

sys.path.append(os.getcwd())

try:
    from futuregrid.utils import fgLog
except:
    sys.path.append(os.path.dirname( __file__ ) + "/../../../") #Directory where fg.py is
    try:
        from utils import fgLog
    except:
        sys.path.append(os.getcwd() + "/../../../")
        from utils import fgLog
    
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
    ret = False
    configFile = IRServerConf().getServerConfig()
    config = ConfigParser.ConfigParser()
    config.read(configFile)
    logfile = config.get("RepoServer", "log")
    
    log = fgLog.fgLog(logfile, logging.INFO, "IRUtil Auth", False)

    authProvider = cred._provider
    authCred = cred._cred
    # print "'" + userId + "':'" + authProvider + "':'" + authCred + "'"
    if(authProvider == "ldappass"):
        if(authCred != ""):
	    host = config.get('LDAP', 'LDAPHOST')
            adminuser = config.get('LDAP', 'LDAPUSER')
            adminpass = config.get('LDAP', 'LDAPPASS')
            #print adminuser, adminpass
            userdn = "uid=" + userId + ",ou=People,dc=futuregrid,dc=org"
            #print userdn
            ldapconn = ldap.initialize("ldap://" + host)
            log.info("Initializing the LDAP connection to server: " + host)
            try:
                ldapconn.start_tls_s()
                log.info("tls started...")
                ldapconn.bind_s(adminuser, adminpass)
                m = hashlib.md5()
                m.update(authCred)
                passwd_input = m.hexdigest()
                #print passwd_input
                passwd_processed = "{MD5}" + base64.b64encode(binascii.unhexlify(passwd_input))
                #print passwd_processed
                #print base64.b64encode(passwd_processed)
                if(ldapconn.compare_s(userdn, 'userPassword', passwd_processed)):
                    ret = True
                    log.info("User '" + userId + "' successfully authenticated")
                else:
		    ret = False
		    log.info("User '" + userId + "' failed to authenticate due to incorrect credential")
                #print ldapconn.compare_s(userdn, 'mail', "kevinwangfg@gmail.com")
                #basedn = "ou=People,dc=futuregrid,dc=org"
                #filter = "(uid=" + userId + ")"
                #attrs = ['userPassword']
                #print ldapconn.search_s( basedn, ldap.SCOPE_SUBTREE, filter, attrs )
            except ldap.INVALID_CREDENTIALS:
                log.info("Your username or password is incorrect. Cannot bind as admin.")
                ret = False
            except ldap.LDAPError:
		log.info("User '" + userId + "' failed to authenticate due to LDAP error. The user may not exist.")
                ret = False
            finally:
                log.info("Unbinding from the LDAP.")
                ldapconn.unbind()
    elif(authProvider == "drupalplain"):
        if(authCred != ""):
            m = hashlib.md5()
            m.update(authCred)
            passwd_input = m.hexdigest()

            dbhost = config.get('PortalDB', 'host')
            dbuser = config.get('PortalDB', 'user')
            dbpasswd = config.get('PortalDB', 'passwd')
            dbname = config.get('PortalDB', 'db')
            
            conn = MySQLdb.connect(dbhost,dbuser,dbpasswd,dbname)
            cursor = conn.cursor()
            queryuser = "select pass from users where name='" + userId + "'"
            cursor.execute(queryuser)
            passwd_db = ""
            passwd = cursor.fetchall()
            for thepass in passwd:
                passwd_db = list(thepass)[0]
            if(passwd_db != "" and passwd_db==passwd_input):
                ret = True
                log.info("User " + userId + " successfully authenticated")
            else:
		log.info("User " + userId + " failed to authenticate")
    return ret

if __name__ == "__main__":
    cred = IRCredential("ldappass", "REMOVED")
    if(auth("testuser", cred)):
        print "logged in"
    else:
        print "access denied"
