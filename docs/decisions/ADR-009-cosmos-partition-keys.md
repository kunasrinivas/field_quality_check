# ADR-009: Cosmos DB Container Partition Key Design

**Date:** 2026-05-02
**Status:** Accepted

## Context

Cosmos DB distributes data across physical partitions based on a partition key. Choosing the wrong partition key causes hot partitions (one partition receives all traffic), cross-partition fan-out queries (slow and expensive), or uneven storage distribution. The three containers in `fqct-data` serve distinct query patterns driven by the multi-agent workflow.

## Decision

| Container | Partition key | Rationale |
|---|---|---|
| `audit-trail` | `/workOrderId` | Every AI decision, approval, and rework request belongs to a work order. All downstream queries filter by work order. |
| `agent-conversations` | `/sessionId` | Each review run is an isolated session. Agents write and read turns within a single session; cross-session queries do not occur at runtime. |
| `work-orders` | `/contractorId` | Work orders are grouped and retrieved by contractor — compliance checks, invoice aggregation, and dispute resolution all scope to a contractor. |

All containers use partition key version 2 (hash v2), which distributes data more evenly than v1.

## Consequences

- **No cross-partition queries for hot paths** — The three primary runtime access patterns (look up decisions for a work order, replay an agent session, list work orders for a contractor) are all single-partition reads.
- **Reporting queries will fan out** — Aggregate queries such as "all rework requests this month across all contractors" will cross partitions. These are analytics/reporting queries suited to Power BI via Cosmos DB change feed or export — not real-time agent queries — so fan-out cost is acceptable.
- **Cardinality is appropriate** — Work order IDs, session IDs, and contractor IDs all have high cardinality and even distribution, avoiding the hot partition anti-pattern.
- **Revisit at production scale** — If work order volume per contractor becomes very high, `/workOrderId` in `work-orders` may be a better partition key than `/contractorId`. Monitor partition size metrics before going to production.
