import sys
import os
import click
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, ArrayType
from pyspark.sql.functions import col, explode_outer, to_json
# Unset SPARK_HOME to prevent PySpark from using incompatible system Spark versions (e.g. Spark 4.0 vs PySpark 3.5)
if 'SPARK_HOME' in os.environ:
    del os.environ['SPARK_HOME']

# Set HADOOP_HOME to CWD if not set, to avoid some Windows permission errors (though winutils might still be missing)
if 'HADOOP_HOME' not in os.environ:
    os.environ['HADOOP_HOME'] = os.getcwd()

def flatten_dataframe(df, cols_not_to_explode):

    """
    Recursively flattens a DataFrame.
    
    Args:
        df: Input DataFrame
        cols_not_to_explode: List of column names (strings) that should NOT be exploded if they are arrays.
    """
    # Normalize exclusion list to fully flattened names if possible, 
    # but initially they match schema names.
    
    # We loop until no *processable* complex types remain.
    # Processable means:
    # - Structs (always flattened)
    # - Arrays (exploded ONLY IF not in cols_not_to_explode)
    
    while True:
        fields = df.schema.fields
        
        # Identify complex fields that we actually want to transform
        complex_fields = []
        for f in fields:
            if isinstance(f.dataType, StructType):
                complex_fields.append(f)
            elif isinstance(f.dataType, ArrayType):
                # Only explode if the array contains complex types (Structs or other Arrays)
                # Arrays of primitive types (String, Int, etc) should remain as arrays.
                is_complex_element = isinstance(f.dataType.elementType, (StructType, ArrayType))
                if f.name not in cols_not_to_explode and is_complex_element:
                    complex_fields.append(f)
        
        # If nothing left to transform, we are done
        if not complex_fields:
            break
            
        # Build the select expressions for this iteration
        cols_to_select = []
        
        # 1. Pass through simple columns OR arrays we are ignoring
        for f in fields:
            is_target_complex = False
            if f in complex_fields:
                is_target_complex = True
            
            if not is_target_complex:
                cols_to_select.append(col(f.name))
        
        # 2. Transform the target complex columns
        for f in complex_fields:
            if isinstance(f.dataType, StructType):
                # Flatten Struct
                for nested_field in f.dataType.fields:
                    cols_to_select.append(
                        col(f"{f.name}.{nested_field.name}").alias(f"{f.name}_{nested_field.name}")
                    )
            elif isinstance(f.dataType, ArrayType):
                # Explode Array
                cols_to_select.append(
                    explode_outer(col(f.name)).alias(f.name)
                )
        
        # Apply selection
        df = df.select(cols_to_select)
        
    return df

    return df


@click.command()
@click.option('--file_path', required=True, type=str, help='Path to the input JSON file.')
@click.option('--mode', type=click.Choice(['cartesian', 'nested']), default='cartesian', help='Flattening mode: "cartesian" (fully flat) or "nested" (keep structure).')
@click.option('--cols_not_to_explode', default='', help='Comma-separated list of columns to preserve as arrays.')
def main(file_path, cols_not_to_explode, mode):
    """
    Flattens a JSON file to Parquet, exploding arrays and flattening structs.
    """
    output_path = file_path.replace(".json", "") + ".parquet"
    
    # Parse the exclusion list
    if cols_not_to_explode:
        exclude_list = [x.strip() for x in cols_not_to_explode.split(',')]
    else:
        exclude_list = []
        
    print(f"Input File: {file_path}")
    print(f"Output File: {output_path}")
    print(f"Mode: {mode}")
    print(f"Columns to NOT explode: {exclude_list}")

    spark = SparkSession.builder \
        .appName("DynamicJsonFlatten") \
        .master("local[*]") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    try:
        # Added strict options from original script
        df = spark.read \
            .option("multiLine", "true") \
            .option("mode", "FAILFAST") \
            .option("primitivesAsString", "true") \
            .option("inferSchema", "false") \
            .json(file_path)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    print("\n--- Original Schema ---")
    df.printSchema()

    if mode == 'cartesian':
        print("Flattening data (Cartesian Mode)...")
        flat_df = flatten_dataframe(df, exclude_list)
    else:
        print("Skipping flattening (Nested Mode)...")
        # Convert complex types to JSON strings to allow Pandas/Parquet serialization
        cols_to_select = []
        for f in df.schema.fields:
            if isinstance(f.dataType, (ArrayType, StructType)):
                # Convert to JSON string
                cols_to_select.append(to_json(col(f.name)).alias(f.name))
            else:
                cols_to_select.append(col(f.name))
        
        flat_df = df.select(cols_to_select)

    print("\n--- Final Schema ---")
    flat_df.printSchema()

    print("\n--- Data Preview ---")
    flat_df.show(n=20, truncate=False)

    # Write using Pandas to avoid Hadoop winutils/hadoop.dll requirement on Windows
    print(f"Writing to {output_path} (via Pandas)...")
    try:
        # Check if file exists and delete it because to_parquet might fail or append? 
        # Pandas to_parquet overwrites by default? 
        # Clean up existing output
        if os.path.exists(output_path):
            if os.path.isdir(output_path):
                import shutil
                shutil.rmtree(output_path)
            else:
                os.remove(output_path)
            
        flat_df.toPandas().to_parquet(output_path, engine='pyarrow', index=False)
        print("Done.")
    except Exception as e:
        print(f"Error writing Parquet: {e}")
        # Fallback to spark write just in case, or report error
        pass


if __name__ == "__main__":
    main()

