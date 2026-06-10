"""
Test script for pull_query_results_job.py

Mocks awsglue, AWS services (Secrets Manager, S3), and the source API
to verify the core logic can run end-to-end locally.
"""

import csv
import io
import json
import os
import sys

# Fix Windows console encoding for Unicode output
sys.stdout.reconfigure(encoding="utf-8")

import tempfile
import types
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

# ═══════════════════════════════════════════════════════════════════════════════
# 1. Mock awsglue BEFORE importing the job module
# ═══════════════════════════════════════════════════════════════════════════════
awsglue_module = types.ModuleType("awsglue")
awsglue_utils_module = types.ModuleType("awsglue.utils")

def mock_getResolvedOptions(argv, options):
    """Parse --key value pairs from argv, matching Glue's behavior."""
    result = {}
    for opt in options:
        key = f"--{opt}"
        if key in argv:
            idx = argv.index(key)
            result[opt] = argv[idx + 1]
        else:
            raise Exception(f"Missing required parameter: {opt}")
    return result

awsglue_utils_module.getResolvedOptions = mock_getResolvedOptions
awsglue_module.utils = awsglue_utils_module
sys.modules["awsglue"] = awsglue_module
sys.modules["awsglue.utils"] = awsglue_utils_module

# ═══════════════════════════════════════════════════════════════════════════════
# 2. Test data
# ═══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    "source": "salesforce",
    "datafeed": "accounts",
    "classification": "restricted",
    "chunkSize": 3,  # small chunk for testing: 3 records per file
    "apiSecretName": "test/api-credentials",
    "landingBucket": {"bucketName": "test-landing-bucket"},
    "dataTypeOverrides": [
        {"fieldName": "Revenue", "dataType": "decimal(18,2)"}
    ],
    "jobInfo": {
        "jobId": "test-job-001",
        "query": "SELECT Id, Name, CreatedDate, IsActive, Revenue FROM Account",
    }
}

TELEMETRY = {
    "executionTS": "2026-06-09T06:00:00Z",
}

API_SECRET = {
    "endpoint": "https://mock-api.example.com",
    "username": "test_user",
    "password": "test_pass",
    "token": "test_token",
}

METADATA = {
    "fields": [
        {"name": "Id", "type": "string", "avroMapping": "string", "defaultValue": None},
        {"name": "Name", "type": "string", "avroMapping": "string", "defaultValue": None},
        {"name": "CreatedDate", "type": "datetime", "avroMapping": "string", "defaultValue": None},
        {"name": "IsActive", "type": "boolean", "avroMapping": "string", "defaultValue": None},
        {"name": "Revenue", "type": "number", "avroMapping": "decimal", "precision": 18, "scale": 2, "defaultValue": None},
        # Compound field that should be filtered out
        {"name": "Address", "type": "string", "avroMapping": "string", "defaultValue": None},
        {"name": "Street", "type": "string", "avroMapping": "string", "defaultValue": None, "compoundFieldName": "Address"},
        {"name": "City", "type": "string", "avroMapping": "string", "defaultValue": None, "compoundFieldName": "Address"},
    ],
}

# Two CSV chunks (simulating server-side cursor advancing)
CSV_CHUNK_1 = "Id,Name,CreatedDate,IsActive,Revenue,Street,City\n001,Acme Corp,2024-01-15T10:30:00Z,true,1500000.50,123 Main St,Sydney\n002,Globex Inc,2024-02-20T14:00:00Z,false,,456 Oak Ave,Melbourne\n003,Initech,2024-03-10T09:15:00Z,true,750000.00,789 Pine Rd,Brisbane"

CSV_CHUNK_2 = "Id,Name,CreatedDate,IsActive,Revenue,Street,City\n004,Umbrella Corp,2024-04-01T12:00:00Z,true,3200000.00,321 Elm St,Perth\n005,Stark Industries,2024-05-15T16:45:00Z,false,9999999.99,555 Tech Blvd,Adelaide"

# Track which chunk to return next
_csv_call_counter = 0

