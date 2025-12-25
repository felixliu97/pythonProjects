# Apache PyFlink Cheatsheet

## 🚀 1. Environment Setup

### Prerequisites
- **Python**: 3.6, 3.7, 3.8, or 3.9 (PyFlink 1.16+)
- **Java**: Java 8 or Java 11 (Required for Flink runner)

### Installation
```bash
# Install PyFlink
pip install apache-flink

# Verify installation
python -c "import pyflink; print(pyflink.__version__)"
```

### Environment Variables (Windows PowerShell)
```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-11"
$env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
```

---

## 🏗️ 2. Basic Skeleton

### DataStream API
Used for low-level stream processing flexibility.

```python
from pyflink.datastream import StreamExecutionEnvironment

def main():
    # 1. Create Environment
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(1)

    # 2. Source
    ds = env.from_collection([(1, 'a'), (2, 'b'), (3, 'c')])

    # 3. Transform
    ds = ds.map(lambda x: (x[0] + 1, x[1]))

    # 4. Sink
    ds.print()

    # 5. Execute
    env.execute("My DataStream Job")

if __name__ == '__main__':
    main()
```

### Table API
Used for relational/SQL-like processing.

```python
from pyflink.table import EnvironmentSettings, TableEnvironment

def main():
    # 1. Create Environment
    settings = EnvironmentSettings.in_streaming_mode()
    t_env = TableEnvironment.create(settings)

    # 2. Create Table (Source/Sink via SQL)
    t_env.execute_sql("""
        CREATE TEMPORARY TABLE MySource (
            id INT,
            word STRING
        ) WITH (
            'connector' = 'datagen',
            'rows-per-second' = '1'
        )
    """)

    # 3. Query/Transform
    tab = t_env.from_path("MySource")
    result_tab = tab.select(tab.id + 1, tab.word)

    # 4. Execute/Print
    result_tab.execute().print()

if __name__ == '__main__':
    main()
```

---

## 📡 3. Sources (DataStream)

### From Collection
```python
ds = env.from_collection([1, 2, 3])
```

### From File
```python
# Read line by line
ds = env.read_text_file("input.txt")
```

### From Kafka
Requires `flink-connector-kafka` jar.

```python
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema

kafka_props = {'bootstrap.servers': 'localhost:9092', 'group.id': 'my-group'}
kafka_source = FlinkKafkaConsumer('my-topic', SimpleStringSchema(), properties=kafka_props)

ds = env.add_source(kafka_source)
```

---

## 🔄 4. Transformations

### Map
One-to-one transformation.
```python
ds.map(lambda x: x * 2, output_type=Types.INT())
```

### FlatMap
One-to-many/zero transformation (e.g., split sentence into words).
```python
def split(s):
    for word in s.split():
        yield word

ds.flat_map(split, output_type=Types.STRING())
```

### Filter
Keep elements that match condition.
```python
ds.filter(lambda x: x > 10)
```

### KeyBy & Reduce
Aggregation on keyed streams.
```python
# Input: (word, count)
ds.key_by(lambda x: x[0]) \
  .reduce(lambda a, b: (a[0], a[1] + b[1]))
```

---

## 🪟 5. Windowing

### Tumbling Window (Fixed non-overlapping)
```python
from pyflink.datastream.window import TumblingProcessingTimeWindows
from pyflink.common import Time

ds.key_by(lambda x: x[0]) \
  .window(TumblingProcessingTimeWindows.of(Time.seconds(5))) \
  .sum(1)
```

### Sliding Window (Overlapping)
```python
from pyflink.datastream.window import SlidingProcessingTimeWindows

# 10s window, slides every 5s
ds.key_by(...) \
  .window(SlidingProcessingTimeWindows.of(Time.seconds(10), Time.seconds(5))) \
  .sum(1)
```

---

## 📊 6. Table API & SQL

### Define Source (DataGen / Kafka / Filesystem)
```sql
CREATE TABLE KafkaSource (
    user_id BIGINT,
    item_id STRING,
    ts TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'user_behavior',
    'properties.bootstrap.servers' = 'localhost:9092',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);
```

### SQL Query
```python
result = t_env.sql_query("""
    SELECT user_id, COUNT(item_id) as item_count 
    FROM KafkaSource 
    GROUP BY user_id
""")
```

