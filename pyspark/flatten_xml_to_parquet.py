import sys
import os
import click
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, ArrayType
from pyspark.sql.functions import col, explode_outer, to_json

# Unset SPARK_HOME to prevent PySpark from using incompatible system Spark versions
if 'SPARK_HOME' in os.environ:
    del os.environ['SPARK_HOME']

# Set HADOOP_HOME to CWD if not set, to avoid some Windows permission errors
if 'HADOOP_HOME' not in os.environ:
    os.environ['HADOOP_HOME'] = os.getcwd()

import re
import uuid
import json

def flatten_dataframe(df, cols_not_to_explode):
    """
    Recursively flattens a DataFrame.
    
    Args:
        df: Input DataFrame
        cols_not_to_explode: List of column names (strings) that should NOT be exploded if they are arrays.
    """
    while True:
        fields = df.schema.fields
        
        # Identify complex fields that we actually want to transform
        complex_fields = []
        for f in fields:
            if isinstance(f.dataType, StructType):
                complex_fields.append(f)
            elif isinstance(f.dataType, ArrayType):
                # Only explode if the array contains complex types (Structs or other Arrays)
                if f.name not in cols_not_to_explode:
                     complex_fields.append(f)
        
        # If nothing left to transform, we are done
        if not complex_fields:
            break
            
        cols_to_select = []
        for f in fields:
            is_target_complex = False
            if f in complex_fields:
                is_target_complex = True
            
            if not is_target_complex:
                cols_to_select.append(col(f.name))
        
        for f in complex_fields:
            if isinstance(f.dataType, StructType):
                for nested_field in f.dataType.fields:
                    cols_to_select.append(
                        col(f"{f.name}.{nested_field.name}").alias(f"{f.name}_{nested_field.name}")
                    )
            elif isinstance(f.dataType, ArrayType):
                cols_to_select.append(
                    explode_outer(col(f.name)).alias(f.name)
                )
        
        df = df.select(cols_to_select)
        
    return df

def clean_xml_content(xml_file):
    """
    Reads the XML file, fixes common issues (multiple roots, multiple declarations),
    and returns the path to a temporary cleaned XML file.
    """
    print(f"Cleaning XML file: {xml_file}...")
    with open(xml_file, "r", encoding='utf-8') as provided_file:
        orig_xml_file_data = provided_file.read()
        
    linesfound = len(orig_xml_file_data.splitlines(keepends=True))
    if linesfound > 1:
        if orig_xml_file_data.splitlines(keepends=False)[0].startswith('<?xml version'):
            if len(re.findall(r"(<\?xml[^>]+\?>)", orig_xml_file_data)) >= 2:
                # Multiple declarations found
                try:
                    first_declaration = re.findall(r"(<\?xml[^>]+\?>)", orig_xml_file_data)[0]
                except:
                    first_declaration = ''
                # Keep first declaration, wrap everything else in root, remove other declarations
                content_body = re.sub(r"(<\?xml[^>]+\?>)", "", orig_xml_file_data)
                new_xml_file_data = f"{first_declaration}\n<root>{content_body}</root>"
            else:
                # One declaration, assuming checking for multiple roots logic or just wrapping
                # Original logic: re.sub(r"(<\?xml[^>]+\?>)",r"\1<root>",orig_xml_file_data.splitlines(keepends=True)[0] + ''.join(orig_xml_file_data.splitlines(keepends=True)[1:])+'\n</root>')
                # Simpler approach: Keep decl, wrap rest in root
                lines = orig_xml_file_data.splitlines(keepends=True)
                new_xml_file_data = lines[0] + "<root>\n" + "".join(lines[1:]) + "\n</root>"
        else:
            # No declaration
            new_xml_file_data = '<root>\n' + orig_xml_file_data + '\n</root>'
    else:
        # Single line
        if orig_xml_file_data.startswith('<?xml version'):
            new_xml_file_data = re.sub(r"(<\?xml[^>]+\?>)", r"\1<root>", orig_xml_file_data) + "</root>"
        else:
            new_xml_file_data = '<root>' + orig_xml_file_data + '</root>'

    # Write to temp file
    temp_filename = f"temp_cleaned_{uuid.uuid4()}.xml"
    with open(temp_filename, "w", encoding='utf-8') as f:
        f.write(new_xml_file_data)
    
    print(f"Created temporary cleaned file: {temp_filename}")
    return temp_filename