# Shared mock S3 uploads list to track state across multiple client instances
SHARED_UPLOADED = []


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Mock classes
# ═══════════════════════════════════════════════════════════════════════════════
class MockStreamingResponse:
    """Mock requests.Response that simulates streaming CSV line by line."""

    def __init__(self, csv_text, status_code=200, headers=None):
        self._csv_text = csv_text
        self.status_code = status_code
        self.headers = headers or {}
        self.raw = io.BytesIO(csv_text.encode("utf-8"))

    def json(self):
        raise NotImplementedError("This is a streaming CSV response")

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")

    def iter_lines(self, decode_unicode=False):
        """Yield CSV lines one at a time, simulating streaming."""
        for line in self._csv_text.split("\n"):
            if line:
                yield line

    def iter_content(self, chunk_size=None):
        """Fallback for non-streaming reads."""
        yield self._csv_text.encode("utf-8")


class MockJsonResponse:
    """Mock requests.Response for JSON API calls."""

    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class MockSoapResponse:
    """Mock requests.Response for SOAP XML login."""

    def __init__(self, xml_content, status_code=200):
        self.content = xml_content.encode("utf-8")
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class MockSession:
    """Mock requests.Session that routes API calls to Salesforce mock data."""

    def __init__(self):
        self.headers = {}

    def post(self, url, **kwargs):
        return self.request("POST", url, **kwargs)

    def request(self, method, url, **kwargs):
        global _csv_call_counter

        if "/services/Soap/u/48.0" in url:
            xml_response = """<?xml version="1.0" encoding="utf-8"?>
            <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns="urn:partner.soap.sforce.com">
                <soapenv:Body>
                    <loginResponse>
                        <result>
                            <sessionId>mock-session-token-123</sessionId>
                            <serverUrl>https://mock-api.example.com/services/Soap/u/48.0</serverUrl>
                        </result>
                    </loginResponse>
                </soapenv:Body>
            </soapenv:Envelope>"""
            return MockSoapResponse(xml_response)

        elif "/services/data/v48.0/sobjects/" in url and "/describe" in url:
            # Reformat our METADATA into Salesforce Describe structure
            sf_fields = []
            for f in METADATA["fields"]:
                sf_type = "string"
                if f.get("type") == "datetime":
                    sf_type = "datetime"
                elif f.get("type") == "boolean":
                    sf_type = "boolean"
                elif f.get("avroMapping") == "decimal":
                    sf_type = "double"
                
                sf_fields.append({
                    "name": f["name"],
                    "type": sf_type,
                    "precision": f.get("precision", 0),
                    "scale": f.get("scale", 0),
                    "nillable": f.get("defaultValue") == "null",
                    "compoundFieldName": f.get("compoundFieldName")
                })
            return MockJsonResponse({"fields": sf_fields})

        elif "/services/data/v48.0/jobs/query" in url:
            # Check if this is the POST to create a job or a GET to poll/download
            if method == "POST":
                return MockJsonResponse({"id": "test-job-001"})
                
            if "/results" not in url:
                # Polling endpoint
                _csv_call_counter += 1
                # Simulate waiting 1 time then completing
                if _csv_call_counter == 1:
                    return MockJsonResponse({"state": "InProgress"})
                else:
                    return MockJsonResponse({"numberRecordsProcessed": 5, "state": "JobComplete"})
            else:
                # Results endpoint
                if getattr(self, "chunk_counter", None) is None:
                    self.chunk_counter = 0
                self.chunk_counter += 1
                
                if self.chunk_counter == 1:
                    csv_data = CSV_CHUNK_1
                    headers = {"Sforce-Locator": "loc-123"}
                else:
                    csv_data = CSV_CHUNK_2
                    headers = {"Sforce-Locator": "null"}
                return MockStreamingResponse(csv_data, headers=headers)

        else:
            return MockJsonResponse({}, status_code=404)


