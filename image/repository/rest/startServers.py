#!/user/bin/python


from optparse import OptionParser
import sys
import os
from types import *
import socket
from subprocess import *
import logging
import logging.handlers
from xml.dom.minidom import Document,parse



def main():

    log_filename = 'fg-image-deploy.log'
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler = logging.FileHandler(log_filename)
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Add options
    parser = OptionParser()
    logger.info('Starting image deployer...')
    parser.add_option("-d", '--dbserver', dest='dbserver', help='Specify the port for mongodb server.')
    parser.add_option("-a", '--adminport', dest='adminport' help='Specify the http admin port number.')
    parser.add_option("-s", '--adminsecureport', dest='adminsecureport', help='Specify the https admin port number.')
    parser.add_option("-p", '--usersecureport', dest='usersecureport', help='Specify the https user port number.')
    parser.add_option("-n", "--username", dest="username", help="Specify the username delegated to the user port.")
    parser.add_option("-r", "--useradmin", dest="useradmin", help="Specify the admin based user name.")
    

    (ops, args) = parser.parse_args()

    if not ops.debug:
	logging.basicConfig(level=logging.INFO)
	ch.setLevel(logging.INFO)
	

    global name
    
	
    user = os.environ['MONGO_DB']
    except KeyError :
    print "Please, define your MONGO_DB environment variable in order to find the database directory"
    sys.exit()
            user = ops.mongo
	    cmd = 'mkdir mongodb'
	    runcmd(cmd)
	    cmd = 'setenv MONGO_DB ' + getHome() + mongodb
	    runcmd(cmd)
	    cmd = 'sudo wget ' + http://fastdl.mongodb.org/osx/mongodb-osx-i386-1.8.2.tgz
	    runcmd(cmd)
	    cmd = 'mv mongodb-osx-i386-1.8.2.tgz mongodb'
	    runcmd(cmd)


#        if type(ops.dbserver) is not NoneType:   
#        else:

	    


# Check if the cherrypy directory exist
#if [ -d "$MONGO_DB"]; then
#    wget http://fastdl.mongodb.org/osx/mongodb-osx-i386-1.8.2.tgz
    
#elif

#else
    
#fi


#echo "######################################################################"
#echo "Starting mongod"
#echo "######################################################################"
#mongod --port 23000 &
#mongoPID=$!
#sleep 1

#lsof -i tcp:23000

#wait



#echo "######################################################################"
#echo "Starting CherryPy server "
#echo "######################################################################"

#python restFrontEnd.py &> cherry.log &
#serverPID=$!
#sleep 1

#lsof -i tcp:8080
#lsof -i tcp:23000






#wait


#echo "Enter return to kill mongod and cherrypy server"
#read line

#kill -9 ${serverPID}
#kill -9 ${mongoPID}


#rm /data/db/mongod.lock

#lsof -i tcp:8080
#lsof -i tcp:23000





# Handy Extract Program, from http://tldp.org/LDP/abs/html/sample-bashrc.html
#function extract()    
#{
#     if [ -f $1 ] ; then
#         case $1 in
#             *.tar.bz2)   tar xvjf $MONGO_TAR ;;
#             *.tar.gz)    tar xvzf $MONGO_TAR ;;
#             *.bz2)       bunzip2 $MONGO_TAR      ;;
#             *.rar)       unrar x $MONGO_TAR      ;;
#             *.gz)        gunzip $MONGO_TAR       ;;
#             *.tar)       tar xvf $MONGO_TAR      ;;
#             *.tbz2)      tar xvjf $MONGO_TAR     ;;
#             *.tgz)       tar xvzf $MONGO_TAR     ;;
#             *.zip)       unzip $MONGO_TAR        ;;
#             *.Z)         uncompress $MONGO_TAR   ;;
#             *.7z)        7z x $1         ;;
#             *)           echo "'$1' cannot be extracted via >extract<" ;;
#         esac
#     else
#         echo "'$1' is not a valid file"
#     fi
}

