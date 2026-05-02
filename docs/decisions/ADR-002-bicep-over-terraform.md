# ADR-002: Bicep for Infrastructure as Code (over Terraform or ARM)

**Date:** 2026-05-01
**Status:** Accepted

## Context

The infrastructure needs to be version-controlled, repeatable, and deployable via CI/CD. The main candidates were ARM JSON templates, Bicep, and Terraform.

## Decision

Use Azure Bicep as the IaC language for all Azure resource definitions.

## Consequences

- **No state file** — Unlike Terraform, Bicep uses Azure's own ARM deployment engine as the source of truth. There is no `.tfstate` file to store, lock, or corrupt, which removes a class of CI/CD failure modes.
- **Cleaner syntax than ARM** — Bicep compiles to ARM JSON but is far more readable. Parameters, variables, modules, and outputs are first-class constructs.
- **Native `uniqueString()` and other ARM functions** — Built-in functions like `uniqueString(resourceGroup().id)` and `take()` make deterministic globally-unique naming straightforward without external tooling.
- **Modular from the start** — `infra/main.bicep` acts as the root orchestrator; each resource type lives in `infra/modules/`. This mirrors how the system grows: adding a new Azure service = adding one module file and one `module` block in `main.bicep`.
- **Azure-only** — Bicep cannot target non-Azure resources. If the project ever needs multi-cloud, Terraform would need to be adopted. This risk is accepted given the Azure-first platform decision (ADR-001).
