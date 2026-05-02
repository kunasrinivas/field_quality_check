# ADR-014: Azure AI Vision for Image Analysis

**Date:** 2026-05-02
**Status:** Accepted

## Context

The Vision Interpretation pipeline needs to extract structured information from contractor field photos: what work was performed, what equipment is visible, and whether the scene is consistent with the work order. Options considered:

1. **Azure AI Vision (ImageAnalysis API)** — managed Azure service, `CAPTION`, `OBJECTS`, and `TAGS` visual features, REST + SDK, pay-per-call.
2. **Azure OpenAI GPT-4 Vision** — multimodal LLM, richer reasoning, higher cost, requires prompt engineering.
3. **Custom Vision** — trainable classifier, requires labelled training data we do not have.
4. **Open-source model (e.g. CLIP, BLIP)** — self-hosted, operational overhead, no managed SLA.

## Decision

Use **Azure AI Vision** (`ImageAnalysisClient`, SDK `azure-ai-vision-imageanalysis==1.0.0`) with `CAPTION`, `OBJECTS`, and `TAGS` features for Sprint 3.

## Consequences

- **Stays within Azure** — No cross-cloud data egress; consistent with the platform decision in ADR-001.
- **Structured output without prompt engineering** — Vision returns typed JSON (`caption.text`, `tags.list`, `objects.list`) which maps directly to the `audit-trail` Cosmos document. A GPT-4V approach would require output parsing.
- **S1 tier** — 10 transactions/second, 5,000 free calls/month on F0 (dev uses S1 for reliability). Cost is ~$1/1,000 calls — negligible at POC volumes.
- **Confidence thresholds** — `vision_agent.py` filters tags ≥ 0.70 and objects ≥ 0.60 to reduce noise. These thresholds are tunable without changing infrastructure.
- **Upgrade path** — Sprint 5 adds LLM reasoning on top of the Vision structured output. GPT-4 (text) receives the `caption` + filtered `tags` as context rather than the raw image, which is cheaper than GPT-4V per call and keeps Vision as the authoritative perception layer.
- **Region** — Deployed to `northeurope` to match Cosmos DB and SQL, avoiding cross-region latency on the Functions → Vision call path.
