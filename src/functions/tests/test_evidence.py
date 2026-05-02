"""Unit tests for POST /evidence — submit_evidence handler."""
import json
from unittest.mock import MagicMock, patch

import pytest

import function_app
from tests.conftest import _make_request


class TestSubmitEvidence:
    def test_happy_path_returns_202(self, mock_blob_svc):
        req = _make_request(
            method="POST",
            params={"workOrderId": "WO-001", "filename": "photo.jpg"},
            body=b"\xff\xd8\xff",  # fake JPEG bytes
        )
        resp = function_app.submit_evidence(req)

        assert resp.status_code == 202
        body = json.loads(resp.get_body())
        assert body["status"] == "accepted"
        assert body["workOrderId"] == "WO-001"
        assert body["blobPath"] == "WO-001/photo.jpg"
        assert "jobId" in body

    def test_blob_uploaded_to_correct_path(self, mock_blob_svc, mock_blob_client):
        req = _make_request(
            method="POST",
            params={"workOrderId": "WO-999", "filename": "site.png"},
            body=b"binary-image-data",
        )
        function_app.submit_evidence(req)

        mock_blob_svc.get_blob_client.assert_called_once_with(
            container="raw-evidence", blob="WO-999/site.png"
        )
        mock_blob_client.upload_blob.assert_called_once_with(
            b"binary-image-data", overwrite=True
        )

    def test_missing_work_order_id_returns_400(self, mock_blob_svc):
        req = _make_request(
            method="POST",
            params={"filename": "photo.jpg"},
            body=b"data",
        )
        resp = function_app.submit_evidence(req)

        assert resp.status_code == 400
        assert "workOrderId" in json.loads(resp.get_body())["error"]

    def test_missing_filename_returns_400(self, mock_blob_svc):
        req = _make_request(
            method="POST",
            params={"workOrderId": "WO-001"},
            body=b"data",
        )
        resp = function_app.submit_evidence(req)

        assert resp.status_code == 400
        assert "filename" in json.loads(resp.get_body())["error"]

    def test_empty_body_returns_400(self, mock_blob_svc):
        req = _make_request(
            method="POST",
            params={"workOrderId": "WO-001", "filename": "photo.jpg"},
            body=b"",
        )
        resp = function_app.submit_evidence(req)

        assert resp.status_code == 400
        assert "file bytes" in json.loads(resp.get_body())["error"]

    def test_blob_upload_failure_returns_502(self, mock_blob_svc, mock_blob_client):
        mock_blob_client.upload_blob.side_effect = Exception("network timeout")

        req = _make_request(
            method="POST",
            params={"workOrderId": "WO-001", "filename": "photo.jpg"},
            body=b"image-data",
        )
        resp = function_app.submit_evidence(req)

        assert resp.status_code == 502
        assert "Upload failed" in json.loads(resp.get_body())["error"]

    def test_each_call_generates_unique_job_id(self, mock_blob_svc):
        req = lambda: _make_request(
            method="POST",
            params={"workOrderId": "WO-001", "filename": "photo.jpg"},
            body=b"data",
        )
        r1 = json.loads(function_app.submit_evidence(req()).get_body())
        r2 = json.loads(function_app.submit_evidence(req()).get_body())

        assert r1["jobId"] != r2["jobId"]

    def test_whitespace_only_work_order_id_returns_400(self, mock_blob_svc):
        req = _make_request(
            method="POST",
            params={"workOrderId": "   ", "filename": "photo.jpg"},
            body=b"data",
        )
        resp = function_app.submit_evidence(req)

        assert resp.status_code == 400
