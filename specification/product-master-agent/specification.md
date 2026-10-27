# Specification: product-master-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [x] Read the project input: `product-requirements-document.md` and `intent.md` at the solution root
- [x] Bootstrap agent code in `assets/product-master-agent/` using instructions from the `sap-agent-bootstrap` section (invoke from inside `assets/product-master-agent/`, use copy commands — do NOT create files manually)
- [x] Install dependencies, validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

> Read [guidelines-agent-skills.md](../guidelines-agent-skills.md) before deciding.

The product lookup workflow is a single-step data retrieval task (no complex branching, no multi-step approval logic). A runtime skill is **not required** — all instructions fit naturally in the system prompt.

- [x] Confirm no runtime skills are needed; proceed without creating any `skills/` folder

---

## Project-Specific Tasks

### System Prompt & Agent Identity

- [x] Set the agent name to `Product Master Data Agent` and description to `Answers natural language questions about product master data from SAP S/4HANA Cloud Public Edition`
- [x] Write the system prompt in `assets/product-master-agent/app/agent.py` with the following instructions:
  - You are a Product Master Data Assistant for Sales Representatives. You help Sales Reps get instant, accurate answers about products from SAP S/4HANA.
  - You answer questions about: product descriptions, product categories, base units of measure, and product classifications.
  - You do NOT answer questions about pricing, stock availability, or order creation — if asked, clearly state these are not available and suggest the user check directly in SAP.
  - IMPORTANT: You MUST use tools to retrieve live data. Never fabricate, guess, or invent product data. Relay tool errors verbatim without adding suggestions.
  - When calling tools that support pagination, always set the page size parameter (`top`, `limit`, `pageSize`, etc.) to a maximum of 100 items to prevent context overflow. Inform the user when this limit is applied.
  - If a tool returns an error, report the error message exactly as received. Do not suggest workarounds unless asked.
  - Support multi-turn conversations: if the user asks a follow-up question about a product already discussed in the session, reuse the context without requiring them to repeat the product identifier.
  - Always present product information in a structured, readable format (use labels and short sentences, not raw JSON).

### Natural Language Product Query (REQ-01)

- [x] Implement intent handling so the agent correctly interprets natural language questions about products (e.g. "What is product P-1001?", "Tell me about product X", "Describe product ABC-100")
- [x] Ensure the agent calls the appropriate MCP tool when a product identifier is mentioned or can be inferred from context
- [x] Implement clarifying question logic: if the user's question is ambiguous and no product identifier can be inferred, ask the user to provide the product ID or a more specific name before making a tool call

### Product Detail Retrieval (REQ-02)

- [x] Use the MCP tools generated from `CE_PRODUCT_0003:v3` to retrieve product details
- [x] Ensure the agent extracts and presents at minimum: product description, product category, and base unit of measure from the API response
- [x] Handle the case where the product does not exist: clearly inform the user "Product [ID] was not found in SAP S/4HANA"

### Product Classification Query (REQ-03)

- [x] Use the MCP tools generated from `API_CLFN_PRODUCT_SRV:v1` to retrieve product classification data
- [x] Present classification information clearly when requested (e.g. "What class does product X belong to?")
- [x] If no classification data exists for a product, inform the user clearly rather than returning an empty or confusing response

### Multi-Turn Conversation Support (REQ-04)

- [x] Ensure the agent maintains conversation context across turns within a session (product ID / name mentioned earlier should be retained)
- [x] Validate that follow-up queries like "What about its category?" resolve correctly to the previously discussed product

### Out-of-Scope Handling (REQ-06)

- [x] Implement explicit handling for out-of-scope questions (pricing, availability, order management):
  - Detect these topics in the user's question
  - Respond with a clear explanation that this capability is not yet available
  - Suggest a manual alternative (e.g. "Please check pricing directly in SAP or contact your pricing team")

---

## API Integrations

### CE_PRODUCT_0003:v3 — Product (Cloud Edition)
- **API spec file:** `specification/product-master-agent/api-specs/CE_PRODUCT_0003_v3.edmx`
- **ORD ID:** `sap.s4:apiResource:CE_PRODUCT_0003:v3`

