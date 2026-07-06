# FederalSpendAI — Cursor Agent Charter

FederalSpendAI is an open-source MCP server and CLI for **Canadian federal government contract spending analysis** using official open data.

## Prerequisites

1. Install: `pip install -e ".[dev]"`
2. Ingest data:
   - Dev fixtures: `federalspendai ingest --datasets awards --fixture-dir tests/fixtures`
   - Production: `federalspendai ingest --datasets awards`
3. Start MCP: `federalspendai serve`

## Data sources (open only)

- **CanadaBuys award notices** — CKAN `a1acb126-9ce8-40a9-b889-5da2b1dd20cb`
- **CanadaBuys contract history** — CKAN `4fe645a1-ffcd-40c1-9385-2c771be956a4`
- **Proactive Disclosure contracts** — CKAN `d8f85d91-7dec-4fd1-8055-483b77225d8b`

## MCP tool catalog

| Tool | Use when |
|------|----------|
| `federalspend_status_tool` | Checking whether data is loaded and fresh |
| `search_contracts_tool` | Finding contracts by vendor, dept, keyword, amount, dates |
| `contract_details_tool` | Full details for one contract |
| `contract_count_tool` | Aggregated counts by dimension |
| `top_vendors_tool` | Ranking suppliers by spend |
| `spending_by_department_tool` | Department-level spend totals |
| `spending_by_category_tool` | UNSPSC / category spend totals |
| `list_departments_tool` | Disambiguating department names |

## Example prompts

1. **Vendor research:** "List departments, then search contracts for vendor 'Lockheed' over $500k."
2. **Oversight:** "Show spending by department and top 10 vendors for PSPC."
3. **Contract lookup:** "Get contract details for reference MX-444028039551."

## Response format

All tools return `{ "_meta": { source, lang, cached, timestamp }, "data": ... }` or `{ "error": { code, message } }`.

## Planned extensions

- NLP on contract text (spaCy + Blackstone)
- Semantic search (sentence-transformers)
- Anomaly detection (scikit-learn)
- Cognitive Substrate event export hooks
