#!/usr/bin/env python
"""
This class is to use Mysql and Cumulus (OpenStack Storage Object) as Image Repository back-end 

MySQL Databases Info:

    A database with all the info is called imagesS. It contains two tables
        data      (Image details and URI)
        meta        (Image metadata)


"""
__author__ = 'Javier Diaz'
__version__ = '0.1'


from IRDataAccessMysql import ImgStoreMysql
from IRDataAccessMysql import ImgMetaStoreMysql
from IRDataAccessMysql import IRUserStoreMysql
from IRTypes import ImgEntry
from IRTypes import ImgMeta
from IRTypes import IRUser
from datetime import datetime
import os
import re
import MySQLdb
import string
import IRUtil
import sys
import boto
from boto.s3.key import Key
from boto.s3.connection import OrdinaryCallingFormat
from boto.s3.connection import S3Connection

class ImgStoreCumulusMysql(ImgStoreMysql):

    ############################################################
    # __init__
    ############################################################
    def __init__(self, address, addressS, fgirdir, log):
        """
        Initialize object
        
        Keyword parameters:             
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        _items = list of imgEntry
        _dbName = name of the database
        
        """                
        super(ImgStoreMysql, self).__init__()
                
        self._dbName="imagesC"
        self._tabledata="data"
        self._tablemeta="meta"
        self._mysqlcfg=IRUtil.getMysqlcfg()
        self._iradminsuer=IRUtil.getMysqluser()
        
        self._log=log
        
        self._dbConnection=None
        if (address != ""):
            self._mysqlAddress=address
        else:
            self._mysqlAddress=self._getAddress()
        
               
        self._cumulusAddress=addressS
        self._cumulusConnection=None
        self._containerName="images"
            

    
    ############################################################
    # getItemUri
    ############################################################
    def getItemUri(self, imgId, userId):
        return "For now we do not provide this feature with the Cumulus system as backend."
        

    ############################################################
    # getItem
    ############################################################
    def getItem(self, imgId, userId):
        """
        Get Image file identified by the imgId
        
        keywords:
        imgId: identifies the image
        
        return the image uri
        """
                        
        imgLinks=[]  
        result = self.queryStore([imgId], imgLinks, userId)
        
        if (result):
            return imgLinks[0]
        else:
            return None
        

           
    ############################################################
    # queryStore
    ############################################################
    def queryStore(self, imgIds, imgLinks, userId):
        """        
        Query the DB and provide the uri.    
        
        keywords:
        imgIds: this is the list of images that I need
        imgLinks: This is an output parameter. Return the list URIs
        """
        
        itemsFound=0
                
        if (self.mysqlConnection() and self.cumulusConnection()):
            try:
                cursor= self._dbConnection.cursor()                
                contain= self._cumulusConnection.get_bucket(self._containerName)                
                k=Key(contain) 
                 
                for imgId in imgIds:
                    access=False
                    if(self.existAndOwner(imgId, userId)):
                        access=True
                    elif(self.isPublic(imgId)):
                        access=True
                    
                    if (access):
                        sql = "SELECT accessCount FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
                        #print sql
                        cursor.execute(sql)
                        results=cursor.fetchone()
                        
                        if(results!=None):
                            k.key=imgId                        
                            #Boto does not stream, so we have to create the file here instead of in getItem
                            imagepath='/tmp/'+imgId+".img"                                                                            
                            k.get_contents_to_filename(imagepath)                                                                           
                             
                            imgLinks.append(imagepath)
                            
                            accessCount=int(results[0])+1
                            
                            update="UPDATE %s SET lastAccess='%s', accessCount='%d' WHERE imgId='%s'" \
                                           % (self._tabledata,datetime.utcnow(),accessCount, imgId)
                            #print update
                            cursor.execute(update)
                            self._dbConnection.commit()
                                                            
                            itemsFound+=1                    
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))
                self._log.error("No such file or directory. Image details: "+item.__str__())                
            except TypeError as detail:
                self._log.error("TypeError in ImgStorecumulusMysql - queryToStore: "+format(detail))
            except boto.exception.S3ResponseError as detail:
                self._log.error("Code and reason "+detail.code+" "+detail.reason)
                self._log.error("Error in ImgStoreCumulusMysql - queryToStore. full error "+str(sys.exc_info()))
            except:
                self._log.error("Error in ImgStorecumulusMysql - queryToStore. "+str(sys.exc_info()))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. Query failed")
       
        if (itemsFound >= 1):
            return True
        else:
            return False
           
    ############################################################
    # persistToStore
    ############################################################
    def persistToStore(self, items):
        """Copy imgEntry to the DB. 
        
        Keyword arguments:
        items= list of ImgEntrys
                
        return: True if all items are stored successfully, False in any other case
        """               
         
        imgStored=0
                        
        if (self.mysqlConnection() and self.cumulusConnection()):
            
            try:
                contain= self._cumulusConnection.get_bucket(self._containerName)
            except boto.exception.S3ResponseError as detail:
                if(detail.reason.strip()=="Not Found"):                
                    self._log.warning("Creating bucket")
                    self._cumulusConnection.create_bucket(self._containerName)
                    contain= self._cumulusConnection.get_bucket(self._containerName)
                else:
                    self._log.error("Code and reason "+detail.code+" "+detail.reason)
                    self._log.error("Error in ImgStorecumulusMysql - queryToStore. full error "+str(sys.exc_info()))
            except:
                self._log.error("Error in ImgStorecumulusMysql - persistToStore. "+str(sys.exc_info()))   
            
            try:
                cursor= self._dbConnection.cursor()      
                
                k=Key(contain)
                      
                for item in items:
                    
                    k.key= item._imgId                    
                    k.set_contents_from_filename(item._imgURI)
                    
                    sql = "INSERT INTO %s (imgId, imgMetaData, imgUri, createdDate, lastAccess, accessCount, size) \
       VALUES ('%s', '%s', '%s', '%s', '%s', '%d', '%d' )" % \
       (self._tabledata, item._imgId, item._imgId, "", datetime.utcnow(), datetime.utcnow(), 0, item._size)
                    
                    cursor.execute(sql)
                    self._dbConnection.commit()
                                                   
                    imgStored+=1
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))
                self._log.error("No such file or directory. Image details: "+item.__str__())                 
            except TypeError as detail:
                self._log.error("TypeError in ImgStorecumulusMysql - persistToStore "+format(detail))
            except:
                self._log.error("Error in ImgStorecumulusMysql - persistToStore. "+str(sys.exc_info()))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. The file has not been stored")
        
        for item in items:
            if (re.search('^/tmp/', item._imgURI)):
                cmd="rm -f "+ item._imgURI         
                os.system(cmd)
        
        if (imgStored == len(items)):
            return True
        else:
            return False
        
    
    ############################################################
    # removeItem 
    ############################################################
    def removeItem (self, userId, imgId, size):
        #what are we going to do with concurrency?
        """
        Remove the Image file and Metainfo if imgId exists and your are the owner.
        
        IMPORTANT: if you want to update both imgEntry and imgMeta, 
                   you have to update first imgMeta and then imgEntry,
                   because imgEntry's update method change the _id of the imgMeta document
                
        keywords:
        imgId : identifies the image (I think that we can remove this)
        imgEntry : new info to update. It HAS TO include the owner in _imgMeta
        
        Return boolean
        """   
        
        removed=False     
        
        if (self.mysqlConnection() and self.cumulusConnection()):     ##Error 2006: MySQL server has gone away???
            
            ##Solve with this. LOOK INTO MYSQL CONNECTIONS
            con= MySQLdb.connect(host=self._mysqlAddress,                                                                                  
                                           db=self._dbName,
                                           read_default_file=self._mysqlcfg,
                                           user=self._iradminsuer)
            if(self.existAndOwner(imgId, userId)):            
                try:
                    cursor= con.cursor()
                    contain= self._cumulusConnection.get_bucket(self._containerName)               
                    contain.delete_key(imgId)
                    
                    sql = "SELECT size FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
                    #print sql
                    cursor.execute(sql)
                    results=cursor.fetchone()
                    size[0]=int(results[0])                                      
                    
                                        
                    sql="DELETE FROM %s WHERE imgId='%s'" % (self._tabledata,imgId)                    
                    sql1="DELETE FROM %s WHERE imgId='%s'" % (self._tablemeta,imgId)
                    
                    cursor.execute(sql)                    
                    cursor.execute(sql1)
                    con.commit()
                    
                    removed=True
                    
                except MySQLdb.Error, e:
                    self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
                    con.rollback()                           
                except IOError as (errno, strerror):
                    self._log.error("I/O error({0}): {1}".format(errno, strerror))
                    self._log.error("No such file or directory. Image details: "+item.__str__())                 
                except TypeError as detail:
                    self._log.error("TypeError in ImgStoreMongo - removeItem "+format(detail))
                except:
                    self._log.error("Error in ImgStorecumulusMysql - removeItem. "+str(sys.exc_info()))
                finally:
                    con.close()
            else:
                con.close()
                self._log.error("The Image does not exist or the user is not the owner")
        else:
            self._log.error("Could not get access to the database. The file has not been removed")
            
        return removed
            
    ############################################################
    # existAndOwner
    ############################################################
    def existAndOwner(self, imgId, ownerId):
        """
        To verify if the file exists and I am the owner
        
        keywords:
        imgId: The id of the image
        ownerId: The owner Id
        
        Return: boolean
        """
        
        exists=False
        owner=False
                
        
        try:
            cursor= self._dbConnection.cursor()         
            contain= self._cumulusConnection.get_bucket(self._containerName)
                        
            if contain.get_key(imgId) != None:
                exists=True         

                     
            sql = "SELECT owner FROM %s WHERE imgId='%s' and owner='%s'"% (self._tablemeta, imgId, ownerId)
            
            cursor.execute(sql)
            results=cursor.fetchone()
            
            if(results!=None):                  
                owner=True                      
                    
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
        except IOError as (errno, strerror):
            self._log.error("I/O error({0}): {1}".format(errno, strerror))
            self._log.error("No such file or directory. Image details: "+item.__str__())                
        except TypeError as detail:
            self._log.error("TypeError in ImgStoreMysql - existAndOwner: "+format(detail)) 
        except:
            self._log.error("Error in ImgStorecumulusMysql - existAndOwner. "+str(sys.exc_info()))
       
        if (exists and owner):
            return True
        else:
            return False
    
    ############################################################
    # cumulusConnection
    ############################################################
    def cumulusConnection(self):
        """
        Connect with Nimbus Cumulus
        
        """
        connected = False
        
        #username an password will be moved to the config file
        id='PgkhmT23FUv7aRZND7BOW'
        pw='Bf9ppgw9mzxe2EoKjbVl0wjaNJoHlIPxJ6QAgA0pOj'
        cf=OrdinaryCallingFormat()
        try:
            self._cumulusConnection= S3Connection(id, pw, host=self._cumulusAddress, port=8888, is_secure=False, calling_format=cf)
            connected=True
        except:
            self._log.error("Error in cumulus connection. "+str(sys.exc_info()))
            
        return connected

