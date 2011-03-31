#!/usr/bin/env python
"""
This class is to use Mysql and the Filesystem as Image Repository back-end


MySQL Databases Info:

    A database with all the info is called images. It contains two tables
        data      (Image details and URI)
        meta        (Image metadata)


"""
__author__ = 'Javier Diaz'
__version__ = '0.1'


from IRDataAccess import AbstractImgStore
from IRDataAccess import AbstractImgMetaStore
from IRDataAccess import AbstractIRUserStore
from IRTypes import ImgEntry
from IRTypes import ImgMeta
from IRTypes import IRUser
from datetime import datetime
import os
import re
import MySQLdb
import string
import IRUtil

class ImgStoreMysql(AbstractImgStore):

    def __init__(self, address,fgirdir, log):
        """
        Initialize object
        
        Keyword parameters:             
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        _items = list of imgEntry
        _dbName = name of the database
        
        """                
        super(ImgStoreMysql, self).__init__()
                
        self._dbName="images"
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
            
    def _getAddress(self):
        """Read from a config file and get the mongos address (list of address:port 
        separated by commas)
        """
        return "192.168.1.1"
    
    def getItemUri(self, imgId, userId):
        return self.getItem(imgId, userId)
        
    def getItem(self, imgId, userId):
        """
        Get Image file identified by the imgId
        
        keywords:
        imgId: identifies the image
        
        return the Image file as a str
        """
        imgLinks=[]  
        result = self.queryStore([imgId], imgLinks, userId)
        
        if (result):     
            return imgLinks[0]
        else:
            return None
        
    def addItem(self, imgEntry1):
        """
        Add imgEntry to store or Update it if exists and the user is the owner
        
        keywords:
        imgEntry : Image information. 
        """
        #self._items.append(imgEntry)
        status=False
        status=self.persistToStore([imgEntry1])            
                    
        return status
    """
    def updateItem(self, userId, imgId, imgEntry1):
        #what are we going to do with concurrency? because I need to remove the old file
        #Here we can implement the same syntax than in the Meta query method and it can 
              #be useful for both, since we update what the query ask to
        
        Update the item if imgId exists and your are the owner.
        
        IMPORTANT: if you want to update both imgEntry and imgMeta, 
                   you have to update first imgMeta and then imgEntry,
                   because imgEntry's update method change the _id of the imgMeta document
                
        keywords:
        imgId : identifies the image (I think that we can remove this)
        imgEntry : new info to update. 
        
        Return boolean
                 
        updated=False
        if (self.mysqlConnection()):
            if(self.existAndOwner(imgId, userId)):            
                try:
                    cursor= self._dbConnection.cursor()   
                    update="UPDATE %s SET createdDate='%s', lastAccess='%s', accessCount='%d' WHERE imgId='%s'" \
                                       % (self._tabledata,datetime.utcnow(),datetime.utcnow(),0, imgId)
                        #print update
                    cursor.execute(update)
                    self._dbConnection.commit()
                
                    updated=True  
                except MySQLdb.Error, e:
                    print "Error %d: %s" % (e.args[0], e.args[1])
                    self._dbConnection.rollback()                           
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    print "No such file or directory. Image details: "+item.__str__()+"\n"                 
                except TypeError as detail:
                    print "TypeError in ImgMetaStoreMongo - persistToStore "+format(detail)
                finally:
                    self._dbConnection.close()
            else:
                print "The Image does not exist or the user is not the owner"
                self._dbConnection.close()
        else:
            print "Could not get access to the database. The file has not been updated"
            
        return updated   
    """  
    
    def histImg (self,imgId):
        """
        Query DB to provide history information about the image Usage
        
        keyworks
        imgId: if you want to get info of only one image
        
        return list of imgEntry or None
        
        """
        success=False             
        if (self.mysqlConnection()):
            try:
                cursor= self._dbConnection.cursor()
                
                if (imgId.strip()=="None"):
                    sql = "SELECT imgId, createdDate,lastAccess,accessCount FROM "+self._tabledata
                else:
                    sql = "SELECT imgId, createdDate,lastAccess,accessCount FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
                
                cursor.execute(sql)
                results=cursor.fetchall()
                
                #self._log.debug(str(results))
                                             
                for dic in results:               
                    tmpEntry=ImgEntry(dic[0],"","",0,str(dic[1]).split(".")[0],str(dic[2]).split(".")[0],dic[3])                    
                    self._items[tmpEntry._imgId] = tmpEntry
                    
                success=True    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))
                self._log.error("No such file or directory. Image details: "+item.__str__())                
            except TypeError as detail:
                self._log.error("TypeError in ImgStoreMysql - histimg: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database in ImgStoreMysql. Query failed")
    
        if success:
            return self._items
        else:
            return None
           
    def queryStore(self, imgIds, imgLinks, userId):
        """        
        Query the DB and provide the uri.    
        
        keywords:
        imgIds: this is the list of images that I need
        imgLinks: This is an output parameter. Return the list URIs
        """
        
        itemsFound=0
                
        if (self.mysqlConnection()):
            try:
                cursor= self._dbConnection.cursor()
                       
                for imgId in imgIds:
                    access=False
                    if(self.existAndOwner(imgId, userId)):
                        access=True
                    elif(self.isPublic(imgId)):
                        access=True
                    
                    if (access):                    
                        sql = "SELECT imgUri, accessCount FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
                        #print sql
                        cursor.execute(sql)
                        results=cursor.fetchone()
                        #print results
                        
                        if(results!=None):
                            imgLinks.append(results[0])
                            accessCount=int(results[1])+1
                            
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
                self._log.error("TypeError in ImgStoreMysql - queryToStore: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. Query failed")
       
        if (itemsFound >= 1):
            return True
        else:
            return False
           
    def persistToStore(self, items):
        """Copy imgEntry to the DB. 
        
        Keyword arguments:
        items= list of ImgEntrys
                
        return: True if all items are stored successfully, False in any other case
        """               
         
        imgStored=0
                        
        if (self.mysqlConnection()):
            try:
                cursor= self._dbConnection.cursor()         
                for item in items:
                    
                    sql = "INSERT INTO %s (imgId, imgMetaData, imgUri, createdDate, lastAccess, accessCount, size) \
       VALUES ('%s', '%s', '%s', '%s', '%s', '%d', '%d' )" % \
       (self._tabledata, item._imgId, item._imgId, item._imgURI, datetime.utcnow(), datetime.utcnow(), 0, item._size)
                    
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
                self._log.error("TypeError in ImgStoreMysql - persistToStore "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. The file has not been stored")
       
        if (imgStored == len(items)):
            return True
        else:
            return False
        
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
        
        if (self.mysqlConnection()):             ##Error 2006: MySQL server has gone away???
            
            ##Solve with this. LOOK INTO MYSQL CONNECTIONS
            con= MySQLdb.connect(host=self._mysqlAddress,                                                                                  
                                           db=self._dbName,
                                           read_default_file=self._mysqlcfg,
                                           user=self._iradminsuer)
            if(self.existAndOwner(imgId, userId)):            
                try:
                    cursor= con.cursor()
                    
                    sql = "SELECT size FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
                    #print sql
                    cursor.execute(sql)
                    results=cursor.fetchone()
                    size[0]=int(results[0])
                    
                    uri=self.getItem(imgId, userId)
                    os.system("rm -rf "+uri)
                    
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
                finally:
                    con.close()
            else:
                con.close()
                self._log.error("The Image does not exist or the user is not the owner")
        else:
            self._log.error("Could not get access to the database. The file has not been removed")
            
        return removed
             
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
                    
            sql = "SELECT imgUri FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
            #print sql
            cursor.execute(sql)
            results=cursor.fetchone()
           
            if(results!=None):
                if (os.path.isfile(results[0])):               
                    exists=True
                     
            sql = "SELECT owner FROM %s WHERE imgId='%s' and owner='%s'"% (self._tablemeta, imgId, ownerId)
            #print sql
            cursor.execute(sql)
            results=cursor.fetchone()
            #print results
            if(results!=None):                  
                owner=True                      
                    
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
        except IOError as (errno, strerror):
            self._log.error("I/O error({0}): {1}".format(errno, strerror))
            self._log.error("No such file or directory. Image details: "+item.__str__())                
        except TypeError as detail:
            self._log.error("TypeError in ImgStoreMysql - existAndOwner: "+format(detail)) 
       
        if (exists and owner):
            return True
        else:
            return False
    
    def isPublic(self, imgId):
        """
        To verify if the file is public
        
        keywords:
        imgId: The id of the image        
        
        Return: boolean
        """
       
        public=False
        
        try:
            cursor= self._dbConnection.cursor()      
                     
            sql = "SELECT permission FROM %s WHERE imgId='%s'"% (self._tablemeta, imgId)
            #print sql
            cursor.execute(sql)
            results=cursor.fetchone()
            #self._log.debug(results)
            if (results!=None):
                if(results[0]=="public"):                                      
                    public=True                       
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
        except IOError as (errno, strerror):
            self._log.error("I/O error({0}): {1}".format(errno, strerror))
            self._log.error("No such file or directory. Image details: "+item.__str__())                
        except TypeError as detail:
            self._log.error("TypeError in ImgStoreMysql - isPublic: "+format(detail)) 
       
        return public
                     
    def mysqlConnection(self):  
        """connect with the mongos available
        
        .mysql.cnf contains:
                [client]
                passwd="complicatedpass"
        
        return: Connection object if succeed or False in other case
        
        """        
        #TODO: change to a global connection??                
        connected = False 
        try:
            self._dbConnection = MySQLdb.connect(host=self._mysqlAddress,                                                                                  
                                           db=self._dbName,
                                           read_default_file=self._mysqlcfg,
                                           user=self._iradminsuer)
            connected = True
            
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
        except TypeError as detail:  
            self._log.error("TypeError in ImgStoreMysql - mysqlConnection "+format(detail))

        return connected 
  




"""end of class"""

class ImgMetaStoreMysql(AbstractImgMetaStore):
    
    def __init__(self, address,fgirdir, log):        
        """
        Initialize object
        
        Keyword arguments:        
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        
        """           
        super(ImgMetaStoreMysql, self).__init__()     
        #self._items={}
        self._dbName="images"
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
            
    def _getAddress(self):
        """Read from a config file and get the mongos address (list of address:port 
        separated by commas)
        """
        return "192.168.1.1:23000,192.168.1.8:23000"
    
    def getItem(self, imgId):
        criteria = "* where imgid="+imgId
        return self.queryStore (criteria)
        
    def addItem(self, imgMeta):
        """
        Add imgEntry to store or Update it if exists and the user is the owner
        
        keywords:
        imgEntry : Image information. 
        """
        #self._items.append(imgEntry)
        status=False
        status=self.persistToStore([imgMeta])            
                    
        return status          
        
    def updateItem(self, userId, imgId, imgMeta1):
         #what are we going to do with concurrency? because I need to remove the old file
        """
        IMPORTANT: if you want to update both imgEntry and imgMeta, 
                   you have to update first imgMeta and then imgEntry,
                   because imgEntry's update method change the _id of the imgMeta document
                   
        keywords:
        imgId : identifies the image (I think that we can remove this)
        imgMeta : new info to update. 
        
        Return boolean
        """ 
        success=False
        
        if (self.mysqlConnection()):  
            if(self.existAndOwner(imgId, userId)):
                try:
                    cursor= self._dbConnection.cursor()                       
                   
                    sql="UPDATE "+self._tablemeta+" SET "
                    
                    temp=imgMeta1.__repr__()
                    temp = temp.replace('\"','')
                    
                    #self._log.debug(str(temp))
                    
                    attributes = temp.split(',')
                    #self._log.debug(str(attributes))
                    
                    #control tag
                    tagstr=""
                    newattr=[]
                    i=0
                    while (i < len(attributes)):                        
                        if attributes[i].strip().startswith('tag='):
                            tagstr+=attributes[i]                             
                            more=True                            
                            while(more):
                                if(attributes[i+1].strip().startswith('vmType=')):
                                    more=False
                                else:
                                     tagstr+=","+attributes[i+1]
                                     i+=1
                            newattr.append(tagstr)
                        else:
                            newattr.append(attributes[i])
                        i+=1
                                        
                    for item in newattr:
                        attribute = item.strip()
                        #print attribute
                        #self._log.debug(str(attribute))
                        tmp = attribute.split("=")
                        key = tmp[0].strip()            
                        value = tmp[1].strip()
                        if not (value=='' or key=="imgId" or key=="owner"):            
                            #print key +"  "+value
                            sql+=key+"=\'"+value+"\', "
                    sql=sql[:-2]
                    
                    sql+=" WHERE imgId=\'"+imgId+"\'"
                    #print sql                
                     
                    cursor.execute(sql)
                    self._dbConnection.commit()
                                                            
                    success=True                                      
                  
                except MySQLdb.Error, e:
                    self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
                    self._dbConnection.rollback()
                except IOError as (errno, strerror):
                    self._log.error("I/O error({0}): {1}".format(errno, strerror))
                    self._log.error("No such file or directory. Image details: "+imgMeta1.__str__())                 
                except TypeError as detail:
                    self._log.error("TypeError in ImgMetaStoreMongo - updateItem "+format(detail))                         
                finally:
                    self._dbConnection.close()
                                  
            else:
                self._log.error("The Image does not exist or the user is not the owner")
                self._dbConnection.close()   
        else:            
            self._log.error("Could not get access to the database. The file has not been updated")
        
        return success
    
    
    def getItems(self, criteria):
        if self.queryStore(criteria):
            return self._items
        else:
            return None
        
    def queryStore(self, criteria):
        """
        Query the db and store the documents in self._items
        
        keyword:
           criteria:
                *      
                * where field=XX, field2=YY
                field1, field2    
                field1,field2 where field3=XX, field4=YY               
                
        TODO:  after the where, the two parts of the equal must be together with no white spaces.                
                                
        return list of dictionaries with the Metadata
        """
        #print criteria
        success=False
        where=False   
        sql=""
        beforewhere=""
        if (self.mysqlConnection()):
            try:
                cursor= self._dbConnection.cursor()         
                    
                #sql = "SELECT imgUri FROM %s WHERE imgId = '%s' "% (self._tablemeta, imgId)
                #print sql
                criteria=string.lower(criteria.strip())  #remove spaces before                
                segs = criteria.split("where")                
                if (len(segs)==1):
                    if (re.search("=",segs[0])==None):
                        sql="SELECT "+segs[0]+" FROM %s" % (self._tablemeta)
                        beforewhere=segs[0]
                    else:
                        where=True
                if (len(segs)==2 or where):
                    if (where):
                        splitwhere=segs[0]
                        beforewhere="*"
                    else:
                        beforewhere=segs[0]
                        splitwhere=segs[1]
                    aux = splitwhere.split(",")     
                                                               
                    aux1 = [z.strip() for z in aux]
                    counter=0
                    fieldswhere="WHERE "
                    for j in aux1:         
                        if (j != ""):                                
                            aux2 = j.split("=")
                            fieldswhere+=aux2[0].strip()+"='"+aux2[1].strip()+"'"
                            counter+=1
                            if (counter<len(aux1)):
                                fieldswhere+=" and "
                    sql="SELECT "+beforewhere+" FROM "+self._tablemeta+" "+fieldswhere 
                    #print sql
                else:                    
                    success=False
                
                cursor.execute(sql)
                results=cursor.fetchall()
                
                if((beforewhere.strip())=="*"):
                    for result in results:                        
                        tmpMeta=self.convertDicToObject(result, True)
                        self._items[tmpMeta._imgId] = tmpMeta
                else:                    
                    for result in results:
                        dic={}                    
                        fields=(beforewhere.strip()).split(",")                   
                        
                        for z in range(len(result)):
                            dic[fields[z].strip()]=result[z]
                        
                        tmpMeta=self.convertDicToObject(dic, False)
                        self._items[tmpMeta._imgId] = tmpMeta                      
                
                success=True
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))
                self._log.error("No such file or directory. Image details: "+item.__str__())                
            except TypeError as detail:
                self._log.error("TypeError in ImgMetaStoreMysql - querytostore: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database in ImgMetaStoreMysql. Query failed")
       
        return success
    
    def convertDicToObject(self, dic, fullMode): 
        """
        This method convert a dictionary in a ImgMetaStoreMongo object
        
        keywords:
        dic: dictionary to convert
        fullMode: boolean. This indicates the way to convert the dic
        
        return: ImgMetaStoreMongo
        """
        if (fullMode):            
            tmpMeta = ImgMeta(dic[0], dic[1], dic[2],dic[3], 
                                          dic[4], dic[5], dic[6], 
                                          dic[7], dic[8], dic[9])            
        else:
            tmpMeta = ImgMeta("", "", "", "", "", "", "", 0, "", "")                    
            for i in dic.keys():
                if (i == "imgid"):
                    tmpMeta._imgId=dic[i]
                elif (i == "os"):
                    tmpMeta._os=dic[i]
                elif (i == "arch"):
                    tmpMeta._arch=dic[i]
                elif (i == "owner"):
                    tmpMeta._owner=dic[i]
                elif (i == "description"):
                    tmpMeta._description=dic[i]
                elif (i == "tag"):                                
                    tmpMeta._tag=",".join(str(bit) for bit in dic[i])
                elif (i == "vmtype"):
                    tmpMeta._vmType=dic[i]
                elif (i == "imgtype"):
                    tmpMeta._imgType=dic[i]
                elif (i == "permission"):
                    tmpMeta._permission=dic[i]
                elif (i == "imgstatus"):
                    tmpMeta._imgStatus=dic[i]
        
        #print tmpMeta
        
        return tmpMeta                 
                                  
    def persistToStore(self, items):
        """Copy imgMeta to the DB. 
        
        Keyword arguments:
        items= list of ImgMeta
                
        return: True if all items are stored successfully, False in any other case
        """    
        
        imgStored=0
        if (self.mysqlConnection()):
            try:
                cursor= self._dbConnection.cursor()         
                for item in items:                    
                    sql = "INSERT INTO %s (imgId, os, arch, vmType, \
                    imgType, permission, owner, imgStatus, description, tag) \
       VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s' , '%s', '%s')" % \
       (self._tablemeta, item._imgId, item._os, item._arch, item._vmType, item._imgType, item._permission, 
        item._owner, item._imgStatus, item._description, item._tag)
                       
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
                self._log.error("TypeError in ImgMetaStoreMongo - persistToStore "+format(detail))                         
            finally:
                self._dbConnection.close()
                                  
        else:
            self._log.error("Could not get access to the database. The file has not been stored")
       
        if (imgStored == len(items)):
            return True
        else:
            return False
    
    def removeItem (self, imdId):
        self._log.error("Data has not been deleted. Please, use the ImgStoreMysql to delete items ")
        
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
                 
            sql = "SELECT imgUri FROM %s WHERE imgId = '%s' "% (self._tabledata, imgId)
            #print sql
            cursor.execute(sql)
            results=cursor.fetchone()
            #print results
            if(results!=None):
                if (os.path.isfile(results[0])):               
                    exists=True
                       
            sql = "SELECT owner FROM %s WHERE imgId='%s' and owner='%s'"% (self._tablemeta, imgId, ownerId)
            #print sql
            cursor.execute(sql)
            results=cursor.fetchone()
            #print results
            if(results!=None):                  
                owner=True                      
                 
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
        except IOError as (errno, strerror):
            self._log.error("I/O error({0}): {1}".format(errno, strerror))
            self._log.error("No such file or directory. Image details: "+item.__str__())                
        except TypeError as detail:
            self._log.error("TypeError in ImgStoreMysql - existAndOwner: "+format(detail))   
       
        if (exists and owner):
            return True
        else:
            return False
        
    def mysqlConnection(self):
        """connect with the mysql db
        
        .mysql.cnf contains:
                [client]
                passwd="complicatedpass"
        
        return: Connection object if succeed or False in other case
        
        """        
        #TODO: change to a global connection??                
        connected = False 
        try:
            self._dbConnection = MySQLdb.connect(host=self._mysqlAddress,                                                                                  
                                           db=self._dbName,
                                           read_default_file=self._mysqlcfg,
                                           user=self._iradminsuer)
            connected = True
            
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
        except TypeError as detail:  
            self._log.error("TypeError in ImgStoreMysql - mysqlConnection "+format(detail))

        return connected 
        
