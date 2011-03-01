#!/usr/bin/env python
from IRTypes import ImgMeta
from IRTypes import ImgEntry
from IRTypes import IRUser
from IRTypes import IRCredential

aUser = IRUser("fuwang")
aCred = IRCredential("ssh","SSH PUBLIC KEY HERE")
aUser.setCred(aCred)
aMeta = ImgMeta("a fake id", "RHEL5", "i386", aUser, "Test image", "a tag");
img = ImgEntry("img id", aMeta, "sierra.futuregrid.org:/N/u/fuwang/DUMMY");
print img._createdDate, img._lastAccess, img._accessCount, img._imgURI
print aMeta
