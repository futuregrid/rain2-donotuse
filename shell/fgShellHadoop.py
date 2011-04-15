#!/usr/bin/python
"""
FutureGrid Command Line Interface

FG-Hadoop
"""
import os
#import cmd
import readline
import sys
from futuregrid.shell import fgShellUtils
from futuregrid.hadoop.fgHadoop import fgHadoop
from futuregrid.image.repository.client import IRTypes
import logging
from futuregrid.utils import fgLog
from cmd2 import Cmd
from cmd2 import options
from cmd2 import make_option


class fgShellHadoop(Cmd):
    
    def __init__(self):
        self._fgHadoop = fgHadoop()   
    
    @options([make_option('-j','--jobname', help='Provide a name for the job.'),
              make_option('-i','--inputdir', help='Directory containing the input data for the job'),
              make_option('-o','--outputdir', help='Directory to store the output data from the job'),
              make_option('-q', '--queue', help='Queue to submit the job', default="batch"),    
              make_option('-w', '--walltime', help='Walltime for the job (hh:mm:ss)', default='00:20:00'),    
              make_option('-n', '--nodes', help='Number of nodes for the job', default=2, type=int)    ]) 
    def do_hadooprunjob(self, args, opts):
        """Test Help"""
        hadoop_home = os.environ.get("HADOOP_HOME")
        job_name = opts.jobname
          
        if (not hadoop_home):
            print("HADOOP_HOME is not set.")
        elif(not job_name):
            print("Job name (-j or --jobname) is required.")
        else :                 
            hadoop_cmd = ''.join(args)                           
            # for some reason __init__() does not get called..Hence putting this here 
            #self._fgHadoop = fgHadoop()
            self._fgHadoop.runJob(opts, hadoop_cmd, job_name)
            #self._log.error("SHElll test in fgshell repo")
    