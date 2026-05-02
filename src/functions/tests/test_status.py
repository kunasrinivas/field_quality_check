"""Unit tests for GET /status/{workOrderId} — get_status handler."""
import json
from unittest.mock import MagicMock, patch

import pytest
from azure.cosmos import exceptions as cosmos_exc

import function_app
from tests.conftest import _make_request

_AUDIT_RECORD = {
    "workOrderId": "WO-2026-00123",
    "status": "approved",
    "decision": {
        "approvedAmount": 850.00,
        "deviations": [],
        "justification": "All work completed to standard.",
    },
    "createdAt": "2026-05-01T12:00:00Z",
    "_ts": 1746100800,
}


class TestGetStatus:
    def test_happy_path_returns_200(self, mock_cosmos_container):
        mock_cosmos_container.query_items.return_value = [_AUDIT_RECORD]

        req = _make_request(
            method="GET",
            route_params={"workOrderId": "WO-2026-00123"},
        )
        resp = function_app.get_status(req, "WO-2026-00123")

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["workOrderId"] == "WO-2026-00123"
        assert body["status"] == "approved"
        assert body["decision"]["approvedAmount"] == 850.00

    def test_not_found_returns_404(self, mock_cosmos_container):
        mock_cosmos_container.query_items.return_value = []

        req = _make_request(method="GET", route_params={"workOrderId": "WO-MISSING"})
        resp = function_app.get_status(req, "WO-MISSING")

        assert resp.status_code == 404
        assert "WO-MISSING" in json.loads(resp.get_body())["error"]

    def test_cosmos_error_returns_502(self, mock_cosmos_container):
        err = cosmos_exc.CosmosHttpResponseError(
            message="Service unavailable",
            response=MagicMock(status_code=503, headers={}),
        )
        mock_cosmos_container.query_items.side_effect = err

        req = _make_request(method="GET", route_params={"workOrderId": "WO-001"})
        resp = function_app.get_status(req, "WO-001")

        assert resp.status_code == 502
        assert "Database error" in json.loads(resp.get_body())["error"]

    def test_query_uses_correct_partition_key(self, mock_cosmos_container):
        mock_cosmos_container.query_items.return_value = [_AUDIT_RECORD]

        req = _make_request(method="GET", route_params={"workOrderId": "WO-001"})
        function_app.get_status(req, "WO-001")

        call_kwargs = mock_cosmos_container.query_items.call_args[1]
        assert call_kwargs.get("partition_key") == "WO-001"

    def test_query_filters_by_work_order_id(self, mock_cosmos_container):
        mock_cosmos_container.query_items.return_value = [_AUDIT_RECORD]

        req = _make_request(method="GET", route_params={"workOrderId": "WO-001"})
        function_app.get_status(req, "WO-001")

        call_kwargs = mock_cosmos_container.query_items.call_args[1]
        params = call_kwargs.get("parameters", [])
        id_param = next((p for p in params if p["name"] == "@id"), None)
        assert id_param is not None
        assert id_param["value"] == "WO-001"

    def test_uses_audit_trail_container(self):
        """Handler must request the 'audit-trail' container by name."""
        req = _make_request(method="GET", route_params={"workOrderId": "WO-001"})
        with patch("function_app._cosmos_container") as mock_container_factory:
            mock_container = MagicMock()
            mock_container.query_items.return_value = [_AUDIT_RECORD]
            mock_container_factory.return_value = mock_container

            function_app.get_status(req, "WO-001")

        mock_container_factory.assert_called_once_with("audit-trail")

    def test_response_contains_created_at(self, mock_cosmos_container):
        mock_cosmos_container.query_items.return_value = [_AUDIT_RECORD]

        req = _make_request(method="GET", route_params={"workOrderId": "WO-001"})
        resp = function_app.get_status(req, "WO-001")

        body = json.loads(resp.get_body())
        assert body["createdAt"] == "2026-05-01T12:00:00Z"

    def test_pending_status_no_decision(self, mock_cosmos_container):
        pending_record = {
            "workOrderId": "WO-PENDING",
            "status": "pending",
            "createdAt": "2026-05-01T10:00:00Z",
            "_ts": 1746093600,
        }
        mock_cosmos_container.query_items.return_value = [pending_record]

        req = _make_request(method="GET", route_params={"workOrderId": "WO-PENDING"})
        resp = function_app.get_status(req, "WO-PENDING")

        assert resp.status_code == 200
        body = json.loads(resp.get_body())
        assert body["status"] == "pending"
        assert body.get("decision") is None