```text
MCP API: sap.s4:apiResource:CE_PRODUCT_0003:v3
MCP tool scope: read-only
Resources in scope: Product, ProductDescription, ProductPlant, ProductValuationAccount
```

### API_CLFN_PRODUCT_SRV:v1 — Product Master Including Classification
- **API spec file:** `specification/product-master-agent/api-specs/API_CLFN_PRODUCT_SRV_v1.edmx`
- **ORD ID:** `sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1`

```text
MCP API: sap.s4:apiResource:API_CLFN_PRODUCT_SRV:v1
MCP tool scope: read-only
Resources in scope: A_ClfnProduct, A_ClfnProductClass, A_ClfnProductCharc
```

---

## Business Instrumentation

- [x] Implement business step instrumentation for each milestone from the PRD using structured logging with pattern `[MILESTONE_ID].[achieved|missed]: [description]` and OpenTelemetry custom spans:

  | Milestone ID | Description | Log on Achievement | Log on Miss |
  |---|---|---|---|
  | M1 | Question Received | `M1.achieved: user question received and intent classification started` | `M1.missed: no user input received or session initialization failed` |
  | M2 | Data Retrieved | `M2.achieved: product data retrieved from S/4HANA API for product [product_id]` | `M2.missed: S/4HANA API call failed or returned no data for product [product_id]` |
  | M3 | Answer Delivered | `M3.achieved: answer delivered to user for query [query_summary]` | `M3.missed: response generation failed or empty response returned` |
  | M4 | Agent Deployed | `M4.achieved: agent verified in production Joule environment by Sales Representative` | `M4.missed: deployment verification failed or agent not accessible in Joule` |

- [x] Extract business logic from `stream()` into a plain async helper (e.g. `_run_agent()`) to instrument with OpenTelemetry spans without `GeneratorExit` context errors
- [x] Verify `bootstrap(app)` is called after `app = server.build()` in `main.py`

---

## MCP Tool Integration

> Read [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) for complete MCP integration patterns.
> This asset uses **Path A** (API spec files — no existing MCP server).

- [x] Verify `specification/product-master-agent/api-specs/` contains both spec files:
  - `CE_PRODUCT_0003_v3.edmx`
  - `API_CLFN_PRODUCT_SRV_v1.edmx`
- [x] Invoke the `mcp-translation-file` skill for each API spec file to generate translation cards (outputs to `specification/product-master-agent/mcps/<api-spec-stem>/`)
- [x] Invoke the `setup-solution` skill to create MCP server assets for both translation files
- [x] After `setup-solution` completes, read the generated `asset.yaml` for each MCP server asset and copy the `ordId` value exactly — do NOT invent or guess ORD IDs
- [x] Wire MCP tool loading in `agent.py` using `get_mcp_tools()` from the `mcp_tools` module — never import directly from `sap_cloud_sdk.agentgateway`
- [x] Add MCP server dependencies to `assets/product-master-agent/asset.yaml` under `requires` — one entry per generated MCP server using the exact ORD IDs from the generated assets
- [x] Generate `mcp-mock.json` using the `mcp-mock-config` skill after both MCP translation files and setup-solution are complete

---

## Testing

> See [guidelines-agent-python.md](../guidelines-agent-python.md) for Python testing setup and patterns.

- [x] `conftest.py` only sets `IBD_TESTING=true`
- [x] Write unit tests in `assets/product-master-agent/tests/`:
  - `test_get_product_details.py` — tests the product detail retrieval tool interaction (mock MCP response, assert formatted output)
  - `test_get_product_classification.py` — tests the product classification tool interaction (mock MCP response, assert classification output)
  - `test_out_of_scope_handling.py` — tests that pricing/availability questions are handled gracefully without tool calls
  - `test_product_not_found.py` — tests that the agent handles a "not found" API response correctly
- [x] Write one integration test `test_integration.py` executing the end-to-end agent flow: user asks a product question → agent calls MCP tool → agent returns structured answer (all external systems mocked)
- [x] Run `pytest` from `assets/product-master-agent/` (no args) — if coverage < 70%, add tests until threshold is met
- [x] Run `pytest` again from `assets/product-master-agent/` (no args) to generate final `test_report.json`
- [x] Verify `test_report.json` exists in `assets/product-master-agent/`
