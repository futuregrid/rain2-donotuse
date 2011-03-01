VER: 0.1a
------------
This is the prototype of the FG Image Repository which layouts the basic code framework and implements some basic functionality using python.

The code tree structure:
|-- client
|   |-- IRClient.py
|   |-- IRServiceProxy.py
|   |-- IRTest.py
|   `-- IRTypes.py
|-- README.txt
`-- server
    |-- IRDataAccessMongo.py
    |-- IRDataAccessMysql.py
    |-- IRDataAccess.py
    |-- IRService.py
    |-- IRTypes.py
    `-- IRUtil.py

It follows the architecture design document that has been developed in the FG wiki. Please refer to the wiki SW-010 document for the detailed info.
    
The code has two portions: server and client.

Server configuration:
We need to configure BACKEND and ADDRESS. We can also change the images directory used in the variable IRService._fgirimgstore. This variable is unique for each backend (in the case of MongoDB is only a temporal dir, the images are not stored there)
-FileSystem (no DBs)
    BACKEND="file" ADDRESS=""
    Files with name 'IRMetaStore' and 'IRImgStore' should be created to store the image data.
    A directory with name 'irstore' should be created to store the real image files.
-MongoDB
    Config example: BACKEND="mongodb" ADDRESS="localhost:23000"
    ADDRESS indicates the MongoDB connection, it could be the address of the mongod process in a simple installation or the address of the mongos process in a distributed deployment (we recommend have mongos in the same machine that the IR server)
-MySQL 
   Config example: BACKEND="mysql" ADDRESS="localhost"
   A directory with name 'irstore' should be created to store the real image files.
   Create user IRUser and store the password in a file $HOME/.mysql.cnf. The format is:
   [client]
   password=yourpass

The client side is to be distributed to user environment from where user can access the Image Repository.

Please note some configurations in IRServiceProxy.py need to be changed to reflect your deployment. In later phase we'll provide intallation script to do this automatically. The first one is the machine where the server is deployed and the second one is the local directory where the client is.
    SERVICEENDP = "xray.futuregrid.org"
    FGIRDIR = "/N/u/fuwang/fgir/"
    
The users need to have access to the irstore where the images to be put, and also the FGIRDIR so the remote command could be executed.

To run the client, make sure that python is installed. Then

IRClient.py -h 

to get the help info on available commands.

PLEASE NOTE:
1. Some of the functionality is not yet implemented. Basic operations like query, put, get, modify are supported.
2. SSH/SCP is used for authentication/authorization. This is not an ideal way in long run since it lacks of fine-grained authorization.
3. We have a plan that improve this prototype with a> replace the file based data access by a distributed DB based solution(MangoDB is now on the list); b> convert the ssh and remote execution paradigm with service based solution as the names already implied. However this need to be in alignment with the security solution to be used, e.g., an extra secret access token may be needed for each user..
