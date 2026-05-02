# Telecom Contractor Field Work Review System — Building Blocks & Tasks

> **Legend:** ✅ Done · 🔄 In progress · ⬜ Not started

---

## PI 1 — Foundation & Data Platform

### Sprint 1: Infrastructure Baseline ✅ Complete

| Task | Status | Notes |
| --- | --- | --- |
| GitHub repository + CI/CD pipeline | ✅ | Single `workflow_dispatch` workflow, create/delete modes, confirmation gate |
| Azure Resource Group (`fqct-rg-dev`) | ✅ | `westeurope`, GDPR-compliant region |
| Azure Blob Storage (`fqctstg<hash>`) | ✅ | `raw-evidence` + `processed-evidence` containers, TLS 1.2, no public access |
| Azure Key Vault (`fqct-kv-dev`) | ✅ | RBAC mode, soft delete 90d, purge protection, SP roles assigned |
| Azure SQL Database (`fqct-db-dev`) | ✅ | Basic tier, SQL auth via GitHub Secret, AllowAzureServices firewall rule |
| Azure Cosmos DB (`fqct-cosmos-<hash>`) | ✅ | Serverless, Session consistency, 3 containers with partition keys |
| IaC modularised | ✅ | `infra/modules/`: storage, keyvault, sql, cosmosdb |
| Workflow security hardening | ✅ | `--output none` on all az commands, secrets via step-level env, Bicep outputs only |
| Resource naming convention | ✅ | `fqct-` prefix, `fqctstg` for storage (Azure constraint), `uniqueString` for global uniqueness |
| Architecture Decision Records | ✅ | ADR-001 through ADR-011 in `docs/decisions/` |

### Sprint 2: Ingestion Layer ✅ Complete

| Task | Status | Notes |
| --- | --- | --- |
| API Management Bicep module | ✅ | `infra/modules/apim.bicep` — Consumption tier, 3 operations, Functions backend |
| Azure Functions Bicep module | ✅ | `infra/modules/functions.bicep` — Linux Consumption, Python 3.11, system-assigned MI |
| Functions runtime storage | ✅ | `fqctfnstg<hash>` — separate from evidence storage |
| OpenAPI spec | ✅ | `src/api/openapi.yaml` — 3 endpoints, raw binary upload, full schemas |
| Contractor portal stub | ✅ | `src/portal/index.html` — evidence upload, invoice submit, status check forms |
| `function_app.py` — blob trigger | ✅ | Fires on `raw-evidence/{workOrderId}/` upload; Vision call stubbed for Sprint 3 |
| `function_app.py` — `POST /evidence` | ✅ | Raw binary upload → `raw-evidence/{workOrderId}/{filename}` via BlobServiceClient |
| `function_app.py` — `POST /invoice` | ✅ | JSON validated → inserted into SQL `dbo.invoices` via pyodbc |
| `function_app.py` — `GET /status` | ✅ | Queries Cosmos `audit-trail` by `workOrderId` partition key; returns 404 until Sprint 3 writes records |
| ODBC driver prefix in SQL_CONNECTION | ✅ | `functions.bicep` — ODBC Driver 18 prepended; pyodbc ready on Linux runtime |
| APIM_PUBLISHER_EMAIL moved to secrets | ✅ | Removed from `dev.json`; injected via GitHub Secret at deploy time |
| ADR-012 | ✅ | APIM Consumption tier decision documented |
| Git tag | ⬜ | `v1-ingestion-layer` |

---

## PI 2 — Vision & Knowledge Retrieval

### Sprint 3: Computer Vision 🔄 In progress

| Task | Status | Notes |
| --- | --- | --- |
| Azure AI Vision resource (`fqct-vision-dev`) | ✅ | `infra/modules/vision.bicep` — ComputerVision S1, `northeurope`, endpoint/key wired into Functions |
| Blob trigger → Vision API → Cosmos | ✅ | Images only (POC) — `_analyse_image()` calls Vision with CAPTION/OBJECTS/TAGS; result written to `audit-trail` |
| Move to `processed-evidence` container | ✅ | `_move_to_processed()` uploads blob after Vision analysis; non-images skipped entirely |
| Vision Interpretation Agent (skeleton) | ✅ | `src/agents/vision_agent.py` — `WorkSummary` dataclass, `interpret()` with confidence thresholds |
| OpenAPI spec — images only | ✅ | Removed `video/mp4`; added `image/gif`, `image/bmp`, `image/tiff`, `image/webp` |
| Contractor portal — images only | ✅ | `accept="image/*"` on file input; label updated |
| Unit tests — Vision pipeline | ✅ | 31 tests covering blob trigger, `_is_image`, `_analyse_image`, `_write_audit_record`, `_move_to_processed` |
| Git tag | ⬜ | `v2-vision-agent` |

