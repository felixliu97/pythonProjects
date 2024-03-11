import re, os, glob, sys, json, pyspark
from pyspark.sql.functions import *
from pyspark.context import SparkContext
from pyspark.sql.session import SparkSession
from pyspark.sql import types as T
import argparse
sc = SparkContext('local')
spark = SparkSession(sc)
spark.sparkContext.setLogLevel("WARN")

parser = argparse.ArgumentParser(
    prog='json_to_parquet.py',
    description='Converts JSONs to Parquet.'
)

parser.add_argument(
    'input_path',
    type=str,
    help='Path of input directory. (Required)'
)

parser.add_argument(
    'output_path',
    type=str,
    help='Path of output directory. (Required)'
)

parser.add_argument(
    'cols_not_to_explode',
    nargs='?',
    default=None,
    help='List of columns to not explode. (Optional)'
)