#! /usr/bin/env python

import xml.dom.minidom
import os
import subprocess
import sys

#
# no comments provided
#
# no man page provided, e.g. there shoudl be a README.txt that at
# least points to the man page in the portal
#
# no failsaves provided if specified dirs already exist
#
# is cleanup needed?
#


def get_config_document():
    doc = xml.dom.minidom.Document()
    config_element = doc.createElement("configuration")
    doc.appendChild(config_element)
    return doc, config_element

def create_property(name, value, doc):
    property_element = doc.createElement("property")
    
    name_element = doc.createElement("name")
    name_text_node = doc.createTextNode(name)
    name_element.appendChild(name_text_node)
    
    value_element = doc.createElement("value")
    value_text_node = doc.createTextNode(value)
    value_element.appendChild(value_text_node)
    
    property_element.appendChild(name_element)
    property_element.appendChild(value_element)
    return property_element


def create_hdfs_site(dfs_name_dir, dfs_data_dir):
    doc, config_element = get_config_document()
    config_element.appendChild(create_property("dfs.name.dir", dfs_name_dir, doc))
    config_element.appendChild(create_property("dfs.data.dir", dfs_data_dir, doc))
    return doc

def create_mapred_site(master_node_ip, mapred_local_dir):
    doc, config_element = get_config_document()
    #doc, dfs_name_property =  create_property("dfs.name.dir", "/tmp/matlab/name", doc)
    config_element.appendChild(create_property("mapred.job.tracker", master_node_ip+":53777", doc))
    config_element.appendChild(create_property("mapred.local.dir", mapred_local_dir, doc))
    return doc

def create_core_site(master_node_ip):
    doc, config_element = get_config_document()
    #doc, dfs_name_property =  create_property("dfs.name.dir", "/tmp/matlab/name", doc)
    config_element.appendChild(create_property("fs.default.name", master_node_ip+":55450", doc))
    return doc

def write_xmldoc_to_screen(doc):
    prettyString  = doc.toprettyxml();
    print prettyString;
    
def write_xmldoc_to_file(doc, filename):
    prettyString  = doc.toprettyxml();
    xml_file = open(filename,"w")
    xml_file.write(prettyString)
    xml_file.close()

# local_base_dir - dir to store 
def generate_hadoop_configs(nodes, local_base_dir, conf_dir):
    if local_base_dir:
        local_base_dir = local_base_dir + os.sep
    if conf_dir:
        conf_dir = conf_dir + os.sep        
        
    master_node = nodes[0]
    
    masters_file_name = conf_dir+"masters"
    masters_file = open(masters_file_name,"w")
    masters_file.write(master_node)
    masters_file.close()
    
    slaves_file_name = conf_dir+"slaves"
    slaves_file = open(slaves_file_name,"w")
    slaves_file.writelines(x+'\n' for x in nodes[1:])
    slaves_file.close()
    
    hdfs_site_doc = create_hdfs_site(local_base_dir+"name",local_base_dir+"data")
    write_xmldoc_to_file(hdfs_site_doc, conf_dir+"hdfs-site.xml")
    
    core_site_doc = create_core_site(master_node)
    write_xmldoc_to_file(core_site_doc, conf_dir+"core-site.xml")
    
    mapred_site_doc =  create_mapred_site(master_node,local_base_dir+"local")
    write_xmldoc_to_file(mapred_site_doc, conf_dir+"mapred-site.xml")
    
    return hdfs_site_doc, core_site_doc, mapred_site_doc

def prepare_file_system(nodes, local_base_dir):
    for node in nodes :
        subprocess.call("ssh "+node+" rm -rf "+local_base_dir, shell=True)
        subprocess.call("ssh "+node+" mkdir -p "+local_base_dir, shell=True)
        subprocess.call("ssh "+node+" mkdir "+local_base_dir+"/logs", shell=True)
        
# unify list order preserving
def unify(seq):  
    checked = [] 
    for e in seq: 
        if e not in checked: 
            checked.append(e) 
    return checked

def process_ips(nodes):
    # filter duplicates
    nodes = unify(nodes)
    for index, node in enumerate(nodes):
        node  = node.rstrip()
        nodes[index] = node.replace("i", "172.29.200.", 1);        
    return nodes

from optparse import OptionParser
parser = OptionParser()
(options, args) = parser.parse_args()

if (len(args) == 3):
    #print args
    nodes_file = open(args[0],"r")
    nodes = nodes_file.readlines()
    local_base_dir = args[1]
    hadoop_conf_dir = args[2]
    
    nodes = process_ips(nodes)
    generate_hadoop_configs(nodes, local_base_dir, hadoop_conf_dir)
    prepare_file_system(nodes, local_base_dir)
    
else :
    print "Invalid Arguments"

#nodes = nodes_file.readlines()
#odes = process_ips(nodes)
#print nodes


#nodes = ["129.1.1.1","129.1.1.2","129.1.1.3","129.1.1.4"]
#generate_hadoop_configs(nodes, "/tmp/test1", "temp")
#write_xmldoc_to_screen(hdfs_site_doc)
