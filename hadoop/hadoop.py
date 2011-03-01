#
# author: Gregor von Lqszewski
#
write command so e can do 

fg-hadoop -terminate
fg-hadoop -start
fg-hadoop -info
fg-hadoop -util
....

possibly put all the oher code into a single fg-hadoop-api.py?


class hadoop

    def __init__(self):
        print "put the init code here"
    
    def terminate (self):
        print "put the termination code here"


    def initialize (self):
        print "put the initialize code here"
        
    def info (self):
        print "put the info code here"

    def start (self):
        print "start a hadoop run"
      
    def command (self, argument):
        print "interprete a hadop command here"
        
#
#
#
##