# ADR-011: Workflow Security Hardening (Output Suppression and Secret Hygiene)

**Date:** 2026-05-02
**Status:** Accepted

## Context

GitHub Actions workflow logs are stored and accessible to all repository collaborators. Azure CLI commands emit full ARM JSON responses by default, which embed subscription IDs, tenant IDs, and full resource IDs in every output line. Subscription IDs are not secret in the cryptographic sense but their exposure in public or semi-public CI logs unnecessarily increases the attack surface for subscription enumeration and targeted phishing.

## Decision

Apply the following hardening rules to the deployment workflow:

1. **`--output none`** on every `az` command that does not need parsed output (`az group create`, `az deployment group create`, `az role assignment create`, `az group delete`).
2. **Read Bicep outputs by name** — After deployment, query only the specific output field needed (e.g., `--query "properties.outputs.storageAccountName.value"`) rather than displaying the full deployment JSON.
3. **`@secure()` on all secret parameters** — Bicep excludes `@secure()` parameters from deployment operation logs stored in Azure.
4. **SQL password via step-level `env:`** — The secret is bound at the step level (`env: SQL_ADMIN_PASSWORD: ${{ secrets.SQL_ADMIN_PASSWORD }}`), not interpolated directly into the `run:` script string, which would expose it in the process list on the runner.
5. **No echo of resource IDs or object IDs** — Variables like `VAULT_ID` and `SERVICE_PRINCIPAL_OBJECT_ID` are used but never echoed to the log.

## Consequences

- **Logs are safe to share** — Workflow run logs can be shared with collaborators or referenced in bug reports without risk of exposing sensitive identifiers.
- **Deployment status is still visible** — Resource names (storage account name, SQL FQDN, Cosmos account name) are echoed explicitly after deployment. Engineers can confirm what was created without seeing subscription IDs.
- **Reduced debuggability** — `--output none` means that if a CLI command fails, the error message from ARM is still shown (errors go to stderr, not stdout), but success responses are suppressed. This is the right trade-off.
- **Step-level `env:` for secrets** — This is the GitHub Actions recommended pattern. Secrets injected via `env:` are masked in logs automatically by GitHub's secret scanning, even if accidentally echoed.
