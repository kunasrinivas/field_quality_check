"""Unit tests for the blob trigger — evidence_blob_trigger + helpers."""
from unittest.mock import MagicMock, patch, call

import pytest

import function_app


def _make_blob(name: str, length: int = 1024, content: bytes = b"fake-image") -> MagicMock:
    blob = MagicMock()
    blob.name = name
    blob.length = length
    blob.read.return_value = content
    return blob


class TestEvidenceBlobTrigger:
    def test_smoke_image_does_not_raise(self):
        blob = _make_blob("WO-001/photo.jpg")
        with patch("function_app._analyse_image", return_value={}), \
             patch("function_app._write_audit_record"), \
             patch("function_app._move_to_processed"):
            function_app.evidence_blob_trigger(blob)

    def test_non_image_is_skipped(self):
        blob = _make_blob("WO-001/clip.mp4")
        with patch("function_app._analyse_image") as mock_vision:
            function_app.evidence_blob_trigger(blob)
            mock_vision.assert_not_called()

    def test_flat_blob_name_falls_back_gracefully(self):
        blob = _make_blob("orphan.jpg")
        with patch("function_app._analyse_image", return_value={}), \
             patch("function_app._write_audit_record"), \
             patch("function_app._move_to_processed"):
            function_app.evidence_blob_trigger(blob)

    def test_image_triggers_full_pipeline(self):
        blob = _make_blob("WO-999/site.png", content=b"img")
        with patch("function_app._analyse_image", return_value={"caption": "cables"}) as mock_a, \
             patch("function_app._write_audit_record") as mock_w, \
             patch("function_app._move_to_processed") as mock_m:
            function_app.evidence_blob_trigger(blob)

        mock_a.assert_called_once_with(b"img", "WO-999", "site.png")
        mock_w.assert_called_once_with("WO-999", "site.png", {"caption": "cables"})
        mock_m.assert_called_once_with("WO-999", "site.png", b"img")

    def test_logs_file_size(self, caplog):
        import logging
        blob = _make_blob("WO-001/img.jpg", length=204_800)
        with caplog.at_level(logging.INFO), \
             patch("function_app._analyse_image", return_value={}), \
             patch("function_app._write_audit_record"), \
             patch("function_app._move_to_processed"):
            function_app.evidence_blob_trigger(blob)
        assert "204800" in caplog.text


class TestIsImage:
    def test_jpg(self): assert function_app._is_image("photo.jpg")
    def test_jpeg(self): assert function_app._is_image("photo.JPEG")
    def test_png(self): assert function_app._is_image("image.png")
    def test_gif(self): assert function_app._is_image("anim.gif")
    def test_bmp(self): assert function_app._is_image("scan.bmp")
    def test_tiff(self): assert function_app._is_image("scan.tiff")
    def test_webp(self): assert function_app._is_image("photo.webp")
    def test_mp4_rejected(self): assert not function_app._is_image("clip.mp4")
    def test_mov_rejected(self): assert not function_app._is_image("clip.mov")
    def test_pdf_rejected(self): assert not function_app._is_image("doc.pdf")


class TestAnalyseImage:
    def _mock_vision_result(self):
        result = MagicMock()
        result.caption.text = "A technician installing cables on a telecom tower"
        result.caption.confidence = 0.92345
        tag = MagicMock()
        tag.name = "cable"
        tag.confidence = 0.95
        result.tags.list = [tag]
        obj = MagicMock()
        obj.tags = [MagicMock(name="tower", confidence=0.88)]
        obj.tags[0].name = "tower"
        obj.tags[0].confidence = 0.88
        result.objects.list = [obj]
        return result

    def test_returns_caption_and_tags(self):
        mock_result = self._mock_vision_result()
        with patch("function_app._vision") as mock_v:
            mock_v.return_value.analyze.return_value = mock_result
            out = function_app._analyse_image(b"bytes", "WO-1", "photo.jpg")

        assert out["caption"] == "A technician installing cables on a telecom tower"
        assert abs(out["captionConfidence"] - 0.9235) < 0.0001
        assert any(t["name"] == "cable" for t in out["tags"])

    def test_vision_failure_returns_error_dict(self):
        with patch("function_app._vision") as mock_v:
            mock_v.return_value.analyze.side_effect = Exception("timeout")
            out = function_app._analyse_image(b"bytes", "WO-1", "photo.jpg")

        assert "error" in out


class TestWriteAuditRecord:
    def test_upserts_to_cosmos(self, mock_cosmos_container):
        function_app._write_audit_record("WO-1", "photo.jpg", {"caption": "cables"})
        mock_cosmos_container.upsert_item.assert_called_once()
        item = mock_cosmos_container.upsert_item.call_args[0][0]
        assert item["workOrderId"] == "WO-1"
        assert item["status"] == "pending"
        assert item["visionAnalysis"] == {"caption": "cables"}

    def test_cosmos_failure_does_not_raise(self, mock_cosmos_container):
        mock_cosmos_container.upsert_item.side_effect = Exception("cosmos down")
        function_app._write_audit_record("WO-1", "photo.jpg", {})  # should not raise


class TestMoveToProcessed:
    def test_uploads_to_processed_container(self, mock_blob_svc, mock_blob_client):
        function_app._move_to_processed("WO-1", "photo.jpg", b"img-bytes")
        mock_blob_svc.get_blob_client.assert_called_once_with(
            container="processed-evidence", blob="WO-1/photo.jpg"
        )
        mock_blob_client.upload_blob.assert_called_once_with(b"img-bytes", overwrite=True)

    def test_upload_failure_does_not_raise(self, mock_blob_svc, mock_blob_client):
        mock_blob_client.upload_blob.side_effect = Exception("storage down")
        function_app._move_to_processed("WO-1", "photo.jpg", b"bytes")  # should not raise
