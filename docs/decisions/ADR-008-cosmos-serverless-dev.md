# ADR-008: Cosmos DB Serverless Mode for Dev Environment

**Date:** 2026-05-02
**Status:** Accepted

## Context

Azure Cosmos DB offers two capacity modes: **provisioned throughput** (fixed RU/s, billed per hour regardless of usage) and **serverless** (billed per request unit consumed, no minimum commitment). The dev environment has unpredictable, low-volume traffic during build and test phases.

## Decision

Deploy Cosmos DB in serverless mode for the `dev` environment.

## Consequences

- **Zero idle cost** — During development, the database is queried infrequently. Serverless means no RU/s are reserved; cost scales to near-zero when unused.
- **No capacity planning required** — Provisioned throughput requires estimating peak RU/s up front and partitioning accordingly. Serverless defers this decision until production traffic patterns are understood.
- **Production migration required** — Serverless accounts cannot be converted to provisioned throughput in place. When moving to staging/production, a new Cosmos DB account must be created with provisioned mode and data migrated. This is a known cost accepted at this stage.
- **5000 RU/s burst cap** — Serverless has a per-request burst limit of 5000 RU/s. This is sufficient for dev and early UAT but would be a bottleneck at production load. The production Bicep module should use provisioned throughput with autoscale.
- **Session consistency chosen** — Session consistency provides read-your-own-writes guarantees within a session (sufficient for the agent conversation and audit trail use cases) without the cost of Strong consistency or the staleness risk of Eventual.
