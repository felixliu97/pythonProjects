# Pull Query Results — Glue Python Shell Job

> Lambda → Glue 迁移文档：`index.js` → `pull_query_results_job.py`

## 1. 为什么要从 Lambda 迁移到 Glue

原始 Lambda (`index.js`) 在生产中存在以下问题：

| 问题 | Lambda 现状 | Glue Python Shell 解决方案 |
|------|-----------|--------------------------|
| **Timeout** | 最长 15 分钟，大数据量下频繁超时 | Glue Job 默认 48 小时，无超时风险 |
| **内存限制** | 最大 10GB，大 CSV 流需要手动分块 | Python Shell 最高 1 DPU (16GB)，pandas 分块读取，内存可控 |
| **Avro 编码** | 手动 `avsc` 流式编码，单线程处理 | `fastavro.write.Writer` + try/finally flush，分块安全写入 |
| **错误处理** | Promise 链嵌套，软失败 (SOFT Failure) 掩盖真实错误 | 显式 try/except + `@retry` 装饰器，指数退避重试 |
| **S3 上传** | 每个文件单独 `s3.upload()`，无重试 | `boto3.upload_file()` + 网络层 retry |

## 2. 架构对比

```
Lambda (原始)                           Glue Python Shell (新)
─────────────────────────              ──────────────────────────────────
Event → Handler                        Glue Job Parameters (S3 URI)
  ├── pullTableMetadata(config, jobInfo)  ├── Step 1: getResolvedOptions
  ├── _buildAvroSchema(config, metadata)  │           → 从 S3 读取 config/job_info JSON
  ├── pullQueryResults(config, jobInfo)   ├── Step 2: Secrets Manager → ApiConnector
  │   → 第一次调用                         ├── Step 3: POST /api/metadata → build Avro schema
  ├── for each file 1..N:                 ├── Step 4: for file 1..N:
  │   ├── uploadFileStream(dataStream)    │   ├── pullQueryResults(config, jobInfo)
  │   ├── if not last:                    │   │   → 服务端游标自动推进，返回下一个 chunk
  │   │   pullQueryResults(config,jobInfo)│   ├── CSV → Avro (pandas + fastavro Writer)
  │   └── _checkUploadedS3Object          │   ├── upload_to_s3
  ├── _updateManifest                     │   └── cleanup temp files
  └── _uploadManifest                     └── Done: log summary
```

> **关键行为保持一致**：原始 JS 中 `pullQueryResults(config, jobInfo)` 使用**服务端隐式游标**，每次调用返回下一个数据块。Python 版本保持完全相同的 API 调用方式——只传 `config` 和 `jobInfo`，不传 `fileNumber`。

## 3. 输入参数

Glue Job 接收 **Glue Job Parameters**，配置文件存放在 S3 上：

| 参数名 | 是否必填 | 说明 |
|--------|---------|------|
| `--config_s3_uri` | ✅ 必填 | config JSON 的 S3 路径 |
| `--job_info_s3_uri` | ✅ 必填 | job_info JSON 的 S3 路径 |
| `--telemetry_s3_uri` | ❌ 可选 | telemetry JSON 的 S3 路径 |

### API 凭证（Secrets Manager）

`apiSecretName` 写在 config JSON 内部，Job 启动时自动从 AWS Secrets Manager 获取凭证。

Secret 中的 JSON 结构：
```json
{
  "endpoint": "https://api.source-system.com",
  "username": "svc_glue_user",
  "password": "xxx",
  "token":    "yyy"
}
```

> Job 启动时会校验 secret 是否包含全部 4 个 required keys（`endpoint`, `username`, `password`, `token`），缺少任何一个都会立即抛出 `ValueError`。

### config JSON（存放在 S3）

```json
{
  "source": "salesforce",
  "dataFeed": "accounts",
  "classification": "restricted",
  "chunkSize": 500000,
  "apiSecretName": "prod/edwdl/api-credentials",
  "landingBucket": {
    "bucketName": "my-landing-bucket"
  },
  "dataTypeOverrides": [
    { "fieldName": "CustomField__c", "dataType": "decimal(18,2)" }
  ]
}
```

### job_info JSON（存放在 S3）

```json
{
  "numberRecordsProcessed": 1500000,
  "jobId": "job-abc-123",
  "query": "SELECT Id, Name, CreatedDate FROM Account"
}
```

