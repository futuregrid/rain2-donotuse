"""
utility class for static methods
"""

from random import randrange

    

def getImgId():
    imgId = str(randrange(9999999999999))
    return imgId
    
def auth(userId, cred):
    return True
