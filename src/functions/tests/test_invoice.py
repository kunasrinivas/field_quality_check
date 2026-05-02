"""Unit tests for POST /invoice — submit_invoice handler."""
import json
import sys
from unittest.mock import call

import pytest

# pyodbc may be shimmed in sys.modules by conftest; import after conftest runs.
import pyodbc  # noqa: E402

import function_app
from tests.conftest import _make_request

_VALID_INVOICE = {
    "workOrderId": "WO-2026-00123",
    "contractorId": "CTR-0042",
    "lineItems": [
        {"description": "Cable installation", "quantity": 10, "unitPrice": 85.00}
    ],
    "totalAmount": 850.00,
    "currency": "EUR",
}


class TestSubmitInvoice:
    def test_happy_path_returns_202(self, mock_sql_conn):
        req = _make_request(method="POST", body=_VALID_INVOICE)
        resp = function_app.submit_invoice(req)

        assert resp.status_code == 202
        body = json.loads(resp.get_body())
        assert body["status"] == "received"
        assert body["workOrderId"] == "WO-2026-00123"
        assert "invoiceId" in body

    def test_ddl_and_insert_both_executed(self, mock_sql_conn):
        conn, cursor = mock_sql_conn
        req = _make_request(method="POST", body=_VALID_INVOICE)
        function_app.submit_invoice(req)

        calls = [c[0][0] for c in cursor.execute.call_args_list]
        assert any("OBJECT_ID" in s for s in calls), "DDL guard not called"
        assert any("INSERT INTO dbo.invoices" in s for s in calls), "INSERT not called"

    def test_insert_uses_correct_values(self, mock_sql_conn):
        conn, cursor = mock_sql_conn
        req = _make_request(method="POST", body=_VALID_INVOICE)
        function_app.submit_invoice(req)

        insert_call = next(
            c for c in cursor.execute.call_args_list
            if "INSERT INTO dbo.invoices" in c[0][0]
        )
        args = insert_call[0][1:]  # positional args after the SQL string
        # args: invoiceId, workOrderId, contractorId, lineItems, totalAmount, currency
        assert args[1] == "WO-2026-00123"
        assert args[2] == "CTR-0042"
        assert args[4] == 850.00
        assert args[5] == "EUR"

    def test_invalid_json_returns_400(self, mock_sql_conn):
        req = _make_request(method="POST", body=b"not-json{")
        resp = function_app.submit_invoice(req)

        assert resp.status_code == 400
        assert "JSON" in json.loads(resp.get_body())["error"]

    def test_missing_work_order_id_returns_400(self, mock_sql_conn):
        body = {**_VALID_INVOICE}
        del body["workOrderId"]
        req = _make_request(method="POST", body=body)
        resp = function_app.submit_invoice(req)

        assert resp.status_code == 400

    def test_missing_contractor_id_returns_400(self, mock_sql_conn):
        body = {**_VALID_INVOICE}
        del body["contractorId"]
        req = _make_request(method="POST", body=body)
        resp = function_app.submit_invoice(req)

        assert resp.status_code == 400

    def test_missing_total_amount_returns_400(self, mock_sql_conn):
        body = {**_VALID_INVOICE}
        del body["totalAmount"]
        req = _make_request(method="POST", body=body)
        resp = function_app.submit_invoice(req)

        assert resp.status_code == 400
        assert "totalAmount" in json.loads(resp.get_body())["error"]

    def test_sql_error_returns_502(self, mock_sql_conn):
        conn, cursor = mock_sql_conn
        cursor.execute.side_effect = pyodbc.Error("HY000", "connection refused")

        req = _make_request(method="POST", body=_VALID_INVOICE)
        resp = function_app.submit_invoice(req)

        assert resp.status_code == 502
        assert "Database error" in json.loads(resp.get_body())["error"]

    def test_currency_defaults_to_eur(self, mock_sql_conn):
        conn, cursor = mock_sql_conn
        body = {**_VALID_INVOICE}
        del body["currency"]
        req = _make_request(method="POST", body=body)
        function_app.submit_invoice(req)

        insert_call = next(
            c for c in cursor.execute.call_args_list
            if "INSERT INTO dbo.invoices" in c[0][0]
        )
        assert insert_call[0][6] == "EUR"

    def test_each_call_generates_unique_invoice_id(self, mock_sql_conn):
        req = lambda: _make_request(method="POST", body=_VALID_INVOICE)
        r1 = json.loads(function_app.submit_invoice(req()).get_body())
        r2 = json.loads(function_app.submit_invoice(req()).get_body())

        assert r1["invoiceId"] != r2["invoiceId"]

    def test_line_items_serialised_as_json(self, mock_sql_conn):
        conn, cursor = mock_sql_conn
        req = _make_request(method="POST", body=_VALID_INVOICE)
        function_app.submit_invoice(req)

        insert_call = next(
            c for c in cursor.execute.call_args_list
            if "INSERT INTO dbo.invoices" in c[0][0]
        )
        line_items_arg = insert_call[0][4]
        parsed = json.loads(line_items_arg)
        assert isinstance(parsed, list)
        assert parsed[0]["description"] == "Cable installation"
