#!/usr/bin/env python
"""
This class is to use Mysql and Swift (OpenStack Storage Object) as Image Repository back-end 

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
import cloudfiles
import sys

class ImgStoreSwiftMysql(ImgStoreMysql):

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
                
        self._dbName="imagesS"
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
        
               
        self._swiftAddress=addressS
        self._swiftConnection=None
        self._containerName="images"
            

    
    ############################################################
    # getItemUri
    ############################################################
    def getItemUri(self, imgId, userId):
        return "For now we do not provide this feature with the Swift system as backend."
        

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
            filename="/tmp/"+imgId+".img"
            if not os.path.isfile(filename):
                f = open(filename, 'w')
            else:
                for i in range(1000):
                    filename="/tmp/"+imgId+".img"+i.__str__()
                    if not os.path.isfile(filename):
                        f = open(filename, 'w')
                        break
            
            #I think that this need the connection with Swift
            for chunk in imgLinks[0].stream():  
                f.write(chunk)   
            f.close()
                              
            return filename
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
                
        if (self.mysqlConnection() and self.swiftConnection()):
            try:
                cursor= self._dbConnection.cursor()                
                contain= self._swiftConnection.get_container(self._containerName)
                 
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
                            imgLinks.append(contain.get_object(imgId))
                            
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
                self._log.error("TypeError in ImgStoreSwiftMysql - queryToStore: "+format(detail))
            except cloudfiles.errors.NoSuchObject:
                self._log.error("File not found")
            except:
                self._log.error("Error in ImgStoreSwiftMysql - queryToStore. "+str(sys.exc_info()))
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
                        
        if (self.mysqlConnection() and self.swiftConnection()):
            
            try:
                contain= self._swiftConnection.get_container(self._containerName)
            except cloudfiles.errors.NoSuchContainer:
                self._swiftConnection.create_container(self._containerName)
                contain= self._swiftConnection.get_container(self._containerName)
                self._log.warning("Creating the container")
            except:
                self._log.error("Error in ImgStoreSwiftMysql - persistToStore. "+str(sys.exc_info()))  
            
            try:
                cursor= self._dbConnection.cursor()            
                for item in items:
                    
                    img=contain.create_object(item._imgId)
                    img.load_from_filename(item._imgURI)
                    
                    sql = "INSERT INTO %s (imgId, imgMetaData, imgUri, createdDate, lastAccess, accessCount, size) \
       VALUES ('%s', '%s', '%s', '%s', '%s', '%d', '%d' )" % \
       (self._tabledata, item._imgId, item._imgId, "", datetime.utcnow(), datetime.utcnow(), 0, item._size)
                    
                    cursor.execute(sql)
                    self._dbConnection.commit()
                                                   
                    imgStored+=1
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
                self._dbConnection.rollback()                           
            except IOError:                
                self._log.error("Error in ImgStoreSwiftMysql - persistToStore. "+str(sys.exc_info()))
                self._log.error("No such file or directory. Image details: "+item.__str__())                 
            except TypeError:
                self._log.error("TypeError in ImgStoreSwiftMysql - persistToStore "+str(sys.exc_info()))                 
            except TypeError as detail:
                self._log.error("TypeError in ImgStoreSwiftMysql - persistToStore "+format(detail))
            except:
                self._log.error("Error in ImgStoreSwiftMysql - persistToStore. "+str(sys.exc_info()))
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
        
        if (self.mysqlConnection() and self.swiftConnection()):     ##Error 2006: MySQL server has gone away???
            
            ##Solve with this. LOOK INTO MYSQL CONNECTIONS
            con= MySQLdb.connect(host=self._mysqlAddress,                                                                                  
                                           db=self._dbName,
                                           read_default_file=self._mysqlcfg,
                                           user=self._iradminsuer)
            if(self.existAndOwner(imgId, userId)):            
                try:
                    cursor= con.cursor()
                    contain= self._swiftConnection.get_container(self._containerName)
                    
                    sql = "SELECT size FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
                    #print sql
                    cursor.execute(sql)
                    results=cursor.fetchone()
                    size[0]=int(results[0])
                                       
                    contain.delete_object(imgId)
                                        
                    sql="DELETE FROM %s WHERE imgId='%s'" % (self._tabledata,imgId)                    
                    sql1="DELETE FROM %s WHERE imgId='%s'" % (self._tablemeta,imgId)
                    
                    cursor.execute(sql)                    
                    cursor.execute(sql1)
                    con.commit()
                    
                    removed=True
                    
                except MySQLdb.Error, e:
                    self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
                    con.rollback()                           
                except IOError:                
                    self._log.error("Error in ImgStoreSwiftMysql - removeItem. "+str(sys.exc_info()))
                    self._log.error("No such file or directory. Image details: "+item.__str__())                 
                except TypeError:
                    self._log.error("TypeError in ImgStoreSwiftMysql - removeItem "+str(sys.exc_info()))  
                except:
                    self._log.error("Error in ImgStoreSwiftMysql - removeItem. "+str(sys.exc_info()))
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
            contain= self._swiftConnection.get_container(self._containerName)
            
            if imgId in contain.list_objects():
                exists=True
                     
            sql = "SELECT owner FROM %s WHERE imgId='%s' and owner='%s'"% (self._tablemeta, imgId, ownerId)
            
            cursor.execute(sql)
            results=cursor.fetchone()
            
            if(results!=None):                  
                owner=True                      
                    
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
        except IOError:                
            self._log.error("Error in ImgStoreSwiftMongo - existandOwner. "+str(sys.exc_info()))
            self._log.error("No such file or directory. Image details: "+item.__str__())                 
        except TypeError:
            self._log.error("TypeError in ImgStoreSwiftMongo - existandOwner "+str(sys.exc_info()))  
       
        if (exists and owner):
            return True
        else:
            return False
    
    ############################################################
    # swiftConnection
    ############################################################
    def swiftConnection(self):
        """
        Connect with OpenStack swift
        
        """
        connected = False
        
        #username an password will be moved to the config file
        try:
            self._swiftConnection= cloudfiles.get_connection('test:tester','testing',authurl='https://'+self._swiftAddress+':8080/auth/v1.0')
            connected=True
        except:
            self._log.error("Error in swift connection. "+str(sys.exc_info()))
            
        return connected

class ImgMetaStoreSwiftMysql(ImgMetaStoreMysql):


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
                
        self._dbName="imagesS"
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
                       
class IRUserStoreSwiftMysql(IRUserStoreMysql):

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
                
        self._dbName="imagesS"
        self._tabledata="users"        
        self._mysqlcfg=IRUtil.getMysqlcfg()
        self._iradminsuer=IRUtil.getMysqluser()
        self._log=log
        
        self._dbConnection = None
        if (address != ""):
            self._mysqlAddress=address
        else:
            self._mysqlAddress=self._getAddress()

  
