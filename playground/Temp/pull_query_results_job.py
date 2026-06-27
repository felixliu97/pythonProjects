"""
Pull Query Results → Avro → S3

Glue Python Shell job for Salesforce Direct Integration.
Pulls data from Salesforce Bulk API, converts to Avro, uploads to S3.
"""

import csv
import io
import json
import logging
import math
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import boto3
import fastavro
import fastavro.write

# Map Salesforce types to Avro types
SALESFORCE_TO_AVRO_MAPPING = {
    'int': 'int',
    'integer': 'int',
    'percent': 'float',
    'float': 'float',
    'decimal': 'float',
    'double': 'double',
    'datetime': 'datetime'
}
import requests

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
    stream=sys.stdout,
    force=True,  # Overrides any existing logger configuration from AWS Glue
)
logger = logging.getLogger("pull_query_results")
logger.setLevel(logging.INFO)

# ── Secrets Manager ──────────────────────────────────────────────────────────
def get_api_credentials(secret_name: str) -> dict:
    """Fetch API credentials from AWS Secrets Manager."""
    logger.info(f"Fetching API credentials from Secrets Manager: {secret_name}")
    sm = boto3.client("secretsmanager")
    response = sm.get_secret_value(SecretId=secret_name)
    secret = json.loads(response["SecretString"])

    for key in ("endpoint", "username", "password", "token"):
        if key not in secret:
            raise ValueError(f"Secret '{secret_name}' missing required key: {key}")

    logger.info(f"API credentials loaded (endpoint: {secret['endpoint']})")
    return secret

