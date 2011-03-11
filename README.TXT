Requirements
cmd2 
   wget http://pypi.python.org/packages/2.6/c/cmd2/cmd2-0.6.2-py2.6.egg#md5=4c1804bdb53acd313ef83d150ed1cc46
   sudo easy install cmd2-0.6.2-py2.6.egg

It is configured to be placed in /opt/futuregrid/futuregrid/. The file /opt/futuregrid/futuregrid/fg.py must be copied to /opt/futuregrid and will be the futuregrid executable (we need to look into that, to leave only one futuregrid)

Other configuration details may be needed. Thus, each component will have a README.txt file.

For testing purpose, please add your ssh-key to your local .ssh/authorized_keys because the Image Repository uses ssh to executer commands in the server side (localhost)
TBD
