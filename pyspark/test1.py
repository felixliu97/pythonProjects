# Imports
from pyspark.sql import SparkSession

# Create SparkSession
spark = SparkSession.builder.appName('PySpark Sample DataFrame').getOrCreate()

# Define Schema
schema = ["Language", "Version"]

# Prepare Data
data = (("Jdk","17.0.12"), ("Python", "3.13.1"), ("Spark", "3.5.4"),   \
    ("Hadoop", "3.3 and later"), ("Winutils", "3.3"),  \
  )

# Create DataFrame
df = spark.createDataFrame(data, schema)
df.printSchema()
df.show(5,truncate=False)