import xml.etree.ElementTree as ET

def elem_to_dict(elem, strip_tag_namespaces=True):
    """
    Converts an ElementTree Element into a dictionary.
    Handles nested elements, attributes, and text.
    Similar logic to what spark-xml does but simplified.
    """
    d = {}
    
    # helper to strip namespaces
    def get_tag(tag):
        if strip_tag_namespaces and '}' in tag:
            return tag.split('}', 1)[1]
        return tag

    # Attributes
    if elem.attrib:
        for k, v in elem.attrib.items():
            # spark-xml usually prefixes attributes with _
            d[f"_{get_tag(k)}"] = v

    # Children
    children = list(elem)
    if children:
        for child in children:
            child_tag = get_tag(child.tag)
            child_dict = elem_to_dict(child, strip_tag_namespaces)
            
            # If child has no keys (was text only), use its value
            # Actually elem_to_dict returns a dict or value?
            # Let's make it always return a dict looking structure unless leaf
            
            # Handling repeated tags -> list
            if child_tag in d:
                # If existing is not a list, convert to list
                if not isinstance(d[child_tag], list):
                    d[child_tag] = [d[child_tag]]
                d[child_tag].append(child_dict)
            else:
                d[child_tag] = child_dict
    
    # Text
    text = elem.text.strip() if elem.text else ""
    if text:
        if children or elem.attrib:
            # If mixed content or attribs, text usually goes to specific key like _VALUE
            # or just ignored/handled differently. spark-xml default is _VALUE for mixed.
            # But let's check if we just have a leaf node with attribs.
            if not children:
                 # leaf with attribs: usually tag: {_attr: val, #value: text}
                 # spark-xml uses _VALUE by default for text content if schema is struct
                 d["_VALUE"] = text
        else:
            # Leaf node, no attribs, no children -> just return text
            return text
            
    return d

def parse_xml_to_list(xml_file, row_tag):
    """
    Parses the XML file and extracts elements matching matching row_tag.
    Returns a list of dictionaries.
    """
    data_list = []
    
    # Use iterparse to handle potentially larger files better than parse()
    try:
        context = ET.iterparse(xml_file, events=("end",))
        for event, elem in context:
            # Strip namespace for comparison logic
            tag_name = elem.tag
            if '}' in tag_name:
                tag_name = tag_name.split('}', 1)[1]
            
            if tag_name == row_tag:
                data_list.append(elem_to_dict(elem))
                elem.clear() # clear memory
    except Exception as e:
        print(f"Error parsing XML with ElementTree: {e}")
        raise e
        
    return unify_data_structure(data_list)

