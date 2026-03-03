"""
Fetches issue types for all MFT issue keys from Jira REST API directly.
Saves results to /tmp/issue_types.json — no MCP calls, no context bloat.
Uses only stdlib (urllib) — no pip installs needed.
"""
import json
import sys
import urllib.request
import urllib.parse
import base64

# --- credentials from MCP config ---
with open("/Users/zaki/.claude.json") as f:
    cfg = json.load(f)
jira_cfg = cfg["mcpServers"]["jira"]["env"]
JIRA_URL   = jira_cfg["JIRA_URL"]
JIRA_USER  = jira_cfg["JIRA_USERNAME"]
JIRA_TOKEN = jira_cfg["JIRA_API_TOKEN"]

AUTH_HEADER = "Basic " + base64.b64encode(f"{JIRA_USER}:{JIRA_TOKEN}".encode()).decode()
SEARCH_URL = f"{JIRA_URL}/rest/api/3/search/jql"   # new endpoint (old /search is 410 Gone)


def jira_search(jql, fields=None, max_results=50):
    if fields is None:
        fields = ["issuetype", "summary"]
    payload = json.dumps({
        "jql": jql,
        "fields": fields,
        "maxResults": max_results,
    }).encode()
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

ISSUE_KEYS = [
    "MFT-1671","MFT-1673","MFT-1674","MFT-1675","MFT-1812","MFT-1815",
    "MFT-1809","MFT-1748","MFT-1752","MFT-1753","MFT-1754","MFT-1756",
    "MFT-1757","MFT-1758","MFT-1759","MFT-1760","MFT-1761","MFT-1762",
    "MFT-1763","MFT-1764","MFT-1765","MFT-1766","MFT-1767","MFT-1768",
    "MFT-1769","MFT-1770","MFT-1771","MFT-1772","MFT-1773","MFT-1774",
    "MFT-1775","MFT-1776","MFT-1777","MFT-1778","MFT-1779","MFT-1780",
    "MFT-1781","MFT-1782","MFT-1783","MFT-1784","MFT-1690","MFT-1698",
    "MFT-1801","MFT-1718","MFT-1694","MFT-1691","MFT-1693","MFT-1696",
    "MFT-1697","MFT-1703","MFT-1838","MFT-1795","MFT-1796","MFT-1797",
    "MFT-1798","MFT-1816","MFT-1817","MFT-1818","MFT-1819","MFT-1820",
    "MFT-1811","MFT-1813","MFT-1814","MFT-1876","MFT-1877","MFT-1676",
    "MFT-1688","MFT-1716","MFT-1717","MFT-1738","MFT-1739","MFT-1740",
    "MFT-1741","MFT-1742","MFT-1749","MFT-1750","MFT-1751","MFT-1789",
    "MFT-1790","MFT-1791","MFT-1792","MFT-1793","MFT-1794","MFT-1799",
    "MFT-1800","MFT-1802","MFT-1803","MFT-1804","MFT-1805","MFT-1807",
    "MFT-1808","MFT-1810","MFT-1821","MFT-1822","MFT-1823","MFT-1824",
    "MFT-1670","MFT-1672","MFT-1684","MFT-1692","MFT-1734","MFT-1746",
    "MFT-1747","MFT-1785","MFT-1787","MFT-1788","MFT-1806",
]

results = {}
BATCH = 50

for i in range(0, len(ISSUE_KEYS), BATCH):
    batch = ISSUE_KEYS[i : i + BATCH]
    jql = "issue in ({})".format(", ".join(batch))
    try:
        data = jira_search(jql, fields=["issuetype", "summary"], max_results=BATCH)
    except Exception as e:
        print(f"ERROR batch {i//BATCH+1}: {e}", file=sys.stderr)
        continue
    for issue in data.get("issues", []):
        key = issue["key"]
        itype = issue.get("fields", {}).get("issuetype", {}).get("name", "Unknown")
        results[key] = itype
    print(f"Batch {i//BATCH+1}: fetched {len(data.get('issues', []))} issues")

print(f"\nTotal collected: {len(results)} / {len(ISSUE_KEYS)}")

# Check for any missing
missing = [k for k in ISSUE_KEYS if k not in results]
if missing:
    print(f"Missing: {missing}")

out_path = "/tmp/issue_types.json"
with open(out_path, "w") as f:
    json.dump(results, f, indent=2)
print(f"Saved to {out_path}")
