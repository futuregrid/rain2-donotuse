#!/usr/bin/env python
"""
This class is to use MongoDB as Image Repository back-end

Create a config file with
    list of mongos: ip/address and port
    list of db names: I would say one per imgType    

MongoDB Databases Info:

    A database with all the info. The problem of the Option 1 is that we need to perform 
                                   a minimum of two queries to get an image
                                  The problem of Option 2 could be that if the db is too big,
                                   we could have performance problems... or not, lets see ;)
        images.fs.chunks (GridFS files)
        images.fs.files  (GridFS metadata)
        images.data      (Image details)
        images.meta        (Image metadata)

REMEBER: imgId will be _id (String) in the data collection, which is also _id (ObjectId) in fs.files. 
               In the first case it is an String and in the second one is an ObjectId
"""
__author__ = 'Javier Diaz'
__version__ = '0.1'

from IRDataAccess import AbstractImgStore
from IRDataAccess import AbstractImgMetaStore
from IRDataAccess import AbstractIRUserStore
import pymongo
from pymongo import Connection
from pymongo.objectid import ObjectId
import gridfs
import bson
from IRTypes import ImgEntry
from IRTypes import ImgMeta
from IRTypes import IRUser
from datetime import datetime
import os
import re

class ImgStoreMongo(AbstractImgStore):

    def __init__(self, address,fgirdir):
        """
        Initialize object
        
        Keyword parameters:             
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        _items = list of imgEntry
        _dbName = name of the database
        
        """                
        super(ImgStoreMongo, self).__init__()
        #self._items={}
        self._dbName="images"
        self._dbConnection=None
        if (address != ""):
            self._mongoAddress=address
        else:
            self._mongoAddress=self._getAddress()
            
    def _getAddress(self):
        """Read from a config file and get the mongos address (list of address:port 
        separated by commas)
        """
        return "192.168.1.1:23000,192.168.1.8:23000"
    
    def getItemUri(self, imgId):
        return "MongoDB cannot provide an image URI, try to retrieve the image."
        
    def getItem(self, imgId):
        """
        Get Image file identified by the imgId
        
        keywords:
        imgId: identifies the image
        
        return the image uri
        """
                        
        imgLinks=[]  
        result = self.queryStore([imgId], imgLinks)
        
        if (result):
            filename="/tmp/"+imgId+".img"
            if not os.path.isfile(filename):
                f = open(filename, 'w')
            else:
                for i in range(100):
                    filename="/tmp/"+imgId+".img"+i.__str__()
                    if not os.path.isfile(filename):
                        f = open(filename, 'w')
                        break
               
            f.write(imgLinks[0].read())   #read return an str
            f.close()
                              
            return filename
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
         
        imgUpdated=False
        if (self.mongoConnection()):            
            oldDeleted=False
            newimgId=""
                
            if (self.existAndOwner(imgId, userId)):
                try:
                    dbLink = self._dbConnection[self._dbName]
                    collection = dbLink["data"]
                    collectionMeta = dbLink["meta"]
                    gridfsLink=gridfs.GridFS(dbLink)
                    
                    collection.update({"_id": imgId}, 
                                          {"$set": {"createdDate" : datetime.utcnow(), 
                                                    "lastAccess" : datetime.utcnow(),
                                                    "accessCount" : 0}
                                                    }, safe=True)
                    
                    #aux=item._imgURI.split("/")
                    #filename=aux[len(aux)-1].strip()      
                     
                    with open(imgEntry1._imgURI) as image:
                        imgIdOb = gridfsLink.put(image, chunksize=4096*1024) 
                                                           
                    newimgId=imgIdOb.__str__().decode('utf-8') # we store an String instead of an ObjectId.
                                                                                         
                    
                    #store the document in a variable
                    oldMeta = collectionMeta.find_one({"_id": imgEntry1._imgId})
                    oldData = collection.find_one({"_id": imgEntry1._imgId})
                    #set a new _id on the document
                    oldMeta['_id'] = newimgId
                    oldData['_id'] = newimgId
                    
                    #print "UpdateItem in ImgStoreMongo"
                    #print oldMeta
                    #print oldData
                    #insert the document, using the new _id
                    collectionMeta.insert(oldMeta, safe=True)
                    collection.insert(oldData, safe=True)
                    # remove the old document with the old _id
                    collection.remove({"_id": imgEntry1._imgId}, safe=True) #Wait for replication? w=3 option
                    collectionMeta.remove({"_id": imgEntry1._imgId}, safe=True)
                    oldDeleted=gridfsLink.delete(ObjectId(imgEntry1._imgId))
                    imgEntry1._imgId=newimgId        
                    imgUpdated=True
                    
                except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
                    print "Autoreconnected."                 
                except pymongo.errors.ConnectionFailure:
                    print "Connection failure. The file has not been updated"                                           
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    print "No such file or directory. Image details: "+imgEntry1.__str__()+"\n"                 
                except TypeError as detail:
                    print "TypeError in ImgStoreMongo - UpdateImage"                
                except pymongo.errors.OperationFailure:
                    print "Operation Failure in ImgStoreMongo - UpdateImage"
                finally:
                    self._dbConnection.disconnect()
            else:
                print "The Image file has not been updated. The imgId is wrong or the User is not the owner"          
        else:            
            print "Could not get access to the database. The Image file has not been updated"
            
        if (re.search('^/tmp/', imgEntry1._imgURI)):
            cmd="rm -rf "+ imgEntry1._imgURI         
            os.system(cmd)
            
        return imgUpdated  
    """                
    def queryStore(self, imgIds, imgLinks):
        """        
        Query the DB and provide the GridOut of the Images to create them with read method.    
        
        keywords:
        imgIds: this is the list of images that I need
        imgEntries: This is an output parameter. Return the list of GridOut objects
                      To read the file it is needed to use the read() method    
        """
        del imgLinks[:]
        itemsFound = 0
                    
        if (self.mongoConnection()):
            try:
                dbLink = self._dbConnection[self._dbName]
                collection = dbLink["data"]
                gridfsLink=gridfs.GridFS(dbLink)                
                for imgId in imgIds:
                    imgLinks.append(gridfsLink.get(ObjectId(imgId)))
                    
                    collection.update({"_id": imgId}, 
                                  {"$inc": {"accessCount": 1},}, safe=True)
                    collection.update({"_id": imgId}, 
                                  {"$set": {"lastAccess": datetime.utcnow()},}, safe=True)
                    #print "here"                                         
                    itemsFound +=1    
            except pymongo.errors.AutoReconnect:
                print "Autoreconnected in ImgStoreMongo - queryStore \n" 
            except pymongo.errors.ConnectionFailure:
                print "Connection failure: the query cannot be performed \n"  
            except TypeError as detail:
                print "TypeError in ImgStoreMongo - queryStore"
            except bson.errors.InvalidId:
                print "Error, there is no Image with such Id. (ImgStoreMongo - queryStore)"
            except gridfs.errors.NoFile:
                print "File not found"
            finally:
                self._dbConnection.disconnect()    
        else:
            print "Could not get access to the database. The file has not been stored"
            
        if (itemsFound == len(imgIds)):
            return True
        else:
            return False
           
    def persistToStore(self, items):
        """Copy imgEntry and imgMeta to the DB. It first store the imgEntry to get the file Id
        
        Keyword arguments:
        items= list of ImgEntrys
                
        return: True if all items are stored successfully, False in any other case
        """               
        self._dbConnection = self.mongoConnection()
        imgStored=0
                
        if (self.mongoConnection()):
            try:
                dbLink = self._dbConnection[self._dbName]
                collection = dbLink["data"]
                collectionMeta = dbLink["meta"]
                gridfsLink=gridfs.GridFS(dbLink)
                for item in items:
                    #each imgType is stored in a different DB
                    #dbLink = self._dbConnection[self._dbNames.get(item._imgMeta._imgType)]                
                    """Store the file. 
                    The filename and the fileID are different in MongoDB.
                    We should include the filename in ImgEntry"""
                    """The default chunksize is 256kb. We should made tests with different sizes
                    4MB is the biggest and should be the most efficient for big binary files"""
                                  
                    
                    with open(item._imgURI) as image:
                        imgId = gridfsLink.put(image, chunksize=4096*1024)
                    
                    item._imgId=imgId.__str__().decode('utf-8') # we store an String instead of an ObjectId.
                    #item._imgMeta._imgId=imgId #not needed                                                                       
                    
                    tags=item._imgMeta._tag.split(",")
                    tags_list = [x.strip() for x in tags]
                    meta = {"_id": item._imgId,
                            "os" : item._imgMeta._os,
                            "arch" : item._imgMeta._arch,
                            "owner" : item._imgMeta._owner,
                            "description" : item._imgMeta._description,
                            "tag" : tags_list,
                            "vmType" : item._imgMeta._vmType,
                            "imgType" : item._imgMeta._imgType,
                            "permission" : item._imgMeta._permission,
                            "imgStatus" : item._imgMeta._imgStatus,                            
                            }
                    data = {"_id": item._imgId,
                            "createdDate" : datetime.utcnow(), 
                            "lastAccess" : datetime.utcnow(),
                            "accessCount" : 0,
                            }
                    
                    collectionMeta.insert(meta, safe=True)
                    collection.insert(data, safe=True)
                                                            
                    imgStored+=1
                                      
                    
            except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
                print "Autoreconnected."                 
            except pymongo.errors.ConnectionFailure:
                print "Connection failure. The file has not been stored. Image details: "+item.__str__()+"\n"                                           
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                print "No such file or directory. Image details: "+item.__str__()+"\n"                 
            except TypeError as detail:
                print "TypeError in ImgStoreMongo - persistToStore"
            except pymongo.errors.OperationFailure:
                print "Operation Failure in ImgStoreMongo - persistenToStore"              
            finally:
                self._dbConnection.disconnect()                      
        else:
            print "Could not get access to the database. The file has not been stored"

        if (re.search('^/tmp/', item._imgURI)):
            cmd="rm -rf "+ item._imgURI         
            os.system(cmd)
        
        if (imgStored == len(items)):
            return True
        else:
            return False
        
    def removeItem (self, userId, imgId):
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
        if (self.mongoConnection()):
            if(self.existAndOwner(imgId, userId)):    
                try:
                    dbLink = self._dbConnection[self._dbName]
                    collection = dbLink["data"]
                    collectionMeta = dbLink["meta"]
                    gridfsLink=gridfs.GridFS(dbLink)
                       
                    gridfsLink.delete(ObjectId(imgId))
                    collection.remove({"_id": imgId}, safe=True) #Wait for replication? w=3 option
                    collectionMeta.remove({"_id": imgId}, safe=True)
                    removed=True
                except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
                    print "Autoreconnected."                 
                except pymongo.errors.ConnectionFailure:
                    print "Connection failure. The file has not been updated"                                           
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    print "No such file or directory. Image details: "+imgEntry1.__str__()+"\n"                 
                except TypeError as detail:
                    print "TypeError in ImgStoreMongo - RemoveItem"                
                except pymongo.errors.OperationFailure:
                    print "Operation Failure in ImgStoreMongo - RemoveItem"
                finally:
                    self._dbConnection.disconnect()
            else:
                print "The Image does not exist or the user is not the owner"
        else:
            print "Could not get access to the database. The file has not been removed"
            
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
        isOwner=False       
        
        try:
            dbLink = self._dbConnection[self._dbName]
            collection = dbLink["meta"]
            gridfsLink=gridfs.GridFS(dbLink)
                
            exists=gridfsLink.exists(ObjectId(imgId))            
            #print imgId         
            #print ownerId
            aux=collection.find_one({"_id": imgId, "owner": ownerId})
            if (aux == None):
                isOwner = False
            else:
                isOwner = True
            #print isOwner                 
        except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
            print "Autoreconnected."                 
        except pymongo.errors.ConnectionFailure:
            print "Connection failure" 
        except TypeError as detail:
            print "TypeError in ImgStoreMongo - existAndOwner"
        except bson.errors.InvalidId:
            print "Error, not a valid ObjectId in ImgStoreMongo - existAndOwner"
        except gridfs.errors.NoFile:
            print "File not found"
                
        if (exists and isOwner):
            return True
        else:
            return False
                      
    def mongoConnection(self):
        """connect with the mongos available
        
        return: Connection object if succeed or False in other case
        
        """        
        #TODO: change to a global connection??                
        connected = False 
        try:
            self._dbConnection = Connection(self._mongoAddress)
            connected = True

        except pymongo.errors.ConnectionFailure as detail:
            print "Connection failed for "+self._mongoAddress
        except TypeError:  
            print "TypeError in ImgStoreMongo - mongoConnection"

        return connected

"""end of class"""

class ImgMetaStoreMongo(AbstractImgMetaStore):
    
    def __init__(self, address,fgirdir):        
        """
        Initialize object
        
        Keyword arguments:        
        _mongoaddress = mongos addresses and ports separated by commas (optional if config file exits)
        
        """           
        super(ImgMetaStoreMongo, self).__init__()     
        #self._items={}
        self._dbName="images"
        self._dbConnection=None
        if (address != ""):
            self._mongoAddress=address
        else:
            self._mongoAddress=self._getAddress()
            
    def _getAddress(self):
        """Read from a config file and get the mongos address (list of address:port 
        separated by commas)
        """
        return "192.168.1.1:23000,192.168.1.8:23000"
    
    def getItem(self, imgId):
        criteria = "* where id="+imgId
        return queryStore (criteria)
        
    def addItem(self, imgMeta):
        print "Please, use the ImgStoreMongo to add new items"            
                    
        return False
    
    def existAndOwner(self, imgId, ownerId):
        """
        To verify if the file exists and I am the owner
        
        keywords:
        imgId: The id of the image
        ownerId: The owner Id
        
        Return: boolean
        """
        exists=False
        isOwner=False    
           
        try:
            dbLink = self._dbConnection[self._dbName]
            collection = dbLink["meta"]
            gridfsLink=gridfs.GridFS(dbLink)
              
            exists=gridfsLink.exists(ObjectId(imgId))            
                             
            aux=collection.find_one({"_id": imgId, "owner": ownerId})
            if (aux == None):
                isOwner = False
            else:
                isOwner = True
            #print imgId
            #print ownerId               
        except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
            print "Autoreconnected."                 
        except pymongo.errors.ConnectionFailure:
            print "Connection failure" 
        except TypeError as detail:
            print "TypeError in ImgStoreMongo - existAndOwner"
        except bson.errors.InvalidId:
            print "Error, not a valid ObjectId in ImgStoreMongo - existAndOwner"
        except gridfs.errors.NoFile:
            print "File not found"
        
        if (exists and isOwner):
            return True
        else:
            return False
        
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
        imgUpdated=False
        
        if (self.mongoConnection()):
            oldDeleted=False
            newimgId=""
            if(self.existAndOwner(imgId, userId)):
                try:
                    dbLink = self._dbConnection[self._dbName]
                    #collection = dbLink["data"]
                    collectionMeta = dbLink["meta"]
                    
                    tags=imgMeta1._tag.split(",")
                    tags_list = [x.strip() for x in tags]
                    
                    dic={}
                    temp=imgMeta1.__repr__()
                    temp = temp.replace('\"','')
                    #print temp
                    attributes = temp.split(',')
                    for item in attributes:
                        attribute = item.strip()
                        #print attribute
                        tmp = attribute.split("=")
                        key = tmp[0].strip()            
                        value = tmp[1].strip()
                        if not (value=='' or key=="imgId" or key=="owner"):            
                            #print key +"  "+value
                            dic[key]=value
                                                               
                    collectionMeta.update({"_id": imgId}, 
                                      {"$set": dic }, safe=True)
                    
                    imgUpdated=True
                    
                except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
                    print "Autoreconnected."                 
                except pymongo.errors.ConnectionFailure:
                    print "Connection failure. The file has not been updated"                                           
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    print "No such file or directory. Image details: "+imgEntry1.__str__()+"\n"                 
                except TypeError as detail:
                    print "TypeError in ImgMetaStoreMongo - UpdateImage"                
                except pymongo.errors.OperationFailure:
                    print "Operation Failure in ImgMetaStoreMongo - UpdateImage"
                finally:
                    self._dbConnection.disconnect()
            else:
                print "The Information has not been updated. The imgId is wrong or the User is not the owner"          
        else:            
            print "Could not get access to the database. The Information has not been updated"   
                    
        return imgUpdated  
    
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
        success = False               
        if (self.mongoConnection()):
            try:
                dbLink = self._dbConnection[self._dbName]
                collection = dbLink["meta"]                
                
                criteria=criteria.strip()  #remove spaces before
                segs = criteria.split(" ")  #splits in parts                
                args = [x.strip() for x in segs]
                
                fieldsFound=False
                where=False                
                fieldsWhere={}
                fields=[]    
                for i in range(len(args)):                      
                    if ( args[i] != " "):
                        if not fieldsFound:
                            if (args[i] == "*"):                                
                                del fields[:]
                                fields = "*"
                                fieldsFound=True
                            else:
                                aux = args[i].split(",")                                                
                                aux1 = [z.strip() for z in aux]
                                for j in aux1:                                
                                    if (j != ""):
                                        if (j == "*"):
                                            del fields[:]
                                            fields = "*"
                                            fieldsFound=True
                                        elif (j == "where" or j == "WHERE"):
                                            where=True
                                            fieldsFound=True        
                                        else:
                                            fields.append(j) 
                        elif not where:
                            if ( args[i] == "where" or args[i] == "WHERE"):
                                where=True
                        else:
                            aux = args[i].split(",")                                                
                            aux1 = [z.strip() for z in aux]
                            for j in aux1:         
                                if (j != ""):                                
                                    aux2 = j.split("=")
                                    if (aux2[0].strip() == "imgId"):
                                        fieldsWhere["_id"]=aux2[1].strip()                                                                            
                                    #elif (aux2[0].strip() == "imgType" or aux2[0].strip() == "vmType" or aux2[0].strip() == "imgStatus"):
                                     #   fieldsWhere[aux2[0].strip()]=int(aux2[1].strip())
                                    else:
                                        fieldsWhere[aux2[0].strip()]=aux2[1].strip()                                                          
                          
                #print "fields "+fields.__str__()
                #print "fieldsWhere "+fieldsWhere.__str__()   
                
                if ( fields == "*"):
                    results=collection.find(fieldsWhere)
                    for resultList in results:
                        #print resultList
                        tmpMeta = self.convertDicToObject(resultList, True)
                        self._items[tmpMeta._imgId] = tmpMeta
                else:
                    results=collection.find(fieldsWhere, fields)                    
                    for resultList in results:
                        tmpMeta = self.convertDicToObject(resultList, False)                    
                        self._items[tmpMeta._imgId] = tmpMeta                      
                                
                success=True
                    
            except pymongo.errors.AutoReconnect:
                print "Autoreconnected in ImgMetaStoreMongo - queryStore \n" 
            except pymongo.errors.ConnectionFailure:
                print "Connection failure: the query cannot be performed \n"  
            except TypeError as detail:
                print "TypeError in ImgMetaStoreMongo - queryStore"
            finally:
                self._dbConnection.disconnect()    
        else:
            print "Could not get access to the database. Query failed"
        
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
            tags=','.join(str(bit) for bit in dic['tag'])
            tmpMeta = ImgMeta(dic['_id'], dic['os'], dic['arch'],dic['owner'], 
                                          dic["description"], tags, dic["vmType"], 
                                          dic["imgType"], dic["permission"], dic["imgStatus"])
        else:
            tmpMeta = ImgMeta("", "", "", "", "", "", "", 0, "", "")                    
            for i in dic.keys():
                if (i == "_id"):
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
                elif (i == "vmType"):
                    tmpMeta._vmType=dic[i]
                elif (i == "imgType"):
                    tmpMeta._imgType=dic[i]
                elif (i == "permission"):
                    tmpMeta._permission=dic[i]
                elif (i == "imgStatus"):
                    tmpMeta._imgStatus=dic[i]
        
        #print tmpMeta._tag
        
        return tmpMeta           
                                  
    def persistToStore(self, items):
        #this method is used only in ImgStoreMongo
        print "Data has not been stored. Please, use the ImgStoreMongo to add new items"
    
    def removeItem (self, imdId):
        #this method is used only in ImgStoreMongo
        print "Data has not been deleted. Please, use the ImgStoreMongo to delete items "
        
    def mongoConnection(self):
        """connect with the mongos available
        
        return: Connection object if succeed or False in other case
        
        """        
        #TODO: change to a global connection??
                
        connected = False 
        try:
            self._dbConnection = Connection(self._mongoAddress)
            connected = True

        except pymongo.errors.ConnectionFailure as detail:
            print "Connection failed for "+self._mongoAddress
        except TypeError:  
            print "TypeError in ImgStoreMongo - mongoConnection"

        return connected
        
class IRUserStoreMongo(AbstractIRUserStore):  # TODO
    '''
    User store existing as a file or db
    
    If we got a huge number of user ^^ try to create an index to accelerate searchs
         collection.ensure_index("userId")
    '''
    def __init__(self, address,fgirdir):
        super(IRUserStoreMongo, self).__init__()        
        #self._items = []
        self._dbName = "users"   #file location for users
        self._dbConnection=None
        if (address != ""):
            self._mongoAddress=address
        else:
            self._mongoAddress=self._getAddress()
            
    def _getAddress(self):
        """Read from a config file and get the mongos address (list of address:port 
        separated by commas)
        """
        return "192.168.1.1:23000,192.168.1.8:23000"
           
    def getUser(self, userId):
        """Get user from the store by Id'''
                
        Keyword arguments:
        userId = the username (it is the same that in the system)
                
        return: IRUser object
        """
        found=False
        tmpUser=IRUser("")
                
        if (self.mongoConnection()):
            try:
                dbLink = self._dbConnection[self._dbName]
                collection = dbLink["data"]                
                                
                dic=collection.find_one({"userId": userId})
                
                if not dic == None:
                    
                    tmpUser = IRUser(dic['userId'], dic['cred'], dic['fsUsed'],dic['fsCap'],dic['lastLogin'], 
                                          dic["status"], dic["role"])
                    found = True
                                                      
            except pymongo.errors.AutoReconnect: 
                print "Autoreconnected in IRUserStoreMongo - getUser"                 
            except pymongo.errors.ConnectionFailure:
                print "Connection failure in IRUserStoreMongo - getUser"                                           
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                print "IOError in IRUserStoreMongo - getUser"                 
            
            except pymongo.errors.OperationFailure:
                print "Operation Failure in IRUserStoreMongo - getUser"
            finally:
                self._dbConnection.disconnect()    
        else:
            print "Could not get access to the database. The file has not been stored"
        
        
        if (found):
            return tmpUser
        else:
            return None
        
    
    def updateDiskUsed (self, userId, size): #TODO verify this. Decide if size will be a string or a int    
        """
        Update the disk usage of a user when it add a new Image
        
        keywords:
        userId
        size: size of the new image stored by the user.
        
        return: boolean
        """
        success = False
        
        if (self.mongoConnection()):
            try:
                dbLink = self._dbConnection[self._dbName]
                collection = dbLink["data"]     
                
                currentSize=collection.find_one({"userId": userId})
                
                totalSize= int(currentSize['fsUsed']) + int(size)
                collection.update({"userId": userId}, 
                                  {"$set": {"fsUsed" : totalSize,}
                                            }, safe=True)
            except pymongo.errors.AutoReconnect:
                print "Autoreconnected in IRUserStoreMongo - updateDiskUsed \n" 
            except pymongo.errors.ConnectionFailure:
                print "Connection failure: the query cannot be performed \n"  
            except TypeError as detail:
                print "TypeError in IRUserStoreMongo - updateDiskUsed"
            finally:
                self._dbConnection.disconnect()    
        else:
            print "Could not get access to the database. The disk usage has not been updated"
        
        return success
    
        
    def addUser(self, user):
        """
        Add user to the database
        
        keywords:
        user: IRUser object
        
        return boolean
        """
        return self.persistToStore([user])
    
        
    def persistToStore(self, users):
        """
        Add user to the database
        
        keywords:
        users: list of IRUser object
        
        return boolean. True only if all users where added correctly to the db
        """
        userStored=0
                
        if (self.mongoConnection()):
            try:
                dbLink = self._dbConnection[self._dbName]
                collection = dbLink["data"]
                
                for user in users:
                    meta = {"userId": user._userId,
                            "cred" : user._cred,
                            "fsUsed" : user._fsUsed,
                            "fsCap"  : user._fsCap,
                            "lastLogin" : user._lastLogin,
                            "status" : user._status,
                            "role" : user._role,                                                  
                            }            
                    
                    if (collection.find_one({"userId": user._userId}) == None):
                        collection.insert(meta, safe=True)                                                        
                        userStored+=1
                    else:
                        print "The userId "+user._userId+" exits in the database"
                                                 
                    
            except pymongo.errors.AutoReconnect:  #TODO: Study what happens with that. store or not store the file
                print "Autoreconnected."                 
            except pymongo.errors.ConnectionFailure:
                print "Connection failure. The user has not been stored."                                           
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                print "No such file or directory."                 
            except TypeError as detail:
                print "TypeError in IRUserStoreMongo - addUser"
            except pymongo.errors.OperationFailure:
                print "Operation Failure in IRUserStoreMongo - addUser"
            finally:
                self._dbConnection.disconnect()    
        else:
            print "Could not get access to the database. The user has not been stored"
        
        if (userStored == len(users)):
            return True
        else:
            return False
            
    def uploadValidator(self, userId, imgSize):
        user = self.getUser([userId])
        ret = False
        if (user!=None):            
            if imgSize + user._fsUsed <= user._fsCap:
                ret = True
        else:
            ret="NoUser"
        return True       ###MODIFY THIS TO ENABLE QUOTE
    
    def mongoConnection(self):
        """connect with the mongos available
        
        return: Connection object if succeed or False in other case
        
        """        
        #TODO: change to a global connection??
                
        connected = False 
        try:
            self._dbConnection = Connection(self._mongoAddress)
            connected = True

        except pymongo.errors.ConnectionFailure as detail:
            print "Connection failed for "+self._mongoAddress
        except TypeError:  
            print "TypeError in IRUserStoreMongo - mongoConnection"

        return connected