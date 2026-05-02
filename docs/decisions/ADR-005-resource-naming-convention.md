# ADR-005: Resource Naming Convention (`fqct-` prefix)

**Date:** 2026-05-01
**Status:** Accepted

## Context

Azure subscriptions often contain resources from multiple projects. Without a consistent prefix, resources become hard to identify, filter, and govern via Azure Policy. Azure resource naming also has per-type constraints that must be respected.

## Decision

All resources in this project use the `fqct-` prefix followed by a resource-type abbreviation and environment suffix.

| Resource type | Pattern | Example |
|---|---|---|
| Resource Group | `fqct-rg-<env>` | `fqct-rg-dev` |
| Key Vault | `fqct-kv-<env>` | `fqct-kv-dev` |
| SQL Server | `fqct-sql-<hash>` | `fqct-sql-4xkzm7p9` |
| Cosmos DB | `fqct-cosmos-<hash>` | `fqct-cosmos-4xkzm7p9` |
| Storage Account | `fqctstg<hash>` | `fqctstg4xkzm7p9qrd2f` |

The storage account name has no separator because Azure storage names only allow lowercase letters and numbers — hyphens and underscores are not permitted.

## Consequences

- **Consistent filtering** — `az resource list --resource-group fqct-rg-dev` or searching `fqct` in the portal immediately surfaces all project resources.
- **Azure Policy ready** — A naming policy requiring the `fqct-` prefix can be applied at subscription level to prevent ungoverned resources.
- **Storage constraint acknowledged** — `fqctstg` is the closest readable equivalent of `fqct-stg` given the no-hyphen restriction. This inconsistency is a consequence of Azure's storage naming rules, not a design choice.
- **Environment suffix** — `-dev` suffix is baked into names now. When adding staging or production environments, the suffix changes (`-stg`, `-prod`) while the prefix and abbreviation stay the same.
