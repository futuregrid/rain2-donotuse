"""
utility class for static methods
"""


from random import randrange
import os
import ConfigParser
import string
import logging
import sys


def getImgId():
    imgId = str(randrange(9999999999999))
    return imgId