### Python UDF (Scalar)
```python
from pyflink.table.udf import udf
from pyflink.table import DataTypes

@udf(result_type=DataTypes.INT())
def add_five(i):
    return i + 5

t_env.create_temporary_function("add_five", add_five)

# Usage in SQL
t_env.sql_query("SELECT add_five(id) FROM MyTable")
```

---

## 🔧 7. Execution & Deployment

### Local Execution (IDE)
Just run the python script:
```bash
python my_job.py
```

### Cluster Execution (Standalone / YARN / K8s)
Use the `flink` CLI found in the PyFlink installation directory or Flink distribution.

```bash
# Submit job
flink run -py my_job.py

# Submit with external jars (e.g. Kafka connector)
flink run -py my_job.py -j flink-sql-connector-kafka-1.16.0.jar
```

### Parallelism
Set globally or per operator.
```python
# Global
env.set_parallelism(4)

# Per Operator
ds.map(...).set_parallelism(2)
```

## 📦 8. Managing JAR Dependencies
PyFlink often requires Java JARs for connectors (Kafka, JDBC, etc.).

1. **Download JAR**: Get the matching version from Maven Central.
2. **Add to Env**:
   ```python
   # For DataStream
   env.add_jars("file:///path/to/connector.jar")
   
   # For Table API
   t_env.get_config().get_configuration().set_string("pipeline.jars", "file:///path/to/connector.jar")
   ```
3. **Or Submit CLI**: `flink run -j path/to.jar ...`

---

## 🧩 9. Real-World Patterns

### Kafka JOIN PostgreSQL (Lookup Join)
Enriching a real-time stream (Kafka) with static/slow-changing data (Postgres). Requires `flink-connector-jdbc` and PostgreSQL driver jars.

```sql
-- 1. Stream Source (Kafka)
CREATE TABLE Orders (
    order_id INT,
    product_id INT,
    user_id INT,
    ts TIMESTAMP(3),
    WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'orders',
    'properties.bootstrap.servers' = 'localhost:9092',
    'format' = 'json'
);

-- 2. Lookup Source (Postgres)
CREATE TABLE Users (
    user_id INT,
    user_name STRING,
    email STRING
) WITH (
    'connector' = 'jdbc',
    'url' = 'jdbc:postgresql://localhost:5432/mydb',
    'table-name' = 'users',
    'username' = 'postgres',
    'password' = 'password'
);

-- 3. Lookup Join Query
-- Must use FOR SYSTEM_TIME AS OF match_row.proctime
SELECT 
    o.order_id, 
    o.product_id, 
    u.user_name, 
    u.email
FROM Orders AS o
JOIN Users FOR SYSTEM_TIME AS OF o.proctime AS u
ON o.user_id = u.user_id;
```

### Kafka JOIN Kafka (Nested JSON & Interval Join)
Joining two streams (e.g., Clicks and Views) with complex nested data.

**Nested JSON Sample:**
`{"event_id": 1, "details": {"page": "home", "tags": ["mobile", "promo"]}}`

```sql
-- 1. Source A (Clicks) with Nested Schema
CREATE TABLE Clicks (
    event_id INT,
    details ROW<page STRING, tags ARRAY<STRING>>, -- Nested Row/Array
    ts TIMESTAMP(3),
    WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'clicks',
    'properties.bootstrap.servers' = 'localhost:9092',
    'format' = 'json'
);

-- 2. Source B (Views)
CREATE TABLE Views (
    event_id INT,
    page_id STRING,
    ts TIMESTAMP(3),
    WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'views',
    'properties.bootstrap.servers' = 'localhost:9092',
    'format' = 'json'
);

-- 3. Interval Join & Array Access
-- Join matching events occurring within 10 minutes of each other
SELECT 
    c.event_id,
    c.details.page AS page_name, -- Access Nested Field
    c.details.tags[1] AS first_tag, -- Access Array Element
    v.page_id
FROM Clicks c
JOIN Views v 
ON c.event_id = v.event_id 
AND c.ts BETWEEN v.ts - INTERVAL '10' MINUTE AND v.ts + INTERVAL '10' MINUTE;
```