def unify_data_structure(data_list):
    """
    Scans the list of dictionaries to find fields that are lists in *some* rows.
    Then updates *all* rows to ensure those fields are always lists.
    Fixes Spark schema inference errors for mixed single/list content.
    """
    list_paths = set()

    def find_lists(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if isinstance(v, list):
                    list_paths.add(new_path)
                    for item in v:
                        find_lists(item, new_path)
                else:
                    find_lists(v, new_path)
        elif isinstance(obj, list):
            # Should not happen if called correctly on dicts/inner lists recursively
            for item in obj:
                find_lists(item, path)

    # Pass 1: Identify all paths that are lists anywhere
    for row in data_list:
        find_lists(row)

    def enforce_lists(obj, path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}" if path else k
                if new_path in list_paths:
                    if not isinstance(v, list):
                        # Convert single item to list
                        obj[k] = [v]
                        # Recurse on the new list item
                        enforce_lists(obj[k][0], new_path)
                    else:
                        # Already a list, recurse on elements
                        for item in v:
                            enforce_lists(item, new_path)
                else:
                    enforce_lists(v, new_path)
        elif isinstance(obj, list):
             for item in obj:
                enforce_lists(item, path)

    # Pass 2: Enforce list types
    for row in data_list:
        enforce_lists(row)
        
    return data_list

def detect_row_tag(xml_file):
    """
    Scans the XML file to detect the most appropriate row_tag.
    Heuristic:
    - Finds the root element.
    - Counts the occurrences of its immediate children.
    - If any child appears > 1 times, returns the most frequent child tag.
    - If all children are unique or no children, returns the root tag.
    """
    print(f"Detecting row tag for {xml_file}...")
    counts = {}
    root_tag = None
    
    try:
        # Use iterparse to stream
        context = ET.iterparse(xml_file, events=("start",))
        depth = 0
        root_elem = None
        
        for event, elem in context:
            # Strip namespace
            tag = elem.tag
            if '}' in tag:
                tag = tag.split('}', 1)[1]
            
            if root_tag is None:
                root_tag = tag
                root_elem = elem
                depth = 1 # Root is depth 1 effectively here? 
                # Actually logic is simpler: root is the first element found by iterparse start
                continue

            # We only care about immediate children of root
            # But iterparse is depth-first? No, start event order is document order.
            # To know if it is a direct child of root, we need depth tracking or check parent?
            # iterparse doesn't give parent.
            # But we can assume that if we are iterating start events:
            # 1. Root starts.
            # 2. Child1 starts.
            # 3. Grandchild starts...
            # This is hard to track depth with just 'start' events without 'end'.
            # Let's use start and end.
            pass
            
    except Exception:
        pass
        
    # Re-implement with start/end for depth tracking
    try:
        context = ET.iterparse(xml_file, events=("start", "end"))
        depth = 0
        root_tag = None
        counts = {}
        
        # Limit scan to avoid reading massive files entirely if clear pattern emerges?
        # Let's scan up to X elements? No, correctness first.
        
        for event, elem in context:
            if event == "start":
                depth += 1
                if depth == 1:
                    # This is the root
                    tag = elem.tag
                    if '}' in tag:
                        tag = tag.split('}', 1)[1]
                    root_tag = tag
                elif depth == 2:
                    # This is a direct child of root
                    tag = elem.tag
                    if '}' in tag:
                        tag = tag.split('}', 1)[1]
                    counts[tag] = counts.get(tag, 0) + 1
            elif event == "end":
                depth -= 1
                elem.clear() # Free memory
                
        # Heuristic:
        if not counts:
            # No children, or empty
            print(f"  Detected tags: None. Defaulting to root: {root_tag}")
            return root_tag
            
        # Find most frequent child
        most_frequent = max(counts, key=counts.get)
        count = counts[most_frequent]
        
        print(f"  Detected root: {root_tag}")
        print(f"  Immediate children counts: {counts}")
        
        if count > 1:
            print(f"  Selecting repeating child '{most_frequent}' as row tag.")
            return most_frequent
        else:
            print(f"  No repeating children found. Selecting root '{root_tag}' as row tag.")
            return root_tag

    except Exception as e:
        print(f"Error detecting row tag: {e}")
    return 'root' # Fallback

@click.command()
@click.option('--file_path', required=True, type=str, help='Path to the input XML file.')
@click.option('--row_tag', default=None, required=False, help='The XML tag to identify rows. If not provided, will be auto-detected.')
@click.option('--mode', type=click.Choice(['cartesian', 'nested']), default='cartesian', help='Flattening mode: "cartesian" (fully flat) or "nested" (keep structure).')
@click.option('--cols_not_to_explode', default='', help='Comma-separated list of columns to preserve as arrays.')
@click.option('--clean', is_flag=True, default=False, help='Pre-process XML to fix multiple roots or declarations (WARNING: reads entire file into memory).')
def main(file_path, row_tag, cols_not_to_explode, mode, clean):
    """
    Flattens an XML file to Parquet, exploding arrays and flattening structs.
    """
    output_path = file_path.replace(".xml", "") + "_flat.parquet"
    
    # Pre-process cleaning if requested
    temp_cleaned_file = None
    temp_json_file = None
    input_path_to_use = file_path
    
    if clean:
        try:
            temp_cleaned_file = clean_xml_content(file_path)
            input_path_to_use = temp_cleaned_file
        except Exception as e:
            print(f"Error cleaning XML: {e}")
            return

    # Auto-detect row_tag if not provided
    if not row_tag:
        try:
            row_tag = detect_row_tag(input_path_to_use)
            print(f"Auto-detected row_tag: {row_tag}")
        except Exception as e:
            print(f"Error detecting row_tag: {e}")
            return # Or default to 'root'?
    
    # Parse the exclusion list
    if cols_not_to_explode:
        exclude_list = [x.strip() for x in cols_not_to_explode.split(',')]
    else:
        exclude_list = []
        
    print(f"Input File: {file_path}")
    print(f"Row Tag: {row_tag}")
    print(f"Output File: {output_path}")

    spark = SparkSession.builder \
        .appName("DynamicXmlFlatten") \
        .master("local[*]") \
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    try:
        # Use custom parser instead of spark-xml
        print(f"Parsing XML using custom python parser (row_tag='{row_tag}')...")
        data_rows = parse_xml_to_list(input_path_to_use, row_tag)
        
        if not data_rows:
            print(f"\n[WARNING] No rows found for tag '{row_tag}'.")
            # If we cleaned it, maybe row_tag is nested under 'root'? 
            # But parse_xml_to_list searches by tag name anywhere, so it should be fine.
            if temp_cleaned_file and os.path.exists(temp_cleaned_file):
                 os.remove(temp_cleaned_file)
            return

        # Infer schema and create DataFrame
        # write to temp json file to avoid "Python worker failed to connect back" on Windows
        print("Writing parsed data to temp JSON for Spark inference...")
        temp_json_file = f"temp_data_{uuid.uuid4()}.json"
        with open(temp_json_file, 'w', encoding='utf-8') as f:
            for row in data_rows:
                f.write(json.dumps(row) + "\n")
        
        df = spark.read.json(temp_json_file)
            
    except Exception as e:
        print(f"Error reading/parsing XML: {e}")
        # Clean up temp files if exist
        if temp_cleaned_file and os.path.exists(temp_cleaned_file):
            os.remove(temp_cleaned_file)
        if temp_json_file and os.path.exists(temp_json_file):
             os.remove(temp_json_file)
        return

    print("\n--- Original Schema ---")
    df.printSchema()

    if len(df.schema.fields) == 0:
        print("\n[WARNING] The DataFrame schema is empty. This usually means the 'row_tag' is incorrect.")
        print(f"Current row_tag: '{row_tag}'")
        print("Please check your XML file and specify the correct identifying tag for rows using --row_tag.")
        if temp_cleaned_file and os.path.exists(temp_cleaned_file):
             os.remove(temp_cleaned_file)
        return

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

    # print("\n--- Data Preview ---")
    # flat_df.show(n=20, truncate=False)

    print(f"Writing to {output_path} (via Pandas)...")
    try:
        if os.path.exists(output_path):
            if os.path.isdir(output_path):
                import shutil
                shutil.rmtree(output_path)
            else:
                os.remove(output_path)
        
        # Convert to Pandas and write to Parquet
        # Using pyarrow for Parquet support
        flat_df.toPandas().to_parquet(output_path, engine='pyarrow', index=False)
        print("Done.")
    except Exception as e:
        print(f"Error writing Parquet: {e}")
    finally:
        # Clean up temp file
        if temp_cleaned_file and os.path.exists(temp_cleaned_file):
            print(f"Removing temp file: {temp_cleaned_file}")
            try:
                os.remove(temp_cleaned_file)
            except:
                pass
        if temp_json_file and os.path.exists(temp_json_file):
            try:
                os.remove(temp_json_file)
            except:
                pass

if __name__ == "__main__":
    main()