# ── Retry helper ─────────────────────────────────────────────────────────────
def retry(max_attempts: int = 3, backoff_base: float = 2.0, retryable_exceptions=(requests.RequestException,)):
    """Simple retry decorator with exponential backoff."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {exc}")
                        raise
                    wait = backoff_base ** attempt
                    logger.warning(f"{func.__name__} attempt {attempt} failed: {exc}. Retrying in {wait:.0f}s...")
                    time.sleep(wait)
            raise last_exc  # should not reach here
        return wrapper
    return decorator

# ── Salesforce Connector ──────────────────────────────────────────────────────
class SalesforceConnector:
    """Handles SOAP Authentication and Bulk API 2.0 calls to Salesforce."""

    def __init__(self, endpoint: str, username: str, password: str, token: str):
        self.endpoint = endpoint.rstrip("/")
        self.username = username
        self.password = password
        self.token = token
        self.session = requests.Session()
        self.session_token = None
        self.instance_url = None
        self._authenticate()

    def _authenticate(self):
        """Log in to Salesforce using the SOAP API to bypass Connected App requirements."""
        logger.info(f"Authenticating to Salesforce SOAP Endpoint: {self.endpoint}...")
        soap_url = f"{self.endpoint}/services/Soap/u/48.0"
        
        soap_body = f"""<?xml version="1.0" encoding="utf-8" ?>
        <env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                      xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
            <env:Body>
                <n1:login xmlns:n1="urn:partner.soap.sforce.com">
                    <n1:username>{self.username}</n1:username>
                    <n1:password>{self.password}{self.token}</n1:password>
                </n1:login>
            </env:Body>
        </env:Envelope>"""
        
        headers = {
            "Content-Type": "text/xml; charset=UTF-8",
            "SOAPAction": "login"
        }
        
        resp = self.session.post(soap_url, data=soap_body, headers=headers, timeout=30)
        resp.raise_for_status()
        
        # Parse SOAP Response XML
        root = ET.fromstring(resp.content)
        namespaces = {
            'soapenv': 'http://schemas.xmlsoap.org/soap/envelope/',
            'urn': 'urn:partner.soap.sforce.com'
        }
        
        session_id_node = root.find('.//urn:sessionId', namespaces)
        server_url_node = root.find('.//urn:serverUrl', namespaces)
        
        if session_id_node is None or server_url_node is None:
            raise ValueError("SOAP Login response did not contain sessionId or serverUrl.")
            
        self.session_token = session_id_node.text
        server_url = server_url_node.text
        self.instance_url = server_url.split('/services/Soap')[0]
        
        # Update session with authentication headers
        self.session.headers.update({
            "Authorization": f"Bearer {self.session_token}",
            "X-SFDC-Session": self.session_token,
            "Content-Type": "application/json"
        })
        logger.info(f"Authentication successful (Instance URL: {self.instance_url})")

    def _request(self, method: str, path: str, **kwargs):
        """Internal helper to make requests to the authenticated instance_url."""
        url = f"{self.instance_url}{path}"
        resp = self.session.request(method, url, **kwargs)
        if resp.status_code == 401:
            logger.warning("Session expired or invalid, re-authenticating...")
            self._authenticate()
            url = f"{self.instance_url}{path}"
            resp = self.session.request(method, url, **kwargs)
        resp.raise_for_status()
        return resp

    def get_table_metadata(self, data_feed: str) -> dict:
        """
        Pull SObject schema metadata directly from Salesforce.
        Converts the Salesforce Describe API response into the structure expected by build_avro_schema.
        """
        logger.info(f"Describing SObject metadata for: {data_feed}")
        
        # Call Salesforce Describe API
        resp = self._request("GET", f"/services/data/v48.0/sobjects/{data_feed}/describe", timeout=60)
        describe_data = resp.json()
        
        fields = []
        for sf_field in describe_data.get("fields", []):
            field_def = {
                "name": sf_field.get("name"),
                "type": sf_field.get("type"),
                "precision": sf_field.get("precision", 0),
                "scale": sf_field.get("scale", 0),
                "defaultValue": "null" if sf_field.get("nillable") else None,
                "compoundFieldName": sf_field.get("compoundFieldName")
            }
            fields.append(field_def)
            
        logger.info(f"Retrieved metadata: {len(fields)} fields mapped from describe")
        return {"fields": fields}

    def execute_query(self, query: str, poll_interval: int = 10) -> tuple:
        """
        Submits a query and polls until JobComplete. 
        Returns (job_id, num_records).
        """
        logger.info(f"Submitting Query: {query}")
        resp = self._request("POST", "/services/data/v48.0/jobs/query", json={"operation": "query", "query": query})
        job_id = resp.json().get("id")
        logger.info(f"Job ID: {job_id}. Waiting for completion...")
        
        import time
        while True:
            status = self.get_query_job_status(job_id)
            state = status.get("state")
            
            if state == "JobComplete":
                num_records = status.get("numberRecordsProcessed", 0)
                logger.info(f"Job {job_id} completed! Processed {num_records} records.")
                return job_id, num_records
            elif state in ("Failed", "Aborted"):
                raise Exception(f"Job {job_id} failed: {status.get('errorMessage')}")
                
            time.sleep(poll_interval)

    @retry(max_attempts=3, backoff_base=2.0)
    def get_query_job_status(self, job_id: str) -> dict:
        """
        Fetch the status of a Bulk API 2.0 query job.
        Used to get 'numberRecordsProcessed' for progress logging.
        """
        if not job_id:
            raise ValueError("No jobId provided to fetch status.")
            
        logger.info(f"Fetching job status for Job: {job_id}")
        
        path = f"/services/data/v48.0/jobs/query/{job_id}"
        resp = self._request("GET", path)
        return resp.json()

    @retry(max_attempts=3, backoff_base=2.0)
    def pull_query_results_stream(self, job_id: str, locator: str = None, max_records: int = None):
        """
        Pull query results directly from Salesforce Bulk API 2.0.
        Uses the Salesforce Bulk query results endpoint:
        GET /services/data/v48.0/jobs/query/{jobId}/results
        """
        if not job_id:
            raise ValueError("No jobId provided to pull results.")
            
        log_msg = f"Fetching Bulk Query Results from Salesforce for Job: {job_id}"
        if locator and locator != "null":
            log_msg += f" (Locator: {locator})"
        logger.info(log_msg)
        
        # Salesforce returns query results as a CSV stream
        headers = {"Accept": "text/csv"}
        
        path = f"/services/data/v48.0/jobs/query/{job_id}/results"
        query_params = []
        if locator and locator != "null":
            query_params.append(f"locator={locator}")
        if max_records:
            query_params.append(f"maxRecords={max_records}")
            
        if query_params:
            path += "?" + "&".join(query_params)
            
        resp = self._request(
            "GET", 
            path, 
            headers=headers,
            stream=True, 
            timeout=3600
        )
        return resp

# ── Avro Schema Builder ─────────────────────────────────────────────────────
def build_avro_schema(data_feed: str, metadata: dict, data_type_overrides: list = None) -> dict:
    """
    Convert API field metadata into an Avro schema dict.
    Handles dataTypeOverrides, compound fields, datetime → long (epoch millis), etc.
    """
    fields = metadata["fields"]
    overrides = {o["fieldName"]: o["dataType"] for o in (data_type_overrides or [])}
    compound_fields = {f["compoundFieldName"] for f in fields if f.get("compoundFieldName")}

    avro_fields = []
    for field in fields:
        name = field["name"]
        if name in compound_fields:
            continue

        nullable = field.get("defaultValue") in (None, "null")

        # Determine Avro type
        sf_type = field.get("type", "string")
        if name in overrides:
            avro_type = {"type": "string", "logicalType": overrides[name]}
        else:
            mapped_type = SALESFORCE_TO_AVRO_MAPPING.get(sf_type, "string")
            if mapped_type == "datetime":
                avro_type = {"type": "long", "logicalType": "timestamp-millis"}
            else:
                avro_type = mapped_type

        if nullable:
            avro_type = ["null", avro_type]

        avro_fields.append({"name": name, "type": avro_type})

    schema = {
        "type": "record",
        "name": f"{data_feed}_record",
        "fields": avro_fields,
    }
    logger.info(f"Avro schema built with {len(avro_fields)} fields")
    return schema

# ── CSV → Avro Conversion (chunked, memory-safe) ────────────────────────────
def _transform_row(row: dict, avro_schema: dict, field_types: dict) -> dict:
    """Transform a single CSV row dict into an Avro-compatible record, casting types."""
    record = {}
    for field_def in avro_schema["fields"]:
        name = field_def["name"]
        val = row.get(name, "")

        is_nullable = isinstance(field_def["type"], list) and "null" in field_def["type"]

        if val == "" and is_nullable:
            record[name] = None
        elif val == "":
            record[name] = ""
        else:
            ftype = field_types.get(name, "string")
            if ftype == "datetime":
                try:
                    iso_str = val.replace("Z", "+00:00")
                    from datetime import datetime, timezone
                    dt = datetime.fromisoformat(iso_str)
                    record[name] = int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)
                except (ValueError, TypeError, AttributeError):
                    record[name] = None if is_nullable else 0
            elif ftype == "int":
                try:
                    record[name] = int(float(val))
                except ValueError:
                    record[name] = None if is_nullable else 0
            elif ftype in ("float", "double", "decimal"):
                try:
                    record[name] = float(val)
                except ValueError:
                    record[name] = None if is_nullable else 0.0
            else:
                record[name] = val

    return record

def _generate_lines(response):
    """
    Safely stream lines from a requests Response.
    Unlike response.iter_lines(), this yields lines WITH their trailing newlines,
    which allows csv.reader to correctly parse embedded newlines in double-quoted fields.
    """
    buffer = ""
    for chunk in response.iter_content(chunk_size=65536, decode_unicode=True):
        if chunk:
            buffer += chunk
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                yield line + "\n"
    if buffer:
        yield buffer

def stream_response_to_avro(
    response, avro_path: str, avro_schema: dict, metadata: dict,
    expected_total: int = 0, rows_before: int = 0,
) -> int:
    """
    Stream an HTTP CSV response directly into an Avro file.
    No CSV file is written to disk -- parses CSV directly from the connection stream
    to correctly handle embedded newlines in double-quoted fields.
    """
    logger.info(f"Streaming API response -> Avro: {avro_path}")

    # Extract types for casting
    field_types = {}
    for f in avro_schema["fields"]:
        t = f["type"]
        actual_type = [x for x in t if x != "null"][0] if isinstance(t, list) else t
        if isinstance(actual_type, dict) and actual_type.get("logicalType") == "timestamp-millis":
            field_types[f["name"]] = "datetime"
        elif isinstance(actual_type, str):
            field_types[f["name"]] = actual_type

    parsed_schema = fastavro.parse_schema(avro_schema)

    total_rows = 0
    bytes_received = 0

    with open(avro_path, "wb") as out:
        writer = fastavro.write.Writer(out, parsed_schema)
        try:
            csv_reader = csv.reader(_generate_lines(response))

            # First line is the CSV header
            fieldnames = next(csv_reader, None)
            if fieldnames is None:
                logger.warning("Empty response from API, writing empty Avro file")
                return 0

            batch_size = 10_000

            for values in csv_reader:
                if not values:
                    continue
                row = dict(zip(fieldnames, values))

                # Estimate bytes for logging
                row_bytes = sum(len(str(v).encode('utf-8')) for v in values) + len(values)
                bytes_received += row_bytes

                record = _transform_row(row, avro_schema, field_types)
                writer.write(record)
                total_rows += 1

                if total_rows % batch_size == 0:
                    cumulative = rows_before + total_rows
                    if expected_total:
                        pct = min(cumulative / expected_total * 100, 100)
                        logger.info(
                            f"  Streamed {cumulative:,} / {expected_total:,} rows "
                            f"({pct:.0f}%) "
                            f"({bytes_received / (1024 * 1024):.1f} MB received)"
                        )
                    else:
                        logger.info(
                            f"  Streamed {cumulative:,} rows "
                            f"({bytes_received / (1024 * 1024):.1f} MB received)"
                        )
        finally:
            writer.flush()

    avro_size = Path(avro_path).stat().st_size
    logger.info(
        f"Wrote {total_rows:,} records to {avro_path} "
        f"(received {bytes_received / (1024 * 1024):.1f} MB CSV, "
        f"wrote {avro_size / (1024 * 1024):.1f} MB Avro)"
    )
    return total_rows

# ── S3 Operations & Manifest ──────────────────────────────────────────────────
def upload_to_s3(local_path: str, bucket: str, s3_key: str):
    """Upload a local file to S3."""
    s3 = boto3.client("s3")
    file_size = Path(local_path).stat().st_size
    logger.info(f"Uploading {file_size / (1024*1024):.1f} MB → s3://{bucket}/{s3_key}")
    s3.upload_file(local_path, bucket, s3_key)
    logger.info(f"Upload complete: s3://{bucket}/{s3_key}")

def update_and_upload_manifest(
    bucket: str,
    prefix: str,
    prefix_location: str,
    total_files: int,
    row_count: int,
    error_msg: str = None
):
    """Read existing manifest from S3, update it, and upload it back."""
    s3 = boto3.client("s3")
    manifest_key = f"{prefix_location}/{prefix}_manifest.json"
    logger.info(f"Updating manifest in S3: s3://{bucket}/{manifest_key}")
    
    try:
        try:
            response = s3.get_object(Bucket=bucket, Key=manifest_key)
            manifest = json.loads(response["Body"].read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Could not read existing manifest file (might not exist yet): {e}")
            manifest = {}
        
        if error_msg:
            manifest["errorMessages"] = error_msg
        else:
            manifest["files"] = [
                f"{prefix}_part_{file_num}_of_{total_files}.avro"
                for file_num in range(1, total_files + 1)
            ]
            manifest["rowCount"] = str(row_count)
        
        s3.put_object(
            Bucket=bucket,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=8).encode("utf-8"),
        )
        logger.info(f"Manifest successfully updated: s3://{bucket}/{manifest_key}")
    except Exception as e:
        logger.error(f"Failed to update manifest: {e}")
        raise

def main():
    execution_ts = "2026-06-09T06:00:00Z"
    query = f"SELECT Id, Name, CreatedDate, IsActive, Revenue FROM Account WHERE CreatedDate < {execution_ts}"

    config = {
        "source": "salesforce",
        "datafeed": "accounts",
        "classification": "restricted",
        "chunkSize": 500000,
        "apiSecretName": "test/api-credentials",
        "landingBucket": {"bucketName": "test-landing-bucket"},
        "executionTs": execution_ts,
        "dataTypeOverrides": [
            {"fieldName": "Revenue", "dataType": "decimal(18,2)"}
        ],
    }

    # ── Derive paths & chunk count ───────────────────────────────────────
    bucket = config["landingBucket"]["bucketName"]
    s3_prefix = (
        f"{config['source']}/{config['classification']}/"
        f"{config['datafeed']}/{execution_ts}"
    )
    chunk_size = config.get("chunkSize", 500000)
    manifest_prefix = f"{config['source']}_{config['datafeed']}"

    logger.info(f"Source: {config['source']}, DataFeed: {config['datafeed']}")
    logger.info(f"ChunkSize: {chunk_size}")

    try:
        # ── 1. Auth ──────────────────────────────────────────────────────────
        secret_name = config.get("apiSecretName", "")
        creds = get_api_credentials(secret_name)
        api = SalesforceConnector(
            endpoint=creds["endpoint"],
            username=creds["username"],
            password=creds["password"],
            token=creds["token"],
        )

        # ── 2. Get metadata → build Avro schema ──────────────────────────────
        metadata = api.get_table_metadata(config["datafeed"])
        avro_schema = build_avro_schema(
            data_feed=config["datafeed"],
            metadata=metadata,
            data_type_overrides=config.get("dataTypeOverrides")
        )

        # ── 3. Execute Query & Wait ─────────────────────────────────────────
        job_id, num_records = api.execute_query(query)
        total_files = max(1, math.ceil(num_records / chunk_size)) if num_records else 1

        # ── 4. Stream Results → Avro → S3 ───────────────────────────────────
        uploaded_files = []
        total_rows = 0
        locator = None
        file_num = 1

        while True:
            logger.info(f"── File {file_num} of {total_files} ────────────────────────────")

            logger.info(f"Requesting data stream for file {file_num} of {total_files}")
            response = api.pull_query_results_stream(
                job_id, 
                locator=locator, 
                max_records=chunk_size
            )
            
            # Extract locator for the next chunk
            locator = response.headers.get("Sforce-Locator")
            if locator == "null":
                locator = None

            with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as tmp_avro:
                avro_path = tmp_avro.name
                
            row_count = stream_response_to_avro(
                response, avro_path, avro_schema, metadata,
                expected_total=num_records, rows_before=total_rows,
            )
            total_rows += row_count

            avro_filename = f"{config['source']}_{config['datafeed']}_part_{file_num}_of_{total_files}.avro"
            avro_s3_key = f"{s3_prefix}/{avro_filename}"
            upload_to_s3(avro_path, bucket, avro_s3_key)
            uploaded_files.append(avro_s3_key)

            Path(avro_path).unlink(missing_ok=True)
            
            if not locator:
                break
                
            file_num += 1

        # ── 5. Validate row count ─────────────────────────────────────────────
        if total_rows != num_records:
            logger.warning(
                f"Row count mismatch! Bulk API reported {num_records:,} records "
                f"but {total_rows:,} rows were written to Avro."
            )

        # ── 6. Update manifest on success ────────────────────────────────────
        update_and_upload_manifest(
            bucket=bucket,
            prefix=manifest_prefix,
            prefix_location=s3_prefix,
            total_files=len(uploaded_files),
            row_count=total_rows,
        )

        # ── Done ─────────────────────────────────────────────────────────────
        logger.info("=" * 60)
        logger.info("Done!")
        logger.info(f"  Total rows : {total_rows}")
        logger.info(f"  Files      : {len(uploaded_files)}")
        for f in uploaded_files:
            logger.info(f"    s3://{bucket}/{f}")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        try:
            update_and_upload_manifest(
                bucket=bucket,
                prefix=manifest_prefix,
                prefix_location=s3_prefix,
                total_files=len(uploaded_files) if 'uploaded_files' in locals() else 0,
                row_count=0,
                error_msg=str(e),
            )
        except Exception as manifest_err:
            logger.error(f"Failed to update manifest during error handling: {manifest_err}")
        raise

if __name__ == "__main__":
    main()
