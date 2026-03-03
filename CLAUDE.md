# Product Discovery Workspace

This workspace is for product discovery projects at Tabby. Each major project gets a dedicated folder with a structured README seeded from relevant context sources (existing NotebookLM notebooks, BigQuery data). BigQuery and NotebookLM are **context sources**, not things to create per project.

---

## MAJOR PROJECT AUTOMATION

### Trigger Detection

When the user says any of the following (or semantically equivalent phrasing), treat it as a **major project creation request**:

- "I want to start a major project named X"
- "Create a major project called X"
- "New major project: X"
- "Start a project named X"
- "Set up a project for X"
- "I'm starting a major project on X"

Extract the project name X from the message. Also note any mentioned context sources (e.g. "much context can be obtained from [NotebookLM notebook name]").

---

### Name Normalization Rules

Derive two forms from the raw project name:

1. **Folder name** — human-readable, title case, spaces preserved:
   - Capitalize each word
   - Strip leading/trailing whitespace
   - Example: "bnpl checkout analysis" → "BNPL Checkout Analysis"

2. **Snake case name** — for internal IDs and registry:
   - Lowercase everything
   - Replace spaces and hyphens with underscores
   - Remove all characters that are not letters, numbers, or underscores
   - Collapse consecutive underscores into one
   - Strip leading/trailing underscores
   - Example: "B2B POS - Phase 1" → `b2b_pos_phase_1`

---

### Step-by-Step Execution Protocol

When a major project creation trigger is detected, execute ALL steps below in order.

#### Step 1: Confirm with User

Before creating anything, show this and **wait for explicit "yes"**:

```
I'll create a major project with the following:

  Folder:     /Users/zaki/Downloads/Product discovery/<FolderName>/
  Context:    [list any mentioned NotebookLM notebooks or BigQuery datasets to query]

Shall I proceed?
```

#### Step 2: Query Context Sources

If the user mentioned any NotebookLM notebooks as context sources:
- Use `mcp__notebooklm-mcp__notebook_list` to find the notebook by name
- Use `mcp__notebooklm-mcp__notebook_query` to extract:
  - Current state / problem statement
  - Key objectives and outcomes
  - Phases, milestones, or engineering tasks
  - Key open questions and risks
  - Teams and stakeholders involved
  - Relevant data sources (BigQuery tables, etc.)

If the user mentioned BigQuery as a context source, query relevant tables using `mcp__bigquery__execute_sql`.

#### Step 3: Create Project Folder Structure

Run these Bash commands:

```bash
mkdir -p "/Users/zaki/Downloads/Product discovery/<FolderName>/queries"
mkdir -p "/Users/zaki/Downloads/Product discovery/<FolderName>/data"
mkdir -p "/Users/zaki/Downloads/Product discovery/<FolderName>/analysis"
mkdir -p "/Users/zaki/Downloads/Product discovery/<FolderName>/notebooks"
mkdir -p "/Users/zaki/Downloads/Product discovery/<FolderName>/outputs"
touch "/Users/zaki/Downloads/Product discovery/<FolderName>/queries/.gitkeep"
touch "/Users/zaki/Downloads/Product discovery/<FolderName>/data/.gitkeep"
touch "/Users/zaki/Downloads/Product discovery/<FolderName>/analysis/.gitkeep"
touch "/Users/zaki/Downloads/Product discovery/<FolderName>/notebooks/.gitkeep"
touch "/Users/zaki/Downloads/Product discovery/<FolderName>/outputs/.gitkeep"
```

If the folder already exists, warn the user but continue.

#### Step 4: Write README.md

Write `/Users/zaki/Downloads/Product discovery/<FolderName>/README.md` using the template below, populated with all context gathered in Step 2. Do not overwrite if a README already exists.

The README must include (populated from context, not left blank):
- **Objective** — what the project achieves
- **Problem Statement** — current pain, root cause
- **Target State** — what done looks like
- **Phases / Milestones** — structured plan with checkboxes
- **Key Open Questions** — unresolved decisions as a table
- **Teams & Stakeholders** — who is involved and their roles
- **Risks** — severity and mitigations
- **Data Sources** — NotebookLM notebooks and BigQuery sources used
- **Progress Log** — seeded with creation date

#### Step 5: Update Project Registry

Read `/Users/zaki/Downloads/Product discovery/projects.json` (treat as `[]` if missing).
Append and write back:

```json
{
  "name": "<FolderName>",
  "snake_case": "<snake_case_name>",
  "created_at": "<YYYY-MM-DD>",
  "folder_path": "/Users/zaki/Downloads/Product discovery/<FolderName>/",
  "notebooklm_source": "<notebook name if used, else null>",
  "notebooklm_source_id": "<notebook id if used, else null>",
  "notebooklm_source_url": "<notebook url if used, else null>"
}
```

#### Step 6: Report Completion

```
✓ Project "<FolderName>" created.

  Folder:  /Users/zaki/Downloads/Product discovery/<FolderName>/
  Context: Sourced from [notebook/BQ sources used]
  README:  Populated with project brief, phases, risks, open questions

Next steps:
  - Review and refine the README.md
  - Add SQL queries to queries/ for any BQ analysis needed
  - Add docs/exports to notebooks/ for offline reference
```

---

## README Template

