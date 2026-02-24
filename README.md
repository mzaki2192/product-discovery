# product-discovery

A product discovery workspace with NotebookLM MCP integration for AI-powered research.

## NotebookLM MCP Integration

This project is configured to use [NotebookLM](https://notebooklm.google.com) via the [Model Context Protocol (MCP)](https://modelcontextprotocol.io), allowing Claude to query your NotebookLM notebooks directly.

### Prerequisites

- Node.js 18+ and npm
- A Google account with access to NotebookLM

### Setup

The MCP server is configured in `.mcp.json` and runs via `npx` — no separate install needed.

On first use, Claude will prompt you to authenticate:

> "Log me in to NotebookLM."

This opens a browser window for Google OAuth. Your session is saved locally and persists across uses.

### Available Capabilities

Once connected, Claude can:

- **List notebooks** — browse your NotebookLM library
- **Query notebooks** — ask grounded, citation-backed questions
- **Manage sources** — add, update, or remove notebook sources
- **Save notebooks** — store frequently used notebooks with tags

### Configuration Profiles

Control which tools are available by setting the `NOTEBOOKLM_PROFILE` environment variable:

| Profile | Tools | Use case |
|---------|-------|----------|
| `minimal` | 5 | Query-only, lowest token usage |
| `standard` | 10 | Adds library management (default) |
| `full` | 16 | All tools including admin operations |

To set a profile, add it to `.mcp.json`:

```json
{
  "mcpServers": {
    "notebooklm": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "notebooklm-mcp@latest"],
      "env": {
        "NOTEBOOKLM_PROFILE": "minimal"
      }
    }
  }
}
```

### MCP Server

| Field | Value |
|-------|-------|
| Package | [`notebooklm-mcp`](https://www.npmjs.com/package/notebooklm-mcp) |
| Version | latest |
| Transport | stdio |
