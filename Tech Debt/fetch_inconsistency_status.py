"""
Fetches current Jira status + assignee for issues referenced in the Inconsistencies sheet.
Saves results to /tmp/inconsistency_status.json
"""
import json
import sys
import urllib.request
import base64

with open("/Users/zaki/.claude.json") as f:
    cfg = json.load(f)
jira_cfg = cfg["mcpServers"]["jira"]["env"]
JIRA_URL   = jira_cfg["JIRA_URL"]
JIRA_USER  = jira_cfg["JIRA_USERNAME"]
JIRA_TOKEN = jira_cfg["JIRA_API_TOKEN"]

AUTH_HEADER = "Basic " + base64.b64encode(f"{JIRA_USER}:{JIRA_TOKEN}".encode()).decode()
SEARCH_URL = f"{JIRA_URL}/rest/api/3/search/jql"

def jira_search(jql, fields, max_results=50):
    payload = json.dumps({"jql": jql, "fields": fields, "maxResults": max_results}).encode()
    req = urllib.request.Request(
        SEARCH_URL,
        data=payload,
        headers={
            "Authorization": AUTH_HEADER,
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())

# Section 2 — In Excel but NOT in Jira (verify if they actually exist now)
SECTION_2 = ["MFT-1695","MFT-1699","MFT-1700","MFT-1704","MFT-1705","MFT-1755","MFT-1830","MFT-1831"]

# Section 4 — Verdict vs Jira Status Conflicts
SECTION_4 = ["MFT-1779","MFT-1718","MFT-1816"]

ALL_KEYS = SECTION_2 + SECTION_4

jql = "issue in ({})".format(", ".join(ALL_KEYS))
try:
    data = jira_search(jql, fields=["status", "assignee", "summary", "issuetype"], max_results=50)
except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)

results = {}
for issue in data.get("issues", []):
    key = issue["key"]
    fields = issue.get("fields", {})
    results[key] = {
        "summary": fields.get("summary", ""),
        "status": fields.get("status", {}).get("name", "Unknown"),
        "assignee": (fields.get("assignee") or {}).get("displayName", "Unassigned"),
        "issuetype": fields.get("issuetype", {}).get("name", "Unknown"),
    }

print(f"Found {len(results)} / {len(ALL_KEYS)} issues in Jira\n")

print("=== Section 2 (Excel not in Jira) ===")
for k in SECTION_2:
    if k in results:
        r = results[k]
        print(f"  {k} ✓ EXISTS  status={r['status']}  assignee={r['assignee']}")
    else:
        print(f"  {k} ✗ NOT FOUND in Jira")

print("\n=== Section 4 (Verdict conflicts) ===")
for k in SECTION_4:
    if k in results:
        r = results[k]
        print(f"  {k}  status={r['status']}  assignee={r['assignee']}  summary={r['summary'][:60]}")
    else:
        print(f"  {k} ✗ NOT FOUND in Jira")

with open("/tmp/inconsistency_status.json", "w") as f:
    json.dump(results, f, indent=2)
print(f"\nSaved to /tmp/inconsistency_status.json")