```markdown
# <FolderName>

**Created:** <YYYY-MM-DD>
**Status:** Active
**NotebookLM Source:** [<Notebook Name>](<notebook_url>)   ← remove if not applicable

---

## Objective

<1–3 sentence description of what this project achieves>

## Problem Statement

<Current pain points, root causes, data discrepancies>

## Target State

<What "done" looks like — system behaviour, data flows, deprecations>

---

## Migration Phases / Plan

### Phase 1 — <Name>
- [ ] Task 1
- [ ] Task 2

### Phase 2 — <Name>
- [ ] Task 1

### Phase 3 — <Name>
- [ ] Task 1

---

## Key Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | ... | ... | Open |

---

## Teams & Stakeholders

| Team | Role | Key People |
|------|------|------------|
| ... | ... | ... |

---

## Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| ... | High/Medium/Low | ... |

---

## Data Sources

| Source | Location | Purpose |
|--------|----------|---------|
| <NotebookLM name> | [Link](<url>) | Primary context and discovery docs |
| BigQuery `tabby-dp` | <dataset/table> | <purpose> |

---

## Folder Structure

| Folder | Purpose |
|--------|---------|
| `queries/` | BigQuery SQL files |
| `data/` | Raw data exports and snapshots |
| `analysis/` | Python scripts and notebooks |
| `notebooks/` | NotebookLM exports, docs, notes |
| `outputs/` | Reports, dashboards, deliverables |

---

## Progress Log

| Date | Update |
|------|--------|
| <YYYY-MM-DD> | Project created |
```

---

## Jira MCP Usage Rules (Prevent "Prompt Too Long" Errors)

Jira MCP responses are large and accumulate fast in context. Violating these rules causes "prompt is too long" failures.

### Field Selection — always minimise payload

| Situation | Fields to use |
|-----------|--------------|
| Default / most queries | `"summary,status,assignee,priority"` |
| Need issue type | `"summary,issuetype,status"` via `jira_search` (see below) |
| Need description | Add `description` only when user explicitly asks for it |
| Need everything | **Avoid `fields="*all"` entirely if possible** |

- Always set `comment_limit=0` on `jira_get_issue` unless comments are explicitly needed.
- Never use `fields="*all"` for more than **1 issue at a time**.

### Batch Sizes — never fire too many calls in parallel

| Operation | Max parallel calls |
|-----------|-------------------|
| `jira_get_issue` (any fields) | **3** |
| `jira_get_issue` with `fields="*all"` | **1** |
| `jira_search` | **2** |

### Bulk Issue Lookups (>10 issues) — use jira_search with JQL batches

Instead of N individual `jira_get_issue` calls, use `jira_search` with a JQL `issue in (...)` clause:

```
jql: "issue in (MFT-1671, MFT-1672, ..., MFT-1700)"
fields: "summary,issuetype,status,assignee"
limit: 30
```

- One `jira_search` call can return up to 50 issues.
- For 107 issues: 3 calls of ~36 keys each — vastly cheaper than 107 individual calls.
- Never include `description` in bulk lookups.

### When `fields="*all"` is unavoidable (e.g. accessing non-standard fields)

**Do not use MCP at all for bulk fetches.** Use a Python script instead:

1. Write a Python script using `requests` to call the Jira REST API directly.
2. Save all results to a JSON file (`/tmp/issue_types.json` or similar).
3. Run a separate Python script to read the JSON and update Excel/output.
4. This keeps bulk API responses **out of the Claude context window entirely**.

```python
# Example pattern for bulk Jira REST API fetch
import requests, json, os

JIRA_URL   = os.environ.get("JIRA_URL", "https://tabby.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")
JIRA_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

keys = ["MFT-1671", "MFT-1673", ...]  # all keys

results = {}
for i in range(0, len(keys), 50):
    batch = keys[i:i+50]
    jql = "issue in ({})".format(",".join(batch))
    r = requests.get(
        f"{JIRA_URL}/rest/api/3/search",
        params={"jql": jql, "fields": "issuetype,summary", "maxResults": 50},
        auth=(JIRA_EMAIL, JIRA_TOKEN),
    )
    for issue in r.json().get("issues", []):
        results[issue["key"]] = issue["fields"]["issuetype"]["name"]

with open("/tmp/issue_types.json", "w") as f:
    json.dump(results, f)
```

Check environment variables `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN` before falling back to hardcoded values.

### Summary: Anti-patterns that cause "prompt too long"

| Anti-pattern | Fix |
|-------------|-----|
| 107 parallel `jira_get_issue` calls | Use `jira_search` with JQL batches |
| 18 parallel `fields="*all"` calls | Max 1 `*all` call at a time; prefer Python script |
| `fields="*all"` for bulk enrichment | Write Python script, save to JSON, read from file |
| Default fields including `description` | Explicitly set fields, omit `description` |
| `limit: 10` (default) on searches | Use `limit: 5` or lower |

---

## MCP Tools Reference

**NotebookLM (context source — query existing notebooks, do not create new ones):**

| Tool | Purpose |
|------|---------|
| `mcp__notebooklm-mcp__notebook_list` | Find notebooks by name |
| `mcp__notebooklm-mcp__notebook_query` | Extract context from a notebook |
| `mcp__notebooklm-mcp__notebook_get` | Get notebook metadata and sources |
| `mcp__notebooklm-mcp__source_get_content` | Read raw source content |

**BigQuery (context source — query existing data, do not create datasets):**

| Tool | Purpose |
|------|---------|
| `mcp__bigquery__execute_sql` | Run analysis and reconciliation queries |
| `mcp__bigquery__list_dataset_ids` | Discover available datasets |
| `mcp__bigquery__list_table_ids` | Discover tables in a dataset |
| `mcp__bigquery__get_table_info` | Understand table schema |
