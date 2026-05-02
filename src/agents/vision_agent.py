"""
Vision Interpretation Agent — Sprint 3 skeleton.

Reads Vision API analysis results from a Cosmos audit-trail record and
produces a structured WorkSummary with an overall confidence score.
Sprint 5 will replace interpret() with full LLM-assisted reasoning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkSummary:
    work_order_id: str
    description: str
    confidence: float
    tags: list[str] = field(default_factory=list)
    objects_detected: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def interpret(audit_record: dict[str, Any]) -> WorkSummary:
    """
    Produce a structured work summary from a Cosmos audit-trail record.

    Filters tags and objects by confidence threshold so only meaningful
    detections are surfaced to downstream agents.
    """
    vision = audit_record.get("visionAnalysis", {})

    caption = vision.get("caption") or "No description available"
    confidence = float(vision.get("captionConfidence") or 0.0)

    tags = [
        t["name"]
        for t in vision.get("tags", [])
        if t.get("confidence", 0.0) >= 0.7
    ]
    objects = [
        o["name"]
        for o in vision.get("objects", [])
        if o.get("confidence", 0.0) >= 0.6
    ]

    return WorkSummary(
        work_order_id=audit_record.get("workOrderId", "unknown"),
        description=caption,
        confidence=round(confidence, 4),
        tags=tags,
        objects_detected=objects,
        raw=vision,
    )
