"""
utility class for static methods
"""

#from IRDataAccess import IRUserStore
from random import randrange

class IRUtil(object):
#    userStore = IRUserStore()
    
    @staticmethod
    def getImgId():
        fakeid = "id" + str(randrange(9999999))
        return fakeid
    """
    #MOVED to IRUserStore
    @staticmethod    
    def uploadValidator(userId, imgSize):
        user = IRUtil.userStore.getUser(userId)
        ret = True
        if imgSize + user._fsUsed > user._fsCap:
            ret = False
        return ret
    """
    @staticmethod    
    def auth(userId, cred):
        return True