### telemetry JSON（存放在 S3，可选）

```json
{
  "executionTS": "2026-06-05T06:00:00Z"
}
```

### 调用示例

```bash
aws glue start-job-run \
  --job-name pull-query-results \
  --arguments '{
    "--config_s3_uri":    "s3://my-config-bucket/jobs/pull-query/config.json",
    "--job_info_s3_uri":  "s3://my-config-bucket/jobs/pull-query/job_info.json",
    "--telemetry_s3_uri": "s3://my-config-bucket/jobs/pull-query/telemetry.json"
  }'
```

## 4. API 调用 — 与原始 JS 的对照

### 认证

原始 JS 中认证封装在 `api-connectors-library` 内部。Python 版本在 `ApiConnector.__init__` 中显式实现：

```
POST {endpoint}/auth/login
Body: { "username": "...", "password": "...", "token": "..." }
Response: { "sessionToken": "..." } 或 { "access_token": "..." }
→ 后续请求 Header: Authorization: Bearer {sessionToken}
```

### pullTableMetadata

| | 原始 JS | Python |
|---|---|---|
| 调用 | `pullTableMetadata(config, jobInfo)` | `api.get_table_metadata(config, job_info)` |
| 端点 | `api-connectors-library` 内部 | `POST /api/metadata` |
| Payload | `config` + `jobInfo` (全量) | `{ source, dataFeed, jobId, query }` |

### pullQueryResults

| | 原始 JS | Python |
|---|---|---|
| 调用 | `pullQueryResults(config, jobInfo)` | `api.pull_query_results_stream(config, job_info, output_path)` |
| 端点 | `api-connectors-library` 内部 | `POST /api/query/results` |
| Payload | `config` + `jobInfo` (全量) | `{ source, dataFeed, jobId, query }` |
| 游标 | 服务端隐式推进 | **相同** — 服务端隐式推进 |
| 返回 | `dataStream` (Node readable stream) | 写入本地 CSV 文件 |
| 调用次数 | `totalFileNumbers` 次 | **相同** — `total_files` 次 |

> ⚠️ **注意**：原始 JS 不向 API 传递 `fileNumber` / `totalFileNumbers`。服务端通过内部游标（session-based cursor）追踪当前进度，每次调用自动返回下一批数据。Python 版本保持此行为不变。

## 5. 执行流程

### Step 1: 加载配置

- 通过 `getResolvedOptions` 解析 Glue Job Parameters
- 从 S3 下载并解析 config、job_info、telemetry JSON
- 根据 `chunkSize` 和 `numberRecordsProcessed` 计算需要下载的文件总数：
  - `total_files = ceil(numberRecordsProcessed / chunkSize)`
  - 如果 `total_files == 0`（0 条记录），设为 1（与原始 JS 第 281-283 行逻辑一致）

### Step 2: 认证 & 获取 Metadata

- 从 Secrets Manager 获取 API 凭证
- `ApiConnector` 初始化时自动调用 `POST /auth/login`
- 调用 `POST /api/metadata` 获取字段元数据
- 基于 metadata 构建 Avro schema：
  - `datetime` → `{"type": "long", "logicalType": "timestamp-millis"}`
  - `boolean` / `decimal` / 其他 → `string`（保持与原始 JS `avsc` 行为一致）
  - 带 `defaultValue = null` 的字段 → `["null", type]`（nullable）
  - 过滤 compound fields（与原始 JS 第 64-68 行逻辑一致）

### Step 3: 循环拉取 → 流式转换 → 上传

```
for file_num in range(1, total_files + 1):    # 对应 JS 第 329 行

    ── 3a. 调用 API 拉取数据流 ──────────────────────────────────
    pullQueryResults(config, jobInfo)  ← 与 JS 完全相同的 API 调用
      → 服务端游标自动推进，返回第 file_num 批数据流
      → 带 @retry(max_attempts=3, backoff=2^n 秒)
      → 401 自动重新认证

    ── 3b. CSV 流式解析并写入 Avro ─────────────────────────────
    requests.Response.iter_lines()  # 流式迭代，不缓存 CSV
      → csv.reader / DictReader
      → _transform_row()  # datetime → epoch millis, 空值 → null
      → fastavro.write.Writer  # 写入临时 Avro 文件

    ── 3c. 上传到 S3 & 校验 ────────────────────────────────────
    s3://bucket/{source}/{classification}/{dataFeed}/{executionTS}/
      {dataFeed}_part_{file_num}_of_{total_files}.avro
    # ↑ 命名格式与原始 JS 第 293 行完全一致
    → boto3.client("s3").upload_file()
    → check_uploaded_s3_object() (利用 HeadObject 校验并确保非空)

    ── 3d. 清理临时 Avro 文件 ──────────────────────────────────
    删除 /tmp 中的临时 .avro 文件，避免占用磁盘空间
```

