# Snowflake Cheatsheet

## 1. CONTEXT & CONNECTION
> **用途**：设置当前会话的权限上下文和资源边界（Role、Warehouse、Database、Schema）。用于资源隔离与费用控制。

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
> **用途**：管理虚拟仓库（弹性计算资源）。控制计算节点的物理规格、自动挂起/自动恢复，以最大限度减少不必要的账单支出。

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
> **用途**：管理数据目录和表结构。支持零拷贝克隆（CLONE）实现免存储费用的数据备份或测试；提供临时表（Session级别）和瞬态表（无Fail-safe机制，降低存储成本）。

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
> **用途**：将各种数据源的数据批量加载到表中。通常从内部或外部阶段区（如 S3、Azure Blob、GCS）加载数据，并自带灵活的错误捕获策略。

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
> **用途**：免 schema 查询半结构化数据。允许直接将 JSON、Avro、Parquet 加载为 `VARIANT` 列，并使用 `:` 和 `LATERAL FLATTEN` 优雅地解析和扁平化数组。

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
> **用途**：数据历史追溯与灾难恢复。时间旅行（Time Travel）支持查询或恢复过去 90 天内任意时间点的数据；故障安全（Fail-safe）由 Snowflake 官方维护，提供灾难级别的 7 天数据保护。

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
> **用途**：极速查询优化。包含三层缓存：结果缓存（24小时内未更改数据可免计算费查询）、元数据缓存（自动维护行数等基本统计信息）和 Warehouse 本地 SSD 缓存（存储热数据，减少远端对象存储 I/O）。

``` sql
-- Result Cache (24 hours, exact query match)
-- Metadata Cache (Near instant counts)
SELECT COUNT(*) FROM my_table; -- Uses metadata cache

-- Warehouse Cache (Local Disk / SSD)
-- Data loaded into warehouse SSDs during processing
```

## 8. SYSTEM FUNCTIONS
> **用途**：查询元数据及执行管理员任务的内置系统函数。例如分析表的聚簇质量、判断当前会话用户的登录环境等。

``` sql
-- Generate Cluster Key info
SELECT SYSTEM$CLUSTERING_INFORMATION('my_table');

-- Current User
SELECT CURRENT_USER();
```

## 9. USER & ROLE MANAGEMENT
> **用途**：基于角色的访问控制（RBAC）。Snowflake 遵循最低特权原则，所有权限必须授予角色，再由角色分配给用户以确立多租户架构安全。

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
> **用途**：共享实时数据。无需进行传统的数据导出与 ETL 物理复制，数据提供者可允许消费者直接实时地跨账户查询只读数据。

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
> **用途**：对计算、存储和用户活动的集中式合规性审计。主要使用 `SNOWFLAKE` 数据库下提供的只读系统账户视图。

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
> **用途**：构建持续集成与传统 ELT 数据流。`Stream` 用于捕捉底层表的变化（CDC）；`Task` 可以依赖 Cron 或前置 Task 完成异步顺序链式 SQL 调度。

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

## 13. SNOWPARK, CORTEX AI & PYTHON SPs
> **用途**：运行非 SQL 计算和内置的人工智能推理。Snowpark 为 Python 提供了 DataFrame 开发体验，Cortex 提供了托管的大语言模型与向量计算函数，同时支持完全在 Snowflake 安全沙箱中运行 Python 存储过程。

