#!/usr/bin/env python
"""
Class to store the EC2 and S3 Information 
"""

__author__ = 'Javier Diaz'
__version__ = '0.9'


class IMEc2Environ(object):
    
    ############################################################
    # __init__
    ############################################################
    def __init__(self):
        super(IMEc2Environ, self).__init__()

        self.ec2_url, self.s3_url, self.path, self.region,  self.bucket, self.base_key, self.s3id, self.s3key, self.cannonicalid = ""
        self.ec2_port, self.s3_port = 0
        
    def setEc2_url(self, ec2_url):
        self.ec2_url=ec2_url
    def setEc2_port(self, ec2_port):
        self.ec2_port=ec2_port
    def setS3_url(self, s3_url):
        self.s3_url=s3_url
    def setS3_port(self, s3_port):
        self.s3_port=s3_port        
    def setPath(self, path):
        self.path=path
    def setRegion(self, region):
        self.region=region
    def setBucket(self, bucket):
        self.bucket=bucket
    def setBase_key(self, base_key):
        self.base_key=base_key
    def setS3id(self, s3id):
        self.s3id=s3id
    def setS3key(self, s3key):
        self.s3key=s3key
    def setCannonicalId(self, cannonicalid):
        self.cannonicalid=cannonicalid
    
    def getEc2_url(self, ec2_url):
        return self.ec2_url
    def getEc2_port(self, ec2_port):
        return self.ec2_port
    def getS3_url(self, s3_url):
        return self.s3_url
    def getS3_port(self, s3_port):
        return self.s3_port        
    def getPath(self, path):
        return self.path
    def getRegion(self, region):
        return self.region
    def getBucket(self, bucket):
        return self.bucket
    def getBase_key(self, base_key):
        return self.base_key
    def getS3id(self, s3id):
        return self.s3id
    def getS3key(self, s3key):
        return self.s3key
    def getCannonicalId(self, cannonicalid):
        return self.cannonicalid