### JS vs Python 调用顺序对照

```
JS (原始):                              Python (新):
─────────────────────                   ─────────────────────
pullTableMetadata(config, jobInfo)      get_table_metadata(config, job_info)
pullQueryResults(config, jobInfo)  ─┐   for file_num in 1..N:
for file 1..N:                      │     pullQueryResults(config, jobInfo)  ← 每次循环开头调
  uploadFileStream(dataStream)      │     stream_response_to_avro(stream → avro)
  if not last:                      │     upload_to_s3(avro)
    pullQueryResults(config,jobInfo)─┘     check_uploaded_s3_object(avro)
                                           cleanup temp files
                                        update_and_upload_manifest()
```

> 原始 JS 是先拉再传（pipeline），Python 是拉-转-传-校验-清理后再拉下一个，最后统一更新 Manifest。行为等价，且对内存与磁盘更加友好。

## 6. S3 输出结构

```
s3://my-landing-bucket/
  └── salesforce/restricted/accounts/2026-06-05T06:00:00Z/
      ├── accounts_part_1_of_3.avro
      ├── accounts_part_2_of_3.avro
      └── accounts_part_3_of_3.avro
```

文件命名格式：`{dataFeed}_part_{fileNumber}_of_{totalFiles}.avro`

> 与原始 JS 第 293 行一致：`` `${config.dataFeed}_part_${filesWritten}_of_${totalFileNumbers}.avro` ``

## 7. 与原始 JS 的功能差异

| 功能 | 原始 JS (Lambda) | Python (Glue) | 说明 |
|------|-----------------|---------------|------|
| Manifest 更新 | ✅ `_updateManifest` + `_uploadManifest` | ✅ 已实现 | `update_and_upload_manifest` 同样从 S3 获取现有 manifest，更新已写入文件和行数并上传 |
| S3 对象校验 | ✅ `_checkUploadedS3Object` (HeadObject) | ✅ 已实现 | `check_uploaded_s3_object` 在每次上传后执行 HeadObject 并校验 ContentLength 是否大于 0 |
| 0 条记录处理 | ✅ `totalFileNumbers = 1` | ✅ `max(1, ...)` | 行为一致 |
| 并行上传 | ✅ `Promise.all(uploads)` | ❌ 串行 | Python Shell 单线程，串行更稳定，且方便错误捕获 |
| 软失败 | ✅ SOFT Failure (catch → resolve) | ❌ 直接抛异常 | Glue Job 有 Max Retries 与 alert 机制，异常抛出会使 Job 状态正确报错 |

## 8. 错误处理 & 重试

| 场景 | 处理方式 |
|------|---------|
| API 请求失败（网络错误、5xx） | `@retry` 装饰器，最多 3 次，指数退避（2s → 4s → 8s） |
| 401 Unauthorized | `_request()` 自动重新认证后重试（与 `api-connectors-library` 行为一致） |
| Secrets Manager 缺少必要字段 | 立即抛出 `ValueError`，Job 终止 |
| API 返回非 2xx | `resp.raise_for_status()` 抛出 `HTTPError` |

## 9. Glue Job 配置建议

| 参数 | 建议值 | 说明 |
|------|--------|------|
| Job type | **Python Shell** | 无需 Spark，依赖轻量 |
| Python version | **3.9** 或 **3.10** | 支持内建泛型类型提示 |
| DPU | `1` 或 `0.0625` | 采用纯流式架构（非 pandas），内存占用极低，即使 0.0625 DPU (1.5GB 内存) 也可轻松处理 GB 级数据 |
| Max capacity | `1.0` 或 `0.0625` | Python Shell 支持 0.0625 或 1.0 DPU |
| Timeout | `120 min` | 根据网络传输速度调整 |
| Max Retries | `1` | 代码层已有 retry |
| `--additional-python-modules` | `fastavro` | requests / boto3 已预装，无需额外加载 pandas 依赖 |

## 10. 日志输出