``` sql
-- 1. Snowpark Python (Conceptual API)
-- import snowflake.snowpark as snowpark
-- from snowflake.snowpark.functions import col
-- df = session.table("my_table").filter(col("id") > 10).group_by("category").count()
-- df.write.mode("overwrite").save_as_table("my_summary")

-- 2. Stored Procedure in Python (Returning Value)
CREATE OR REPLACE PROCEDURE greet_user(name STRING)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'main'
AS
$$
def main(session, name):
    return f"Hello, {name}!"
$$;

-- 3. Stored Procedure in Python (Returning Table)
CREATE OR REPLACE PROCEDURE get_high_value_users(min_spend FLOAT)
RETURNS TABLE(user_id INT, total_spend FLOAT)
LANGUAGE PYTHON
RUNTIME_VERSION = '3.8'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'main'
AS
$$
from snowflake.snowpark.functions import col
def main(session, min_spend):
    df = session.table("users_table").filter(col("spend") >= min_spend)
    return df
$$;

-- 4. Cortex AI / LLM Functions
-- Complete/Generate Text (Supports llama3.1-70b, mistral-large2, etc.)
SELECT SNOWFLAKE.CORTEX.COMPLETE('llama3.1-70b', 'Write a SQL query tutorial in 3 bullet points.');

-- Summarize Text
SELECT SNOWFLAKE.CORTEX.SUMMARIZE(review_text) FROM product_reviews;

-- Sentiment Analysis (Returns score between -1 and 1)
SELECT SNOWFLAKE.CORTEX.SENTIMENT(comment_text) FROM user_feedback;

-- Translate Text
SELECT SNOWFLAKE.CORTEX.TRANSLATE('Bonjour tout le monde', 'fr', 'en');

-- Extract Answer from Unstructured Text
SELECT SNOWFLAKE.CORTEX.EXTRACT_ANSWER(contract_text, 'What is the expiration date?');

-- Embed Text (Generate vectors for semantic search)
SELECT SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m-v1.5', 'Text to embed');
```

## 14. SECURITY & GOVERNANCE
> **用途**：敏感数据保护与合规性治理。涵盖字段的动态脱敏策略、行级访问限制（多租户数据隔离）、限制访问的 IP 网络策略，以及用于安全审计的数据标签（Tags）。

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
> **用途**：大表性能加速。包含自维护的物化视图、针对高基数键点查询的搜索优化服务（Search Optimization Service）以及自动接管庞大计算量以缩短查询响应的查询加速服务（QAS）。

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
> **用途**：应对不同数据和业务场景的底层表设计。包含对接 Apache Iceberg 开放格式的外部表，以及为高并发、低延迟 OLTP（混合事务/分析）设计的混合表（Hybrid Tables）。

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
> **用途**：异地容灾与多云多活备份。支持跨区域和跨云服务商同步数据库、用户权限和仓库状态，提供一键故障转移。

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
> **用途**：成本限额与监控的安全阀门。监控特定虚拟仓库或整个账户的信用额度（Credit）消耗，超出阈值时实现自动警告、挂起当前计算或强制中断运行。

``` sql
-- Create Monitor (Limit credit usage)
CREATE RESOURCE MONITOR my_monitor WITH CREDIT_QUOTA = 100
TRIGGERS ON 90 PERCENT DO NOTIFY
         ON 100 PERCENT DO SUSPEND;

ALTER WAREHOUSE my_wh SET RESOURCE_MONITOR = my_monitor;
```

## 19. OTHER FEATURES
> **用途**：企业级扩展能力。包括基于事件驱动自动触发的无服务器持续加载（Snowpipe）、跨账户的隐私计算安全干净房（Data Clean Rooms）及第三方数据市场。

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

## 20. MERGE & DATA MANIPULATION (UPSERT)
> **用途**：单条 SQL 语句原子性地执行更新、删除和插入。广泛应用于从暂存区到目标表的增量更新及 Slowly Changing Dimensions (SCD) 的维护。

