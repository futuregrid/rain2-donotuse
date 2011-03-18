#!/usr/bin/env python
"""
A shell command to dynamically deploy an Apache Hadoop environments on FG.

This command line tool deploys Apache Hadoop in to a FutureGrid resource 
and executes the given job. Users can specify a directory containing input 
data, which will get uploaded to the HDFS under the "input" directory. 
Users can also specify a directory to download the output data (contents 
of the "output" directory) from HDFS. HADOOP_HOME environment variable, 
pointing to the Hadoop distribution, needs to be set before running this 
command.
"""

__author__ = 'Thilina Gunarathne'
__version__ = '0.1'

import subprocess
import time
import sys
import os
import argparse

# GVL:

# code does not take into account if jobname already exists?
#
# no documentation provided
#

# TODO : Configure the conf location

def generate_job_script(job_name, hadoop_command, data_input_dir,
                        data_output_dir, walltime, num_nodes, queue,) :
    local_storage_dir = "/tmp/$PBS_JOBID-fg-hadoop"
    hadoop_conf_dir = "$HADOOP_HOME/conf"
    
    job_script = "#!/bin/bash \n"

    job_script +="#PBS -l nodes=" + str(num_nodes) + ":ppn=8 \n"
    if(walltime):
        job_script +="#PBS -l walltime=" + walltime + " \n"
        
    job_script +="#PBS -N " + job_name + " \n"
    if(queue):
        job_script +="#PBS -q " + queue + " \n"
    
    job_script +="#PBS -V \n"
    job_script +="#PBS -o " + job_name + ".$PBS_JOBID.out \n \n"
    
    job_script +="echo Generating Configuration Scripts \n"
    job_script +="python " + sys.path[0] + "/generate-xml.py $PBS_NODEFILE " 
    job_script += local_storage_dir + " " + hadoop_conf_dir + " \n\n"
    
    job_script +="echo Formatting HDFS  \n"
    job_script +="$HADOOP_HOME/bin/hadoop namenode -format   \n\n"

    job_script +="echo starting the cluster  \n"
    job_script +="$HADOOP_HOME/bin/start-dfs.sh  \n" #--config $HADOOP_CONF_DIR
    job_script +="$HADOOP_HOME/bin/hadoop dfsadmin -safemode wait \n"
    job_script +="sleep 30 \n" # safemode wait seems to be still buggy
    
    if(data_input_dir):
        job_script +="$HADOOP_HOME/bin/hadoop fs -put "
        job_script += data_input_dir + " input \n" 
        
    job_script +="$HADOOP_HOME/bin/start-mapred.sh  \n \n"
    
    job_script +="echo Running the hadoop job  \n"    
    job_script +="$HADOOP_HOME/bin/hadoop " + hadoop_command + "\n \n"
    
    if(data_output_dir):
        job_script +="$HADOOP_HOME/bin/hadoop fs -get output " 
        job_script += data_output_dir + " \n"
    
    job_script +="$HADOOP_HOME/bin/stop-mapred.sh" + "\n"
    job_script +="$HADOOP_HOME/bin/stop-dfs.sh" + "\n"
    
    masters_file_name = job_name + "-fg-hadoop.job"
    masters_file = open(masters_file_name, "w")
    masters_file.write(job_script)
    masters_file.close()
    return masters_file_name
    
    
def main():        
    parser = argparse.ArgumentParser(description='Run a Hadoop Job in FutureGrid')
    parser.add_argument('jobname', help='Name of the job')
    
    #optional arguments
    parser.add_argument('-i','--inputdir', help='Directory containing the input data for the job')
    parser.add_argument('-o','--outputdir', help='Directory to store the output data from the job')
    parser.add_argument('-q', '--queue', help='Queue to submit the job', default="batch")
    # TODO: add a type function to validate walltime
    parser.add_argument('-w', '--walltime', help='Walltime for the job (hh:mm:ss)', default='00:20:00')    
    parser.add_argument('-n', '--nodes', help='Number of nodes for the job', default=2, type=int)    
    
    #hadoop command
    parser.add_argument('hadoopcmd', nargs='+', help='''Hadoop job command to 
        run in the cluster. Please use "input" & "output" as HDFS input & output
        directories ''')

    args = parser.parse_args()
    
    hadoop_home = os.environ.get("HADOOP_HOME")
    if (not hadoop_home):
        print("HADOOP_HOME is not set.")
        sys.exit()
        
    hadoop_cmd = ' '.join(args.hadoopcmd)
    
    job_script = generate_job_script(args.jobname,hadoop_cmd, 
        args.inputdir, args.outputdir,args.walltime,args.nodes,args.queue)
    
    subprocess.call("qsub " + job_script, shell=True)

    
# TODO export HADOOP_LOG_DIR=${HADOOP_HOME}/log
if __name__ == "__main__":
    main()
