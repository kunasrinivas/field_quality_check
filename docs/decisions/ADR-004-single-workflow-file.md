# ADR-004: Single Consolidated Workflow File

**Date:** 2026-05-01
**Status:** Accepted

## Context

The project initially had two separate workflow files: `deploy_infrastructure.yml` (handling resource group and Key Vault creation manually via CLI) and `deploy-infra.yml` (handling Bicep template deployment). This split created duplication and confusion about which file was authoritative.

## Decision

Merge both files into a single `deploy_infrastructure.yml` with sequential steps covering the full lifecycle: resource group → Bicep deployment → Key Vault RBAC assignment → deletion.

## Consequences

- **Single source of truth** — One file defines the entire create and delete lifecycle. There is no ambiguity about which workflow to trigger.
- **Step ordering is explicit** — Sequential steps make the dependency chain visible: RG must exist before Bicep runs; Bicep must complete before RBAC can be assigned to the Key Vault it just created.
- **Simpler onboarding** — A new team member reads one file to understand how infrastructure is provisioned and torn down.
- **Less flexibility** — A single file cannot be partially triggered (e.g., "just redeploy Bicep without touching RBAC"). If that becomes a need, the file can be split at that point with clear justification.
