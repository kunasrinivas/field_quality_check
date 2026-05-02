"""Unit tests for the blob trigger — evidence_blob_trigger handler."""
from unittest.mock import MagicMock

import pytest

import function_app


def _make_blob(name: str, length: int = 1024) -> MagicMock:
    """Build a minimal InputStream mock with the fields the trigger reads."""
    blob = MagicMock()
    blob.name = name
    blob.length = length
    return blob


class TestEvidenceBlobTrigger:
    def test_smoke_does_not_raise(self):
        """Handler must not raise for a well-formed blob path."""
        blob = _make_blob("WO-2026-00123/photo.jpg")
        function_app.evidence_blob_trigger(blob)  # should not raise

    def test_extracts_work_order_id_from_path(self, caplog):
        import logging
        blob = _make_blob("WO-ABC/site-visit.mp4", length=5_000_000)
        with caplog.at_level(logging.INFO):
            function_app.evidence_blob_trigger(blob)

        assert "WO-ABC" in caplog.text
        assert "site-visit.mp4" in caplog.text

    def test_flat_blob_name_falls_back_gracefully(self):
        """A blob without a '/' in its name should not raise."""
        blob = _make_blob("orphan-file.jpg")
        function_app.evidence_blob_trigger(blob)  # should not raise

    def test_logs_file_size(self, caplog):
        import logging
        blob = _make_blob("WO-001/img.jpg", length=204_800)
        with caplog.at_level(logging.INFO):
            function_app.evidence_blob_trigger(blob)

        assert "204800" in caplog.text
