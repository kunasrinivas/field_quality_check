# ADR-006: `uniqueString(resourceGroup().id)` for Globally-Scoped Resource Names

**Date:** 2026-05-01
**Status:** Accepted

## Context

Azure storage accounts, SQL servers, and Cosmos DB accounts must have globally unique names across all Azure tenants worldwide. A fixed name like `fqctstoragedev` will almost certainly be claimed by another subscription, causing deployment failures with a cryptic "name already taken" error.

## Decision

Use Bicep's `uniqueString(resourceGroup().id)` to derive a deterministic suffix for all globally-scoped resource names. The suffix is computed once as `param resourceSuffix` and reused across all modules via `take(resourceSuffix, 8)` where length is constrained.

```bicep
param resourceSuffix string = uniqueString(resourceGroup().id)

var storageAccountName  = 'fqctstg${resourceSuffix}'          // full 13-char hash (24 chars total)
var sqlServerName        = 'fqct-sql-${take(resourceSuffix, 8)}'
var cosmosAccountName    = 'fqct-cosmos-${take(resourceSuffix, 8)}'
```

## Consequences

- **Globally unique** — `uniqueString()` produces a 13-character Base36 hash. Collision probability with another subscription using the same resource group ID is negligible.
- **Deterministic** — The same resource group always produces the same name. Re-running the workflow does not create a new resource; `--mode Incremental` finds the existing one by name.
- **No manual tracking needed** — Engineers do not need to record or coordinate names across environments. The name is always derivable from the resource group ID.
- **Names are opaque in the portal** — `fqctstg4xkzm7p9qrd2f` is not human-readable. The deployment workflow compensates by echoing the resolved names to the Actions log after each deployment.
- **`take()` for SQL and Cosmos** — SQL server and Cosmos DB names have stricter length limits (63 and 44 chars respectively). `take(resourceSuffix, 8)` uses 8 characters of the hash, which is sufficient for uniqueness given the `fqct-` prefix already constrains the namespace.
