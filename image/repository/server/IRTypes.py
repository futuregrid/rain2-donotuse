#!/usr/bin/env python
"""
Definitions of types

This module defines the common types for the FGIR. These include defining user, credential, img metadata entry, img entry, etc..
"""

__author__ = 'Fugang Wang'
__version__ = '0.9'

from datetime import datetime

class IRUser(object):

    Status = ["pending", "active", "inactive"]
    Role = ["user", "admin"]

    #fsCap in bytes. 4G by default
    def __init__(self, userId, cred = None, fsCap = 4294967296, fsUsed = 0,
                 lastLogin = None, status = Status[0], role = Role[0], ownedImgs = 0):
        super(IRUser, self).__init__()
        self._userId = userId
        self._cred = cred
        self._fsCap = fsCap
        self._fsUsed = fsUsed
        self._lastLogin = lastLogin
        self._status = status
        self._role = role
        self._ownedImgs = ownedImgs

    def setCred(self, cred):
        self._cred = cred

    def __repr__(self):
        return "\"userId=%s, cred=%s, fsCap=%s, fsUsed=%s, lastLogin(UTC)=%s, status=%s, role=%s, ownedImgs=%s \"" % \
                (self._userId, self._cred, self._fsCap, self._fsUsed, \
                 self._lastLogin, self._status, self._role, self._ownedImgs)

    def __str__(self):
        return "\"%s, %s, %d, %d, %s, %s, %s, %s\"" % \
                (self._userId, self._cred, self._fsCap, self._fsUsed, \
                 self._lastLogin, self._status, self._role, self._ownedImgs)

class ImgMeta(object):

    """
    class VmType:
        NONE=0
        XEN=10
        KVM=11
        
    class ImgType:
        MACHINE=0
        KERNEL=1
        EUCALYPTUS=10
        NIMBUS=11
        OPENNEBULA=12
        OPENSTACK=13
        
    class ImgStatus:
        AVAILABLE=0
        LOCKED=1
    """
    metaArgsIdx = {
        "imgId": 0,
        "os": 1,
        "arch": 2,
        "owner": 3,
        "description": 4,
        "tag": 5,
        "vmtype": 6,
        "imgtype": 7,
        "permission": 8,
        "imgstatus": 9
    }

    VmType = ["none", "xen", "kvm", "virtualbox", "vmware"]
    ImgType = ["machine", "kernel", "eucalyptus", "nimbus", "opennebula", "openstack"]
    ImgStatus = ["available", "locked"]
    Permission = ["public", "private"]

    argsDefault = ['', '', '', '', '', '',
                   VmType[0], ImgType[0],
                   Permission[1], ImgStatus[0]]

    def __init__(self,
                 imgId,
                 os,
                 arch,
                 owner,
                 description,
                 tag,
                 vmType = "none",
                 imgType = "machine",
                 permission = "private",
                 imgStatus = "available"
                 ):
        super(ImgMeta, self).__init__()
        self._imgId = imgId
        self._os = os
        self._arch = arch
        self._vmType = vmType
        self._imgType = imgType
        self._permission = permission
        self._owner = owner
        self._imgStatus = imgStatus
        self._description = description
        self._tag = tag

    def __repr__(self):
        return "\"imgId=%s, os=%s, arch=%s, owner=%s, description=%s, tag=%s, vmType=%s, imgType=%s, permission=%s, status=%s\"" % \
                (self._imgId, self._os, self._arch, self._owner, \
                 self._description, self._tag, self._vmType, self._imgType, \
                 self._permission, self._imgStatus)

    def __str__(self):
        return "\"%s, %s, %s, %s, %s, %s, %s, %s, %s, %s\"" % \
                (self._imgId, self._os, self._arch, self._owner, \
                 self._description, self._tag, self._vmType, self._imgType, \
                 self._permission, self._imgStatus)

class ImgEntry(object):
    def __init__(self,
                 imgId,
                 imgMeta,
                 imgURI,
                 size,
                 extension,
                 createdDate = datetime.utcnow(),
                 lastAccess = datetime.utcnow(),
                 accessCount = 0
                 ):
        super(ImgEntry, self).__init__()
        self._imgId = imgId
        self._imgMeta = imgMeta
        self._imgURI = imgURI
        self._createdDate = createdDate
        self._lastAccess = lastAccess
        self._accessCount = accessCount
        self._size = size
        self._extension=extension

    ############################################################
    # __repr__
    ############################################################
    def __repr__(self):
        return "\"imgId=%s, imgURI=%s, createdDate(UTC)=%s, lastAccess(UTC)=%s, accessCount=%s, size=%s, extension=%s\"" % \
                (self._imgId, self._imgURI, self._createdDate, self._lastAccess, \
                 self._accessCount, self._size, self._extension)

    ############################################################
    # __str__
    ############################################################
    def __str__(self):
        return "\"%s, %s, %s, %s, %s, %s, %s\"" % \
                (self._imgId, self._imgURI, self._createdDate, self._lastAccess, \
                 self._accessCount, self._size, self._extension)

    def get(self, userId, imgId):
        pass

    def put(self, userId, attrStr, imgFile):
        pass

    def remove(self, userId, imgId):
        pass