class IRUserStoreMysql(AbstractIRUserStore):  # TODO
    '''
    User store existing as a file or db
    
    If we got a huge number of user ^^ try to create an index to accelerate searchs
         collection.ensure_index("userId")
    '''
    def __init__(self, address,fgirdir, log):  
        super(IRUserStoreMysql, self).__init__()        
        #self._items = []        
        self._dbName="images"
        self._tabledata="users"        
        self._mysqlcfg=IRUtil.getMysqlcfg()
        self._iradminsuer=IRUtil.getMysqluser()
        self._log=log
        
        self._dbConnection = None
        if (address != ""):
            self._mysqlAddress=address
        else:
            self._mysqlAddress=self._getAddress()
            
    def _getAddress(self):
        """Read from a config file and get the mongos address (list of address:port 
        separated by commas)
        """
        return "192.168.1.1:23000,192.168.1.8:23000"
        
    
    def queryStore(self, userId, userIdtoSearch):
        """
        Query the db and store the documents in self._items
                      
                                
        return list of dictionaries with the Metadata
        """
        found=False
        tmpUser={}
        if (self.mysqlConnection()):
            try:                
                cursor= self._dbConnection.cursor()
                
                if(userIdtoSearch!=None):                    
                    if(userIdtoSearch==userId or self.isAdmin(userId)):                        
                        sql = "SELECT * FROM %s WHERE userId = '%s' "% (self._tabledata, userIdtoSearch)
                        cursor.execute(sql)
                        results=cursor.fetchone()                  
                        
                        if (results != None):
                            tmpUser[results[0]]=IRUser(results[0],results[1],int(results[2]),int(results[3]),
                                                  results[4],results[5],results[6],results[7])
                            self._log.debug("queryStore  "+str(tmpUser))                                                                        
                            found=True                 
                elif (self.isAdmin(userId)):
                    sql = "SELECT * FROM %s"% (self._tabledata)
                    cursor.execute(sql)
                    results=cursor.fetchall()                    
                    
                    for result in results:
                        tmpUser[result[0]]=IRUser(result[0],result[1],int(result[2]),int(result[3]),
                                              result[4],result[5],result[6],result[7])
                        #self._log.debug("queryStore  "+str(tmpUser))                                                                      
                        found=True      
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))                                
            except TypeError as detail:
                self._log.error("TypeError in IRUserStoreMongo - queryStore: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database.")
       
        if (found):
            return tmpUser
        else:
            return None
           
    def _getUser(self, userId):
        """Get user from the store by Id'''
                
        Keyword arguments:
        userId = the username (it is the same that in the system)
                
        return: IRUser object
        """
    
        user=self.queryStore(userId,userId)
        if(user!=None):
            return user[userId]
        else:
            return None

    
    def updateAccounting (self, userId, size, num):     
        """
        Update the disk usage and number of owned images of a user when it add a new Image
        
        keywords:
        userId
        size: size of the new image stored by the user.
        
        return: boolean
        """
        success=False
        if (self.mysqlConnection()):
            try:
                if(self.isAdmin(userId)):
                    cursor= self._dbConnection.cursor()
                    
                    sql = "SELECT fsUsed, ownedImgs FROM %s WHERE userId = '%s' "% (self._tabledata, userId)
                    cursor.execute(sql)
                    results=cursor.fetchone()                    
                    currentSize=results[0]
                    currentNum=results[1]
                    
                    totalSize=int(currentSize)+int(size)
                    total=int(currentNum)+int(num)
                    
                    if(totalSize<0):
                        totalSize=0
                    if(total<0):
                        total=0
                    
                    update="UPDATE %s SET fsUsed='%d',ownedImgs='%d' WHERE userId='%s'" \
                                   % (self._tabledata, totalSize, total, userId)
                    
                    cursor.execute(update)
                    self._dbConnection.commit()
                                                    
                    success=True                 
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))                                
            except TypeError as detail:
                self._log.error("TypeError in IRUserStoreMongo - updateAccounting: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. The disk usage has not been changed")
       
        return success
    
    
    def setRole(self, userId, userIdtoModify, role):
        """
        Modify the role of a user. Only admins can do it
        
        return boolean
        """
        success=False
        if (self.mysqlConnection()):
            try:
                if(self.isAdmin(userId)):
                    cursor= self._dbConnection.cursor()
                                
                    update="UPDATE %s SET role='%s'WHERE userId='%s'" \
                                   % (self._tabledata, role, userIdtoModify)
                    #print update
                    cursor.execute(update)
                    self._dbConnection.commit()
                                                    
                    success=True                 
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))                                
            except TypeError as detail:
                self._log.error("TypeError in IRUserStoreMongo - setRole: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. The role has not been changed")
       
        return success
    
    def setQuota(self, userId, userIdtoModify, quota):
        """
        Modify the quota of a user. Only admins can do it
        
        return boolean
        """
        success=False
        if (self.mysqlConnection()):
            try:
                if(self.isAdmin(userId)):
                    cursor= self._dbConnection.cursor()
                                
                    update="UPDATE %s SET fsCap='%d'WHERE userId='%s'" \
                                   % (self._tabledata, quota, userIdtoModify)
                    #print update
                    cursor.execute(update)
                    self._dbConnection.commit()
                                                    
                    success=True                 
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))                                
            except TypeError as detail:
                self._log.error("TypeError in IRUserStoreMongo - setQuota: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. The quota has not been changed")
       
        return success
    
    def setUserStatus(self, userId, userIdtoModify, status):
        """
        Modify the status of a user. Only admins can do it
        
        return boolean
        """
        success=False
        if (self.mysqlConnection()):
            try:
                if(self.isAdmin(userId)):
                    cursor= self._dbConnection.cursor()
                                
                    update="UPDATE %s SET status='%s'WHERE userId='%s'" \
                                   % (self._tabledata, status, userIdtoModify)
                    #print update
                    cursor.execute(update)
                    self._dbConnection.commit()
                                                    
                    success=True                 
                    
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                
                self._dbConnection.rollback()                           
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))               
            except TypeError as detail:
                self._log.error("TypeError in IRUserStoreMongo - setUserStatus: "+format(detail))
            finally:
                self._dbConnection.close()                      
        else:
            self._log.error("Could not get access to the database. The user status has not been changed")
       
        return success
    
    def userDel(self, userId, userIdtoDel):
        """
        Modify the quota of a user. Only admins can do it
        
        return boolean
        """
        removed=False     
        
        if (self.mysqlConnection()):             
            try:
                if(self.isAdmin(userId)):
                    cursor= self._dbConnection.cursor()
                    
                    sql="DELETE FROM %s WHERE userId='%s'" % (self._tabledata,userIdtoDel)                    
                                        
                    cursor.execute(sql)
                    self._dbConnection.commit()
                    
                    removed=True
                
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                        
                self._dbConnection.rollback()
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))                
            except TypeError as detail:
                self._log.error("TypeError in IRUserStoreMongo - removeItem "+format(detail))
            finally:
                self._dbConnection.close()            
        else:
            self._log.error("Could not get access to the database. The file has not been removed")
            
        return removed
        
    def userAdd(self, userId, user):
        """
        Add user to the database
        
        keywords:
        user: IRUser object
        
        return boolean
        """
        return self.persistToStore(userId, [user])
    
        
    def persistToStore(self, userId, users):
        """
        Add user to the database
        
        keywords:
        users: list of IRUser object
        
        return boolean. True only if all users where added correctly to the db
        """
        userStored=0
        authorized=False
        if (self.mysqlConnection()):
            try:
                cursor= self._dbConnection.cursor()      
                
                sql = "select * from %s " % (self._tabledata)
                                
                cursor.execute(sql)
                output=cursor.fetchone()
                
                if (output==None):                    
                    self._log.warning("First User inserted is "+ users[0]._userId+". He is admin")
                    users[0]._status="active"
                    users[0]._role="admin"                    
                    authorized=True                   
                else:
                    if(self.isAdmin(userId)):
                        authorized=True
                
                if (authorized):
                   
                    for user in users:  
                        user._lastLogin=datetime.fromordinal(1) #creates time 0001-01-01 00:00:00
                                          
                        sql = "INSERT INTO %s (userId, cred, fsUsed, fsCap, \
                        lastLogin, status, role, ownedImgs) \
           VALUES ('%s', '%s', '%d', '%d', '%s', '%s', '%s', %d)" % \
           (self._tabledata, user._userId,user._cred, user._fsUsed,user._fsCap, user._lastLogin,
                user._status, user._role, user._ownedImgs)
                           
                        cursor.execute(sql)
                        self._dbConnection.commit()
                                                                
                        userStored+=1                                      
                  
            except MySQLdb.Error, e:
                self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
                self._dbConnection.rollback()
            except IOError as (errno, strerror):
                self._log.error("I/O error({0}): {1}".format(errno, strerror))
            except TypeError as detail:
                self._log.error("TypeError in ImgMetaStoreMongo - persistToStore "+format(detail))                         
            finally:
                self._dbConnection.close()
                                  
        else:
            self._log.error("Could not get access to the database. The file has not been stored")
       
        if (userStored >= 1):
            return True
        else:
            return False
    
    def isAdmin(self, userId):
        """
        Verify if a user is admin
        """
        admin=False
                
        try:
            cursor= self._dbConnection.cursor()         
                 
            sql = "SELECT role FROM %s WHERE userId = '%s' "% (self._tabledata, userId)
            #print sql
            cursor.execute(sql)
            results=cursor.fetchone()
            #print results
            if(results!=None):
                if (results[0]=="admin"):               
                    admin=True
                 
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))                                           
        except IOError as (errno, strerror):
            self._log.error("I/O error({0}): {1}".format(errno, strerror))               
        except TypeError as detail:
            self._log.error("TypeError in IRUSerStoreMysql - isAdmin: "+format(detail))   
       
        return admin
            
    def uploadValidator(self, userId, imgSize):
        user = self._getUser(userId)
        ret = False
        if (user!=None):
            if (user._status=="active"):
                #self._log.debug(user._fsCap)                   
                if imgSize + user._fsUsed <= user._fsCap:                    
                    ret = True
            else:
                ret="NoActive"
        else:
            ret="NoUser"
        
        return ret      
    
    def mysqlConnection(self):         
        """connect with the mysql db
        
        .mysql.cnf contains:
                [client]
                passwd="complicatedpass"
        
        return: Connection object if succeed or False in other case
        
        """        
        #TODO: change to a global connection??                
        connected = False 
        try:
            self._dbConnection = MySQLdb.connect(host=self._mysqlAddress,                                                                                  
                                           db=self._dbName,
                                           read_default_file=self._mysqlcfg,
                                           user=self._iradminsuer)
            connected = True
            
        except MySQLdb.Error, e:
            self._log.error("Error %d: %s" % (e.args[0], e.args[1]))
        except TypeError as detail:  
            self._log.error("TypeError in UserStoreMysql - mysqlConnection "+format(detail))

        return connected 