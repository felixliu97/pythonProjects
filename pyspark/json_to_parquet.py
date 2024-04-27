from pyspark.sql import SparkSession
from pyspark.sql import types as T
from pyspark.sql.functions import *
import os, click

sc = SparkContext('local')
spark = SparkSession(sc)
spark.sparkContext.setLogLevel("WARN")

def flatten_df(indf, cols_not_to_explode):
    df = indf
    if cols_not_to_explode:
        complex_cols = dict([(field.name, field.dataType) for field in df.schema.fields if (isinstance(field.dataType, T.StructType) or isinstance(field.dataType, T.ArrayType)) and field.name.lower() not in cols_not_to_explode])
    else:
        complex_cols = dict([(field.name, field.dataType) for field in df.schema.fields if (isinstance(field.dataType, T.StructType) or isinstance(field.dataType, T.ArrayType))])
 
    if len(complex_cols) > 0:
        col_name = list(complex_cols.keys())[0]
        if isinstance(complex_cols[col_name], T.ArrayType):
            df = df.withColumn(col_name, explode_outer(col_name))
            return flatten_df(df, cols_not_to_explode)
        elif isinstance(complex_cols[col_name], T.StructType):
            df = df.select("*", *[col(col_name + "." + field.name).alias(col_name + "_" + field.name) for field in complex_cols[col_name].fields]).drop(col_name)
            return flatten_df(df, cols_not_to_explode)
    else:
        return df

"""
Command line interface for converting a JSON file to a Parquet file.

Args:
    mode (str): The mode of flattening to apply to the DataFrame. Must be either "cartesian" or "nested". Defaults to "cartesian".
    cols_not_to_explode (str): Comma-separated list of columns to exclude from exploding. Defaults to an empty string.

Returns:
    None

Raises:
    Exception: If an error occurs during the conversion process.

Example:
    $ python json_to_parquet.py --mode cartesian --cols_not_to_explode col1,col2
"""
@click.command()
@click.option("--mode", default="cartesian", required=False, type=click.Choice(["cartesian", "nested"]), help="Mode of flattening")
@click.option("--cols_not_to_explode", default="", required=False, help="Columns to exclude from exploding")
def main(mode, cols_not_to_explode):
    print("json_to_parquet.py started.")

    try:
        input_path = os.path.join(os.getcwd(), "input.json")
        df = spark.read.option("multiLine", "true").option("mode", "FAILFAST").option("primitivesAsString", "true").option("inferSchema", "false").json(input_path)
        print("DataFrame loaded successfully.")
        df.printSchema()
        if mode == "cartesian":
            flat_df = flatten_df(df, cols_not_to_explode.split(","))
        elif mode == "nested":
            flat_df = df
        print("Flattened DataFrame:")
        flat_df.printSchema()

        output_path = os.path.join(os.getcwd(), "output")
        flat_df.coalesce(1).write.mode("overwrite").parquet(output_path)
        print("DataFrame written to Parquet file successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()