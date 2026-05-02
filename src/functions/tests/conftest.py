"""
Shared fixtures for function_app unit tests.

All Azure SDK calls are mocked so tests run without any Azure credentials or
system ODBC drivers. pyodbc is shimmed in sys.modules before function_app is
imported so the C-extension never needs to load.
"""
import json
import sys
import os
from typing import Optional
from unittest.mock import MagicMock, patch

import pytest
import azure.functions as func

# ---------------------------------------------------------------------------
# Shim pyodbc before function_app is imported — lets tests run on machines
# that don't have unixodbc installed (e.g. macOS CI agents, developer laptops).
# ---------------------------------------------------------------------------
if "pyodbc" not in sys.modules:
    _pyodbc_mock = MagicMock()
    _pyodbc_mock.Error = Exception  # tests catch pyodbc.Error by name
    sys.modules["pyodbc"] = _pyodbc_mock

# Make function_app importable from the tests sub-package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import function_app  # noqa: E402  (must come after sys.modules shim)


def _make_request(
    method: str = "GET",
    url: str = "https://fqct.azure-api.net/fqct/evidence",
    params: Optional[dict] = None,
    body=None,
    headers: Optional[dict] = None,
    route_params: Optional[dict] = None,
) -> func.HttpRequest:
    """Build an azure.functions.HttpRequest suitable for direct handler calls."""
    if isinstance(body, dict):
        body = json.dumps(body).encode()
    elif isinstance(body, str):
        body = body.encode()
    elif body is None:
        body = b""

    return func.HttpRequest(
        method=method,
        url=url,
        params=params or {},
        headers=headers or {},
        route_params=route_params or {},
        body=body,
    )


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset module-level singletons so each test starts clean."""
    function_app._blob_service = None
    function_app._cosmos_client = None
    yield
    function_app._blob_service = None
    function_app._cosmos_client = None


@pytest.fixture(autouse=True)
def env_vars(monkeypatch):
    """Inject dummy environment variables so the module can initialise."""
    monkeypatch.setenv(
        "EVIDENCE_STORAGE_CONNECTION",
        "DefaultEndpointsProtocol=https;AccountName=fake;AccountKey=ZmFrZWtleQ==;EndpointSuffix=core.windows.net",
    )
    monkeypatch.setenv(
        "COSMOS_CONNECTION",
        "AccountEndpoint=https://fake.documents.azure.com:443/;AccountKey=ZmFrZWtleQ==;",
    )
    monkeypatch.setenv(
        "SQL_CONNECTION",
        "Driver={ODBC Driver 18 for SQL Server};Server=tcp:fake,1433;Initial Catalog=fakedb;UID=admin;PWD=pass;",
    )
    monkeypatch.setenv("EVIDENCE_CONTAINER", "raw-evidence")
    monkeypatch.setenv("COSMOS_DB_NAME", "fqct-data")


@pytest.fixture()
def mock_blob_client():
    """A pre-configured mock BlobClient returned by _blob_svc().get_blob_client()."""
    client = MagicMock()
    client.upload_blob = MagicMock(return_value=None)
    return client


@pytest.fixture()
def mock_blob_svc(mock_blob_client):
    """Patches _blob_svc() so blob operations never hit Azure."""
    svc = MagicMock()
    svc.get_blob_client.return_value = mock_blob_client
    with patch("function_app._blob_svc", return_value=svc):
        yield svc


@pytest.fixture()
def mock_cosmos_container():
    """Patches _cosmos_container() so Cosmos operations never hit Azure."""
    container = MagicMock()
    container.query_items.return_value = []
    with patch("function_app._cosmos_container", return_value=container):
        yield container


@pytest.fixture()
def mock_sql_conn():
    """Patches _sql_conn() so SQL operations never hit Azure."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    with patch("function_app._sql_conn", return_value=conn):
        yield conn, cursor
