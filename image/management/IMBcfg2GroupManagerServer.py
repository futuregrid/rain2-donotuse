#/usr/bin/env python
# Description: Command line front end for image generator
#
# Author: Andrew J. Younge
#


import socket
import sys
from xml.dom.ext import PrettyPrint
from xml.dom.minidom import Document, parse

#Global vars
bundlePath = '/var/lib/bcfg2/Bundler/'
groupPath = '/var/lib/bcfg2/Metadata/'
port = 45678
def main():

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('', port))
    sock.listen(1)
    while True:
        channel, details = sock.accept()
        #print details
        #print 'DEBUG: opened connection with:' + details

        #receive message
        name = channel.recv(512)
        print 'DEBUG: Received name: ' + name
        channel.send('OK')

        os = channel.recv(512)
        print 'DEBUG: Received OS: ' + os
        channel.send('OK')
        version = channel.recv(512)
        print 'DEBUG: Received version: ' + version
        channel.send('OK')
        packages = channel.recv(4096)
        print 'DEBUG: Recevied packages: ' + packages
        channel.send('OK')
        channel.close()

        writebundleXML(name, packages)

        modifyGroups(name, os, version)

def modifyGroups(name, os, version):

    filename = groupPath + 'groups.xml'
    file = open(filename, 'r')
    groups = parse(file)

    groupsNode = groups.childNodes[0]

    newGroup = groups.createElement('Group')
    newGroup.setAttribute('profile', 'true')
    newGroup.setAttribute('public', 'true')
    newGroup.setAttribute('name', name)
    groupsNode.appendChild(newGroup)

    osGroup = groups.createElement('Group')
    osGroup.setAttribute('name', os + '-' + version)
    newGroup.appendChild(osGroup)

    bundleGroup = groups.createElement('Bundle')
    bundleGroup.setAttribute('name', name)
    newGroup.appendChild(bundleGroup)

    file.close()
    file = open(filename, 'w')
    PrettyPrint(groups, file)


def writebundleXML(name, packages):
    #Create the new Bundle
    bundle = Document()

    bundleHead = bundle.createElement('Bundle')
    bundleHead.setAttribute('name', name)
    bundle.appendChild(bundleHead)

    pkgs = packages.split(' ')
    for package in pkgs:

        p = bundle.createElement('Package')
        p.setAttribute('name', package)
        bundleHead.appendChild(p)

    #DEBUG
    #print bundle.toprettyxml(indent='    ')

    #Write to file
    file = open(bundlePath + name + '.xml', 'w')
    PrettyPrint(bundle, file)


if __name__ == "__main__":
    main()
#END