所有日志通过 Python `logging` 模块输出到 CloudWatch（Glue 自动集成）：

```
[INFO] Fetching API credentials from Secrets Manager: prod/edwdl/api-credentials
[INFO] API credentials loaded (endpoint: https://api.source-system.com)
[INFO] Authenticating to https://api.source-system.com...
[INFO] Authentication successful
[INFO] Retrieved metadata: 45 fields
[INFO] Avro schema built with 42 fields
[INFO] Source: salesforce, DataFeed: accounts
[INFO] Records: 1500000, ChunkSize: 500000, Files to write: 3
[INFO] ── File 1 of 3 ────────────────────────────
[INFO] Requesting data stream for file 1 of 3
[INFO] Streaming API response -> Avro: /tmp/tmpeq4v0y8r.avro
[INFO]   Streamed 10,000 rows (1.2 MB received)
[INFO]   Streamed 20,000 rows (2.4 MB received)
...
[INFO] Wrote 500,000 records to /tmp/tmpeq4v0y8r.avro (received 58.6 MB CSV, wrote 22.4 MB Avro)
[INFO] Uploading 22.4 MB → s3://my-landing-bucket/.../accounts_part_1_of_3.avro
[INFO] Upload complete: s3://my-landing-bucket/.../accounts_part_1_of_3.avro
[INFO] Checking S3 object s3://my-landing-bucket/.../accounts_part_1_of_3.avro with HeadObject...
[INFO] S3 object verified successfully: s3://my-landing-bucket/.../accounts_part_1_of_3.avro (size: 23488102 bytes)
[INFO] ── File 2 of 3 ────────────────────────────
...
[INFO] ── File 3 of 3 ────────────────────────────
...
[INFO] Updating manifest in S3: s3://my-landing-bucket/.../salesforce_accounts_manifest.json
[INFO] Manifest successfully updated: s3://my-landing-bucket/.../salesforce_accounts_manifest.json
[INFO] ============================================================
[INFO] Done!
[INFO]   Total rows : 1500000
[INFO]   Files      : 3
[INFO]     s3://my-landing-bucket/.../accounts_part_1_of_3.avro
[INFO]     s3://my-landing-bucket/.../accounts_part_2_of_3.avro
[INFO]     s3://my-landing-bucket/.../accounts_part_3_of_3.avro
[INFO] ============================================================
```

## 11. 需要确认的事项

原始 JS 通过 `api-connectors-library` 封装了所有 API 调用。Python 版本中 API 端点路径是**假设的**：

| 当前假设 | 需要对照 `api-connectors-library` 确认 |
|----------|---------------------------------------|
| `POST /auth/login` | 认证端点路径、请求体格式 |
| 响应中的 `sessionToken` 或 `access_token` | Token 字段名 |
| `POST /api/metadata` | 对应 `pullTableMetadata` 的实际端点和请求体 |
| `POST /api/query/results` | 对应 `pullQueryResults` 的实际端点和请求体 |
| Bearer Token 认证 | 是否 Bearer 或其他 scheme |

> 如果你能提供 `api-connectors-library` 的源码或 Postman collection，可以精确调整端点路径和请求格式。

## 12. `/tmp` 磁盘空间与多文件处理注意

Glue Python Shell 的 `/tmp` 磁盘空间限制通常为 **10GB**（部分受限环境为 **1GB**）。

由于我们采用了**流式架构（Streaming）**，API 响应的 CSV 数据是逐行流式读取并转换的，**完全不写入本地 CSV 文件**。因此：
- `/tmp` 目录中在任意时刻最多只存在 **一个** 临时 Avro 文件。
- 磁盘峰值占用仅为单个 chunk 对应的 **Avro 文件大小**（通常为原始 CSV 文本大小的 30% - 50%）。
- 每次 S3 上传并校验成功后，会立即清理当前 Avro 文件（`Path.unlink(missing_ok=True)`），释放空间后再处理下一个 chunk。
- **即使总共需要下载和写入 3-4 个文件，每个文件最大 1GB，该 Job 也能完全胜任**。因为在同一时刻磁盘上只有 1 个文件，且已做 Avro 压缩，实际占用远低于 1GB。如果环境磁盘非常小，只需调小配置中的 `chunkSize`（如 200,000）即可减小单个临时 Avro 文件的尺寸，完全不会因文件多而导致磁盘空间堆积。
