# Pyspark Cheatsheet

``` bash
#!/bin/bash
```

## 0. SETUP & KERNEL

``` bash
# Install IPyKernel for Jupyter
python -m ipykernel install --user --name PYSPARK_KERNEL
```

## 1. INITIALIZING SPARK SESSION

``` bash
# Python code to initialize SparkSession
cat << 'EOF'
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("MySparkApp") \
    .config("spark.executor.memory", "2g") \
    .getOrCreate()
EOF
```

## 2. LOADING DATA

``` bash
# Read CSV
df = spark.read.csv("path/to/file.csv", header=True, inferSchema=True)

# Read JSON
df = spark.read.json("path/to/file.json")

# Read Parquet
df = spark.read.parquet("path/to/file.parquet")

# Read Text
df = spark.read.text("path/to/file.txt")
```

## 3. BASIC DATAFRAME OPERATIONS

``` bash
# Show data
df.show(5)
df.show(5, truncate=False)

# Print schema
df.printSchema()

# Select columns
df.select("col1", "col2")

# Rename column
df.withColumnRenamed("old_name", "new_name")

# Add/Update column
from pyspark.sql.functions import col, lit
df.withColumn("new_col", col("existing_col") * 2)
df.withColumn("constant_col", lit(10))

# Drop column
df.drop("col_to_drop")

# Filter / Where
df.filter(col("age") > 21)
df.where("age > 21")

# Sort / Order By
df.sort("age", ascending=False)
df.orderBy(col("age").desc())
```

## 4. AGGREGATIONS & GROUPING

``` bash
# Group By and Count
df.groupBy("department").count()

# Multiple Aggregations
from pyspark.sql.functions import avg, max, min
df.groupBy("department").agg(
    avg("salary").alias("avg_salary"),
    max("salary").alias("max_salary")
)

# Distinct values
df.select("department").distinct()
```

## 5. JOINS

``` bash
# Inner Join
df1.join(df2, df1.id == df2.id, "inner")

# Left Join
df1.join(df2, on="id", how="left")
```

## 6. SQL QUERIES

``` bash
# Register Temp View
df.createOrReplaceTempView("people")

# Run SQL
sql_df = spark.sql("SELECT * FROM people WHERE age > 21")
```

## 7. WINDOW FUNCTIONS

``` bash
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number

windowSpec = Window.partitionBy("department").orderBy(col("salary").desc())
df.withColumn("rank", row_number().over(windowSpec))
```

## 8. UDFs (USER DEFINED FUNCTIONS)

``` bash
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

def upper_case(str):
    return str.upper()

upper_case_udf = udf(lambda z: upper_case(z), StringType())
df.select(upper_case_udf("name"))
```

## 9. WRITING DATA

``` bash
# Write to CSV
df.write.csv("output/path", header=True, mode="overwrite")

# Write to Parquet
df.write.parquet("output/path", mode="append")

# Partition By
df.write.partitionBy("year", "month").parquet("output/path")
```

## 10. RDD OPERATIONS (Legacy but useful)

``` bash
rdd = df.rdd
rdd.map(lambda x: x[0]).collect()
```

## 11. ADVANCED: PERFORMANCE & PARTITIONING

``` bash
# Repartition: Increases or decreases partitions, performs full shuffle
df_repartitioned = df.repartition(10)
df_repartitioned = df.repartition(col("category")) # Repartition by column

# Coalesce: Decreases partitions ONLY, minimizes shuffle (no full shuffle)
df_coalesced = df.coalesce(1)

# Get number of partitions
df.rdd.getNumPartitions()

# Configure Shuffle Partitions (Default is 200)
spark.conf.set("spark.sql.shuffle.partitions", "50")
```

## 12. ADVANCED: BROADCAST JOIN

``` bash
# Broadcast Join: Optimizes join when one side is small (sends copy to all nodes)
from pyspark.sql.functions import broadcast

# Force broadcast of the smaller dataframe (df_small)
df_large.join(broadcast(df_small), "id")

# Configure auto-broadcast threshold (Default 10MB, set to -1 to disable)
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "20971520") # 20MB
```

## 13. ADVANCED: CACHING & PERSISTENCE

``` bash
# Cache: Stores in memory (MEMORY_AND_DISK by default for DF)
df.cache()

# Persist: Allows specifying storage level
from pyspark import StorageLevel
df.persist(StorageLevel.MEMORY_ONLY)
df.persist(StorageLevel.DISK_ONLY)

# Unpersist: Remove from memory/disk
df.unpersist()
```

## 14. ADVANCED: DEBUGGING & EXPLAIN

``` bash
# Explain Plan: Shows physical and logical plans
df.explain()
df.explain(True) # Extended mode

# Check for skew (count records per partition)
from pyspark.sql.functions import spark_partition_id
df.groupBy(spark_partition_id()).count().show()
```