``` sql
-- 1. Standard Upsert (Insert if new, Update if exists)
MERGE INTO target_table t
USING source_table s
ON t.id = s.id
WHEN MATCHED THEN
  UPDATE SET t.name = s.name, t.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN
  INSERT (id, name, updated_at) VALUES (s.id, s.name, CURRENT_TIMESTAMP());

-- 2. Multi-clause Merge (Update, Delete, Insert)
-- Note: Order matters! Put more specific conditions first, catch-all last.
MERGE INTO target_table t
USING source_table s
ON t.id = s.id
WHEN MATCHED AND s.action = 'DELETE' THEN 
  DELETE
WHEN MATCHED AND s.status != t.status THEN 
  UPDATE SET t.status = s.status, t.updated_at = CURRENT_TIMESTAMP()
WHEN NOT MATCHED THEN 
  INSERT (id, status, updated_at) VALUES (s.id, s.status, CURRENT_TIMESTAMP());

-- 3. Merge Directly from Stage / Files
MERGE INTO target_table t
USING (
  SELECT $1 AS id, $2 AS name, $3 AS status 
  FROM @my_stage/updates.csv (FILE_FORMAT => my_csv_format)
) s
ON t.id = s.id
WHEN MATCHED THEN 
  UPDATE SET t.name = s.name, t.status = s.status
WHEN NOT MATCHED THEN 
  INSERT (id, name, status) VALUES (s.id, s.name, s.status);

-- 4. Workaround for "WHEN NOT MATCHED BY SOURCE THEN DELETE"
-- Snowflake does not natively support NOT MATCHED BY SOURCE.
-- Pattern A: FULL OUTER JOIN in USING
MERGE INTO target_table t
USING (
  SELECT s.id AS source_id, s.name AS source_name, t.id AS target_id
  FROM source_table s
  FULL OUTER JOIN target_table t ON s.id = t.id
) s
ON t.id = s.target_id
WHEN MATCHED AND s.source_id IS NULL THEN 
  DELETE -- Row missing from source
WHEN MATCHED THEN 
  UPDATE SET t.name = s.source_name -- Row in both
WHEN NOT MATCHED THEN 
  INSERT (id, name) VALUES (s.source_id, s.source_name); -- Row only in source

-- Pattern B: Separate DELETE + MERGE statements (Often more performant)
DELETE FROM target_table t
WHERE NOT EXISTS (SELECT 1 FROM source_table s WHERE t.id = s.id);
-- Followed by standard MERGE
```

## 21. DYNAMIC TABLES
> **用途**：基于声明式 SQL 自动构建轻量级增量 ETL 管道。无需开发复杂的 Streams 和 Tasks，只需指定最终目标查询及期望更新的延迟（`TARGET_LAG`），Snowflake 将自动在后台增量刷新目标表数据。

``` sql
-- 1. Create Dynamic Table (Declarative pipeline, auto-refreshed)
CREATE OR REPLACE DYNAMIC TABLE sales_summary_dt
  TARGET_LAG = '1 minute' -- Refresh interval (or 'DOWNSTREAM')
  WAREHOUSE = compute_wh
AS
  SELECT product_id, SUM(amount) AS total_sales, COUNT(*) AS txn_count
  FROM sales_table
  GROUP BY product_id;

-- 2. Alter Dynamic Table settings
ALTER DYNAMIC TABLE sales_summary_dt SET TARGET_LAG = '5 minutes';
ALTER DYNAMIC TABLE sales_summary_dt SET WAREHOUSE = another_wh;

-- 3. Force Manual Refresh
ALTER DYNAMIC TABLE sales_summary_dt REFRESH;

-- 4. Pause / Resume Dynamic Table
ALTER DYNAMIC TABLE sales_summary_dt SUSPEND;
ALTER DYNAMIC TABLE sales_summary_dt RESUME;

-- 5. Monitor Refresh Graph and History
SELECT * FROM TABLE(INFORMATION_SCHEMA.DYNAMIC_TABLE_REFRESH_HISTORY(
  NAME => 'sales_summary_dt'
));
```

## 22. MODERN SQL CONVENIENCES
> **用途**：现代 SQL 开发便捷语法。通过支持如 `EXCLUDE` 排除列、`RENAME` 快速更名，以及无序手动书写的分组语法 `GROUP BY ALL`，大量消除冗长的冗余样板代码。

``` sql
-- 1. SELECT * EXCLUDE / RENAME
-- Select everything except sensitive columns
SELECT * EXCLUDE (ssn, password) FROM employees;

-- Select everything, renaming specific columns
SELECT * RENAME (id AS employee_id, dept AS department_name) FROM employees;

-- Combine both EXCLUDE and RENAME
SELECT * EXCLUDE (password) RENAME (id AS employee_id) FROM employees;

-- 2. GROUP BY ALL / ORDER BY ALL (Auto-detect columns)
SELECT 
    DATE_TRUNC('month', created_at) AS order_month,
    category,
    region,
    SUM(price) AS total_revenue
FROM orders
GROUP BY ALL
ORDER BY ALL DESC;
```
