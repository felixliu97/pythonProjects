import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql import SparkSession

## @params: [JOB_NAME, S3_INPUT_PATH_1, S3_INPUT_PATH_2, S3_INPUT_PATH_3, S3_OUTPUT_PATH, JOIN_COLUMN]
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'S3_INPUT_PATH_1',
    'S3_INPUT_PATH_2',
    'S3_INPUT_PATH_3',
    'S3_OUTPUT_PATH',
    'JOIN_COLUMN'
])

# If no arguments provided for paths, use the user's specified defaults
bucket = "abc-test-bucket"
s3_input_1 = args.get('S3_INPUT_PATH_1', f"s3://{bucket}/archival/1.csv")
s3_input_2 = args.get('S3_INPUT_PATH_2', f"s3://{bucket}/archival/2.csv")
s3_input_3 = args.get('S3_INPUT_PATH_3', f"s3://{bucket}/archival/3.csv")
s3_output = args.get('S3_OUTPUT_PATH', f"s3://{bucket}/output/consolidated/")
join_col = args.get('JOIN_COLUMN', 'common_id')

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Load the three CSV files from S3
df1 = spark.read.option("header", "true").option("inferSchema", "true").csv(s3_input_1)
print(f"Schema for {s3_input_1}:")
df1.printSchema()

df2 = spark.read.option("header", "true").option("inferSchema", "true").csv(s3_input_2)
print(f"Schema for {s3_input_2}:")
df2.printSchema()

df3 = spark.read.option("header", "true").option("inferSchema", "true").csv(s3_input_3)
print(f"Schema for {s3_input_3}:")
df3.printSchema()

# Standard Spark SQL join
df_joined = df1.join(df2, join_col).join(df3, join_col)

# Write the result to S3 in CSV format
df_joined.write.mode("overwrite").option("header", "true").csv(s3_output)

job.commit()
