import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np
import re, os, glob, sys, pyspark
from io import BytesIO
from pyspark.sql.functions import *
from pyspark.context import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql import types as T
import pyspark.sql.functions as F
from pyspark import SparkContext, SparkConf
# sys.setrecursionlimit(100000000)
# conf = pyspark.SparkConf().setMaster("local").set("spark.driver.extraJavaOptions","-Xss256M")
# sc = SparkContext.getOrCreate(conf=conf)
# spark = SparkSession(sc)
# spark.sparkContext.setLogLevel("WARN")

current_path = os.getcwd()
xml_file = "PurchaseOrders.xml"

def get_the_root(xml_file):
    with open(xml_file,"r") as provided_file:
        orig_xml_file_data = provided_file.read()
        linesfound = len(orig_xml_file_data.splitlines(keepends=True))
        if linesfound > 1:
            if orig_xml_file_data.splitlines(keepends=False)[0].startswith('<?xml version'):
                if len(re.findall(r"(<\?xml[^>]+\?>)"), orig_xml_file_data) >= 2:
                    try:
                        first_declaration = re.findall(r"(<\?xml[^>]+\?>)", orig_xml_file_data)[0]
                    except:
                        first_declaration = ''
                    new_xml_file_data = first_declaration+'\n<root>'+re.sub(r"(<\?xml[^>]+\?>)","",orig_xml_file_data+"</root>")
                else:
                    new_xml_file_data = re.sub(r"(<\?xml[^>]+\?>)",r"\1<root>",orig_xml_file_data.splitlines(keepends=True)[0] + ''.join(orig_xml_file_data.splitlines(keepends=True)[1:])+'\n</root>')
            else:
                new_xml_file_data = '<root>\n'+''.join(orig_xml_file_data.splitlines(keepends=True))+'\n</root>'
        else:
            if orig_xml_file_data.startswith('<?xml version'):
                new_xml_file_data = re.sub(r"(<\?xml[^>]+\?>)",r"\1<root>", orig_xml_file_data) + "</root>"
            else:
                new_xml_file_data = '<root>'+orig_xml_file_data+'</root>'
    tree = ET.ElementTree(ET.fromstring(new_xml_file_data))
    try:
        my_namespaces = dict([node for (_, node) in ET.iterparse(BytesIO(new_xml_file_data.encode('utf-8')), events=['start-ns'])])
    except:
        my_namespaces = None
    return tree.getroot(), my_namespaces

def convert_xml_to_df(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        try:
            my_namespaces = dict([node for (_, node) in ET.iterparse(xml_file, events=['start-ns'])])
        except:
            my_namespaces = None
        print(f"my_namespaces:{my_namespaces}")
        if len(root) > 1 and root[0].tag != root[1].tag:
            root, my_namespaces = get_the_root(xml_file)
    except ET.ParseError as er:
        if 'junk after document element' in str(er):
            root, my_namespaces = get_the_root(xml_file)
        else:
            print(er)
            raise Exception("parsing error")

xml_path = os.path.join(current_path, xml_file)        
convert_xml_to_df(xml_path)
# panddf, my_namespaces = convert_xml_to_df(xml_path)
# print(f"panddf {panddf}")
# print(f"my_namespaces: {my_namespaces}")