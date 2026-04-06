# Snowflake Cheatsheet

## 1. CONTEXT & CONNECTION

``` sql
-- Set context
USE ROLE sysadmin;
USE WAREHOUSE compute_wh;
USE DATABASE my_db;
USE SCHEMA my_schema;

-- Show current context
SELECT CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();
```

## 2. WAREHOUSE MANAGEMENT

``` sql
-- Create Warehouse
CREATE WAREHOUSE my_wh
WITH WAREHOUSE_SIZE = 'X-SMALL'
AUTO_SUSPEND = 60 -- Seconds
AUTO_RESUME = TRUE
INITIALLY_SUSPENDED = TRUE;

-- Resize Warehouse (Instant)
ALTER WAREHOUSE my_wh SET WAREHOUSE_SIZE = 'LARGE';

-- Suspend/Resume
ALTER WAREHOUSE my_wh SUSPEND;
ALTER WAREHOUSE my_wh RESUME;
```

## 3. DATABASES, SCHEMAS & TABLES

``` sql
-- Create Database
CREATE DATABASE IF NOT EXISTS my_db;

-- Create Schema
CREATE SCHEMA IF NOT EXISTS my_schema;

-- Create Table
CREATE TABLE my_table (
    id INTEGER,
    data STRING,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Clone Table (Zero-Copy Clone)
CREATE TABLE my_table_clone CLONE my_table;

-- Transient Table (No Fail-safe, lower cost)
CREATE TRANSIENT TABLE my_transient_table (id INT);

-- Temporary Table (Session only)
CREATE TEMPORARY TABLE my_temp_table (id INT);
```

## 4. DATA LOADING (COPY INTO)

``` sql
-- 1. Create File Format
CREATE OR REPLACE FILE FORMAT my_csv_format
TYPE = 'CSV'
FIELD_DELIMITER = ','
SKIP_HEADER = 1;

-- 2. Create Stage (Internal or External S3/Azure/GCP)
CREATE OR REPLACE STAGE my_stage
FILE_FORMAT = my_csv_format;

-- 3. Copy Data
COPY INTO my_table
FROM @my_stage/data.csv
ON_ERROR = 'CONTINUE'; -- Options: ABORT_STATEMENT, SKIP_FILE, CONTINUE
```

## 5. SEMI-STRUCTURED DATA (JSON)

``` sql
-- Create table with VARIANT column
CREATE TABLE json_table (json_data VARIANT);

-- Query JSON
-- Data: {"id": 1, "details": {"color": "red"}}
SELECT
    json_data:id::INTEGER AS id,
    json_data:details.color::STRING AS color
FROM json_table;

-- Flatten JSON Array
-- Data: {"items": [{"name": "a"}, {"name": "b"}]}
SELECT
    value:name::STRING
FROM json_table,
LATERAL FLATTEN(input => json_data:items);
```

## 6. TIME TRAVEL & FAIL-SAFE

``` sql
-- Query data as of 10 minutes ago
SELECT * FROM my_table AT(OFFSET => -60*10);

-- Query data before a specific query ID
SELECT * FROM my_table BEFORE(STATEMENT => '8e5d0ca9-005e-44e6-b858-a8f5b37c5726');

-- Undrop (Restore) Table
UNDROP TABLE my_table;

-- Set Retention Period (Days)
ALTER TABLE my_table SET DATA_RETENTION_TIME_IN_DAYS = 90;
```

## 7. CACHING

``` sql
-- Result Cache (24 hours, exact query match)
-- Metadata Cache (Near instant counts)
SELECT COUNT(*) FROM my_table; -- Uses metadata cache

-- Warehouse Cache (Local Disk / SSD)
-- Data loaded into warehouse SSDs during processing
```

## 8. SYSTEM FUNCTIONS

``` sql
-- Generate Cluster Key info
SELECT SYSTEM$CLUSTERING_INFORMATION('my_table');

-- Current User
SELECT CURRENT_USER();
```

## 9. USER & ROLE MANAGEMENT

``` sql
-- Create Role
CREATE ROLE my_role;

-- Grant Privileges
GRANT USAGE ON DATABASE my_db TO ROLE my_role;
GRANT SELECT ON ALL TABLES IN SCHEMA my_db.my_schema TO ROLE my_role;

-- Grant Role to User
GRANT ROLE my_role TO USER my_user;
```

## 10. DATA SHARING (SECURE DATA SHARING)

``` sql
-- Create Share
CREATE SHARE my_share;

-- Grant Privileges to Share
GRANT USAGE ON DATABASE my_db TO SHARE my_share;
GRANT USAGE ON SCHEMA my_db.my_schema TO SHARE my_share;
GRANT SELECT ON TABLE my_db.my_schema.my_table TO SHARE my_share;

-- Add Account to Share
ALTER SHARE my_share ADD ACCOUNTS = xy12345; -- Account Locator

-- Show Shares
SHOW SHARES;
```

## 11. ACCOUNT USAGE & MONITORING

