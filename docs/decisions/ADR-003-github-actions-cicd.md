# ADR-003: GitHub Actions for CI/CD

**Date:** 2026-05-01
**Status:** Accepted

## Context

The project needs a CI/CD pipeline for automated infrastructure deployment. The main alternatives were GitHub Actions, Azure DevOps Pipelines, and running scripts manually via Azure CLI.

## Decision

Use GitHub Actions with a single `workflow_dispatch`-triggered workflow for all infrastructure operations.

## Consequences

- **Co-located with code** — The workflow file lives in `.github/workflows/` inside the same repository. No separate pipeline service to configure or authenticate.
- **`workflow_dispatch` over push-triggered** — Infrastructure changes are intentional, destructive if wrong, and should never run on every commit. Manual dispatch with an explicit `mode` input (create/delete) ensures no accidental deployment.
- **GitHub Environments for protection** — The `azure-prod` environment gate means repository admins can require a manual approval before any deployment runs. This is enforced at the GitHub layer, not just in script logic.
- **Secrets management** — `AZURE_CREDENTIALS` and `SQL_ADMIN_PASSWORD` are stored as GitHub Secrets and injected at runtime. They never appear in files committed to the repository.
- **Trade-off vs Azure DevOps** — Azure DevOps Pipelines has deeper native Azure integration (service connections, variable groups). GitHub Actions was chosen for simplicity — the team already uses GitHub for source control, and the `azure/login` action covers the authentication need adequately.
