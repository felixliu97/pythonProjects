# Pandas & Polars Cheatsheet

## 1. SETUP & BASICS

```python
# --- PANDAS ---
import pandas as pd

# From Dictionary
df_pd = pd.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "val": [10.5, 20.0, None]
})

# --- POLARS ---
import polars as pl

# From Dictionary
df_pl = pl.DataFrame({
    "id": [1, 2, 3],
    "name": ["Alice", "Bob", "Charlie"],
    "val": [10.5, 20.0, None]
})
```

## 2. IO (READING & WRITING)

```python
# --- PANDAS ---
# CSV
df = pd.read_csv("data.csv")
df.to_csv("output.csv", index=False)

# Parquet
df = pd.read_parquet("data.parquet")
df.to_parquet("output.parquet")

# --- POLARS ---
# CSV
df = pl.read_csv("data.csv")
df.write_csv("output.csv")

# Parquet
df = pl.read_parquet("data.parquet")
df.write_parquet("output.parquet")

# Lazy Loading (Polars specific)
lf = pl.scan_parquet("data.parquet")
```

## 3. DATA MANIPULATION

### Selection & Filtering

```python
# --- PANDAS ---
# Select columns
df[["name", "val"]]

# Filter rows
df[df["val"] > 10]
df[(df["val"] > 10) & (df["name"] != "Bob")]

# --- POLARS ---
# Select columns
df.select(["name", "val"])

# Filter rows
df.filter(pl.col("val") > 10)
df.filter((pl.col("val") > 10) & (pl.col("name") != "Bob"))
```

### New Columns

```python
# --- PANDAS ---
df["val_doubled"] = df["val"] * 2
df["status"] = "Active"

# --- POLARS ---
df = df.with_columns([
    (pl.col("val") * 2).alias("val_doubled"),
    pl.lit("Active").alias("status")
])
```

### Sorting & Unique

```python
# --- PANDAS ---
df.sort_values("val", ascending=False)
df.drop_duplicates(subset=["name"])

# --- POLARS ---
df.sort("val", descending=True)
df.unique(subset=["name"])
```

### Renaming & Dropping

```python
# --- PANDAS ---
df.rename(columns={"name": "full_name"})
df.drop(columns=["id"])

# --- POLARS ---
df.rename({"name": "full_name"})
df.drop(["id"])
```

## 4. AGGREGATION & GROUPBY

```python
# --- PANDAS ---
df.groupby("name").agg({
    "val": ["sum", "mean"],
    "id": "count"
})

# --- POLARS ---
df.group_by("name").agg([
    pl.col("val").sum().alias("val_sum"),
    pl.col("val").mean().alias("val_mean"),
    pl.col("id").count().alias("id_count")
])
```

## 5. JOINS & CONCATENATION

```python
# --- PANDAS ---
# Join
pd.merge(df1, df2, on="id", how="left")

# Concat (Vertical)
pd.concat([df1, df2], axis=0)

# --- POLARS ---
# Join
df1.join(df2, on="id", how="left")

# Concat (Vertical)
pl.concat([df1, df2], how="vertical")
```

## 6. MISSING DATA

```python
# --- PANDAS ---
df.fillna(0)
df.dropna()

# --- POLARS ---
df.fill_null(0)
df.drop_nulls()
```

## 7. STRINGS & DATES

```python
# --- PANDAS ---
df["name"].str.upper()
df[df["name"].str.contains("Ali")]
pd.to_datetime(df["date_str"])

# --- POLARS ---
df.select(pl.col("name").str.to_uppercase())
df.filter(pl.col("name").str.contains("Ali"))
df.with_columns(pl.col("date_str").str.strptime(pl.Date, "%Y-%m-%d"))
```

## 8. PANDAS <> POLARS INTEROPERABILITY

```python
# Pandas -> Polars
df_pl = pl.from_pandas(df_pd)

# Polars -> Pandas
df_pd = df_pl.to_pandas()
```
