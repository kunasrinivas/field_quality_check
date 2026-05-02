# ADR-013: Images Only for Vision POC (Video Excluded)

**Date:** 2026-05-02
**Status:** Accepted

## Context

The blob trigger ingests contractor-submitted field evidence. Evidence can include photos and video recordings of site work. Azure AI Vision's `ImageAnalysis` API supports static images (JPEG, PNG, GIF, BMP, TIFF, WebP) but does not natively process video frames — video analysis requires a separate Azure Video Indexer service with significantly higher complexity and cost.

## Decision

For PI 2 (the POC phase), accept **images only**. Video files are silently skipped by the blob trigger without error. The OpenAPI spec, contractor portal file picker, and `_is_image()` gate in `function_app.py` all enforce this constraint consistently.

## Consequences

- **Reduced scope and risk** — Vision integration is proven end-to-end on a simpler media type before adding video complexity.
- **Lower cost** — Azure AI Vision S1 is sufficient; Video Indexer would add ~$0.035/min on top.
- **Contractor UX** — The portal `accept="image/*"` restricts the file picker at the browser level. Video uploads are rejected at both the API (`400`) and the blob trigger (skip), so no orphaned video blobs accumulate.
- **Known gap** — Contractors who record video evidence instead of photos are not supported in this POC. If video analysis is required post-POC, the trigger must be extended to extract key frames and pass them to Vision, or to call Video Indexer directly.
- **Reversible** — Removing the `_is_image()` guard and adding Video Indexer support is additive and does not require rearchitecting the ingestion layer.
