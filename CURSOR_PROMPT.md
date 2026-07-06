# FederalSpendAI — Cursor Agent Charter

FederalSpendAI is an OSS MCP server and CLI for **Canadian federal spending analysis** — contracts, Public Accounts, NLP, semantic search, anomalies, and money-flow tracing.

## Prerequisites

```bash
pip install -e ".[dev]"
python -m spacy download en_core_web_sm
federalspendai ingest --datasets awards,public_accounts --fixture-dir tests/fixtures
federalspendai embed
federalspendai serve
```

## MCP tool catalog

### Data & query
- `federalspend_status_tool`, `search_contracts_tool`, `contract_details_tool`
- `contract_count_tool`, `top_vendors_tool`, `spending_by_department_tool`, `spending_by_category_tool`
- `list_departments_tool`, `search_public_accounts_tool`

### NLP
- `extract_legal_entities_tool`, `analyze_contract_text_tool`, `batch_nlp_tool`

### Search
- `semantic_search_contracts_tool`, `hybrid_search_tool`, `build_embeddings_index_tool`

### Analytics
- `detect_anomalies_tool`, `investigate_anomaly_tool`, `correlate_effects_tool`

### Graphs & Substrate
- `build_money_flow_graph_tool`, `trace_money_flow_tool`, `export_graph_tool` (set `emit_events=true` for Substrate)

## Example end-to-end flow

1. `search_contracts_tool(vendor="Irving")`
2. `analyze_contract_text_tool(reference_number="MX-444028039551")`
3. `detect_anomalies_tool(department="Marine Atlantic")`
4. `investigate_anomaly_tool(vendor="Irving Oil Limited")`
5. `trace_money_flow_tool(vendor="Irving Oil Limited")`
6. `export_graph_tool(vendor="Irving Oil Limited", emit_events=true)`

## Response format

`{ "_meta": {...}, "data": ... }` or `{ "error": { "code", "message" } }`
