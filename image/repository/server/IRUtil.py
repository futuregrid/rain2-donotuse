"""
utility class for static methods
"""

import sys,os
from random import randrange
import hashlib
try:
    from ....utils import FGTypes,FGAuth # 3 dir levels up
except:
    sys.path = [os.path.dirname(os.path.abspath(__file__)) + "/../../../utils"] + sys.path
    import FGTypes,FGAuth

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
    return FGAuth.auth(userId, cred)

if __name__ == "__main__":
    m = hashlib.md5()
    m.update("REMOVED")
    passwd_input = m.hexdigest()
    cred = FGTypes.FGCredential("ldappassmd5", passwd_input)
    if(auth("USER", cred)):
        print "logged in"
    else:
        print "access denied"
