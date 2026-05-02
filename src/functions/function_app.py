import json
import logging
import os
import uuid
from typing import Optional

import azure.functions as func
from azure.cosmos import CosmosClient, exceptions as cosmos_exc
from azure.storage.blob import BlobServiceClient
import pyodbc

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# ---------------------------------------------------------------------------
# Module-level singletons — survive warm invocations, reducing cold-start cost.
# BlobServiceClient and CosmosClient are thread-safe; SQL connections are not.
# ---------------------------------------------------------------------------
_blob_service: Optional[BlobServiceClient] = None
_cosmos_client: Optional[CosmosClient] = None


def _blob_svc() -> BlobServiceClient:
    global _blob_service
    if _blob_service is None:
        _blob_service = BlobServiceClient.from_connection_string(
            os.environ["EVIDENCE_STORAGE_CONNECTION"]
        )
    return _blob_service


def _cosmos_container(name: str):
    global _cosmos_client
    if _cosmos_client is None:
        _cosmos_client = CosmosClient.from_connection_string(
            os.environ["COSMOS_CONNECTION"]
        )
    return (
        _cosmos_client
        .get_database_client(os.environ.get("COSMOS_DB_NAME", "fqct-data"))
        .get_container_client(name)
    )


def _sql_conn() -> pyodbc.Connection:
    """New connection per invocation — pyodbc connections are not thread-safe."""
    return pyodbc.connect(os.environ["SQL_CONNECTION"], autocommit=False)


def _json_ok(data: dict, status: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data), status_code=status, mimetype="application/json"
    )


def _json_err(message: str, status: int = 400) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps({"error": message}), status_code=status, mimetype="application/json"
    )


# ---------------------------------------------------------------------------
# SQL bootstrap — creates the invoices table on first use if absent.
# Production environments should use proper migration tooling instead.
# ---------------------------------------------------------------------------
_ENSURE_INVOICES_TABLE = """
IF OBJECT_ID('dbo.invoices', 'U') IS NULL
CREATE TABLE dbo.invoices (
    invoiceId    NVARCHAR(36)    NOT NULL PRIMARY KEY,
    workOrderId  NVARCHAR(255)   NOT NULL,
    contractorId NVARCHAR(255)   NOT NULL,
    lineItems    NVARCHAR(MAX),
    totalAmount  DECIMAL(18, 2),
    currency     NCHAR(3)        NOT NULL DEFAULT 'EUR',
    receivedAt   DATETIME2       NOT NULL DEFAULT GETUTCDATE()
);
"""

_INSERT_INVOICE = """
INSERT INTO dbo.invoices
    (invoiceId, workOrderId, contractorId, lineItems, totalAmount, currency)
VALUES (?, ?, ?, ?, ?, ?);
"""


# ---------------------------------------------------------------------------
# Blob trigger — fires when a file lands in raw-evidence/{workOrderId}/
# ---------------------------------------------------------------------------
@app.blob_trigger(
    arg_name="blob",
    path="raw-evidence/{name}",
    connection="EVIDENCE_STORAGE_CONNECTION",
)
def evidence_blob_trigger(blob: func.InputStream) -> None:
    """
    Fires on every upload to raw-evidence/.
    blob.name is the path within the container, e.g. WO-123/photo.jpg.
    Sprint 3 will add the Vision API call and audit-trail write here.
    """
    parts = blob.name.split("/", 1)
    work_order_id = parts[0] if len(parts) == 2 else "unknown"
    filename = parts[1] if len(parts) == 2 else blob.name

    logging.info(
        "Evidence blob received | workOrderId=%s | file=%s | size=%d bytes",
        work_order_id, filename, blob.length,
    )
    # TODO Sprint 3: call Azure AI Vision, write result to Cosmos audit-trail
    # TODO Sprint 3: copy blob to processed-evidence container


