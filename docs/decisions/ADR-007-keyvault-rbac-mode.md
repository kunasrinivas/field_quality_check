# ADR-007: Key Vault in RBAC Mode (over Access Policies)

**Date:** 2026-05-01
**Status:** Accepted

## Context

Azure Key Vault supports two access control models: the legacy **Access Policies** model (per-vault, per-principal permission lists) and the newer **RBAC** model (Azure role assignments, same plane as all other Azure resources).

## Decision

Key Vault is created with `enableRbacAuthorization: true`. Access is granted via three Azure built-in roles assigned to the deployment service principal:
- `Key Vault Secrets Officer`
- `Key Vault Crypto Officer`
- `Key Vault Certificates Officer`

## Consequences

- **Unified access control plane** — RBAC assignments live alongside all other Azure role assignments. They are auditable, manageable, and policyable via the same Azure IAM tooling used for every other resource.
- **No vault-level policy sprawl** — Access Policies accumulate over time and become hard to audit. RBAC roles are scoped and can be listed cleanly with `az role assignment list --scope <vault-id>`.
- **Required for Azure Policy compliance** — Microsoft's Azure Security Benchmark requires RBAC mode for Key Vaults. This aligns the project with standard enterprise compliance postures from day one.
- **Purge protection + 90-day soft delete** — Both are enabled to satisfy GDPR data retention requirements and prevent accidental permanent deletion of secrets. Once purge protection is enabled on a vault, it cannot be disabled — this is a deliberate, irreversible hardening step.
- **RBAC assignment lag** — After a role is assigned, Azure AD propagation can take 1–2 minutes. The workflow does not sleep for this; if an immediately-subsequent step fails due to permission propagation, a re-run resolves it.
