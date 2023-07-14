from pyspark import SparkContext, SparkConf
from pyspark.sql import SparkSession, SQLContext
import os
import xml.etree.ElementTree as ET
import pandas as pd

conf = SparkConf() \
    .setAppName("Example") \
    .setMaster("local") \
    .set("spark.driver.extraClassPath","C:/pyspark/*")

sc = SparkContext.getOrCreate(conf=conf)
spark = SparkSession(sc)