### Sprint 4: Knowledge Retrieval ⬜ Not started

| Task | Status | Notes |
| --- | --- | --- |
| Azure AI Search (`fqct-search-dev`) | ⬜ | Bicep module, index SOPs, SLAs, contracts |
| Document indexing pipeline | ⬜ | Load compliance docs into search index |
| Semantic + keyword retrieval | ⬜ | Query wrapper for agent context injection |
| Azure Front Door (`fqct-fd-dev`) + WAF | ⬜ | Secure entry routing for APIs |

---

## PI 3 — Multi-Agent Orchestration

### Sprint 5: First Two Agents ⬜ Not started

| Task | Status | Notes |
| --- | --- | --- |
| Vision Interpretation Agent | ⬜ | `src/agents/vision_agent.py` — structured work summary + confidence score |
| Compliance & SLA Agent | ⬜ | `src/agents/compliance_agent.py` — retrieves SOP, checks deviations |
| Agent conversation logging to Cosmos | ⬜ | Write turns to `agent-conversations` container |
| Git tag | ⬜ | `v3-compliance-agent` |

### Sprint 6: Invoice & Decision Agents ⬜ Not started

| Task | Status | Notes |
| --- | --- | --- |
| Invoice Verification Agent | ⬜ | `src/agents/invoice_agent.py` — cross-check invoice vs work order + Vision output |
| Decision & Explanation Agent | ⬜ | `src/agents/decision_agent.py` — approve / partial / rework + justification |
| Azure Logic Apps — HITL workflows | ⬜ | Human-in-the-loop approval routing, rework notifications |
| Approval records written to `audit-trail` | ⬜ | Full decision audit in Cosmos |
| Git tag | ⬜ | `v4-invoice-agent` |

---

## PI 4 — Integration & Hardening

### Sprint 7: External Integrations ⬜ Not started

| Task | Status | Notes |
| --- | --- | --- |
| ERP/billing connector | ⬜ | Push approved amounts to SAP or equivalent |
| Workforce management sync | ⬜ | Work order status updates |
| Ticketing integration | ⬜ | Jira / ServiceNow — rework issue creation |
| AAD-only auth for SQL | ⬜ | Replace SQL auth with managed identity (ADR-010 known gap) |
| Git tag | ⬜ | `v5-integration-test` |

### Sprint 8: Security Hardening + Observability ⬜ Not started

| Task | Status | Notes |
| --- | --- | --- |
| VNETs + private endpoints | ⬜ | All resources: Storage, KV, SQL, Cosmos, Functions |
| Azure Monitor + Log Analytics | ⬜ | Agent decisions, retries, escalations |
| Application Insights | ⬜ | Function and API latency tracing |
| Power BI dashboards | ⬜ | Auto-approval rate, rework frequency, invoice accuracy, latency |
| GDPR audit trail verification | ⬜ | Full data lineage review |
| Responsible AI review | ⬜ | Bias, explainability, human override paths |
| End-to-end test suite | ⬜ | All workflows from upload to decision |

---

## Architecture Decision Records

| ADR | Decision | Date |
| --- | --- | --- |
| [ADR-001](decisions/ADR-001-azure-platform.md) | Microsoft Azure as cloud platform | 2026-05-01 |
| [ADR-002](decisions/ADR-002-bicep-over-terraform.md) | Bicep for IaC over Terraform or ARM | 2026-05-01 |
| [ADR-003](decisions/ADR-003-github-actions-cicd.md) | GitHub Actions for CI/CD | 2026-05-01 |
| [ADR-004](decisions/ADR-004-single-workflow-file.md) | Single consolidated workflow file | 2026-05-01 |
| [ADR-005](decisions/ADR-005-resource-naming-convention.md) | `fqct-` prefix naming convention | 2026-05-01 |
| [ADR-006](decisions/ADR-006-unique-string-naming.md) | `uniqueString()` for globally-scoped names | 2026-05-01 |
| [ADR-007](decisions/ADR-007-keyvault-rbac-mode.md) | Key Vault in RBAC mode | 2026-05-01 |
| [ADR-008](decisions/ADR-008-cosmos-serverless-dev.md) | Cosmos DB serverless for dev | 2026-05-02 |
| [ADR-009](decisions/ADR-009-cosmos-partition-keys.md) | Cosmos DB partition key design | 2026-05-02 |
| [ADR-010](decisions/ADR-010-sql-authentication.md) | SQL Server authentication approach | 2026-05-02 |
| [ADR-011](decisions/ADR-011-workflow-security-hardening.md) | Workflow security hardening | 2026-05-02 |
| [ADR-012](decisions/ADR-012-apim-consumption-tier.md) | API Management Consumption tier for dev | 2026-05-02 |
