# ADR-010: SQL Server Authentication Approach

**Date:** 2026-05-02
**Status:** Accepted

## Context

Azure SQL Server supports three authentication modes: SQL authentication (username + password), Azure AD-only authentication, and mixed mode. The choice affects how application code, Functions, and the deployment pipeline authenticate to the database.

## Decision

Use SQL authentication for the dev environment. The admin password is stored exclusively as a GitHub Secret (`SQL_ADMIN_PASSWORD`) and injected at deploy time via `--parameters sqlAdminPassword="$SQL_ADMIN_PASSWORD"`. It is never written to any file in the repository, including the parameters file `dev.json`.

The Bicep parameter is declared `@secure()` so Bicep's deployment engine treats it as sensitive and excludes it from deployment logs.

## Consequences

- **Simpler dev setup** — Azure AD-only authentication requires assigning an AAD admin to the SQL server and configuring managed identity or service principal access for every connecting service. For dev, SQL auth gets the database running without that overhead.
- **Password risk is contained** — The password never touches the repo, parameters files, or workflow logs. It is only accessible to GitHub Secrets and injected at runtime. This is the minimum viable secret management posture for a non-production environment.
- **Production must migrate to AAD-only** — SQL auth credentials are a shared secret and harder to rotate automatically. Before production, the SQL server should be reconfigured to `azureADOnlyAuthentication: true` with managed identity access for Functions and Logic Apps. This is a known gap, tracked as a Sprint 7 task.
- **Firewall: AllowAzureServices** — A firewall rule with `0.0.0.0 → 0.0.0.0` allows all Azure-hosted services (Functions, Logic Apps) to connect without specifying individual IPs. This is standard practice for Azure PaaS-to-PaaS connectivity but does allow any Azure tenant's services to attempt connections. Network-level hardening (private endpoints, VNet integration) is deferred to Sprint 8.