# ---------------------------------------------------------------------------
# POST /evidence?workOrderId=<id>&filename=<name>
# Body: raw binary (image/jpeg, image/png, video/mp4, etc.)
# ---------------------------------------------------------------------------
@app.route(route="evidence", methods=["POST"])
def submit_evidence(req: func.HttpRequest) -> func.HttpResponse:
    """
    Stores the uploaded file in raw-evidence/{workOrderId}/{filename}.
    Returning 202 immediately; the blob trigger handles downstream processing.
    """
    work_order_id = req.params.get("workOrderId", "").strip()
    filename = req.params.get("filename", "").strip()

    if not work_order_id:
        return _json_err("workOrderId query parameter is required")
    if not filename:
        return _json_err("filename query parameter is required")

    file_bytes = req.get_body()
    if not file_bytes:
        return _json_err("Request body must contain the file bytes")

    job_id = str(uuid.uuid4())
    blob_path = f"{work_order_id}/{filename}"

    try:
        container = os.environ.get("EVIDENCE_CONTAINER", "raw-evidence")
        blob_client = _blob_svc().get_blob_client(container=container, blob=blob_path)
        blob_client.upload_blob(file_bytes, overwrite=True)
    except Exception as exc:
        logging.exception("Blob upload failed | workOrderId=%s", work_order_id)
        return _json_err(f"Upload failed: {exc}", status=502)

    logging.info(
        "Evidence uploaded | jobId=%s | workOrderId=%s | blob=%s | size=%d bytes",
        job_id, work_order_id, blob_path, len(file_bytes),
    )
    return _json_ok(
        {"jobId": job_id, "workOrderId": work_order_id, "blobPath": blob_path, "status": "accepted"},
        status=202,
    )


# ---------------------------------------------------------------------------
# POST /invoice
# Body: { workOrderId, contractorId, lineItems, totalAmount, currency }
# ---------------------------------------------------------------------------
@app.route(route="invoice", methods=["POST"])
def submit_invoice(req: func.HttpRequest) -> func.HttpResponse:
    """
    Validates and persists an invoice to SQL fqct-db-dev.
    Creates the invoices table on first call if absent.
    """
    try:
        body = req.get_json()
    except ValueError:
        return _json_err("Request body must be valid JSON")

    work_order_id = (body.get("workOrderId") or "").strip()
    contractor_id = (body.get("contractorId") or "").strip()
    total_amount = body.get("totalAmount")
    currency = (body.get("currency") or "EUR").strip().upper()
    line_items = body.get("lineItems", [])

    if not work_order_id or not contractor_id:
        return _json_err("workOrderId and contractorId are required")
    if total_amount is None:
        return _json_err("totalAmount is required")

    invoice_id = str(uuid.uuid4())

    try:
        conn = _sql_conn()
        with conn:
            cursor = conn.cursor()
            cursor.execute(_ENSURE_INVOICES_TABLE)
            cursor.execute(
                _INSERT_INVOICE,
                invoice_id,
                work_order_id,
                contractor_id,
                json.dumps(line_items),
                float(total_amount),
                currency,
            )
    except pyodbc.Error as exc:
        logging.exception("SQL insert failed | workOrderId=%s", work_order_id)
        return _json_err(f"Database error: {exc}", status=502)

    logging.info(
        "Invoice stored | invoiceId=%s | workOrderId=%s | total=%.2f %s",
        invoice_id, work_order_id, float(total_amount), currency,
    )
    return _json_ok(
        {"invoiceId": invoice_id, "workOrderId": work_order_id, "status": "received"},
        status=202,
    )


# ---------------------------------------------------------------------------
# GET /status/{workOrderId}
# ---------------------------------------------------------------------------
@app.route(route="status/{workOrderId}", methods=["GET"])
def get_status(req: func.HttpRequest, workOrderId: str) -> func.HttpResponse:
    """
    Returns the latest AI decision record from Cosmos audit-trail.
    Partition key is workOrderId so this is always a single-partition read.
    """
    if not workOrderId:
        return _json_err("workOrderId path parameter is required")

    try:
        container = _cosmos_container("audit-trail")
        items = list(
            container.query_items(
                query=(
                    "SELECT TOP 1 c.workOrderId, c.status, c.decision, c.createdAt "
                    "FROM c WHERE c.workOrderId = @id ORDER BY c._ts DESC"
                ),
                parameters=[{"name": "@id", "value": workOrderId}],
                partition_key=workOrderId,
            )
        )
    except cosmos_exc.CosmosHttpResponseError as exc:
        logging.exception("Cosmos query failed | workOrderId=%s", workOrderId)
        return _json_err(f"Database error: {exc.message}", status=502)

    if not items:
        return _json_err(f"Work order '{workOrderId}' not found", status=404)

    record = items[0]
    logging.info("Status served | workOrderId=%s | status=%s", workOrderId, record.get("status"))

    return _json_ok({
        "workOrderId": record.get("workOrderId"),
        "status": record.get("status", "pending"),
        "decision": record.get("decision"),
        "createdAt": record.get("createdAt"),
    })
