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
    imgId = str(randrange(999999999999999999999999))
    return imgId