class ImgMetaStoreCumulusMysql(ImgMetaStoreMysql):

    ############################################################
    # __init__
    ############################################################
    def __init__(self, address, fgirdir, log):
        """
        Initialize object
        
        Keyword parameters:             
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        _items = list of imgEntry
        _dbName = name of the database
        
        """                
        super(ImgMetaStoreMysql, self).__init__()
                
        self._dbName="imagesC"
        self._tabledata="data"
        self._tablemeta="meta"
        self._mysqlcfg=IRUtil.getMysqlcfg()
        self._iradminsuer=IRUtil.getMysqluser()
        self._log=log
        self._dbConnection=None
        if (address != ""):
            self._mysqlAddress=address
        else:
            self._mysqlAddress=self._getAddress()
                       
class IRUserStoreCumulusMysql(IRUserStoreMysql):

    ############################################################
    # __init__
    ############################################################
    def __init__(self, address,fgirdir, log):
        """
        Initialize object
        
        Keyword parameters:             
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        _items = list of imgEntry
        _dbName = name of the database
        
        """                
        super(IRUserStoreMysql, self).__init__()
                
        self._dbName="imagesC"
        self._tabledata="users"        
        self._mysqlcfg=IRUtil.getMysqlcfg()
        self._iradminsuer=IRUtil.getMysqluser()
        self._log=log
        
        self._dbConnection = None
        if (address != ""):
            self._mysqlAddress=address
        else:
            self._mysqlAddress=self._getAddress()

  