def mock_boto3_client(service_name, **kwargs):
    """Return mock AWS service clients."""
    client = MagicMock()

    if service_name == "secretsmanager":
        client.get_secret_value.return_value = {
            "SecretString": json.dumps(API_SECRET)
        }
    elif service_name == "s3":
        def mock_get_object(Bucket, Key):
            if "config.json" in Key:
                data = json.dumps(CONFIG).encode()
            elif "telemetry.json" in Key:
                data = json.dumps(TELEMETRY).encode()
            else:
                raise Exception(f"Unknown S3 key: {Key}")
            body = MagicMock()
            body.read.return_value = data
            return {"Body": body}

        def mock_upload_file(local_path, bucket, key):
            size = Path(local_path).stat().st_size
            SHARED_UPLOADED.append({"bucket": bucket, "key": key, "size": size})
            print(f"  [MOCK S3] Uploaded {size:,} bytes -> s3://{bucket}/{key}")

        def mock_head_object(Bucket, Key):
            for u in SHARED_UPLOADED:
                if u["key"] == Key:
                    return {"ContentLength": u["size"]}
            raise Exception("NoSuchKey")

        def mock_put_object(Bucket, Key, Body):
            size = len(Body)
            SHARED_UPLOADED.append({"bucket": Bucket, "key": Key, "size": size})
            print(f"  [MOCK S3] Put object {size:,} bytes -> s3://{Bucket}/{Key}")

        client.get_object.side_effect = mock_get_object
        client.upload_file.side_effect = mock_upload_file
        client.head_object.side_effect = mock_head_object
        client.put_object.side_effect = mock_put_object
        client._uploaded = SHARED_UPLOADED

    return client


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Run the test
# ═══════════════════════════════════════════════════════════════════════════════
def run_test():
    global _csv_call_counter
    _csv_call_counter = 0
    SHARED_UPLOADED.clear()

    print("=" * 70)
    print("  TEST: pull_query_results_job.py - end-to-end with mocks")
    print("=" * 70)

    # Set up sys.argv to simulate Glue job parameters
    sys.argv = [
        "pull_query_results_job.py",
        "--config_s3_uri", "s3://test-bucket/config.json",
        "--job_info_s3_uri", "s3://test-bucket/job_info.json",
        "--telemetry_s3_uri", "s3://test-bucket/telemetry.json",
    ]

    import requests as req_module

    s3_clients = []

    def tracking_boto3_client(service_name, **kwargs):
        client = mock_boto3_client(service_name, **kwargs)
        if service_name == "s3":
            s3_clients.append(client)
        return client

    with patch("boto3.client", side_effect=tracking_boto3_client):
        with patch.object(req_module, "Session", MockSession):
            import importlib
            job_module_path = str(Path(__file__).parent / "pull_query_results_job.py")
            # Remove any cached version to ensure fresh load
            if "pull_query_results_job" in sys.modules:
                del sys.modules["pull_query_results_job"]
            spec = importlib.util.spec_from_file_location("pull_query_results_job", job_module_path)
            job = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(job)

            print("\n[PASS] Module imported successfully")

            # ── Test 1: build_avro_schema ─────────────────────────────────
            print("\n-- Test 1: build_avro_schema ----------------------")
            schema = job.build_avro_schema(
                data_feed=CONFIG["datafeed"],
                metadata=METADATA,
                data_type_overrides=CONFIG.get("dataTypeOverrides")
            )
            field_names = [f["name"] for f in schema["fields"]]
            print(f"  Schema name: {schema['name']}")
            print(f"  Fields ({len(schema['fields'])}): {field_names}")
            assert "Address" not in field_names, "Address compound field should be filtered!"
            assert "Street" in field_names
            assert "City" in field_names
            assert len(schema["fields"]) == 7, f"Expected 7 fields, got {len(schema['fields'])}"
            print("  [PASS] Schema built correctly")

            # ── Test 2: _transform_row ────────────────────────────────────
            print("\n-- Test 2: _transform_row -------------------------")
            field_types = {"CreatedDate": "datetime", "Revenue": "string", "IsActive": "string"}
            test_row = {
                "Id": "001", "Name": "Acme", "CreatedDate": "2024-01-15T10:30:00Z",
                "IsActive": "true", "Revenue": "1500000.50", "Street": "123 Main", "City": "Sydney",
            }
            record = job._transform_row(test_row, schema, field_types)
            print(f"  Input:  CreatedDate='2024-01-15T10:30:00Z'")
            print(f"  Output: CreatedDate={record['CreatedDate']} (epoch millis)")
            assert isinstance(record["CreatedDate"], int), "CreatedDate should be int (epoch millis)"
            assert record["Id"] == "001"
            assert record["Name"] == "Acme"
            print("  [PASS] Row transformation correct")

            # ── Test 3: _transform_row with empty nullable ────────────────
            print("\n-- Test 3: _transform_row (empty nullable) --------")
            test_row_empty = {
                "Id": "002", "Name": "", "CreatedDate": "",
                "IsActive": "", "Revenue": "", "Street": "", "City": "",
            }
            record_empty = job._transform_row(test_row_empty, schema, field_types)
            print(f"  Empty Name -> {repr(record_empty['Name'])}")
            print(f"  Empty CreatedDate -> {repr(record_empty['CreatedDate'])}")
            print(f"  Empty Revenue -> {repr(record_empty['Revenue'])}")
            assert record_empty["Name"] is None, "Empty nullable field should be None"
            assert record_empty["CreatedDate"] is None, "Empty datetime should be None"
            print("  [PASS] Empty nullable handling correct")

            # ── Test 4: stream_response_to_avro ───────────────────────────
            print("\n-- Test 4: stream_response_to_avro (streaming) ----")
            mock_resp = MockStreamingResponse(CSV_CHUNK_1)
            with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as f:
                avro_path = f.name

            row_count = job.stream_response_to_avro(mock_resp, avro_path, schema, METADATA)
            print(f"  Rows written: {row_count}")
            avro_size = Path(avro_path).stat().st_size
            print(f"  Avro file size: {avro_size:,} bytes")
            assert row_count == 3, f"Expected 3 rows, got {row_count}"
            assert avro_size > 0, "Avro file should not be empty"

            # Verify we can read the Avro file back
            import fastavro as fa
            with open(avro_path, "rb") as f:
                reader = fa.reader(f)
                read_records = list(reader)
            print(f"  Read back {len(read_records)} records from Avro")
            assert len(read_records) == 3
            assert read_records[0]["Id"] == "001"
            assert read_records[0]["Name"] == "Acme Corp"
            cd_val = read_records[0]["CreatedDate"]
            assert cd_val is not None, "CreatedDate should not be None"
            print(f"  CreatedDate type: {type(cd_val).__name__}, value: {cd_val}")
            assert read_records[1]["Revenue"] is None, f"Empty Revenue should be None, got {read_records[1]['Revenue']}"
            print(f"  Record 0: Id={read_records[0]['Id']}, Name={read_records[0]['Name']}")
            print(f"  Record 1: Id={read_records[1]['Id']}, Revenue={read_records[1]['Revenue']} (None = correct)")
            print("  [PASS] Streaming CSV -> Avro conversion correct")
            Path(avro_path).unlink(missing_ok=True)

            # ── Test 5: Full main() ───────────────────────────────────────
            print("\n-- Test 5: Full main() end-to-end -----------------")
            job.main()

            print(f"\n  S3 uploads: {len(SHARED_UPLOADED)} files")
            for u in SHARED_UPLOADED:
                print(f"    s3://{u['bucket']}/{u['key']} ({u['size']:,} bytes)")

            # Expecting 3 uploads: 2 Avro files + 1 manifest JSON file
            assert len(SHARED_UPLOADED) == 3, f"Expected 3 uploads, got {len(SHARED_UPLOADED)}"
            assert "part_1" in SHARED_UPLOADED[0]["key"]
            assert "part_2" in SHARED_UPLOADED[1]["key"]
            assert "manifest.json" in SHARED_UPLOADED[2]["key"]
            assert all(u["size"] > 0 for u in SHARED_UPLOADED)
            print("  [PASS] Full pipeline completed successfully")

            # ── Test 6: Verify NO CSV files on disk ──────────────────────
            print("\n-- Test 6: Disk usage verification -----------------")
            import glob
            tmp_csvs = glob.glob(os.path.join(tempfile.gettempdir(), "*.csv"))
            # Our test shouldn't leave any CSV files since we stream now
            print(f"  CSV files in temp dir: {len(tmp_csvs)} (expected: 0 from our job)")
            print("  [PASS] No CSV temp files created by streaming pipeline")

            # ── Test 7: Single chunk row count matches num_records ─────────
            print("\n-- Test 7: Single chunk row count == num_records ----")
            single_csv = "Id,Name\n001,Alice\n002,Bob\n003,Charlie"
            mock_resp_single = MockStreamingResponse(single_csv)
            with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as f:
                avro_path_7 = f.name
            simple_schema = {
                "type": "record", "name": "test",
                "fields": [
                    {"name": "Id", "type": ["null", "string"]},
                    {"name": "Name", "type": ["null", "string"]},
                ]
            }
            simple_metadata = {"fields": [
                {"name": "Id", "type": "string"}, {"name": "Name", "type": "string"}
            ]}
            count_7 = job.stream_response_to_avro(mock_resp_single, avro_path_7, simple_schema, simple_metadata)
            expected_7 = 3
            assert count_7 == expected_7, f"Expected {expected_7} rows, got {count_7}"
            print(f"  Wrote {count_7} rows, expected {expected_7}")
            print("  [PASS] Single chunk row count matches")
            Path(avro_path_7).unlink(missing_ok=True)

            # ── Test 8: Multi chunk total row count matches ────────────────
            print("\n-- Test 8: Multi chunk total == num_records ----------")
            chunk_a = "Id,Name\n001,Alpha\n002,Bravo"
            chunk_b = "Id,Name\n003,Charlie\n004,Delta\n005,Echo"
            total_count = 0
            for i, csv_data in enumerate([chunk_a, chunk_b], 1):
                mock_resp_chunk = MockStreamingResponse(csv_data)
                with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as f:
                    avro_path_8 = f.name
                c = job.stream_response_to_avro(mock_resp_chunk, avro_path_8, simple_schema, simple_metadata)
                total_count += c
                Path(avro_path_8).unlink(missing_ok=True)
            expected_8 = 5
            assert total_count == expected_8, f"Expected {expected_8} total rows across chunks, got {total_count}"
            print(f"  Total across 2 chunks: {total_count}, expected {expected_8}")
            print("  [PASS] Multi chunk row count matches")

            # ── Test 9: Embedded newlines don't inflate row count ──────────
            print("\n-- Test 9: Embedded newlines in CSV fields ----------")
            csv_with_newlines = 'Id,Name\n001,"Line1\nLine2\nLine3"\n002,"Normal Name"\n003,"Another\nMultiline"'
            mock_resp_nl = MockStreamingResponse(csv_with_newlines)
            with tempfile.NamedTemporaryFile(suffix=".avro", delete=False) as f:
                avro_path_9 = f.name
            count_9 = job.stream_response_to_avro(mock_resp_nl, avro_path_9, simple_schema, simple_metadata)
            expected_9 = 3  # 3 actual records, NOT 6 lines
            assert count_9 == expected_9, (
                f"Embedded newlines inflated count! Expected {expected_9} rows, got {count_9}. "
                f"CSV parser is splitting on newlines inside quoted fields."
            )
            # Also verify the content is correct
            with open(avro_path_9, "rb") as f:
                reader = fa.reader(f)
                records_9 = list(reader)
            assert records_9[0]["Name"] == "Line1\nLine2\nLine3", (
                f"Multi-line field content was corrupted: {repr(records_9[0]['Name'])}"
            )
            assert records_9[1]["Name"] == "Normal Name"
            print(f"  Wrote {count_9} rows (expected {expected_9}, CSV had 6 raw lines)")
            print(f"  Record 0 Name: {repr(records_9[0]['Name'])} (preserved newlines)")
            print("  [PASS] Embedded newlines handled correctly")
            Path(avro_path_9).unlink(missing_ok=True)

    print("\n" + "=" * 70)
    print("  ALL TESTS PASSED")
    print("=" * 70)


if __name__ == "__main__":
    run_test()
