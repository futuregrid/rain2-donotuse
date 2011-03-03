#! /usr/bin/python

import subprocess
import time
import sys
import os

# GVL:
# please remove the write statements and replace with text block
#
# code does not take into account if jobname already exists?
#
# no documentation provided
#
#

def generate_job_script(job_name, hadoop_command, data_input_dir, 
                        data_output_dir, walltime, queue, num_nodes=1) :
    local_storage_dir = "/tmp/$PBS_JOBID-fg-hadoop"
    hadoop_conf_dir = "$HADOOP_HOME/conf"
    
    masters_file_name = job_name + "-fg-hadoop.job"
    masters_file = open(masters_file_name, "w")
    masters_file.write("#!/bin/bash \n")

    masters_file.write("#PBS -l nodes=" + str(num_nodes) + ":ppn=8 \n")
    if(walltime):
        masters_file.write("#PBS -l walltime=" + walltime + " \n")
        
    masters_file.write("#PBS -N " + job_name + " \n")
    if(queue):
        masters_file.write("#PBS -q " + queue + " \n")
    
    masters_file.write("#PBS -V \n")
    masters_file.write("#PBS -o " + job_name + ".$PBS_JOBID.out \n \n")
    
    masters_file.write("echo Generating Configuration Scripts \n")
    masters_file.write("python "+sys.path[0]+"/generate-xml.py $PBS_NODEFILE "
                        + local_storage_dir + " " + hadoop_conf_dir + " \n\n")
    
    subprocess.call("export FG_HADOOP_HOME=" + sys.path[0], shell=True)
    
    masters_file.write("echo Formatting HDFS  \n")
    masters_file.write("$HADOOP_HOME/bin/hadoop namenode -format   \n\n")

    masters_file.write("Starting the cluster  \n")
    masters_file.write("$HADOOP_HOME/bin/start-dfs.sh  \n") #--config $HADOOP_CONF_DIR
    masters_file.write("$HADOOP_HOME/bin/hadoop dfsadmin -safemode wait \n\n") 
    if(data_input_dir):
        masters_file.write("$HADOOP_HOME/bin/hadoop fs -put " 
                           + data_input_dir + " input \n") 
        
    masters_file.write("$HADOOP_HOME/bin/start-mapred.sh  \n \n")
    
    masters_file.write("echo Running the hadoop job  \n")    
    masters_file.write("$HADOOP_HOME/bin/hadoop " + hadoop_command + "\n \n")
    
    if(data_output_dir):
        masters_file.write("$HADOOP_HOME/bin/hadoop fs -get output " 
                           + data_output_dir + " \n") 
    
    masters_file.write("$HADOOP_HOME/bin/stop-mapred.sh" + "\n")
    masters_file.write("$HADOOP_HOME/bin/stop-dfs.sh" + "\n")
    
    masters_file.close()
    
def temp(): 
    from optparse import OptionParser
    
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                      help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose", default=True,
                      help="don't print status messages to stdout")
    
    (options, args) = parser.parse_args()
    print options.filename
    print args
    nodes_file = open(args, "r")
    nodes = nodes_file.readlines()
    nodes_file.close()

hadoop_home = os.environ.get("HADOOP_HOME")
if (not hadoop_home):
    print("HADOOP_HOME is not set.")
    sys.exit()
    
# setting FG_HADOOP_HOME, which will be used in the job script
generate_job_script("test1", "jar wordcount.jar WordCount input output", 
                    "~/input", "~/output", "0:20:00", "")
# export HADOOP_LOG_DIR=${HADOOP_HOME}/log
# export HADOOP_HOME
# export HADOOP_CONF_DIR 