``` sql
-- Query Account Usage (SNOWFLAKE database)
-- Note: Latency of ~45 mins to 2 hours
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
WHERE START_TIME > DATEADD(hour, -1, CURRENT_TIMESTAMP())
ORDER BY TOTAL_ELAPSED_TIME DESC;

-- Query Login History
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
ORDER BY EVENT_TIMESTAMP DESC;

-- Storage Usage
SELECT * FROM SNOWFLAKE.ACCOUNT_USAGE.STORAGE_USAGE
ORDER BY USAGE_DATE DESC;

-- Information Schema (Real-time, less history)
SELECT * FROM INFORMATION_SCHEMA.QUERY_HISTORY
ORDER BY START_TIME DESC;
```

## 12. ADVANCED OBJECTS (STREAMS & TASKS)

``` sql
-- Create Stream (CDC - Change Data Capture)
CREATE STREAM my_stream ON TABLE my_table;

-- Query Stream
SELECT * FROM my_stream; -- Shows METADATA$ACTION, METADATA$ISUPDATE, etc.

-- Create Task (Scheduled SQL)
CREATE TASK my_task
  WAREHOUSE = compute_wh
  SCHEDULE = '5 MINUTE'
AS
  INSERT INTO my_target_table SELECT * FROM my_stream WHERE METADATA$ACTION = 'INSERT';

-- Resume Task (Created in suspended state)
ALTER TASK my_task RESUME;
```

## 13. SNOWPARK & ML & CORTEX

``` sql
-- Snowpark (Python/Java/Scala DataFrame API)
-- (Conceptual: Use Python worksheet or local environment)
-- import snowflake.snowpark as snowpark
-- session.table("my_table").filter(col("id") > 10).collect()

-- Stored Procedures (Python)
CREATE OR REPLACE PROCEDURE my_proc(input_str STRING)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'main'
AS
$$
def main(session, input_str):
    return f"Hello {input_str}"
$$;

-- Snowflake Cortex (LLM Functions)
-- SELECT SNOWFLAKE.CORTEX.COMPLETE('llama2-70b-chat', 'Tell me a joke');
-- SELECT SNOWFLAKE.CORTEX.SUMMARIZE(email_body);
```

## 14. SECURITY & GOVERNANCE

``` sql
-- Dynamic Data Masking
CREATE OR REPLACE MASKING POLICY email_mask AS (val string) RETURNS string ->
  CASE
    WHEN current_role() IN ('ANALYST') THEN val
    ELSE '***MASKED***'
  END;

ALTER TABLE my_table MODIFY COLUMN data SET MASKING POLICY email_mask;

-- Row Access Policies
CREATE OR REPLACE ROW ACCESS POLICY region_policy AS (region_code varchar) RETURNS BOOLEAN ->
  CASE
    WHEN current_role() = 'ADMIN' THEN TRUE
    ELSE region_code = 'US'
  END;

ALTER TABLE my_table ADD ROW ACCESS POLICY region_policy ON (data);

-- Network Policies (IP Whitelisting)
CREATE NETWORK POLICY my_policy ALLOWED_IP_LIST=('192.168.1.0/24');
ALTER ACCOUNT SET NETWORK POLICY = my_policy;

-- Data Classification & Tagging
CREATE TAG cost_center;
ALTER TABLE my_table SET TAG cost_center = 'finance';
```

## 15. PERFORMANCE OPTIMIZATION

``` sql
-- Materialized Views (Pre-computed results)
CREATE MATERIALIZED VIEW my_mv AS
SELECT id, COUNT(*) as cnt FROM my_table GROUP BY id;

-- Search Optimization Service (Point lookups)
ALTER TABLE my_table ADD SEARCH OPTIMIZATION;

-- Query Acceleration Service (Offload processing)
ALTER WAREHOUSE my_wh SET ENABLE_QUERY_ACCELERATION = TRUE;
```

## 16. TABLE TYPES & STORAGE

``` sql
-- Iceberg Tables (Open Table Format)
CREATE ICEBERG TABLE my_iceberg
  CATALOG = 'SNOWFLAKE'
  EXTERNAL_VOLUME = 'my_vol'
  BASE_LOCATION = 'my_path/';

-- Hybrid Tables (Unistore - OLTP)
CREATE HYBRID TABLE my_hybrid (
    id INT PRIMARY KEY,
    name STRING
);
```

## 17. REPLICATION & FAILOVER

``` sql
-- Enable Replication for Database
ALTER DATABASE my_db ENABLE REPLICATION TO ACCOUNTS xy12345;

-- Failover Group (Replicate multiple objects)
CREATE FAILOVER GROUP my_fg
  OBJECT_TYPES = DATABASES, WAREHOUSES, ROLES
  ALLOWED_ACCOUNTS = xy12345
  REPLICATION_SCHEDULE = '10 MINUTE';
```

## 18. RESOURCE MONITORS

``` sql
-- Create Monitor (Limit credit usage)
CREATE RESOURCE MONITOR my_monitor WITH CREDIT_QUOTA = 100
TRIGGERS ON 90 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE my_wh SET RESOURCE_MONITOR = my_monitor;
```

## 19. OTHER FEATURES

``` sql
-- Snowpipe Auto-Ingest (Continuous Loading)
CREATE PIPE my_pipe AUTO_INGEST = TRUE AS
COPY INTO my_table FROM @my_stage;

-- Data Clean Rooms (Conceptual)
-- Secure sharing environment without exposing raw data.

-- Snowflake Marketplace
-- Access 3rd party data sets directly in your account.

-- Tri-Secret Secure
-- Double encryption (Snowflake key + Customer managed key).
```

