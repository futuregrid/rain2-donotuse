#!/bin/bash
#This must be executed in a CentOS machine with the version 5.5 or 5.6, depending what you need to get.

#version can be 5.6 or 5.5
VER=5.6
OS=centos
IMG_FILE=$OS-$VER-base.img
DEST=/tmp/image

cd /tmp
dd if=/dev/zero of=$IMG_FILE bs=1024k seek=2048 count=0
mke2fs -F -j $IMG_FILE
mkdir $DEST
mount -o loop $IMG_FILE $DEST

if [ $VER =='5.5' ] 
then
    wget http://mirror.centos.org/centos/5.5/os/x86_64/CentOS/centos-release-5-5.el5.centos.x86_64.rpm -O centos-release.rpm
elif [ $VER == '5.6' ]
then
    wget http://mirror.centos.org/centos/5.6/os/x86_64/CentOS/centos-release-5-6.el5.centos.1.x86_64.rpm -O centos-release.rpm
fi

rpm -ihv --nodeps --root $DEST centos-release.rpm
yum --installroot=$DEST -y groupinstall Core
cp /etc/resolv.conf $DEST/etc/
cp /etc/sysconfig/network $DEST/etc/sysconfig/
echo "127.0.0.1 localhost.localdomain localhost" > $DEST/etc/hosts

umount $DEST
#rm -rf $DEST
