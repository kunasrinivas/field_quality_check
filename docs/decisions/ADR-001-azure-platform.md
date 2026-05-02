# ADR-001: Microsoft Azure as the Cloud Platform

**Date:** 2026-05-01
**Status:** Accepted

## Context

The telecom contractor field work review system requires a cloud platform for hosting AI workloads (computer vision, LLMs), data storage, workflow orchestration, and API management. The client operates under GDPR and European data protection law, which constrains where data can reside and processed.

## Decision

Use Microsoft Azure as the sole cloud platform, with all resources deployed to the `westeurope` region.

## Consequences

- **GDPR compliance by default** — `westeurope` (Netherlands) is an EU data residency location; no cross-region data movement is needed.
- **Integrated AI services** — Azure AI Vision, Azure OpenAI, and Azure AI Search are first-party services with native Bicep support, tighter RBAC integration, and no cross-cloud authentication complexity.
- **Enterprise alignment** — Azure AD (Entra ID) is the dominant identity provider in the telecom sector; using Azure avoids a separate IdP federation layer.
- **Lock-in accepted** — The Bicep IaC and Azure-specific service names (Key Vault, Cosmos DB, Azure Functions) are not portable to AWS or GCP. This trade-off is accepted in exchange for tighter native integration and compliance posture.
