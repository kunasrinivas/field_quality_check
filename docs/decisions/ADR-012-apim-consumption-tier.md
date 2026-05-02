# ADR-012: API Management Consumption Tier for Dev

**Date:** 2026-05-02
**Status:** Accepted

## Context

Azure API Management (APIM) is the entry point for all REST API calls from the contractor portal and internal systems. APIM has four tiers: Consumption, Developer, Standard, and Premium. The choice affects cost, deployment time, VNet integration capability, and developer portal availability.

## Decision

Use the **Consumption** tier for the dev environment.

## Consequences

- **Zero idle cost** — Consumption is billed per million calls with no hourly reservation. In dev, traffic is near-zero; cost scales to nothing when unused.
- **Instant provisioning** — Consumption deploys in seconds. Developer tier (the next cheapest) takes 30–45 minutes per deployment, making iterative Bicep testing impractical.
- **No developer portal** — Consumption does not include the APIM developer portal for API discovery. For dev this is acceptable; the OpenAPI spec in `src/api/openapi.yaml` serves as the contract document instead.
- **No VNet integration** — Consumption cannot be joined to a VNet. The Functions backend is reachable over the public internet (protected by function keys). When private endpoints are added in Sprint 8, APIM must be upgraded to Premium tier to join the VNet. This is a known cost escalation point.
- **Production tier decision deferred** — Standard or Premium will be evaluated based on throughput requirements and VNet hardening needs before the Sprint 8 milestone.
