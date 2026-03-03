# Tech Debt

**Created:** 2026-02-27
**Status:** Active
**NotebookLM Source:** [Billing Discovery](https://notebooklm.google.com/notebook/00e2989e-f678-402b-b207-db79eb6cd733)

---

## Objective

Eliminate the systemic technical debt in the Capital service that stems from a duplicated shadow ledger, manual reconciliation processes, and brittle Direct Debit integrations — making Capital a lean orchestration layer that treats Billing as the sole source of truth for loan state, and replacing all manual operational processes with automated, auditable controls.

## Problem Statement

The Capital service has accumulated several layers of tech debt that create operational risk, data integrity gaps, and engineering toil:

1. **Shadow ledger duplication**: Capital maintains its own `capital_wallet` / installment calculations that run in parallel with Billing. This causes persistent data discrepancies — ECL calculation errors, incorrect rounding, wrong overdue statuses — because two systems independently compute the same loan state. 29,000 bills are currently unverified.

2. **Bank statement reconciliation is manual**: 352 bank transfers are unmatched to disbursements. Collections spreadsheets show ~150 entries vs. 300+ actual bank transfers. There is no automated daily reconciliation job; engineers manually cross-reference CSV exports.

3. **Direct Debit mandate sync is fragile**: There is no webhook for DD responses — Capital polls every 3 hours. Mandate status sync bugs require 4–5 hours of manual engineering intervention per incident. DD mandate lifecycle (pending → active → cancelled) is not reliably mirrored in Capital's database.

4. **Reem integration incomplete**: The loan-funding-reem vendor integration is delayed to June due to missing APIs (Repayments API not started, Schedule API missing accruals data, CBUA approval needed for DD integration). Capital holds placeholder code and incomplete provider implementations.

5. **Test coverage gaps**: Multiple critical services (reconciliation, DD mandate sync, billing proxy) have insufficient or missing unit/integration tests, making refactoring high-risk.

6. **Monitoring blindspots**: 20+ tasks relate to missing observability — no structured logging, no dashboards, no alerting for key capital lifecycle events (disbursements, DD failures, mandate expirations).

## Target State

- **Billing is the sole source of truth**: Capital no longer stores or calculates installment amounts, dates, or statuses. All loan state is proxied from Billing via gRPC. `capital_wallet` shadow ledger tables are deprecated and dropped.
- **Automated reconciliation**: An hourly/daily reconciliation job runs automatically, flags mismatches, and produces an auditable report. Zero unmatched bank transfers in steady state.
- **Reliable Direct Debit**: Webhook-driven or event-driven mandate sync replaces polling. Mandate status is always consistent between DD provider and Capital's DB. Incidents require no manual engineering intervention.
- **Reem integration production-ready**: Full disbursement → repayment → schedule flow working end-to-end with Reem APIs once available.
- **Full observability**: Structured logs, Datadog dashboards, and alerts for all critical capital lifecycle events. On-call engineers have sufficient signal to diagnose incidents without raw SQL queries.
- **High test coverage**: All new and refactored services have unit tests ≥ 80% and integration tests covering critical paths.

---

## Migration Phases / Plan

### Phase 1 — Billing Source of Truth Migration
- [ ] Stop storing installment amounts and statuses in capital (`capital_wallet_loan`) — MFT-1809
- [ ] Proxy installment schedule from Billing gRPC (`GetInvoice` / `CreateInvoice`) — MFT-1812
- [ ] Deprecate and remove `fixed_repayments` table and related code — MFT-1698
- [ ] Migrate FRF (Fixed Repayment Frequency) loans to use Billing DD — MFT-1673
- [ ] Migrate Murabaha loans to use Billing DD — MFT-1674
- [ ] Migrate Non-Murabaha loans to use Billing DD — MFT-1675
- [ ] Block changing payout schedule for merchants with pre-approved loans — MFT-1817
- [ ] Remove shadow amount/status fields from capital loan model — MFT-1815

### Phase 2 — Bank Statement Reconciliation
- [ ] Add `bank_statements` table to save raw BS data — MFT-1801
- [ ] Build bank statement ingestion / parser — MFT-1800
- [ ] Build reconciliation matcher (BS entries ↔ disbursements ↔ repayments) — MFT-1799
- [ ] Build automated daily reconciliation job with alerting — MFT-1802
- [ ] Reconciliation dashboard / report output — MFT-1803
- [ ] E2E tests for reconciliation pipeline — MFT-1804

### Phase 3 — Direct Debit Hardening
- [ ] Fix mandate status sync (remove 3-hour polling, replace with reliable sync) — MFT-1716
- [ ] Handle DD webhook responses properly — MFT-1717
- [ ] Fix DD mandate cancellation edge cases — MFT-1718
- [ ] Integration tests for DD mandate lifecycle — MFT-1805

### Phase 4 — Monitoring & Observability (20+ tasks)
- [ ] Add structured logging to disbursement flow — MFT-1752 to MFT-1784 range
- [ ] Datadog dashboards for capital lifecycle events
- [ ] Alerting for DD failures, mandate expirations, reconciliation mismatches
- [ ] Trace correlation IDs across gRPC calls

### Phase 5 — Reem Integration Completion
- [ ] Complete Reem Repayments API integration — MFT-1838
- [ ] Implement Reem Schedule API with accruals — (pending Reem API availability)
- [ ] DD integration with CBUA approval — (blocked on CBUA)
- [ ] E2E Reem disbursement → repayment flow tests

### Phase 6 — QA & Test Coverage
- [ ] Unit tests for billing proxy service — MFT-1738 to MFT-1742
- [ ] Integration tests for loan application flow — MFT-1816
- [ ] Contract tests for all external gRPC interfaces
- [ ] Load/stress tests for reconciliation job

---

## Key Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | When will Reem Repayments API be available? (currently no start date) | Reem / External | Open |
| 2 | Does CBUA approval cover DD integration with Reem, or does it require a separate process? | Legal / Compliance | Open |
| 3 | Is Neo Vision a viable alternative to Reem for June go-live? What is the gap assessment? | Capital PM | Open |
| 4 | What is the exact migration order for loan types to Billing SoT? (FRF → Murabaha → Non-Murabaha) | Capital Engineering | Open |
| 5 | How do we handle in-flight loans during `capital_wallet` deprecation — do they get backfilled or grandfathered? | Capital Engineering | Open |
| 6 | What is the acceptance threshold for reconciliation mismatches before an alert fires? | Finance / Capital PM | Open |
| 7 | Should DD polling be completely removed or kept as a fallback once webhooks are in place? | Capital Engineering | Open |
| 8 | Who owns the bank statement CSV ingestion pipeline — Capital or Finance/Ops? | Capital PM / Finance | Open |
| 9 | Is the Notify v2→v3 migration complete, or are both versions intentionally active? | Capital Engineering | Open |
| 10 | Should `scoring-merchants` gRPC client be deduplicated in `capital_component.go` (currently instantiated twice)? | Capital Engineering | Open |

---

## Teams & Stakeholders

| Team | Role | Key People |
|------|------|------------|
| Capital Engineering | Implementation owners for all tech debt tasks | Alex Dvorin (arch review/ADR approvals), Capital BE squad |
| Billing / Invoicing | Source of truth provider; Billing gRPC must expose all data Capital needs | Billing squad |
| Finance / Collections | Consumers of reconciliation reports; define matching rules | Collections team |
| Direct Debit Provider | External: must provide webhooks or reliable sync mechanism | External vendor |
| Reem (loan-funding-reem) | External disbursement vendor; API delivery timeline owner | Reem |
| Product / Capital PM | Prioritisation, scope sign-off, Reem/Neo Vision decision | Capital PM |
| Legal / Compliance | CBUA approval for DD integration | Legal |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Billing SoT migration breaks in-flight loans with existing `capital_wallet` state | High | Feature-flag per loan type; run shadow mode in parallel before cutover; backfill plan for existing loans |
| Reem APIs not delivered by June, delaying disbursement go-live | High | Evaluate Neo Vision as alternative; decouple Reem integration from core billing SoT work |
| Bank statement reconciliation mismatches discovered mid-migration cannot be resolved retroactively | High | Freeze unmatched transfers list now; resolve before migration; implement idempotent backfill |
| DD mandate sync bugs cause incorrect loan statuses during migration | High | Fix DD sync issues (Phase 3) before billing cutover; add mandate-level integration tests |
| Dropping `fixed_repayments` table before all loan types migrated causes data loss | High | Use soft-delete / archive first; hard-drop only after all loan types confirmed on Billing |
| Monitoring gaps mean silent failures go undetected post-migration | Medium | Phase 4 (observability) must complete before Phase 1 cutover in production |
| Test coverage gaps make refactoring high-risk with no safety net | Medium | Enforce coverage gates in CI for all modified packages |
| CBUA approval delayed, blocking DD + Reem integration | Medium | Parallel-track CBUA application; identify DD-independent Reem flows that can proceed |
| Shadow ledger discrepancies (29,000 unverified bills) not fully reconciled before migration | Medium | Run full reconciliation audit pre-migration; define acceptable error band with Finance |

---

## Data Sources

| Source | Location | Purpose |
|--------|----------|---------|
| Billing Discovery (NotebookLM) | [Link](https://notebooklm.google.com/notebook/00e2989e-f678-402b-b207-db79eb6cd733) | Primary discovery docs: shadow ledger root cause, Billing SoT architecture, reconciliation mandate |
| Capital Merchant Onboarding (NotebookLM) | NotebookLM | Onboarding flow context, merchant lifecycle |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_loans_history` | Historical loan state, installment data |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_direct_debit_mandates` | DD mandate records and status history |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_direct_debit_payments` | DD payment attempts and outcomes |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_disbursement` | Disbursement records (match vs bank statements) |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_loan_applications` | Application funnel data |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_transaction` | Transaction-level capital events |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_wallet_loan` | Shadow ledger loan records (to be deprecated) |
| BigQuery `tabby-dp.merchants_rawdata` | `capital_wallet_repayment` | Shadow ledger repayment records (to be deprecated) |
| GitLab `capital` service | internal codebase | Implementation reference: contracts, wiring, outbox, DD client |
| Jira backlog | `/Users/zaki/Downloads/Jira (1).csv` | 90 tech debt tasks across all themes |
| Granola meeting notes | Granola MCP | Steerco, DD grooming, reconciliation sessions, billing grooming |

---

## Jira Task Quality Summary

Latest refresh run on **2026-03-03** from live Jira descriptions for all issue keys in the report workbook (`Epic Breakdown` sheet).

105 tasks total across the tech debt report. **0 tasks have Acceptance Criteria defined.**

| Quality | Count | Description |
|---------|-------|-------------|
| ✓ Complete | 20 | Context + Outcome/DoD + Approach all present |
| Partial (1 missing) | 8 | Exactly one of Context / Outcome / Approach is missing |
| Partial (2 missing) | 58 | Only one section present |
| ✗ All missing | 19 | None of the three sections detected |

**Issues currently marked `✗ All missing` include:**
`MFT-1670`, `MFT-1674`, `MFT-1675`, `MFT-1676`, `MFT-1688`, `MFT-1691`, `MFT-1692`, `MFT-1693`, `MFT-1694`, `MFT-1696`, `MFT-1697`, `MFT-1698`, `MFT-1747`, `MFT-1801`, `MFT-1806`, `MFT-1809`, `MFT-1813`, `MFT-1817`, `MFT-1877`.

---

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `queries/` | BigQuery SQL files for capital table analysis and reconciliation |
| `data/` | Raw data exports: Jira CSV, bank statement samples, reconciliation snapshots |
| `analysis/` | Python scripts for task quality analysis, reconciliation gap analysis |
| `notebooks/` | NotebookLM exports, meeting notes, ADRs |
| `outputs/` | Reports, dashboards, deliverables |

---

## GitLab Codebase Intelligence

> Source: `tabby.ai/services/capital` (project ID 60527639), analysed 2026-02-27

### What's Already Implemented (vs Jira "To DO")

| Jira Task | Title | Jira Status | Code Reality |
|-----------|-------|-------------|--------------|
| MFT-1688 | Improve reconciliation job + alerts | Done | ✅ `internal/maintenance/service/billing_report.go` — full 3-way reconciliation (Capital ↔ Wallet ↔ Billing gRPC) live |
| MFT-1691 | Create alert for stuck DD repayments | Done | ✅ `internal/maintenance/stuck_repayments_report.go` + `service/stuck_repayments_report.go` — merged 2026-02-24 (534 additions) |
| MFT-1779 | Fix discrepancies from checker | Ready for release | ✅ Merged TODAY (2026-02-27) — rounding fix in billing reconcile job, 2 MRs |
| MFT-1558 | Upload bank statement in capital bucket | *(not in backlog)* | ✅ Merged 2026-02-25 (1881 additions) — GCS upload via `internal/storage/google.go` implemented |
| MFT-1690 | GetLoans Pagination | To DO | ⚠️ Partially done — patched with hard limit of 500 docs (2026-02-19). Proper cursor pagination still needed |
| MFT-1799 | Implement BS file uploader | To DO | ⚠️ MFT-1558 may already cover this — verify scope overlap before starting |

### Active Open MRs (Tech Debt Relevant)

| MR | Branch | Title | Author | Status | Notes |
|----|--------|-------|--------|--------|-------|
| !482 | `billing-schedule` | Added getting installments for billing loans schedule provider | Denis Larionov | 🔴 **BLOCKED** — pipeline failing, 39 comments, not approved | Core Billing SoT work (MFT-1673/1812). Stalled since 2026-02-20 |
| !415 | unknown | Created repayment scheduling command | Denis Larionov | Open, last updated 2026-02-10 | Older companion to !482 |
| !506 | — | MFT-1876 forbid wrong precision for manual repayments | Evgenii Tumanovskii | Open 2026-02-27 | Active precision fix (MFT-1876) |
| !485 | — | MFT-1638 allow KYB for Reem, remove LE resolver | Evgenii Tumanovskii | Open | Reem KYB integration work |
| !498 | — | MFT-1581 CapitalLoan7DaysPastDueEvent | Marat Minnullin | Open | Analytics event |

### Key Code Structures

**`internal/maintenance/`** — Tech debt nerve centre:
- `billing_reconcile_report.go` — `BillingReconcileReport{TotalLoansCount, Mismatches []BillingMismatch{LoanID, LogValue}}`
- `service/billing_report.go` — Tri-way reconciliation: fetches Capital loans → Wallet loans (shadow ledger) → Billing loans (gRPC), diffs them
- `service/service.go` — `BillingClient.GetLoans` interface against `billingloansdk.GetLoans_Request`; also reads `WalletLoanService` (shadow ledger still in the hot path)
- `stuck_repayments_report.go` — `StuckRepayment{LoanID, RepaymentID, Type, Status, StuckDays}`
- `payment_operation_report.go` — Cross-checks Capital, Wallet, and Transfer counts

**`internal/capital/metrics.go`** — Prometheus metrics already registered:
- `loan_disbursed_total`, `loan_disbursed_amount_total` — disbursement counters
- `repayment_status_change_counter` — by status, currency, loan_status
- `loan_status_changes_total` + `loan_status_change_duration_minutes` histogram (buckets: 10m→7d)
- `loan_without_repayments_with_payout` / `with_error` — gauge per loan_id
- ⚠️ **Known TODO in code**: `// TODO: fix metrics to track applications now.` — metrics currently track loans, not applications

**`internal/wallet/`** — The shadow ledger (to be deprecated):
- `loan/` — full lifecycle: `loan.go`, `loan_plan.go`, `disbursement.go`, `repayment.go`, all with enums + tests
- `invoice/`, `transaction/`, `transfer/`, `withdrawal/` — all live, referenced by maintenance service
- ⚠️ Shadow ledger is still in the **hot reconciliation path** — `WalletLoanService.GetLoans()` called on every billing reconcile run

**`internal/capital/v2/repayments/importer/`** — Repayments file importer:
- Has own `metrics.go`, `service/`, `tasks/`, `transport/`, `repository/`
- `repayments_file.go` + tests — basis for MFT-1877/1876 (amount precision)

**`internal/storage/google.go`** — GCS client: `Save()`, `GetList()`, `GetReader()`, signed URL support. Foundation for bank statement storage (MFT-1558 already uses it).

**`internal/capital/v2/`** — 14 subdirectories covering full loan lifecycle:
`account`, `adjustment`, `applicants`, `applications`, `authorities`, `contracts`, `directdebit`, `disbursement`, `loanfunding`, `loans`, `loansnapshot`, `offers`, `repayments`, `reports`, `waitlists`

### Active Engineers on Tech Debt

| Engineer | Focus Area | Recent Work |
|----------|-----------|------------|
| Evgenii Tumanovskii | Billing reconciliation, stuck repayments | MFT-1684, MFT-1688, MFT-1779 (today), MFT-1691 |
| Denis Larionov | Billing SoT schedule (!482, !415) | billing-schedule branch (blocked) |
| Yahya Elaraby | Bank statement upload, GetLoans pagination | MFT-1558, MFT-1690 |
| Grigorii Leshkevich | Fixed repayment amount from payout | MFT-1686 |
| Artem Arakelyan | Repayment sorting | MFT-1336 |
| Marat Minnullin | Analytics events, KYB demo | MFT-1579, MFT-1581 |

---

## Progress Log

| Date | Update |
|------|--------|
| 2026-02-27 | Project created. Context sourced from Billing Discovery (NotebookLM), Capital Merchant Onboarding (NotebookLM), 6 Granola meeting notes (steerco, DD grooming, reconciliation sessions, billing grooming, bank statement recon), BigQuery merchants_rawdata capital tables, GitLab capital service codebase analysis (commits, open MRs, file trees, key files). 90 Jira tasks imported; quality assessment complete. GitLab deep-dive added: found 3 Jira tasks already implemented, 1 blocked critical MR (!482), active rounding bug fixed today. |
