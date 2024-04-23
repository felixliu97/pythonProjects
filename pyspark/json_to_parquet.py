from pyspark.sql import SparkSession
from pyspark.sql.functions import col, explode, explode_outer
from pyspark.sql.types import StructType
import os

def flatten_df(df, prefix=""):
    flat_cols = []
    complex_cols = []

    for field in df.schema.fields:
        if isinstance(field.dataType, StructType):
            complex_cols.append(field.name)
        else:
            flat_cols.append(col(f"{prefix}{field.name}").alias(f"{prefix}{field.name}"))

    for col_name in complex_cols:
        sub_df = df.select(col_name + ".*")
        flat_sub_df = flatten_df(sub_df, prefix=col_name + "_")
        flat_cols.extend(flat_sub_df.columns)

    if complex_cols:
        df = df.select(*flat_cols)
    return df

def main():
    print("json_to_parquet.py started.")
    spark = SparkSession.builder.appName("JSON to Parquet").getOrCreate()

    try:
        current_directory = os.getcwd()
        input_path = os.path.join(current_directory, "input.json")
        df = spark.read.json(input_path, multiLine=True)
        print("DataFrame loaded successfully.")
        df.show()
        df.printSchema()
        flat_df = flatten_df(df)
        print("Flattened DataFrame:")
        flat_df.show()

        output_path = os.path.join(current_directory, "output")
        flat_df.write.mode("overwrite").parquet(output_path)
        print("DataFrame written to Parquet file successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()