# Open-Source Landscape for a Unified Organizational Knowledge Base

*Research date: 2026-11-02. Licenses, star counts and last-push dates are a snapshot from the GitHub API on that date.*

*Simplified 2026-11-04: §16 supersedes the §12 stack, narrows the sources to git, Confluence, database schemas, Lucidchart and an uploads folder, and replaces Postgres with one SQLite file. The standing decision record is [`docs/decisions.md`](../docs/decisions.md). §1–15 are kept as the record of what was considered.*

*Decision record added 2026-11-03: see §12, with the reasoning behind each chosen component in §13 and an adversarial design review of those choices in §14, applied the same day (two components changed, one deferred, two added; Postgres is self-hosted). §15 explains what an entity is and how entity resolution works. How the system is configured and run, including `kb-init`, is in [`docs/design.md`](../docs/design.md), with Markdown diagrams in [`docs/architecture.md`](../docs/architecture.md); the CocoIndex statements in §12 and §13 were corrected for its v1 rewrite at the same time. Per-document permissions and Jira are out of scope. Sections that discuss them are kept as landscape information and are marked superseded in §12.*

## How to read this report

Not every project here was checked to the same depth. Each project carries one of these marks:

| Mark | What was checked |
|---|---|
| **V3** | **Deep-verified.** The deep-research workflow extracted each claim from primary sources. Three independent verifiers then tried to refute it, and it survived. For several of these, the verifiers read the actual source code. |
| **T** | **Tree-checked.** License, stars and activity were checked through the GitHub API. The source tree was then inspected for specific facts, such as which connectors exist or whether there is a split-license directory. |
| **L** | **License-checked.** Only license, stars, last push and archived status were checked through the GitHub API. The license file was read wherever GitHub reports `NOASSERTION`. |
| † | **Not verified in this research.** The detail comes from vendor documentation, a single secondary source, or background knowledge. Confirm it before relying on it. |

The workflow fetched 21 sources, extracted 104 claims and verified 25. Of those, 21 were confirmed and 4 refuted. The second pass then license-checked 85 repositories and inspected the source trees of 8 of them.

---

## 1. Key findings

1. **No open-source project delivers the whole vision under a clean permissive license.** The two closest are PipesHub and Onyx:
   - **PipesHub** (all repo code Apache-2.0) is the closest. It has a knowledge graph, a vector store, MCP server and client, Python/TS/Go SDKs, and connectors that include Postgres, MariaDB, Snowflake, Confluence/Jira (Cloud and Data Center), SharePoint and GitLab. However, the vendor runs an open-core model. Its pricing page reserves SSO/SCIM, RBAC, "entity extraction & knowledge graph updates", the full 50+ connector set and "FULL" permission-aware connectors for a paid Enterprise edition, which can also be self-hosted.
   - **Onyx** (MIT core) has the most mature connector set (about 54 connectors) and its own MCP server. However, all per-source permission sync is in proprietary `ee/` code that needs a paid subscription in production.
2. **Permission-aware retrieval is the biggest gap in freely licensed code.**
   - **Onyx** keeps it in proprietary `ee/` code.
   - **PipesHub** mirrors real ACLs only for connectors it declares `RECORD_LEVEL`. Databases, file shares and personal connectors are `APP_LEVEL`: anyone who can reach the connector sees every record. Permissions are cached for 300 seconds.
   - **Graphiti's** reference MCP server deliberately has no authentication or authorization.
   - **Plan to build this layer** on an Apache-2.0 authorization engine (SpiceDB or OpenFGA).
3. **Code intelligence is well served by MIT/Apache tools.**
   - **codebase-memory-mcp** (MIT, single C binary, 162 Tree-sitter grammars, 17 MCP tools) builds cross-repo HTTP, gRPC and GraphQL edges.
   - **Code-Graph-RAG** (MIT) keeps a shared multi-repo graph with per-project resync.
   - **SCIP and Zoekt** (Apache-2.0) are the precise-navigation and code-search primitives.
4. **For the knowledge graph, Graphiti (Apache-2.0) and LightRAG (MIT) are the leading engines that update incrementally.**
   - **Graphiti** records both when a fact was true and when it was learned, and invalidates outdated facts instead of deleting them.
   - **LightRAG** supports per-document delete with rebuild of the affected entities.
   - **Microsoft GraphRAG's** incremental update silently ignores deleted documents (issue #2590), which makes it a poor fit for continuously synced sources.
5. **Connectors and sync can be assembled from:**
   - **unstructured-ingest** (Apache-2.0). Its source tree has Confluence, Jira, SharePoint, Slack, GitHub, GitLab, Google Drive, OneDrive, Outlook, Notion, SQL and Kafka sources, plus Neo4j, Qdrant, Weaviate and Milvus destinations.
   - **CocoIndex** (Apache-2.0), an incremental engine with Postgres, Kafka, S3 and Google Drive sources and Neo4j and Qdrant targets.
   - **Debezium** (Apache-2.0), for database change data capture (CDC).
   - **Airbyte and PyAirbyte** are Elastic License 2.0 and are flagged.
6. **Copyleft and source-available traps are common in this space, so check each project's license before using it:**
   - **FalkorDB (SSPL) and Memgraph (BSL)** are optional backends for Graphiti and Code-Graph-RAG.
   - **Pathway** (BSL 1.1) is a streaming framework.
   - **GitNexus** is PolyForm Noncommercial.
   - **ParadeDB** is AGPL.
   - **Elasticsearch** is AGPL/SSPL/ELv2.
   - **Neo4j Community** is GPL-3.0.
7. **Nothing was found for these, so they must be built:**
   - Draw.io and Lucidchart ingestion.
   - Mapping database schemas into the graph.
   - One ontology that links code, tickets, docs and people.
   - Ingestion of ops data (logs, incidents, runbooks).
   - An expertise graph of team members.
   - A secure organizational MCP gateway.

---

## 2. Comprehensive repository list (85 repos, grouped by function)

**Legend.** "Lic" is the license as verified. ★ is GitHub stars and "Push" is the last-push date, both as of 2026-11-02. "Mode" is how we could use the project: **Reuse** (use as a dependency), **Extend** (build on its APIs or plugins), **Fork** (take the code and own it), **Study** (architectural reference only) or **Exclude**.

### 2.1 Complete enterprise knowledge platforms

| Project | Lic | ★ | Push | Chk | What it gives us | Mode / flags |
|---|---|---|---|---|---|---|
| [Onyx](https://github.com/onyx-dot-app/onyx) ([docs](https://docs.onyx.app)) | MIT core + **proprietary `ee/`** | 33.2k | 2026-11-02 | V3 | About 54 connectors (Confluence, Jira, Slack, Teams, GitHub, GitLab, Bitbucket, Drive, SharePoint, Notion, Zoom, Gong, Fireflies), hybrid search, chat and agents, its own MCP server (`backend/onyx/mcp_server`). Polls sources every 30 minutes and prunes deleted content every 30 days†. | Fork or Extend the MIT core. **Permission sync, RBAC, SCIM and multi-SSO are in EE.** No database or diagram connectors. |
| [PipesHub](https://github.com/pipeshub-ai/pipeshub-ai) ([docs](https://docs.pipeshub.com)) | Apache-2.0 (whole repo) | 3.9k | 2026-11-02 | V3 | Knowledge graph (Neo4j/ArangoDB), Qdrant and MongoDB. MCP server and client, Py/TS/Go SDKs. About 30+ connector source dirs, including Confluence/Jira Cloud and Data Center, SharePoint, OneDrive, Drive, GitHub, GitLab, Slack, Postgres, MariaDB, Snowflake, ServiceNow, Zoom, Linear, Salesforce. | Fork or Extend. **Open-core**: the pricing page reserves SSO/SCIM, RBAC, LLM entity extraction and KG updates, and the full connector set for Enterprise. Only `RECORD_LEVEL` connectors mirror ACLs. Agents run with their creator's access by default (issue #4545). SAML/OIDC sign-in was removed in 1.0. |
| [pipeshub-ai/mcp-server](https://github.com/pipeshub-ai/mcp-server) | Apache-2.0 | 17 | 2026-11-02 | L | PipesHub's standalone MCP server. | Study or Reuse together with PipesHub. |
| [SWIRL](https://github.com/swirlai/swirl-search) ([docs](https://docs.swirlaiconnect.com)) | Apache-2.0 | 3.1k | 2026-10-27 | V3 | Federated search: queries sources live as the signed-in user, re-ranks the results, and returns RAG answers with citations. No central index, ETL or knowledge graph. | Study the pattern, or Reuse it for sources that must not be copied. The README marks the MCP server and hybrid reranker as Enterprise-only, but a claim saying so was refuted, so the exact boundary is unresolved. |
| [RAGFlow](https://github.com/infiniflow/ragflow) | Apache-2.0 (LICENSE) | 93.4k | 2026-11-02 | T | Deep-document-understanding RAG engine†, GraphRAG mode†, agents†. | Study or Reuse for document RAG. The tree contains `web/src/ee/` ("private" admin UI) even though LICENSE is plain Apache, so review this. Its connector coverage was not confirmed. |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) | MIT | 67.9k | 2026-10-30 | L | Self-hosted multi-user document RAG app with MCP support, a developer API and lightweight collectors (GitHub/GitLab, Confluence)†. | Study or Reuse as a front end. No knowledge graph and no permission sync. |
| [Airweave](https://github.com/airweave-ai/airweave) | MIT | 6.5k | 2026-06-05 | L | Syncs 50+ apps into search exposed through REST and MCP†. | **Archived**, so Fork or Study only. Its sync and connector design is a good reference. |
| [Khoj](https://github.com/khoj-ai/khoj) | **AGPL-3.0** | 37.9k | 2026-08-02 | L | Personal and small-team AI assistant. | **Exclude** because of the license, and it is a poor fit anyway (no enterprise connectors). |

### 2.2 Data connectors and integration frameworks

| Project | Lic | ★ | Push | Chk | What it gives us | Mode / flags |
|---|---|---|---|---|---|---|
| [unstructured-ingest](https://github.com/Unstructured-IO/unstructured-ingest) ([docs](https://docs.unstructured.io/open-source/ingestion/overview)) | Apache-2.0 | 110 | 2026-10-29 | T | Sources in the tree: Confluence, Jira, SharePoint, OneDrive, Outlook, Slack, Discord, GitHub, GitLab, Google Drive, Notion, Salesforce, Zendesk, Airtable, SQL, MongoDB, Kafka, fsspec. Destinations: Neo4j, Qdrant, Weaviate, Milvus, LanceDB, Chroma, Pinecone, Elasticsearch, Couchbase, Databricks. | **Reuse.** The fastest way to get broad source coverage. Per-connector change detection is not documented, and the hosted Unstructured API is a separate paid product. |
| [dlt](https://github.com/dlt-hub/dlt) | Apache-2.0 | 6.1k | 2026-10-31 | L | Python data loading with incremental cursors and a `sql_database` source†. cognee uses it for relational ingestion. | Reuse for database and API extraction. |
| [Debezium](https://github.com/debezium/debezium) | Apache-2.0 | 13.3k | 2026-11-02 | L | Change data capture from Postgres and MySQL logs into Kafka or other sinks†. | Reuse for continuous database sync. |
| [Airbyte](https://github.com/airbytehq/airbyte) / [PyAirbyte](https://github.com/airbytehq/PyAirbyte) | **ELv2** | 22.3k / 342 | 2026-11-02 | L | Very large connector catalog†. | **Flag.** ELv2 allows internal use but forbids offering it as a managed service. Only `airbyte-protocol` is MIT. Keep it out of the primary stack unless legal approves. |
| [LlamaIndex readers (LlamaHub)](https://github.com/run-llama/llama_index) | MIT | 52.8k | 2026-10-26 | L | Many readers for Confluence, Jira, Slack, GitHub, Drive and SharePoint†. | Reuse individual readers. Quality varies from one reader to the next. |
| Onyx MIT connectors (`backend/onyx/connectors`) | MIT | — | — | V3 | About 54 production connectors with polling and pruning. | **Fork individual connectors.** They are MIT outside `ee/`. |
| PipesHub connectors (`backend/python/app/connectors/sources`) | Apache-2.0 | — | — | V3 | Includes the only verified Postgres, MariaDB and Snowflake connectors, plus Confluence and Jira Data Center. | **Fork individual connectors.** Every connector in the repo is Apache-2.0. |

### 2.3 Repository and code intelligence

| Project | Lic | ★ | Push | Chk | What it gives us | Mode / flags |
|---|---|---|---|---|---|---|
| [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp) | MIT | 48.0k | 2026-11-02 | V3 | Single native C binary with 162 vendored Tree-sitter grammars, a SQLite graph with FTS5 (BM25) search and 17 MCP tools (`trace_path`, `detect_changes`, `get_architecture`, `manage_adr`, `ingest_traces`, …). Builds cross-repo `CROSS_HTTP/GRPC/GRAPHQL_CALLS` edges and matches HTTP routes with confidence scores. | **Reuse** as the code-graph engine. The licenses of the bundled grammars and the nomic-embed-code model were not audited. |
| [Code-Graph-RAG](https://github.com/vitali87/code-graph-rag) | MIT | 5.3k | 2026-11-02 | V3 | 14 languages fully parsed with Tree-sitter, 8 more structurally via ast-grep, and compiler front-ends (libclang, go/types, Roslyn/javac/Jedi) for exact facts. Stdio MCP server. One shared multi-repo graph with `update_repository` and `reingest` for incremental updates. SQLite by default. | Reuse or Fork. **`--clean` and `wipe_database` wipe every project.** Its optional Memgraph backend is BSL. |
| [SCIP](https://github.com/scip-code/scip) | Apache-2.0 | 861 | 2026-10-28 | V3 | Protobuf code-index format for go-to-definition, find-references and find-implementations. Bindings for Go, Rust, TS and Haskell, plus a CLI. | **Reuse** as the precise symbol layer and cross-repo symbol identity. |
| [scip-typescript](https://github.com/sourcegraph/scip-typescript) / [scip-java](https://github.com/scip-code/scip-java) / [scip-python](https://github.com/sourcegraph/scip-python) | Apache-2.0 / Apache-2.0 / MIT (Pyright-derived LICENSE.txt) | 119 / 140 / 104 | 2026-11 | L | Per-language SCIP indexers. | Reuse. A claim listing which indexers are production-grade was refuted 0-3, so check each language you need. |
| [Zoekt](https://github.com/sourcegraph/zoekt) | Apache-2.0 | 2.0k | 2026-10-30 | V3 | Trigram code search with substring and regex matching, boolean operators and ranking that uses ctags symbol data. | **Reuse** for multi-repo lexical code search. |
| [Aider](https://github.com/Aider-AI/aider) | Apache-2.0 | 49.9k | 2026-05-22 | L | "Repo map": a Tree-sitter tag extraction ranked by a graph algorithm to give an LLM a compact view of a repo†. | Study the repo-map technique. Pushes have slowed. |
| [codeintel-navigation-mcp](https://pypi.org/project/codeintel-navigation-mcp) | unknown | — | — | — | MCP server combining SCIP, Zoekt and semantic search, with cross-repo blast-radius analysis†. | Study the design. License unverified. |
| [GitNexus](https://github.com/abhigyanpatwari/GitNexus) | **PolyForm Noncommercial** | 48.2k | 2026-11-02 | L | Repo knowledge graph with 16 MCP tools, including cross-repo "group" tools†. | **Exclude.** Not usable commercially. You may study its public design, but do not copy code. |
| [Serena](https://github.com/oraios/serena) | **GPL-3.0** app + MIT SolidLSP | 31.0k | 2026-10-28 | L | LSP-backed MCP server for semantic code navigation†. | The SolidLSP component (MIT) can be reused. The app is GPL, so flag it. |
| [universal-ctags](https://github.com/universal-ctags/ctags) | **GPL-2.0** | 7.3k | 2026-11-02 | L | Symbol tags; Zoekt uses them for ranking. | Fine to run as an external binary. Do not link it into our code. |

### 2.4 AST parsing / Tree-sitter libraries

| Project | Lic | ★ | Push | Chk | What it gives us | Mode |
|---|---|---|---|---|---|---|
| [tree-sitter](https://github.com/tree-sitter/tree-sitter) | MIT | 27.4k | 2026-11-02 | L | Incremental parser core with its query language. | Reuse |
| [py-tree-sitter](https://github.com/tree-sitter/py-tree-sitter) | MIT | 1.5k | 2026-08-30 | L | Python bindings. | Reuse |
| [tree-sitter-language-pack](https://github.com/xberg-io/tree-sitter-language-pack) | MIT | 480 | 2026-11-02 | L | Prebuilt bundle of many grammars (the repo moved to the `xberg-io` org). Check each grammar's license. | Reuse |
| [ast-grep](https://github.com/ast-grep/ast-grep) | MIT | 16.4k | 2026-11-02 | L | Structural search and rewrite over Tree-sitter; Code-Graph-RAG uses it for its 8 structural-only languages. | Reuse |

### 2.5 Document processing and knowledge extraction

| Project | Lic | ★ | Push | Chk | What it gives us | Mode / flags |
|---|---|---|---|---|---|---|
| [Docling](https://github.com/docling-project/docling) ([docs](https://docling-project.github.io/docling/)) | MIT | 70.0k | 2026-11-01 | L | Parses PDF, DOCX, PPTX, XLSX, HTML and images into one DoclingDocument. Layout model (RT-DETR on DocLayNet), TableFormer tables, OCR, and chunkers that keep page and bounding-box provenance for citations. On CPU it benchmarked at 3.1 s/page, faster than Unstructured at 4.2 s/page (from the Docling technical report). | **Reuse.** The model weights carry their own licenses. |
| [docling-mcp](https://github.com/docling-project/docling-mcp) | MIT | 782 | 2026-10-27 | L | Docling exposed as MCP tools. | Reuse |
| [Unstructured](https://github.com/Unstructured-IO/unstructured) | Apache-2.0 | 15.7k | 2026-11-02 | L | Partitioning for more than 65 file formats†. Used by unstructured-ingest. | Reuse |
| [MarkItDown](https://github.com/microsoft/markitdown) | MIT | 193.5k | 2026-10-28 | L | Lightweight conversion of Office files, PDF, HTML and more to Markdown†. | Reuse as a fast path for simple documents. |
| [Apache Tika](https://github.com/apache/tika) | Apache-2.0 | 4.1k | 2026-11-02 | L | Text and metadata extraction for more than 1,000 formats, run as a JVM server†. | Reuse as a long-tail fallback. |
| [MinerU](https://github.com/opendatalab/MinerU) | Apache-2.0 **+ extra terms** | 83.0k | 2026-11-02 | L | High-accuracy PDF parsing. | **Flag.** A commercial license is required above 100M MAU or USD 20M monthly revenue, measured across you and your affiliates. |
| [Whisper](https://github.com/openai/whisper) / [WhisperX](https://github.com/m-bain/whisperX) / [pyannote-audio](https://github.com/pyannote/pyannote-audio) | MIT / BSD-2 / MIT | 111.8k / 25.0k / 10.8k | 2026 | L | Meeting transcription with word timestamps and speaker diarization (who spoke when). | Reuse. Some pyannote models on Hugging Face are gated, so check their terms†. |
| [tbls](https://github.com/k1LoW/tbls) | MIT | 4.4k | 2026-10-31 | L | Generates documentation of tables, columns, foreign keys and comments for Postgres, MySQL and others, including JSON output†. | **Reuse** as the source for database schemas in the graph. |
| [SchemaSpy](https://github.com/schemaspy/schemaspy) | **LGPL-3.0** | 3.7k | 2026-03-05 | L | Database schema analysis and ER diagrams. | Fine to run as an external tool. Prefer tbls. |
| [draw.io](https://github.com/jgraph/drawio) | Apache-2.0 | 9.1k | 2026-10-30 | L | The editor itself. Its file format is mxGraph XML (often compressed). | Reference only. A Draw.io parser is a small custom build (see §10). |

### 2.6 Knowledge-graph and GraphRAG frameworks (and graph stores)

| Project | Lic | ★ | Push | Chk | What it gives us | Mode / flags |
|---|---|---|---|---|---|---|
| [Graphiti](https://github.com/getzep/graphiti) ([docs](https://help.getzep.com/graphiti)) | Apache-2.0 | 32.4k | 2026-11-01 | V3 | Temporal knowledge graph. It updates incrementally from "episodes", tracks both when a fact was true and when it was ingested (`valid_at` / `invalid_at` / `expired_at` / `created_at`), and uses an LLM to invalidate outdated facts. Entity and edge types are defined as Pydantic models. Search combines semantic and BM25 with RRF, and graph traversal is available through search recipes. | **Reuse** as the graph layer. Invalidation is LLM-driven and not deterministic. Bulk add may skip invalidation. It has no connectors, multi-tenancy or access control, and its reference MCP server has no authentication. |
| [LightRAG](https://github.com/hkuds/lightrag) | MIT | 40.5k | 2026-10-29 | V3 | Stores a knowledge graph and vectors together, with five query modes (local, global, hybrid, naive, mix, plus bypass). Supports incremental insert and `adelete_by_doc_id`, which rebuilds shared entities from the extraction cache. | **Reuse** for graph-plus-vector retrieval. Test deletion on each storage backend. It has no connectors. |
| [Microsoft GraphRAG](https://github.com/microsoft/graphrag) | MIT | 36.5k | 2026-11-02 | V3 (issue) | Hierarchical community summaries for "global" questions across a corpus. | Study. `graphrag update` ignores deleted documents (issue #2590), so it is not suited to continuous sync. |
| [cognee](https://github.com/topoteretes/cognee) | Apache-2.0 | 33.0k | 2026-11-02 | T | Knowledge-graph memory for agents. Ingestion is dlt-based, including `dlt_schema_graph.py`, which maps relational schemas into the graph. | Reuse or Study, especially for turning database schemas into graph nodes. |
| [fast-graphrag](https://github.com/circlemind-ai/fast-graphrag) | MIT | 4.0k | 2025-11-01 | L | Lightweight GraphRAG that ranks results with PageRank†. | Study only. No pushes for a year. |
| [neo4j-graphrag-python](https://github.com/neo4j/neo4j-graphrag-python) | Apache-2.0 (+ some PSF-licensed parts) | 1.3k | 2026-11-02 | L | Official Neo4j library for building graphs with KG builders and retrievers†. | Reuse if Neo4j is the graph store. |
| [Apache AGE](https://github.com/apache/age) | Apache-2.0 | 4.9k | 2026-10-13 | L | Property graph and openCypher queries inside Postgres. | Reuse to keep graph, vectors (pgvector) and relational data in one Postgres. |
| [Neo4j Community](https://github.com/neo4j/neo4j) | **GPL-3.0** | 17.4k | 2026-10-23 | L | The default backend for Graphiti, PipesHub and others. | **Flag.** Running it unmodified as a separate server is common practice, but review it. Clustering, RBAC and hot backup are commercial-only†. |
| [Memgraph](https://github.com/memgraph/memgraph) | **BSL 1.1 + MEL** | 4.6k | 2026-11-02 | L | Optional Code-Graph-RAG backend. | **Exclude** from primary recommendations. |
| [FalkorDB](https://github.com/FalkorDB/FalkorDB) | **SSPL** | 10.5k | 2026-11-02 | L | Optional backend for Graphiti and CocoIndex. | **Exclude.** |
| [Kuzu](https://github.com/kuzudb/kuzu) | MIT | 4.0k | 2025-10-10 | L | Embedded graph database. | **Archived**, so avoid it. |

### 2.7 Incremental ingestion and synchronization engines

| Project | Lic | ★ | Push | Chk | What it gives us | Mode / flags |
|---|---|---|---|---|---|---|
| [CocoIndex](https://github.com/cocoindex-io/cocoindex) ([docs](https://cocoindex.io/docs)) | Apache-2.0 | 11.8k | 2026-11-02 | T | Rust core with a Python SDK. Processes only changed data, using content fingerprints to skip unchanged rows. A live-update mode keeps targets current, and it reprocesses when the flow definition changes. Connectors in the tree: localfs, S3, Azure Blob, OCI storage, Google Drive, Postgres, Kafka, BigQuery, Snowflake, SQLite, Neo4j, FalkorDB, Qdrant, LanceDB, SurrealDB, Turbopuffer, Valkey, Doris. | **Reuse** as the indexing engine. It has no Confluence, Jira or Slack sources. The Postgres LISTEN/NOTIFY change capture comes from one changelog only†. |
| [Pathway](https://github.com/pathwaycom/pathway) | **BSL 1.1** | 62.0k | 2026-10-30 | L | Streaming ETL with a Rust engine for live RAG. | **Exclude** from primary recommendations. |
| Debezium, dlt | see §2.2 | | | | Database change capture and incremental API loads. | Reuse |

### 2.8 Vector databases and hybrid search

| Project | Lic | ★ | Push | Chk | Notes | Mode / flags |
|---|---|---|---|---|---|---|
| [OpenSearch](https://github.com/opensearch-project/OpenSearch) | Apache-2.0 | 14.0k | 2026-11-02 | L | Native BM25 plus kNN hybrid search; the permissive replacement for Elasticsearch. | **Reuse** |
| [Qdrant](https://github.com/qdrant/qdrant) | Apache-2.0 | 35.4k | 2026-11-02 | L | Sparse plus dense hybrid search through its Query API, and payload filters. RBAC is a proprietary enterprise feature†. | **Reuse.** Enforce access control in our application layer. |
| [pgvector](https://github.com/pgvector/pgvector) | PostgreSQL License (permissive) | 23.6k | 2026-10-31 | L | Vectors inside Postgres. Combine with Postgres full-text search for hybrid search. | **Reuse** at small to medium scale. |
| [Milvus](https://github.com/milvus-io/milvus) | Apache-2.0 | 46.6k | 2026-11-02 | L | Large-scale vector database with sparse vectors and BM25†. | Reuse |
| [Vespa](https://github.com/vespa-engine/vespa) | Apache-2.0 | 7.2k | 2026-11-02 | L | Hybrid ranking engine. Onyx is reported to use it†. | Reuse |
| [LanceDB](https://github.com/lancedb/lancedb) | Apache-2.0 | 11.8k | 2026-11-02 | L | Embedded columnar vector store with full-text search†. | Reuse for embedded or local use. |
| [Weaviate](https://github.com/weaviate/weaviate) | BSD-3 + **Weaviate License in `wl/`** | 16.9k | 2026-11-02 | L | Hybrid search. | **Flag:** check which features live in `wl/`. |
| [Meilisearch](https://github.com/meilisearch/meilisearch) | MIT + **BUSL-1.1 EE** | 59.8k | 2026-11-02 | L | Keyword and hybrid search. | **Flag.** |
| [Typesense](https://github.com/typesense/typesense) | **GPL-3.0** | 27.1k | 2026-10-30 | L | Search engine. | Flag. |
| [pg_textsearch](https://github.com/timescale/pg_textsearch) | PostgreSQL License (permissive) | 4.1k | 2026-11-02 | L | BM25 index inside Postgres with configurable `k1` and `b`; supports Postgres 17 and 18 (README). Added 2026-11-03. | **Reuse** for keyword search in the single store. |
| [ParadeDB](https://github.com/paradedb/paradedb) | **AGPL-3.0** | 9.5k | 2026-11-02 | L | BM25 inside Postgres. | **Exclude.** |
| [VectorChord-bm25](https://github.com/tensorchord/VectorChord-bm25) | **AGPLv3 or ELv2** | 381 | 2026-08-05 | L | BM25 inside Postgres. Added 2026-11-03. | **Exclude.** |
| [Elasticsearch](https://github.com/elastic/elasticsearch) | **AGPL / SSPL / ELv2** | 78.5k | 2026-11-02 | L | Search engine. | **Exclude.** Use OpenSearch. |
| VectorChord, Redis 8+ | **AGPL or ELv2**; **AGPL/RSAL/SSPL** | — | — | (fetched source) | — | **Exclude.** |

### 2.9 RAG and contextual retrieval frameworks

| Project | Lic | ★ | Push | Chk | Notes |
|---|---|---|---|---|---|
| [LlamaIndex](https://github.com/run-llama/llama_index) | MIT | 52.8k | 2026-10-26 | L | Readers, index abstractions, routers and retrievers. Use it selectively, not as the platform core. |
| [Haystack](https://github.com/deepset-ai/haystack) | Apache-2.0 | 26.9k | 2026-11-02 | L | Pipeline-based RAG with explicit components. Good for the retrieval-service layer. |
| [LangChain](https://github.com/langchain-ai/langchain) | MIT | 148.9k | 2026-11-02 | L | Broad integrations, including the SpiceDB retriever. |

### 2.10 MCP servers and organizational knowledge integrations

| Project | Lic | ★ | Push | Chk | Notes |
|---|---|---|---|---|---|
| [modelcontextprotocol/servers](https://github.com/modelcontextprotocol/servers) | MIT → Apache-2.0 (transition) | 91.7k | 2026-10-29 | L | Reference servers. Both licenses are permissive. |
| [github-mcp-server](https://github.com/github/github-mcp-server) | MIT | 34.2k | 2026-11-02 | L | Official GitHub MCP server for live repo, PR and issue tools. |
| [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) | MIT | 6.1k | 2026-09-19 | L | Confluence and Jira MCP server for Cloud and Server/DC†. |
| [gitlab-mcp](https://github.com/zereight/gitlab-mcp) | MIT | 2.1k | 2026-11-02 | L | GitLab MCP server. |
| [slack-mcp-server](https://github.com/korotovsky/slack-mcp-server) | MIT | 1.9k | 2026-07-16 | L | Slack MCP server. |
| Onyx MCP server (`backend/onyx/mcp_server`) | MIT (core) | — | — | T | Exposes the indexed knowledge to Claude Code, Codex and other MCP clients. |
| Graphiti MCP server | Apache-2.0 | — | — | V3 | 13 tools, including `clear_graph` and `delete_episode`. **No authentication or authorization, by design.** |
| codebase-memory-mcp, Code-Graph-RAG, docling-mcp, pipeshub mcp-server | see above | | | | Specialized MCP servers. |

These live-tool MCP servers do not replace the indexed knowledge base. They complement it for live lookups and actions.

### 2.11 Workflow orchestration and event processing

| Project | Lic | ★ | Push | Chk | Notes |
|---|---|---|---|---|---|
| [Temporal](https://github.com/temporalio/temporal) | MIT | 24.1k | 2026-11-02 | L | Durable workflows. Good fit for long-running per-source sync jobs with retries and cursors. |
| [Dagster](https://github.com/dagster-io/dagster) | Apache-2.0 | 16.4k | 2026-10-30 | L | Asset-oriented orchestration with lineage. Good fit for the "index as data assets" model. |
| [Airflow](https://github.com/apache/airflow) | Apache-2.0 | 47.3k | 2026-11-02 | L | Mature batch scheduling. |
| [Kestra](https://github.com/kestra-io/kestra) | Apache-2.0 | 30.1k | 2026-11-02 | L | Event-driven, YAML-defined flows. Check what its open-source edition covers versus Enterprise†. |
| [Prefect](https://github.com/PrefectHQ/prefect) | Apache-2.0 | 24.1k | 2026-11-02 | L | Python-native workflows. |
| [Hatchet](https://github.com/hatchet-dev/hatchet) | MIT | 8.2k | 2026-11-02 | L | Postgres-backed task queue and workflows. |
| Debezium + Kafka | Apache-2.0 | — | — | L | Event streaming for database changes. |

### 2.12 Security, authorization and permission-aware retrieval

| Project | Lic | ★ | Push | Chk | Notes | Mode |
|---|---|---|---|---|---|---|
| [SpiceDB](https://github.com/authzed/spicedb) | Apache-2.0 | 7.2k | 2026-11-01 | L | Zanzibar-style relationship-based access control (ReBAC). `LookupResources` gives the IDs a user can access, which can pre-filter vector search. | **Reuse** |
| [OpenFGA](https://github.com/openfga/openfga) | Apache-2.0 | 6.1k | 2026-10-30 | L | Zanzibar-style ReBAC (a CNCF project). `ListObjects` supports the same pre-filtering. | **Reuse** (choose either SpiceDB or OpenFGA) |
| [langchain-spicedb](https://github.com/authzed/langchain-spicedb) | Apache-2.0 | 1 | 2026-05-20 | L | Retriever that pre- or post-filters with SpiceDB. Defaults to deny on errors (`fail_open=False`) and drops documents without a resource ID. | Study, or reuse the pattern |
| [needtoknow](https://pypi.org/project/needtoknow/) (repo now [wardowl](https://github.com/muzakkirhussain011/wardowl)) | MIT | 1 | 2026-10-30 | L | Authorization-aware retrieval adapter for OpenFGA, SpiceDB, OPA and Cerbos over Qdrant, pgvector, Milvus, OpenSearch and others. `auto` mode picks pre- or post-filtering, and post-filtering widens the search until enough permitted results are found. | Study, since it has a single maintainer |
| [VaultRAG](https://github.com/AgentPostmortem/VaultRAG) | MIT | 1 | 2026-09-16 | (fetched) | Puts the ACL check in the same Postgres SQL query as hybrid search, so unauthorized chunks are never fetched or scored, and denies access by default. | Study the pattern |
| [Cerbos](https://github.com/cerbos/cerbos) | Apache-2.0 | 4.6k | 2026-11-02 | L | Policy-based access control (attribute and role rules). | Reuse for policy rules |
| [OPA](https://github.com/open-policy-agent/opa) | Apache-2.0 | 12.4k | 2026-11-02 | L | General policy engine. | Reuse for gateway and API policy |
| [OPAL](https://github.com/permitio/opal) | Apache-2.0 | 5.5k | 2026-10-30 | L | Pushes policy and data updates to OPA and Cedar agents in real time. | Study or Reuse for keeping permissions in sync |

---

## 3. Top 20 projects ranked by relevance

Ranking considers fit to the vision, license eligibility, maturity, and how much custom work each one removes.

| # | Project | Layer | Lic | Why it ranks here |
|---|---|---|---|---|
| 1 | **PipesHub** | Full platform | Apache-2.0 (open-core features) | The only Apache project combining a knowledge graph, vectors, MCP, SDKs and database plus SaaS connectors. Even if we never deploy it, its connector and permission code can be forked. |
| 2 | **Onyx** (MIT core) | Full platform | MIT + EE | The most mature connector set, with polling and pruning, hybrid search and an MCP server. Permission sync is EE-only. |
| 3 | **Graphiti** | Knowledge graph | Apache-2.0 | Temporal, incremental graph with hybrid search and custom entity types; the best fit for knowledge that changes continuously. |
| 4 | **codebase-memory-mcp** | Code intelligence | MIT | Cross-repo and cross-service edges, 162 languages and MCP in one binary, which covers repository initialization directly. |
| 5 | **unstructured-ingest** | Connectors | Apache-2.0 | Covers most target SaaS sources, plus graph and vector destinations, in one library. |
| 6 | **CocoIndex** | Incremental sync | Apache-2.0 | Purpose-built incremental indexing with live updates and graph and vector targets. |
| 7 | **Docling** | Document parsing | MIT | High-quality layout and table parsing that keeps provenance for citations; has an MCP server. |
| 8 | **LightRAG** | Graph RAG | MIT | Graph plus vector retrieval with real per-document delete and rebuild. |
| 9 | **Code-Graph-RAG** | Code intelligence | MIT | Multi-repo graph, compiler-accurate facts and incremental `reingest`. An alternative to #4. |
| 10 | **SpiceDB / OpenFGA** | Authorization | Apache-2.0 | The base for the permission layer we must build. |
| 11 | **SCIP** (+ indexers) | Code intelligence | Apache-2.0 | Precise cross-repo symbol identity. |
| 12 | **Zoekt** | Code search | Apache-2.0 | Proven multi-repo code search. |
| 13 | **OpenSearch** | Hybrid search | Apache-2.0 | BM25 plus kNN hybrid at scale, under a permissive license. |
| 14 | **Qdrant** | Vector and hybrid search | Apache-2.0 | Sparse plus dense hybrid search and filters. Already used by PipesHub. |
| 15 | **Debezium** | Database change capture | Apache-2.0 | Continuous Postgres and MySQL sync. |
| 16 | **cognee** | Knowledge-graph memory | Apache-2.0 | Maps relational schemas into the graph via dlt. Reference for database-to-graph mapping. |
| 17 | **Temporal** (or Dagster) | Orchestration | MIT (Apache) | Durable per-source sync workflows. |
| 18 | **mcp-atlassian / github-mcp-server / gitlab-mcp** | Live MCP | MIT | Ready-made live-access tools to offer alongside the indexed knowledge. |
| 19 | **SWIRL** | Federated search | Apache-2.0 | Pattern and code for sources that must not be copied. |
| 20 | **tbls** | Database schema | MIT | Fills the database-schema ingestion gap with structured output. |

**Honorable mentions:** Apache AGE and pgvector (an all-in-Postgres option), Haystack, LlamaIndex, MarkItDown, dlt, AnythingLLM, RAGFlow, Microsoft GraphRAG (for its community-summary ideas), WhisperX, OPAL, and Airweave (archived, but worth studying).

---

## 4. Detailed analysis of the 10 best projects

### 4.1 PipesHub (V3 + additional code findings)
- **Repo:** https://github.com/pipeshub-ai/pipeshub-ai, with docs at https://docs.pipeshub.com
- **Problem it solves:** Self-hosted workplace AI. It connects enterprise apps, indexes them into a graph plus vector store, and serves search, chat and agents. Agents can call it over MCP and SDKs.
- **Features:**
  - Graph-backed retrieval with block-level citations.
  - Real-time and scheduled indexing.
  - A no-code agent builder.
  - MCP server and client.
  - Python, TypeScript and Go SDKs.
- **Architecture and stack:**
  - A Python backend for connectors, indexing and retrieval, plus a Node.js API service for accounts, permissions, knowledge bases and files.
  - Storage is a graph (Neo4j by default, or ArangoDB), Qdrant vectors and MongoDB.
  - Permissions are copied into the graph at sync time and cached in Redis with `DEFAULT_TTL_SECONDS = 300`.
- **Connectors (in `backend/python/app/connectors/sources`):**
  - Atlassian: Confluence Cloud and Data Center, Jira Cloud and Data Center.
  - Microsoft: SharePoint Online, OneDrive, Outlook.
  - Google: Drive, Gmail.
  - Code: GitHub, GitLab (repos, merge requests, issues).
  - Chat: Slack.
  - Databases: Postgres, MariaDB (tables and columns), Snowflake.
  - Others: ServiceNow, Zoom, Notion, Linear, Salesforce, Zendesk, Box, Dropbox, S3, and about 25 more.
- **How it helps:** It is the closest existing blueprint for the whole platform. It is also the only verified source of database connectors and of a working permission model whose code is reusable.
- **Reuse mode:** Fork or Extend. Every file in the repo is Apache-2.0, so taking connectors and the permission model is legally clean.
- **License and commercial terms:**
  - The code is Apache-2.0. The pricing page also lists a paid **Enterprise edition, which can be self-hosted**, offering multi-tenancy, SSO plus SCIM, RBAC, audit logs, "entity extraction & knowledge graph updates", the full connector set ("core set" in Community) and "FULL" permission-aware connectors.
  - Those features appear not to be in the repo. A grep found no SCIM or SAML paths, and the 1.0 upgrade docs say SAML and OIDC sign-in were removed.
- **Maintenance:** About 3.9k stars, pushed daily, very active.
- **Limitations:**
  - Connectors declared `APP_LEVEL` do not mirror source ACLs: Postgres, MariaDB, Snowflake, file shares and the personal variants of several connectors. For these, reaching the connector means seeing every record it synced.
  - A permission revoked in the source stays visible until the next sync plus up to the 300-second cache expiry.
  - Agents shared org-wide search with their creator's access by default (#4545, closed 2026-10-26). The fix only lets an admin opt in to binding a service account.
  - There have been past per-connector ACL bugs (#3094, #1189).
  - It has no code-graph or AST analysis comparable to the code-intelligence tools, and nothing for diagrams.

### 4.2 Onyx (V3)
- **Repo:** https://github.com/onyx-dot-app/onyx, with docs at https://docs.onyx.app
- **Problem it solves:** It calls itself "the knowledge/context layer for your team and AI agents", with enterprise search, chat, agents and actions over 50+ sources.
- **Features:**
  - About 54 real connectors (62 directories minus helper modules).
  - Hybrid search with RAG.
  - Agents and actions.
  - An MCP server in `backend/onyx/mcp_server`.
  - Polls sources every 30 minutes by default and prunes deleted content every 30 days†.
- **Architecture and stack:** A Python backend with Celery background jobs and a Next.js web app. The search index is reported to be Vespa†.
- **Connectors:** Confluence, Jira, Slack, Teams, GitHub, GitLab, Bitbucket, Google Drive, SharePoint, Notion, Zoom, Gong, Fireflies and others. It has **none** for Postgres, MySQL, Lucidchart or Draw.io (confirmed by searching the `DocumentSource` enum).
- **How it helps:** A mature connector library and a reference ingest pipeline. It could be deployed as-is for document and chat search if permission sync is not needed or is bought.
- **Reuse mode:** Fork the MIT core, or lift individual connectors.
- **License:**
  - Code outside `backend/ee`, `web/src/app/ee` and `web/src/ee` is MIT.
  - Code in those `ee` directories is under the **Onyx Enterprise License**. It forbids copying, distributing or selling, and allows production use only with a paid per-seat subscription.
  - **Legal note:** avoid copying `ee/` code into our platform. Even studying it should be cleared by legal; prefer PipesHub's Apache-licensed permission model.
- **Maintenance:** About 33.2k stars, roughly 11k commits†, pushed daily.
- **Limitations:**
  - In the MIT core, `access.py` sets `external_user_emails=[]` and `external_user_group_ids=[]`. The real implementation is loaded from EE through `fetch_ee_implementation_or_noop`.
  - The scheduled permission-sync Celery tasks are also in EE.
  - It has no knowledge graph, code graph, database or diagram sources.

### 4.3 Graphiti (V3)
- **Repo:** https://github.com/getzep/graphiti, with docs at https://help.getzep.com/graphiti
- **Problem it solves:** It builds and queries a knowledge graph that changes over time, for AI agents. It is the open-source core of Zep's paid product.
- **Features:**
  - Incremental ingestion of "episodes".
  - Bi-temporal edges: `valid_at`, `invalid_at`, `expired_at` and `created_at` record when a fact was true and when it was learned.
  - LLM-driven invalidation of contradicted facts (`prompts/invalidate_edges.py`).
  - Custom entity and edge types defined as Pydantic models.
  - Search: semantic plus BM25 merged with RRF by default, with graph traversal (BFS, node-distance reranking, cross-encoder) available through search recipes.
- **Architecture and stack:** A Python library (`graphiti_core`). We supply the graph database (Neo4j, FalkorDB or Neptune), the LLM and the embedder.
- **How it helps:** It is the core of the "organizational knowledge graph". Facts from Jira, Slack, incidents and documents become dated assertions that can be superseded. This supports "what was true when", which matters for decisions, ownership and incidents.
- **Reuse mode:** Reuse as a library.
- **License:**
  - Graphiti itself is Apache-2.0.
  - **Choosing a backend is also a license decision.** FalkorDB is SSPL (exclude). Neo4j Community is GPL-3.0 (flag). Neptune is a proprietary managed AWS service.
- **Maintenance:** About 32.4k stars, pushed 2026-11-01.
- **Limitations:**
  - Invalidation is non-deterministic and depends on the LLM. Weaker LLMs cause ingestion failures, and `add_episode_bulk` reportedly skips invalidation.
  - It has no connectors, no change detection, no multi-tenancy and no access control (those are Zep-only).
  - Its MCP server has no authentication or authorization, and exposes destructive tools such as `clear_graph` to any caller.

### 4.4 codebase-memory-mcp (V3)
- **Repo:** https://github.com/DeusData/codebase-memory-mcp
- **Problem it solves:** It gives agents a persistent, queryable knowledge graph of codebases, including links across repos and services.
- **Features:**
  - 17 MCP tools, including `index_repository`, `search_graph`, `trace_path`, `detect_changes`, `query_graph`, `compare_graphs`, `get_architecture`, `manage_adr` and `ingest_traces`.
  - Keyword search through SQLite FTS5 (BM25).
  - Matches HTTP routes to their call sites with confidence scores.
  - `CROSS_HTTP_CALLS`, `CROSS_GRPC_CALLS` and `CROSS_GRAPHQL_CALLS` edges, emitted in `src/pipeline/pass_cross_repo.c` and tested in `tests/test_cross_repo.c`.
  - Extraction for Kubernetes, Helm, Terraform and Ansible on top of the YAML and HCL grammars.
- **Architecture and stack:** A native C static binary with 162 vendored Tree-sitter grammars and SQLite storage. It needs no Docker or language runtime.
- **How it helps:** It covers "repository initialization" and "cross-repository intelligence" almost directly. It finds service-to-service dependencies, which can be joined to runbooks and incidents in the org graph. `ingest_traces` and `manage_adr` hint at runtime and decision-record linkage.
- **Reuse mode:** Reuse it as a per-repo or org-wide indexer and export its graph into the org graph. Extending it means writing C.
- **License:** MIT. The bundled grammars and the nomic-embed-code model were not audited; `THIRD_PARTY_NOTICES` ships only with releases.
- **Maintenance:** Release v0.12.1 on 2026-10-16, about 48k stars.
- **Limitations:** Its graph schema covers code only. Embedding SQLite in a single binary means a central multi-tenant deployment needs extra design work. Neither code tool joins its graph with document or ticket graphs.

### 4.5 unstructured-ingest (T)
- **Repo:** https://github.com/Unstructured-IO/unstructured-ingest, with docs at https://docs.unstructured.io/open-source/ingestion/overview
- **Problem it solves:** Pulling content from many sources, partitioning it, then chunking, embedding and writing to many destinations.
- **Connectors (from the source tree):**
  - Sources: Confluence, Jira, GitHub, GitLab, Google Drive, SharePoint, OneDrive, Outlook, Slack, Discord, Notion, Salesforce, Zendesk, Airtable, SQL, MongoDB, Kafka, fsspec (S3, GCS, Azure and others), local.
  - Destinations: Neo4j, Qdrant, Weaviate, Milvus, LanceDB, Chroma, Pinecone, Elasticsearch, AstraDB, Couchbase, Databricks, DuckDB, Redis, KDB.AI, Vectara.
  - Each connector installs as a pip extra.
- **Architecture and stack:** Python, with a pipeline of indexer → downloader → partitioner (unstructured) → chunker → embedder → stager → uploader†.
- **How it helps:** It removes most of the SaaS connector work for documents, tickets and chat in one dependency.
- **Reuse mode:** Reuse, and add the connectors we are missing.
- **License:** Apache-2.0. The hosted Unstructured Platform and API are separate paid products.
- **Maintenance:** Pushed 2026-10-29. The star count is low because this is a split-out package; the parent `unstructured` repo has 15.7k stars.
- **Limitations:**
  - Change detection, deletion propagation and permission metadata are not documented per connector†.
  - It has no knowledge-graph extraction of its own.
  - **Next step:** read the Confluence, Jira and Slack connector code to see what it does incrementally and with ACLs.

### 4.6 CocoIndex (T)
- **Repo:** https://github.com/cocoindex-io/cocoindex, with docs at https://cocoindex.io/docs
- **Problem it solves:** Keeping derived indexes (vector, graph, relational) continuously in sync with their sources at low cost.
- **Features:**
  - Incremental processing that skips unchanged rows using content fingerprints.
  - Retries failed rows on the next update.
  - A live-update mode.
  - Reprocesses automatically when the flow definition changes, for example a new chunker or embedder.
  - LLM structured extraction into graph targets with embedding-based deduplication of entities.
  - Postgres change capture through LISTEN/NOTIFY†.
- **Architecture and stack:** A Rust core with a Python SDK. Flow state is kept in Postgres. *Corrected 2026-11-03: that and the LISTEN/NOTIFY item above describe v0. v1 (1.0.0 on 2026-04-22, now 1.1.0) is a rewrite: tracking state lives in a local LMDB file, sources are plain Python functions, and the Postgres source is polled. See `docs/design.md`.*
- **Connectors (from the source tree):**
  - Sources and storage: localfs, S3, Azure Blob, OCI object storage, Google Drive, Postgres, Kafka, Iggy, BigQuery, Snowflake, SQLite.
  - Targets: Neo4j, FalkorDB, Qdrant, LanceDB, SurrealDB, Turbopuffer, Valkey, Doris, zvec.
- **How it helps:** It is the incremental engine that connects source extraction to our graph and vector stores. It handles the "only reprocess what changed" problem that Graphiti and LightRAG leave to us.
- **Reuse mode:** Reuse, and write custom sources for Confluence, Jira and Slack (or wrap unstructured-ingest).
- **License:** Apache-2.0.
- **Maintenance:** About 11.8k stars, pushed daily.
- **Limitations:**
  - It has no enterprise SaaS sources.
  - Google Drive does not report deletions, so it falls back to polling.
  - Most feature claims are vendor-authored.

### 4.7 Docling (L + primary technical report)
- **Repo:** https://github.com/docling-project/docling, with docs at https://docling-project.github.io/docling/. Also see [docling-mcp](https://github.com/docling-project/docling-mcp).
- **Problem it solves:** High-fidelity conversion of complex documents into structured data that is ready for RAG.
- **Features:**
  - Formats: PDF, DOCX, PPTX, XLSX, HTML, images, Markdown and AsciiDoc, all converted into one DoclingDocument.
  - Layout analysis (RT-DETR trained on DocLayNet), table structure (TableFormer), and OCR (EasyOCR or Tesseract). Disabling OCR saves about 60% of CPU time.
  - Exports to JSON (lossless), Markdown and HTML.
  - Chunkers with page and bounding-box provenance, plus LangChain and LlamaIndex integrations.
- **How it helps:** It parses the documentation layer: Confluence and SharePoint attachments, PDFs and slide decks. Its provenance data supports precise citations.
- **Reuse mode:** Reuse, as a library or as the docling-serve REST service†.
- **License:** MIT. The model weights on Hugging Face carry their own licenses.
- **Maintenance:** About 70k stars and an active LF AI & Data project.
- **Limitations:** It does not understand diagram semantics (shapes and edges in Draw.io or Lucid files). GPU-heavy settings are slower than MinerU's.

### 4.8 LightRAG (V3)
- **Repo:** https://github.com/hkuds/lightrag
- **Problem it solves:** Graph-enhanced RAG that is cheaper and simpler than Microsoft GraphRAG and supports incremental updates.
- **Features:**
  - Extracts entities and relations into a graph, alongside vector embeddings.
  - Two-level retrieval that combines specific facts with broader concepts.
  - Query modes: local, global, hybrid, naive, mix (the default) and bypass.
  - Incremental insert through a queued pipeline.
  - `adelete_by_doc_id` deletes entities and relations that came only from the deleted document, rebuilds shared ones from the extraction cache and updates the vectors (automatic since 2025.08).
- **Architecture and stack:** Python, with pluggable key-value, vector and graph storage backends. A server and web UI are also available†.
- **How it helps:** It can be the graph-plus-vector retrieval layer, as an alternative or complement to Graphiti. It is better for document corpora, while Graphiti is better for facts that change over time.
- **Reuse mode:** Reuse.
- **License:** MIT. The optional storage backends carry their own licenses.
- **Maintenance:** About 40.5k stars and 5.8k forks, pushed 2026-10-29.
- **Limitations:** No temporal fact model. Deletion support varies by backend, so test it. No connectors or change detection.

### 4.9 Code-Graph-RAG (V3)
- **Repo:** https://github.com/vitali87/code-graph-rag
- **Problem it solves:** A multi-language code knowledge graph that can be queried in natural language and over MCP.
- **Features:**
  - Languages fully parsed with Tree-sitter: Python, TS, TSX, JS, Rust, Go, Java, C, C++, C#, PHP, Lua, Dart, Julia.
  - Structural-only support through ast-grep: Ruby, Kotlin, Swift, Elixir, Haskell, Solidity, Bash, Nix.
  - Exact facts from compiler front-ends where a toolchain is available.
  - MCP tools: `list_projects`, `delete_project`, `index_repository`, `update_repository` and `reingest` (re-parses the given files plus the files that depend on them).
- **Architecture and stack:** Python, with an embedded SQLite graph by default. Neo4j and Memgraph are optional, and Memgraph is BSL (flag).
- **How it helps:** A code graph with stronger semantics than plain Tree-sitter, thanks to the compiler front-ends. Many repos share one graph, and each project can be resynced on its own.
- **Reuse mode:** Reuse or Fork. It is easier to extend than #4.4 because it is Python.
- **License:** MIT. The project sells only services, with no gated edition.
- **Maintenance:** About 5.3k stars, pushed daily.
- **Limitations:**
  - `--clean` and the `wipe_database` tool wipe every project in the shared graph.
  - It has no cross-service edges like codebase-memory-mcp's.
  - It overlaps heavily with #4.4, so choose one, or bridge them through SCIP.

### 4.10 SpiceDB / OpenFGA (authorization layer; L + fetched docs)
- **Repos:** https://github.com/authzed/spicedb (docs at https://authzed.com/docs) and https://github.com/openfga/openfga (docs at https://openfga.dev/docs)
- **Problem it solves:** Zanzibar-style authorization based on relationships (ReBAC). It answers "can this user see this document?" and "which documents can this user see?" at scale.
- **How it helps:** It becomes the store for source ACLs that our connectors sync: Confluence space and page restrictions, Drive shares, Slack channel membership, GitHub team access.
- **Retrieval pattern:** Call `LookupResources` (SpiceDB) or `ListObjects` (OpenFGA), then run the vector or BM25 query with an ID filter. When the result set is too large, fall back to post-filtering that widens the search. Deny access on errors by default (`fail_open=False`, as in langchain-spicedb).
- **Reuse mode:** Reuse the engine. The ACL sync, the mapping of each source's permissions into the schema, and the retrieval filter are ours to build. needtoknow and VaultRAG are small working references.
- **License:** Both Apache-2.0. OpenFGA is a CNCF project.
- **Maintenance:** 7.2k and 6.1k stars, both active.
- **Limitations:** Every ingested chunk must carry a source object ID. Large result sets need caching or a hybrid of pre- and post-filtering. The latency between a permission revocation in the source and its effect in search is ours to define and enforce.

---

## 5. Capability comparison matrix

● = full, ◐ = partial or caveated, — = none or not applicable, † = not verified.

| Project | SaaS connectors | DB / schema | Code / AST | Doc parsing | Knowledge graph | Vector / hybrid | Incremental sync | Permission-aware | MCP | API / SDK | License | Maturity | Relevance |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PipesHub | ● | ● (no ACLs) | ◐ code search | ◐ | ● (LLM entity extraction = EE) | ● Qdrant | ● | ◐ RECORD_LEVEL only | ● | ● Py/TS/Go | Apache (open-core) | Med | **High** |
| Onyx | ● ~54 | — | ◐ repo/PR/issue text | ◐ | — | ●† | ● poll + prune | ◐ EE only | ● | ● | MIT + EE | High | **High** |
| SWIRL | ● federated | ◐† | — | — | — | — (no index) | n/a | ● query-as-user | ◐ Enterprise? | ● | Apache | Med | Med |
| RAGFlow | ?† | — | — | ●† | ◐† | ●† | ?† | ?† | ◐† | ● | Apache (+ `web/src/ee`) | High | Med |
| AnythingLLM | ◐ | — | — | ● | — | ● | ◐ | — | ● | ● | MIT | High | Low-Med |
| Graphiti | — | — | — | — | ● temporal | ● sem + BM25 + graph | ● episodes | — | ◐ no auth | ● lib | Apache | High | **High** |
| LightRAG | — | — | — | ◐ | ● | ● | ● insert + delete | — | —† | ●† | MIT | High | **High** |
| MS GraphRAG | — | — | — | ◐ | ● communities | ● | ◐ ignores deletes | — | — | ● | MIT | High | Low-Med |
| cognee | ◐ dlt | ● schema → graph | — | ◐ | ● | ● | ◐† | — | ●† | ● | Apache | High | Med |
| codebase-memory-mcp | — | — | ● 162 grammars, cross-repo | — | ● code | ◐ BM25 | ◐ `detect_changes` | — | ● 17 tools | — | MIT | High | **High** |
| Code-Graph-RAG | — | — | ● 14 + 8 languages, compilers | — | ● code | ◐ | ● `reingest` | — | ● | — | MIT | Med | High |
| SCIP + indexers | — | — | ● precise symbols | — | ◐ | — | ◐ | — | — | ● | Apache | Med | High |
| Zoekt | — | — | ● search | — | — | ● trigram | ● | — | — | ● | Apache | High | High |
| unstructured-ingest | ● | ◐ SQL source | ◐ GitHub/GitLab files | ● | ◐ Neo4j destination | ● many destinations | ◐† | —† | — | ● | Apache | Med | **High** |
| CocoIndex | ◐ Drive only | ● Postgres, BigQuery, Snowflake | ◐ via Tree-sitter splitting† | ◐ | ● Neo4j/FalkorDB targets | ● Qdrant/LanceDB/pgvector | ● | — | — | ● | Apache | Med-High | **High** |
| Docling | — | — | — | ● | — | — | — | — | ● docling-mcp | ● | MIT | High | High |
| Debezium | — | ● CDC | — | — | — | — | ● | — | — | ● | Apache | High | Med |
| dlt | ◐† | ● | — | — | — | — | ● | — | — | ● | Apache | High | Med |
| tbls | — | ● schema docs | — | — | ◐ foreign-key relations | — | — | — | — | ● CLI | MIT | Med | Med |
| OpenSearch | — | — | — | — | — | ● BM25 + kNN | — | ◐ security plugin† | — | ● | Apache | High | High |
| Qdrant | — | — | — | — | — | ● sparse + dense | — | ◐ RBAC = enterprise | — | ● | Apache | High | High |
| pgvector + Apache AGE | — | ● | — | — | ● AGE | ◐ (+ Postgres FTS) | — | ◐ Postgres RLS† | — | ● | PostgreSQL / Apache | High | Med |
| SpiceDB / OpenFGA | — | — | — | — | — | — | — | ● engine | — | ● | Apache | High | **High** |
| Temporal / Dagster | — | — | — | — | — | — | ● orchestration | — | — | ● | MIT / Apache | High | Med |
| mcp-atlassian / github-mcp-server / gitlab-mcp / slack-mcp | ◐ live | — | ◐ | — | — | — | n/a live | ◐ user token | ● | — | MIT | Med-High | Med |
| GitNexus | — | — | ● cross-repo | — | ● | — | ◐ | — | ● | — | **PolyForm NC** | High | Exclude |
| Airbyte | ● | ● | — | — | — | — | ● | — | — | ● | **ELv2** | High | Flag |

---

## 6. Recommended libraries and tools for each functional area

| Functional area | First choice | Alternative / complement | Avoid (license) |
|---|---|---|---|
| SaaS connectors (Confluence, Jira, SharePoint, Drive, Slack, Teams, GitHub, GitLab) | unstructured-ingest | Fork individual connectors from PipesHub (Apache) or Onyx (MIT core); LlamaHub readers | Airbyte connectors (ELv2), unless legal approves |
| Database sources (schema and data) | tbls (schema) + Debezium (CDC) | PipesHub Postgres/MariaDB connectors; dlt `sql_database`; cognee `dlt_schema_graph` | — |
| Incremental sync engine | CocoIndex | Temporal or Dagster driving per-source jobs | Pathway (BSL) |
| Document parsing | Docling | Unstructured; MarkItDown (fast path); Tika (long-tail formats) | MinerU above its usage thresholds |
| Meeting transcripts | Source transcripts via connectors (Zoom, Gong and Fireflies in Onyx; Teams via the Graph API) | WhisperX + pyannote for self-transcription | — |
| Diagrams (Draw.io, Lucidchart) | **Build**: parse mxGraph XML for Draw.io; use the Lucid REST API or export for Lucidchart | Docling or OCR as a lossy fallback for exported images | — |
| Code parsing and graph | codebase-memory-mcp | Code-Graph-RAG; Tree-sitter + ast-grep directly | GitNexus (noncommercial), Serena app (GPL) |
| Precise code navigation | SCIP + language indexers | — | — |
| Code search | Zoekt | — | — |
| Knowledge graph engine | Graphiti (temporal facts) | LightRAG (document graph RAG); neo4j-graphrag-python | — |
| Graph store | Neo4j Community (GPL, flag) or Apache AGE (Apache) | — | FalkorDB (SSPL), Memgraph (BSL), Kuzu (archived) |
| Vector and hybrid search | OpenSearch (large scale) or Qdrant | pgvector + Postgres FTS (smaller scale); Milvus; Vespa | Elasticsearch, ParadeDB, VectorChord, Redis 8 |
| RAG and retrieval orchestration | Haystack or a thin custom layer | LlamaIndex, LangChain (selectively) | — |
| Authorization | SpiceDB or OpenFGA | Cerbos or OPA for policy rules; OPAL for keeping them in sync | Onyx EE (proprietary) |
| MCP exposure | Official MCP SDKs + our own gateway | Study the Onyx and PipesHub MCP servers; offer the live servers (github-mcp-server, mcp-atlassian, gitlab-mcp) alongside | Graphiti's MCP server as-is (no auth) |
| Workflow orchestration | Temporal | Dagster, Hatchet, Prefect, Airflow, Kestra | — |

---

## 7. Build vs. reuse assessment

| Layer | Verdict | Reuse | Build |
|---|---|---|---|
| Connectors to SaaS sources | **Reuse + extend** | unstructured-ingest; connectors forked from PipesHub and Onyx | A uniform connector contract (cursor, deletions, ACL export); Lucidchart; ops tools (PagerDuty, Opsgenie, Grafana)† |
| Database ingestion | **Reuse + glue** | tbls, Debezium, dlt | Mapping schemas into the graph; linking tables to code (ORM models) and docs |
| Change detection and sync | **Extend** | CocoIndex, Temporal or Dagster, Debezium | Per-source cursors, deletion propagation, backfill and rate limits, reprocessing when the pipeline changes |
| Document and transcript parsing | **Reuse** | Docling, Unstructured, MarkItDown, WhisperX | Thin adapters only |
| Diagram parsing | **Build** | Docling/OCR fallback | Draw.io XML → nodes and edges; Lucid API → nodes and edges |
| Code intelligence | **Reuse** | codebase-memory-mcp or Code-Graph-RAG, SCIP, Zoekt | Exporting their graphs into the org graph |
| Knowledge graph | **Reuse engine, build ontology** | Graphiti or LightRAG; Neo4j or AGE | The org ontology (Service, Repo, Team, Person, Ticket, Doc, Incident, Runbook, Table, Diagram) and cross-source entity resolution |
| Hybrid search | **Reuse** | OpenSearch or Qdrant | Rank fusion across code, docs and graph |
| Permission-aware retrieval | **Build on a reused engine** | SpiceDB or OpenFGA; patterns from needtoknow, VaultRAG and langchain-spicedb | Per-source ACL sync, identity mapping across systems, pre- and post-filtering, a revocation-latency target, audit |
| API and MCP access | **Build** | MCP SDKs; reference servers | An authenticated multi-tenant gateway that carries the end user's identity, plus tool design, rate limiting and prompt-injection defenses |
| Team expertise | **Build** | Graphiti episodes for captured knowledge | Expert graph from commits, Jira assignments, Slack activity and incident responders; a capture workflow |
| Orchestration | **Reuse** | Temporal or Dagster | Job definitions |

**Strategic options:**

1. **Option A: fork PipesHub as the base.** This gives the fastest full stack: connectors, graph, vectors, MCP, SDKs and a permission model.
   - **Then add:** code intelligence (codebase-memory-mcp), Graphiti-style temporal facts, record-level ACLs for databases and file shares, and our own SSO, which the vendor removed and sells in Enterprise.
   - **Risk:** we would diverge from an open-core upstream that keeps strategic features out of the repo.
2. **Option B: compose from libraries.** unstructured-ingest + CocoIndex + Docling + codebase-memory-mcp + Graphiti + OpenSearch or Qdrant + SpiceDB + Temporal, behind our own API and MCP gateway.
   - **Benefit:** the most control and the cleanest licensing.
   - **Cost:** more integration work, especially in the sync and permission layers.
3. **Option C: Onyx MIT core for documents and chat, plus libraries for code and the graph.** This gives the most mature document connectors, but means rebuilding permission sync outside EE.

These options are presented for comparison; no single stack is being recommended. A short spike of about 2 weeks comparing Option A with Option B on 3 sources (Confluence, GitLab, Postgres) would settle the choice.

---

## 8. Licensing eligibility assessment

**Green: eligible for commercial self-hosted use (MIT, Apache-2.0, BSD, ISC, PostgreSQL):**
- **Platforms and connectors:** PipesHub (code), SWIRL Community, AnythingLLM, Airweave (archived), unstructured, unstructured-ingest, dlt, Debezium.
- **Code intelligence:** Code-Graph-RAG, codebase-memory-mcp, SCIP, scip-typescript, scip-java, scip-python (MIT, derived from Pyright), Zoekt, Aider, tree-sitter, py-tree-sitter, tree-sitter-language-pack, ast-grep.
- **Document processing:** Docling, docling-mcp, MarkItDown, Tika, Whisper, WhisperX, pyannote-audio (code), tbls, draw.io.
- **Knowledge graph:** Graphiti, LightRAG, Microsoft GraphRAG, cognee, fast-graphrag, neo4j-graphrag-python (Apache + PSF), Apache AGE.
- **Sync and search:** CocoIndex, OpenSearch, Qdrant (core), Milvus, pgvector, LanceDB, Vespa.
- **Frameworks and MCP:** LlamaIndex, Haystack, LangChain, MCP servers (MIT/Apache), github-mcp-server, mcp-atlassian, gitlab-mcp, slack-mcp-server.
- **Orchestration and authorization:** Temporal, Dagster, Airflow, Kestra, Prefect, Hatchet, SpiceDB, OpenFGA, Cerbos, OPA, OPAL, langchain-spicedb, needtoknow, VaultRAG.

**Yellow: usable, but needs legal review or care:**

| Project | Issue |
|---|---|
| Onyx | MIT core is fine. Never ship or copy `ee/` code. Production use of EE needs a subscription. |
| PipesHub | All repo code is Apache-2.0. Features the vendor sells (SSO, RBAC, KG updates, full connectors) are absent from the repo, so plan to build them. |
| RAGFlow | Apache LICENSE, but the repo has a `web/src/ee/` directory. Confirm whether any features are gated. |
| Weaviate | BSD-3, except the `wl/` directory, which is under the Weaviate License. |
| Meilisearch | MIT, plus BUSL-1.1 for its Enterprise Edition parts. |
| MinerU | Apache-2.0 plus a commercial-license requirement above 100M MAU or USD 20M monthly revenue. |
| Neo4j Community, Typesense | GPL-3.0. Run unmodified as a separate service; review before embedding. |
| universal-ctags (GPL-2.0), SchemaSpy (LGPL-3.0) | Run as external tools; do not link. |
| Serena | The app is GPL-3.0; only the SolidLSP component is MIT. |
| Qdrant | Core is Apache-2.0; RBAC is proprietary. |
| pyannote models, Docling models, codebase-memory-mcp grammars and embedding model | Check model and grammar licenses separately from the code licenses. |
| Kestra, Prefect, Dagster, Temporal | Each has a commercial cloud or Enterprise tier. Confirm that the self-hosted features we need are in the open-source edition†. |

**Red: exclude from primary recommendations (restrictive or source-available):**

| Project | License |
|---|---|
| GitNexus | PolyForm Noncommercial |
| Khoj | AGPL-3.0 |
| ParadeDB | AGPL-3.0 |
| Elasticsearch | AGPL / SSPL / ELv2 |
| FalkorDB | SSPL |
| Memgraph | BSL 1.1 + Memgraph Enterprise License |
| Pathway | BSL 1.1 |
| Airbyte, PyAirbyte | ELv2. Internal use is allowed, but they cannot be offered as a managed service and are not OSI-approved. |
| VectorChord | AGPL or ELv2 |
| Redis 8+ | AGPL / RSAL / SSPL |
| Onyx `ee/` directories | Proprietary |

**Archived or stale (avoid as dependencies):**
- Airweave: archived, last push 2026-06-05.
- Kuzu: archived, last push 2025-10-10.
- fast-graphrag: no pushes since 2025-11-01.

---

## 9. Key architectural ideas worth adopting

1. **Declare how accurately each connector mirrors source permissions** (from PipesHub's `PermissionModel`). Each connector states whether it carries real per-record ACLs (`RECORD_LEVEL`) or "anyone who can reach the connector sees everything" (`APP_LEVEL`). Show this to admins, and restrict `APP_LEVEL` sources by default.
2. **Pre-filter retrieval with the authorization engine.** Get the IDs a user can access (`LookupResources` / `ListObjects`), search with an ID filter, and fall back to a widening post-filter for large sets. Deny access on errors and when a document has no ACL (langchain-spicedb, needtoknow, VaultRAG).
3. **For Postgres deployments, check ACLs in the same query as search** (VaultRAG). The ACL predicate goes in the same SQL as the vector and BM25 search, so unauthorized chunks are never scored.
4. **Make permission-revocation latency an explicit, enforced target.** PipesHub's 300-second permission cache plus sync interval is an implicit one, and we should set ours deliberately.
5. **Agents act as the end user, never as their creator** (the lesson from PipesHub #4545). Every MCP or API call must carry the end user's identity.
6. **Treat facts as dated assertions that can be superseded** (Graphiti). Invalidate instead of delete, and keep both when a fact was true and when we learned it. This enables "who owned service X in March?" and incident timelines.
7. **Treat deletion propagation as a core feature** (LightRAG `adelete_by_doc_id`). Rebuild shared entities from the extraction cache. Microsoft GraphRAG issue #2590 shows the failure mode to avoid.
8. **Fingerprint content and track the pipeline version** (CocoIndex). Skip unchanged rows, retry failures on the next update, and reprocess automatically when the chunker, embedder or extractor changes.
9. **For sources without change feeds, poll and periodically prune** (Onyx: 30-minute poll, 30-day prune). Use log-based change data capture for databases (Debezium, Postgres LISTEN/NOTIFY).
10. **Keep one shared multi-repo graph with per-project resync and dependency-aware reingest** (Code-Graph-RAG). Add cross-service edges by matching HTTP routes, gRPC and GraphQL calls (codebase-memory-mcp). Together these give a real service dependency map to join with runbooks and incidents.
11. **Layer code intelligence: Tree-sitter for breadth, SCIP or compiler front-ends for precision, Zoekt for text search.** No single tool covers all three.
12. **Use a hybrid of indexed and federated search** (SWIRL). Index what you may copy, and query live, as the user, for sources you shouldn't copy, such as HR or legal data.
13. **Keep provenance on every chunk** (Docling page and bounding box; PipesHub block citations), so answers can cite the exact place in the source.
14. **Ship the code indexer as a single portable binary with embedded SQLite and FTS5** (codebase-memory-mcp). Developers and CI can then run it locally, and the central platform collects the results.

---

## 10. Gaps and capabilities requiring custom development

1. **Permission-aware retrieval under a free license.** This means syncing ACLs for each source (Confluence restrictions, Drive shares, SharePoint permissions, Slack channels, GitHub and GitLab teams, Jira project roles, database grants), mapping identities across systems, writing them into SpiceDB or OpenFGA, filtering at retrieval time, and auditing access. *This is the largest and most security-critical piece to build.*
2. **Diagram ingestion.** No open-source library was found that turns Draw.io or Lucidchart diagrams into graph facts.
   - **Draw.io:** decompress and parse the mxGraph XML in `.drawio` files with the standard library (cells, labels, edges, containers), then map shapes to services and data stores.
   - **Lucidchart:** use the Lucid REST API or document export. It is proprietary SaaS, so the connector is custom.
3. **Mapping database schemas into the graph.** tbls, dlt and cognee give the raw schema. We still need to link tables and columns to ORM models in code, to services, and to the documents that describe them.
4. **One organizational ontology and cross-source entity resolution.** This means linking code, tickets, documents, chat, incidents and people. Examples: a Jira key in a commit message to an issue, a service name to its repo and runbook, a Slack handle to a GitLab user and an employee. The code-graph and document-graph tools each keep separate schemas.
5. **The sync control plane.** Uniform connector contracts covering cursors, backfill, deletions, rate limits, retries, health and lag metrics, and reprocessing when the pipeline changes. CocoIndex and Temporal provide the building blocks but not the control plane.
6. **Ingestion of ops data (logs, monitoring, incidents, runbooks).** No verified open-source connectors were found for PagerDuty, Opsgenie, Grafana or Datadog incidents, or for log summaries. codebase-memory-mcp's `ingest_traces` and Kafka sources are partial starting points. Runbooks stored in Confluence or Git are already covered.
7. **Team expertise and tacit knowledge.** This means an expertise graph derived from commits, reviews, ticket assignments, incident response and Slack answers, plus a lightweight way for people to capture knowledge (as Graphiti episodes). Nothing found does this end to end.
8. **A secure organizational MCP and API gateway.** This needs OAuth and SSO, propagation of the end user's identity, per-tool authorization, rate limiting, audit, prompt-injection defenses and safe tool design (no `clear_graph` for callers). Graphiti's server explicitly declines to provide these, and PipesHub's SSO is behind its Enterprise edition.
9. **SSO, RBAC and multi-tenancy for the platform itself,** if we fork PipesHub or Onyx, because both sell these.
10. **Evaluating retrieval quality.** A benchmark harness of question/answer pairs per source, and regression testing when the ingestion pipeline changes. This was not covered by this research.

---

## 11. Caveats and suggested follow-up checks

- **Verification depth varies.** Only the projects marked V3 had their claims adversarially verified. Projects marked L were checked only for license, activity and archived status. Feature descriptions marked † must be confirmed before you rely on them.
- **Open-core boundaries move.** Onyx edited its license in February 2026, and PipesHub removed SAML and OIDC in 1.0. Recheck before you commit to any of them.
- **Unresolved points:**
  - Which SWIRL features are Enterprise-only. Its README table and a refuted claim disagree.
  - Which SCIP indexers are production-grade for our languages.
  - How unstructured-ingest's Confluence, Jira and Slack connectors handle incremental sync and ACLs.
  - What RAGFlow's `web/src/ee` contains, and what connectors RAGFlow has.
  - Whether the Lucidchart API allows the export we need.
- **Next steps, in order:**
  1. Read the code of unstructured-ingest's connectors and of PipesHub's `RECORD_LEVEL` connectors and permission model.
  2. Run a bake-off between codebase-memory-mcp and Code-Graph-RAG on two internal repos.
  3. Write a Graphiti versus LightRAG proof of concept on one Confluence space plus its Jira project.
  4. Have legal review the Neo4j GPL choice against Apache AGE.

## 12. Decision record (2026-11-03)

*Superseded on 2026-11-04 by §16.*

### Decisions

1. **No per-document permission gating.** Any caller the gateway admits can read anything that was indexed. Access control is (a) which spaces, channels, drives and repositories are connected, which should be org-wide-readable sources only, and (b) who holds a gateway credential.
2. **Jira is out of scope.** No project-management data is ingested. Jira connectors listed in §2 and the "ticket" entity in the proposed ontology are informational only.
3. **Option B is the chosen direction:** permissively licensed libraries composed around one Postgres, exposed through a thin gateway we write.

### What these decisions remove

| Removed | Why | Sections now superseded |
|---|---|---|
| Authorization layer: SpiceDB / OpenFGA, `acl` and `principals` tables, cross-system identity mapping, needtoknow, VaultRAG, langchain-spicedb | No per-document filtering | §2.12, the Authorization row of §6, the Permission-aware row of §7, ideas 1–5 of §9, gap 1 and the SSO/RBAC part of gap 9 in §10 |
| Forking PipesHub's `RECORD_LEVEL` connectors | They were chosen because they export ACLs. `unstructured-ingest` as a plain dependency now covers Confluence, Slack, SharePoint, Drive, GitHub, GitLab and SQL | §4.1 "Reuse mode", §6 Connector row |
| Onyx's main disqualifier | Its EE boundary was permission sync. The MIT core (54 connectors, hybrid search, 30-minute polling and pruning, MCP server) is now a viable deployable alternative | §4.2 limitations, Option C in §7 |
| Jira connector work and the ticket entity | Out of scope | Jira mentions in §2.1, §2.2, §4.1, §4.2, §10 gap 4 |

Gaps that remain custom regardless: diagram parsing (§10 gap 2), database schema to graph (gap 3), one ontology across sources (gap 4), the sync control plane (gap 5), ops data (gap 6), team expertise (gap 7), the gateway minus its authorization parts (gap 8), retrieval evaluation (gap 10).

### Chosen stack

| Layer | Pick | Ceiling → upgrade |
|---|---|---|
| Connectors | `unstructured-ingest` (Apache-2.0) as a dependency. Teams and meeting transcripts forked from Onyx's MIT core | — |
| Incremental sync | CocoIndex (Apache-2.0): fingerprint each record, process only changes, propagate deletes. Since v1 its tracking state is a local LMDB file, not Postgres | Durable multi-step jobs → Temporal |
| Database sources | tbls for schema on a schedule. Row data is not indexed; Debezium is deferred | Rows from an operational database are indexed → Debezium |
| Document parsing | Docling (MIT) | — |
| Code intelligence | codebase-memory-mcp (MIT) per repository; its SQLite graph exported as rows into the shared `entities` and `edges` tables, pinned to its `artifact.json` schema version. Code is not embedded in Postgres | Regex search across every repo → Zoekt |
| Store | One self-hosted Postgres: `chunks` (built-in full-text search), `embeddings` (pgvector HNSW, one local text model), `entities` and `edges` (plain tables, recursive CTE for multi-hop), `documents` (sync state) | Keyword recall is the bottleneck → pg_textsearch (BM25). Queries need variable-length paths → a graph engine (Apache AGE or Neo4j), which arrives with Graphiti. Vectors outgrow one node → Qdrant or OpenSearch, replacing the `embeddings` table only |
| Retrieval | One SQL statement: vector similarity ∪ keyword search ∪ one graph hop (a join on `edges`), fused with RRF, returning chunks with source links | — |
| Entity resolution | Own component. Deterministic rules first (repository URLs on pages, service names from Kubernetes and Terraform, channel conventions), LLM-assisted matching later | — |
| Gateway | Own thin MCP server + REST API: authenticates callers (API key or SSO), tool allow-list, read-only tools, audit, rate limits, response caps | — |
| Conversational knowledge | Deferred. Graphiti episodes for Slack, transcripts and tacit knowledge, once a backend license is cleared (Neo4j is GPL, FalkorDB is SSPL) | — |

*Revised 2026-11-03 after the §14 review, with Postgres confirmed self-hosted: `edges` is a plain table rather than Apache AGE; keyword search starts with Postgres's built-in full-text search (not BM25, since `ts_rank` ignores corpus-wide document frequency) with pg_textsearch as the gated upgrade; Debezium is deferred; entity resolution is added as a built component. The managed-hosting constraints in §14 do not apply to self-hosted Postgres, so these choices rest on simplicity and measurement alone.*

Diagram: https://claude.ai/artifact/1Z5gMQM7iKKM671uoh2RQu

### Alternative kept open

Deploy Onyx's MIT core unmodified for documents and chat, use its built-in MCP server, and build only the code graph and the `edges` ontology beside it. This gives a working search product in days. The costs are two indexes (Onyx's Vespa plus our Postgres graph), a heavier footprint (about eight containers), and no single query that joins code to documents. Choose it if time to first demo matters more than one unified store; choose the stack above if the cross-source graph is the point.

### Custom work remaining

- The gateway: MCP plus REST, caller authentication, tool allow-list, audit, response caps. No destructive tools exposed.
- Entity resolution: the `entities` table and the rules that fill it (§14 finding 5).
- Connector gaps: Teams and transcripts (fork from Onyx MIT); a Draw.io parser (mxGraph XML) and a Lucidchart connector (Lucid REST API).
- The export from codebase-memory-mcp's SQLite graph into `entities` and `edges`, pinned to its schema version.
- The `edges` schema: service, repo, team, person, doc, runbook, table, diagram. Incidents join when an incident source exists.
- Ops data and team expertise (§10 gaps 6 and 7), unchanged.

All of this is glue. None of it is security-critical.

### Verify before building

- `unstructured-ingest`: the Confluence, Slack and SharePoint connectors emit per-record versions, so edits are detectable (checked 2026-11-03). Test that deletions are caught by diffing full listings, especially for Slack when only recent history is fetched (§4.5, §13).
- codebase-memory-mcp: confirm the SQLite schema is stable enough to export from, and audit the licenses of its bundled grammars and embedding model (§4.4).
- CocoIndex: v1 (1.1.0) is a rewrite. Its Postgres source has no change feed and is polled with `auto_refresh`, so the LISTEN/NOTIFY capture in §4.6 does not apply. Confirm that one sync process can run one CocoIndex app per source against a shared state file (`docs/design.md` §7).
- If LightRAG is adopted later for document GraphRAG: confirm its Postgres storage classes, including the Apache AGE graph backend, which were not verified in this research.
- Onyx Teams connector: check its dependencies before forking it out of the MIT core.
- Keyword search: measure built-in full-text recall on a real Confluence space; switch to pg_textsearch only if it is the bottleneck (§14 finding 2).
- Pipeline seam: decide shape (a), (b) or (c) from §14 finding 3 in the first spike, before anything is built on it.
- Embedding model: pick one locally hosted text model for documents and chat (§14 finding 7).

## 13. Component selection rationale

Why each component in the §12 stack was chosen, what it was compared against, and what we accept by choosing it. Licenses, star counts and dates are from the GitHub API on 2026-11-02 or 2026-11-03. Claims marked † were not verified in this research.

### 13.1 Day-one components

| Component | Chosen | Why we chose it | Competitors considered | Advantage over the competitors | Trade-off we accept |
|---|---|---|---|---|---|
| SaaS connectors | **[unstructured-ingest](https://github.com/Unstructured-IO/unstructured-ingest)** (Apache-2.0) | One pip dependency covers Confluence, Slack, SharePoint, OneDrive, Google Drive, GitHub, GitLab and SQL sources, each installed as its own extra. It can also write to Neo4j, Qdrant and other stores if we outgrow Postgres. | Onyx connectors (MIT core, fork); PipesHub connectors (Apache-2.0, fork); LlamaHub readers (MIT); Airbyte / PyAirbyte (**ELv2**); dlt sources (Apache-2.0) | Used as a versioned dependency, so upstream fixes arrive with an upgrade. Onyx's and PipesHub's connectors are wired into their own apps and would be forks we maintain. Permissive where Airbyte is ELv2. One consistent pipeline for every source instead of LlamaHub readers of varying quality†. Change detection exists in the code (checked 2026-11-03): Confluence records each page's version number and modified date and lists every page each run; Slack bumps a conversation's version on new replies and edits and accepts a start date; SharePoint emits a version per record. Deletions are found by diffing successive full listings, which still needs a test for Slack when only recent history is fetched. The split-out repo is small (110 stars; parent `unstructured` has 15.7k). No Teams connector. |
| Teams and meeting transcripts | **Onyx connectors forked from the MIT core** | The only Teams connector found among the candidates, plus Zoom, Gong and Fireflies connectors for meeting transcripts. | unstructured-ingest (no Teams); PipesHub (SharePoint, OneDrive, Outlook and Zoom, no Teams connector found); WhisperX + pyannote (transcribe audio ourselves; BSD-2 / MIT) | Production-used code under MIT. Transcripts arrive as text from the meeting tools, so no audio pipeline is needed. | A fork we own. Teams is the least entangled Onyx connector: its imports stay inside Onyx's connector package plus small utilities, with no dependency on Onyx's database, config or file store (checked 2026-11-03). Teams permission sync lives in Onyx's `ee/` folder, which we neither need nor may copy. |
| Incremental sync | **[CocoIndex](https://github.com/cocoindex-io/cocoindex)** (Apache-2.0) | Built for keeping derived indexes in step with sources: it fingerprints content, reprocesses only what changed, applies deletes to targets, and re-runs when the pipeline definition changes. It has Postgres, Qdrant, Neo4j and LanceDB targets. Since v1 it keeps its own tracking state in a local LMDB file rather than in Postgres (checked 2026-11-03). | Pathway (**BSL 1.1**); Airbyte (**ELv2**); dlt (Apache-2.0); orchestrators such as Temporal, Dagster and Airflow; a hand-written cron job with cursors | Pathway and Airbyte are excluded on license. dlt does incremental extract-and-load with cursors but does not track chunk and embedding fingerprints or re-run on pipeline changes†. Orchestrators schedule work but detect no changes. Writing our own means rebuilding the fingerprint, delete and reprocess logic CocoIndex already has. | No enterprise SaaS sources of its own, so it wraps unstructured-ingest. Most feature claims are vendor-authored. Younger than Airbyte (11.8k stars, pushed daily). |
| Database schema | **[tbls](https://github.com/k1LoW/tbls)** (MIT, Go) | Reads a live Postgres or MySQL database and documents its tables, columns, foreign keys and comments. A single binary that can run on a schedule. | SchemaSpy (**LGPL-3.0**, last push 2026-03-05); dlt `sql_database` (Apache-2.0); cognee `dlt_schema_graph` (Apache-2.0); PipesHub Postgres / MariaDB connectors (Apache-2.0) | Permissive where SchemaSpy is LGPL. No JVM, where SchemaSpy needs one†. More active (pushed 2026-11-03). Reads schema only, which is what the knowledge base needs; dlt and PipesHub copy row data. Its structured output maps directly to table nodes and foreign-key edges†. | Schema only. Linking tables to ORM models in code, and to documents, is our glue. |
| Document parsing | **[Docling](https://github.com/docling-project/docling)** (MIT) | Layout analysis, TableFormer table structure and OCR in one library. Chunks keep their page number and bounding box for precise citations, and docling-mcp exposes it as MCP tools. | Unstructured (Apache-2.0); MarkItDown (MIT); Apache Tika (Apache-2.0); MinerU (Apache-2.0 **plus a commercial threshold**); Marker (Apache-2.0 code; model weights carry their own terms†) | Fastest on CPU in its benchmark of 89 PDFs (4,008 pages): 3.1 s/page against MinerU 3.3, Unstructured 4.2 and Marker over 16. No usage threshold, unlike MinerU (100M MAU or USD 20M monthly revenue). Keeps tables and layout that MarkItDown and Tika flatten†. MIT, hosted by LF AI & Data, 70k stars. | On GPU, MinerU is faster (0.21 against 0.49 s/page). The benchmark is Docling's own. Model weights are licensed separately. It reads no diagram semantics. |
| Code intelligence | **[codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp)** (MIT) | The only verified tool that builds cross-repo service edges: HTTP routes matched to their callers with confidence scores, plus gRPC and GraphQL calls. Those edges are what join a service to its runbook and incidents. 162 grammars including Dockerfile, YAML and HCL with Kubernetes, Helm and Terraform extraction. One static binary that runs in CI. SQLite output is easy to export. 17 MCP tools. | Code-Graph-RAG (MIT); SCIP indexers + Zoekt (Apache-2.0); GitNexus (**PolyForm Noncommercial**); Serena (**GPL-3.0** app); Aider repo map (Apache-2.0) | Code-Graph-RAG has compiler-accurate facts but no cross-service edges, and covers 22 languages against 162. SCIP is precise but needs one indexer per language and ships no graph or MCP server. GitNexus and Serena are excluded on license. Aider's repo map is a prompt technique, not a persistent graph. | Written in C, so extending it is costly. Licenses of its bundled grammars and embedding model were not audited. Its schema covers code only, so the export into `entities` and `edges` is our glue; the export is a documented feature (`artifact.json` carries a schema version) but the project is pre-1.0, so pin the version (§14 finding 8). |
| Store | **One self-hosted Postgres** | Text, vectors and graph in one database: a deleted page loses its chunks, vectors and edges in the same store, so there is no second store to drift. One backup (plus CocoIndex v1's local state file) and one set of operational skills. | Multi-store stacks: PipesHub (MongoDB + Neo4j or ArangoDB + Qdrant + Redis); Onyx (Postgres + Vespa† + Redis†) | No drift between stores after a delete or a failed partial write. A single query can combine vector, keyword and graph results. Fewer services to run and monitor. | A single-node ceiling for vectors. With plain tables and built-in FTS the only extension is pgvector (Postgres 13+), so nothing pins the major version; pg_textsearch, if adopted later, needs 17 or 18. |
| Vector search | **[pgvector](https://github.com/pgvector/pgvector)** (PostgreSQL License) | Vectors live in the same transaction as the text and the graph, with no extra service. | Qdrant (Apache-2.0; RBAC proprietary); Milvus (Apache-2.0); Weaviate (BSD-3 **plus Weaviate License in `wl/`**); LanceDB (Apache-2.0); OpenSearch kNN (Apache-2.0); Elasticsearch (**AGPL / SSPL / ELv2**); VectorChord (**AGPL or ELv2**) | The only option that keeps vectors inside the single store. Permissive license, 23.6k stars, and widely available on managed Postgres†. | HNSW on one node. At large scale the dedicated engines are faster†; the upgrade path replaces only the `embeddings` table. |
| Keyword search | **Built-in Postgres full-text search** on day one; **[pg_textsearch](https://github.com/timescale/pg_textsearch)** (PostgreSQL License) when measured recall requires BM25 (§14 finding 2) | Results are fused by rank (RRF), so the keyword leg needs a sensible ordering rather than calibrated scores, and built-in FTS gives that with no extension. pg_textsearch adds a real BM25 index with configurable `k1` and `b` once keyword recall is shown to be the bottleneck. | Built-in FTS alone (`ts_rank` is not BM25); ParadeDB `pg_search` (**AGPL-3.0**); VectorChord-bm25 (**AGPLv3 or ELv2**); OpenSearch (Apache-2.0, separate service); Meilisearch (MIT **plus BUSL-1.1 EE**); Typesense (**GPL-3.0**); Elasticsearch | The only permissively licensed true-BM25 option found that stays inside Postgres. ParadeDB and VectorChord-bm25 are excluded on license; OpenSearch would mean a second store. | Built-in ranking ignores corpus-wide document frequency, so long or repetitive documents can rank too high; that is what the recall measurement checks. pg_textsearch is Postgres 17 and 18 only, needs `shared_preload_libraries`, and is a younger project (4.1k stars). |
| Graph | **Plain `entities` and `edges` tables**, recursive CTEs for multi-hop (§14 finding 1) | The retrieval contract is one graph hop, which is a join; two or three hops are a recursive CTE. Plain tables are CocoIndex's existing Postgres target, join directly with vector and keyword results, and need no extension. | Apache AGE (Apache-2.0); Neo4j Community (**GPL-3.0**); ArangoDB (**BSL 1.1**); Memgraph (**BSL 1.1 + MEL**); FalkorDB (**SSPL**); Kuzu (MIT, **archived**) | No `agtype` casting in the query, no custom CocoIndex target, nothing to install. Every native graph database on the list is copyleft, source-available or archived; AGE is permissive but more engine than one hop needs. | Variable-length path queries are awkward in SQL. When they are needed, a graph engine returns: AGE (Apache-2.0, fine on self-hosted Postgres) or Neo4j alongside Graphiti. |
| Hybrid retrieval | **Hand-written SQL with reciprocal rank fusion (RRF)** | One statement unions vector, keyword and graph-hop candidates and fuses them by rank. | LlamaIndex (MIT), Haystack (Apache-2.0) and LangChain (MIT) retrievers; LightRAG query modes (MIT); Graphiti search recipes (Apache-2.0) | One round trip and no framework layer to debug. RRF combines ranks, so vector, keyword and graph scores need no calibration against each other. Frameworks pay off mainly when switching between stores, which the single-store design avoids. | We own the query and its tuning. No off-the-shelf reranker; a cross-encoder can be added later†. |
| Gateway | **Our own thin MCP server and REST API**, on the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk) (MIT) | One read-only surface over the whole unified store, with caller authentication, audit and rate limits. | Onyx MCP server; PipesHub `mcp-server`; Graphiti MCP server; codebase-memory-mcp's own tools; live-access servers such as github-mcp-server | Onyx's and PipesHub's servers see only their own index. Graphiti's has no authentication and exposes `clear_graph` to any caller. codebase-memory-mcp sees only code. Ours is the only one that sees code, documents, chat, schemas and diagrams together. | Code we write and maintain, though small: a handful of tools over one SQL function. |
| Entity resolution | **Own component** (§14 finding 5) | The join key between sources is identity: the same service is `payments-api` in GitLab, "Payments API" in Confluence, `payments` in a Kubernetes manifest and `#payments-oncall` in Slack. Nothing off the shelf resolves that across our sources. | Graphiti's LLM entity deduplication (Apache-2.0); CocoIndex's embedding-based deduplication of extracted entities (Apache-2.0); cognee's dlt schema graph (Apache-2.0) | Deterministic rules (repository URLs on pages, service names from Kubernetes and Terraform via codebase-memory-mcp's YAML and HCL extraction, channel naming conventions) are explainable and cheap; LLM matching is added only for the long tail. | The rules are ours to write and maintain, and precision must be measured: a wrong merge joins the wrong runbook to a service. |

**Why not take every SaaS connector from Onyx?** It is a valid alternative. Onyx's connector contract is richer: a time-window poll (`PollConnector.poll_source`), an ID-only listing for finding deletions (`SlimConnector.retrieve_all_slim_docs`) and resumable checkpoints (`CheckpointedConnector`). But the connectors are not a standalone package. Confluence and Slack import Onyx's database enums, app config, access models and indexing heartbeat; SharePoint also imports its file store and file processing. Taking them all means vendoring the connector folder, writing stand-ins for about 10 Onyx core modules, and merging upstream changes by hand. Switch to Onyx for all connectors if a test shows unstructured-ingest missing edits or deletions for a source we need, or if we end up forking more than two or three Onyx connectors anyway.

### 13.2 Deferred components (chosen now for when a ceiling is hit)

| Component | Chosen | Trigger | Competitors considered | Advantage over the competitors | Trade-off we accept |
|---|---|---|---|---|---|
| Facts that change over time | **[Graphiti](https://github.com/getzep/graphiti)** (Apache-2.0) | Slack, transcripts and tacit knowledge need facts that are superseded rather than deleted. | LightRAG (MIT); Microsoft GraphRAG (MIT); cognee (Apache-2.0) | Bi-temporal edges record when a fact was true and when it was learned, and outdated facts are invalidated instead of deleted. LightRAG has no temporal model. GraphRAG's incremental update ignores deleted documents (issue #2590). | Its backends are Neo4j (**GPL-3.0**), FalkorDB (**SSPL**) or Neptune (proprietary); none is AGE, so it adds a second graph store. LLM-driven invalidation is not deterministic. |
| Durable sync jobs | **[Temporal](https://github.com/temporalio/temporal)** (MIT) | Sync needs multi-step jobs with retries and cursors that survive a crash, such as a large backfill. | Dagster (Apache-2.0); Airflow (Apache-2.0); Prefect (Apache-2.0); Kestra (Apache-2.0); Hatchet (MIT) | Durable execution: a workflow resumes from its last completed step after a failure†. MIT license, 24.1k stars. | Another cluster to run. Dagster's asset model is the stronger choice if lineage matters more than durability. |
| Regex search across repositories | **[Zoekt](https://github.com/sourcegraph/zoekt)** (Apache-2.0) | Agents need substring or regex search across every repository. | codebase-memory-mcp's FTS5 (per-repo BM25, no regex); ripgrep over checkouts (no index); GitNexus (**PolyForm Noncommercial**) | A trigram index built for multi-repo code, with symbol-aware ranking from ctags. Maintained by Sourcegraph since 2017. | universal-ctags, which it uses for ranking, is **GPL-2.0**, so run it as an external binary. |
| Large-scale vectors | **[Qdrant](https://github.com/qdrant/qdrant)** or **[OpenSearch](https://github.com/opensearch-project/OpenSearch)** (both Apache-2.0) | Vectors outgrow single-node pgvector HNSW. | Milvus (Apache-2.0); Weaviate (BSD-3 **plus Weaviate License**); Vespa (Apache-2.0); Elasticsearch (**AGPL / SSPL / ELv2**) | Qdrant offers sparse plus dense hybrid search and payload filters; pick it if only vectors move. OpenSearch combines BM25 and kNN in one engine; pick it if keyword search moves too. | Breaks the single-transaction property, so deletes must be propagated to two stores. Qdrant's RBAC is proprietary, which does not matter without per-document permissions. |
| Database change capture | **[Debezium](https://github.com/debezium/debezium)** (Apache-2.0) | Rows from an operational database are indexed (§14 finding 4) | CocoIndex Postgres source (Postgres only; since v1 polled, with no change feed); polling on `updated_at` columns; Airbyte CDC (**ELv2**) | Log-based capture for both Postgres and MySQL without adding columns to application tables; polling misses hard deletes. Mature (13.3k stars). | Runs on Kafka Connect or Debezium Server†. Without a permission gate, choose the tables to index explicitly. |
| Graph engine | **[Apache AGE](https://github.com/apache/age)** (Apache-2.0), or Neo4j Community (**GPL-3.0**) alongside Graphiti | Queries need variable-length paths that recursive CTEs make awkward (§14 finding 1) | Memgraph (**BSL 1.1 + MEL**); FalkorDB (**SSPL**); ArangoDB (**BSL 1.1**) | AGE is permissive and stays inside the self-hosted Postgres; Neo4j is what Graphiti supports. | AGE's `agtype` must be cast to join relational results; Neo4j is GPL and a second store. |

## 14. Design review of the §12 stack (2026-11-03)

An adversarial pass over each component in §12 and the architecture diagram: for each, the attempt to break it, and a verdict. Facts checked on 2026-11-03 are cited inline; † marks claims not verified in this research.

### 14.1 Findings, most serious first

**1. Apache AGE is more than the design uses, and it blocks managed Postgres. Verdict: change.**
The retrieval contract in §12 is one graph hop. One hop is a join; two or three hops are a recursive CTE. AGE earns its keep for variable-length path queries and Cypher ergonomics, neither of which the design calls for. Its `cypher()` function returns `agtype`, which has to be cast before it can join vector and BM25 results, so the "one SQL statement" gets harder, not easier. CocoIndex has Postgres-table, Neo4j and FalkorDB targets but no AGE target, so writing edges into AGE is custom code, while writing them into a plain table is CocoIndex's existing target. Hosting is decisive: AGE is absent from the Amazon RDS extension tables for PostgreSQL 15 to 19 and from the Cloud SQL extension list, and GA only on Azure Database for PostgreSQL Flexible Server (May 2025). Apache labels 1.7.0 "stable"; the `-rc0` release tags are its artifact convention, not a maturity signal. **Recommendation:** plain `entities(id, kind, name)` and `edges(src_id, dst_id, type, props jsonb)` tables, recursive CTEs for multi-hop. Revisit a graph engine when queries need variable-length paths, which is also when Graphiti arrives.

**2. pg_textsearch is the right BM25 engine on the wrong day. Verdict: defer behind a measurement.**
Checked: v1.0 went GA on 2026-04-03 under the PostgreSQL License; Tiger Cloud calls v1.1.0 production-ready; Cloud SQL and AlloyDB offer it in public preview (announced 2026-09-21); it is absent from the RDS tables; it needs `shared_preload_libraries`, so a restart and self-managed configuration; PostgreSQL 17 and 18 only. Because §12 fuses results by rank (RRF), built-in full-text search (`ts_rank_cd`) is an adequate day-one keyword leg. §13 promoted pg_textsearch to day one; that was premature. **Recommendation:** start with built-in FTS, measure keyword recall on a real Confluence space, switch when it is the bottleneck. pg_textsearch stays the chosen BM25 engine in §13, with that trigger.

**3. CocoIndex wrapping unstructured-ingest is the largest integration risk, and the seam does not exist yet. Verdict: decide in the first spike.**
Both are pipeline frameworks with their own opinions. unstructured-ingest runs indexer → downloader → partition → chunk → embed → upload and carries per-record versions; CocoIndex runs sources → transforms → targets with fingerprints and live update. Checked: unstructured-ingest's Postgres destination (`sql/postgres.py`) has no vector or embedding handling, so it cannot write pgvector on its own; CocoIndex's Postgres target can. Neither framework alone gives connectors, fingerprints, deletion propagation and a pgvector target. Three shapes work: (a) unstructured-ingest's indexer and downloader stages only, exposed as CocoIndex sources, with CocoIndex owning chunking, embedding and writes; (b) CocoIndex alone with custom sources on the vendor SDKs; (c) unstructured-ingest alone with a custom Postgres writer and a `documents`-table diff for deletions, losing reprocess-on-pipeline-change. **Lean:** (a), because it keeps both vendors' maintained code and puts the one piece of glue at a thin seam. The diagram currently draws that seam as if it were built.

**4. Debezium is drawn as day one for a decision never taken. Verdict: move to the deferred strip.**
Whether row data from operational databases is indexed at all is undecided; Debezium brings Kafka Connect or Debezium Server† with it. Default to schema only via tbls on a schedule. Note, without any permission gate, operational rows (customer records) are the likeliest source of accidental exposure, so if row data is ever indexed, choose the tables explicitly.

**5. The ontology and entity resolution have no owner. Verdict: add a built component.**
The diagram's caption promises to join a service's code to its docs and runbooks. The join key is identity, and the same service is `payments-api` in GitLab, "Payments API" in Confluence, `payments` in a Kubernetes manifest and `#payments-oncall` in Slack. No component resolves these. codebase-memory-mcp's cross-service edges work within code and do not know the Confluence page. **Recommendation:** an `entities` table with aliases, filled by deterministic rules first (repository URLs found in pages, service names from Kubernetes and Terraform via codebase-memory-mcp's YAML and HCL extraction, channel naming conventions), LLM-assisted matching later. This is the intellectual core of the platform and belongs on the diagram as a built component.

**6. Incidents appear in the caption but not in the sources. Verdict: fix one or the other.**
No PagerDuty, Opsgenie or Grafana source is drawn, and no verified open-source connector for them was found (§10 gap 6). Either add a custom incident source or remove "incidents" from the caption until one exists. Runbooks are covered by Confluence and Git.

**7. The embedding model and chunking are unspecified. Verdict: add a one-line decision.**
`embeddings` exists on the diagram without a model. The choice sets cost, data residency and re-embedding time. **Lean:** one locally hosted open-weights text model through CocoIndex's embedder, applied to documents and chat only. Code is not embedded in Postgres; codebase-memory-mcp keeps its own per-repository FTS5 and embedding index, and only entities and edges are exported. That avoids mixing a code model and a text model in one vector column.

**8. codebase-memory-mcp export is a supported feature, not a hack, but pin it. Verdict: keep with conditions.**
Checked: the README documents an export (`VACUUM INTO`, zstd-compressed SQLite, with `artifact.json` carrying a schema version) and references a breaking schema change (#768) with a skip policy for older indexes. The latest release is v0.12.1 (2026-10-16), pre-1.0. Pin the version, write the exporter against the `artifact.json` schema version with a fixture, and export a minimal set (service, route, caller, file). Its `query_graph` and `get_architecture` MCP tools may be a more stable surface than raw tables†.

**9. Docling: scope it to attachments and estimate the backfill. Verdict: keep.**
At its own benchmark figure of 3.1 s/page on CPU, 5,000 attachment pages cost about 4.3 CPU-hours; 500,000 pages cost about 18 CPU-days per core. Route Confluence HTML and Slack text through plain HTML-to-Markdown conversion, not Docling. The diagram already says "parses attachments"; the report lacked the estimate.

**10. Gateway. Verdict: keep, with two additions.**
A read-only tool surface over one SQL function is right; never expose raw SQL to agents, since prompt injection then becomes corpus exfiltration even without per-document permissions. Add response-size caps and pagination limits so an agent cannot page through the whole corpus. Start with API keys; the MCP specification's OAuth flow is more work† and can follow.

**11. One Postgres. Verdict: keep, and it becomes portable only if findings 1 and 2 are applied.**
With plain tables, built-in FTS and pgvector, the store runs on RDS, Cloud SQL, Azure or self-hosted (pgvector is on all three; checked for RDS and Cloud SQL). With AGE and pg_textsearch, no single managed provider offers both today: Azure has AGE but pg_textsearch was not found there; Cloud SQL has pg_textsearch in preview but not AGE; RDS has neither.

**12. Unchanged after review:** tbls (schema only), the Teams fork from Onyx, the unstructured-ingest Slack-deletion test (§12), Temporal, Zoekt, Qdrant or OpenSearch as the vector upgrade. On Graphiti's backend: running unmodified Neo4j Community as a separate server is common practice under GPL-3.0; the legal review is about that arrangement, not about linking.

### 14.2 Verdict table

| Component | Verdict | Change |
|---|---|---|
| unstructured-ingest + CocoIndex | Decide in spike | Pick shape (a), (b) or (c) from finding 3 before drawing the seam |
| Teams from Onyx MIT core | Keep | — |
| tbls | Keep | — |
| Debezium | Defer | Deferred strip; trigger: row data from an operational database is indexed |
| Docling | Keep | Attachments only; add backfill estimate |
| codebase-memory-mcp | Keep | Pin version; exporter against `artifact.json` schema version; minimal edge set |
| One Postgres 17/18 | Keep | Portable only with the two changes below |
| pgvector | Keep | Decide the embedding model (finding 7) |
| pg_textsearch | Defer | Built-in FTS first; switch on measured recall gap |
| Apache AGE | Change | Plain `entities` and `edges` tables; recursive CTE |
| Hand-written SQL + RRF | Keep | — |
| Gateway | Keep | Response caps; API keys first |
| Entity resolution | Add | New built component; deterministic rules first |
| Incident source | Fix | Add a custom source or drop "incidents" from the caption |
| Graphiti, Temporal, Zoekt, Qdrant/OpenSearch (deferred) | Keep | — |

### 14.3 Diagram changes proposed

1. Store: `edges` becomes a plain table ("recursive CTE for 2–3 hops"); add `entities` (aliases); `chunks` label becomes "built-in FTS; BM25 upgrade gated".
2. Sources: "Postgres · MySQL" becomes "tbls schema (rows deferred)"; Debezium moves to the deferred strip.
3. Ingest: add a dashed "Entity resolution (built)" box between sync and store.
4. Caption: remove "incidents" until an incident source exists.
5. Deferred strip: add pg_textsearch and Debezium with their triggers.

### 14.4 Applied (2026-11-03)

All five changes were applied to the diagram, and §12 and §13 were updated to match. Postgres will be self-hosted, so the managed-hosting constraints in findings 1, 2 and 11 do not apply; the plain-table and built-in-FTS choices stand on simplicity and measurement alone, and both AGE and pg_textsearch remain available later without a platform change. The deferred strip also gained a "graph engine" entry so the return path for AGE or Neo4j stays visible. Still open from this review: the pipeline seam (finding 3) and the embedding model (finding 7), both to be settled in the first spike.

## 15. Entities and entity resolution, explained

An **entity** is a real-world thing the organisation talks about: a service, a repository, a team, a person, a database table, a runbook, a diagram. It is different from the text itself. A Confluence page or a Slack thread is split into **chunks**, the pieces of text that search finds. Chunks *mention* entities, and **edges** connect entities to each other.

### 15.1 Example: one service, four names

The payments service appears in every source under a different name:

| Where | What it is called |
|---|---|
| GitLab | `payments-api` (repository name) |
| Confluence | "Payments API" (page title) |
| Kubernetes manifest | `payments` (deployment name) |
| Slack | `#payments-oncall` (channel) |

To a computer these are four unrelated strings. In the `entities` table they become one row with four aliases:

| id | kind | name | aliases |
|---|---|---|---|
| 42 | service | Payments API | `payments-api`, `payments`, `#payments-oncall` |

The `edges` table then connects entity 42 to other entities:

- 42 **implemented in** repository `gitlab.com/acme/payments-api`
- 42 **calls** entity 57 (Ledger service), found by codebase-memory-mcp from an HTTP call in the code
- 42 **documented by** the Confluence page "Payments API runbook"
- 42 **reads** table `payments.transactions`, found from tbls plus the code's database models
- 42 **discussed in** `#payments-oncall`
- 42 **owned by** the Payments team

### 15.2 Why it matters

Take the question "How do I roll back payments after a bad deploy?"

- **Without entities:** search returns whatever text best matches the words. The runbook appears only if its wording happens to match.
- **With entities:** search finds a chunk mentioning `payments`, recognises it as entity 42, and follows one edge to the runbook, the repository, and the downstream Ledger service a rollback might affect. That single hop is the "graph hop" in the query on the architecture diagram.

### 15.3 Entity resolution

**Entity resolution** is the work of recognising that `payments-api`, "Payments API", `payments` and `#payments-oncall` are the same thing, so they become one row instead of four. It is a component we build (§12, §14 finding 5):

1. **Rules first.** A Confluence page that links to `gitlab.com/acme/payments-api` is about that repository. A Kubernetes deployment named `payments` built from that repository is the same service. A channel named `#<service>-oncall` belongs to that service.
2. **An LLM for the long tail**, for names the rules cannot match, such as "the money service".

The risk is a wrong merge: if two services are merged into one, a question about one returns the other's runbook. Match precision has to be measured, not assumed.

### 15.4 Entity kinds and where they come from

| Kind | Created by |
|---|---|
| service | codebase-memory-mcp (from code, Kubernetes and Terraform files) |
| repo | GitLab and GitHub connectors |
| table | tbls |
| person | Slack and Teams users, commit authors |
| team | Team and channel naming conventions, ownership files† |
| doc, runbook | Confluence, SharePoint and Drive connectors |
| diagram | The Draw.io and Lucidchart parser |

Each connector or indexer creates the entities it knows about; entity resolution then links those separate records together.

## 16. Simplification (2026-11-04)

*Supersedes the §12 stack. The standing decision record, with alternatives, consequences and the deferred list, is [`docs/decisions.md`](../docs/decisions.md). How the simplified system is configured and run is in [`docs/design.md`](../docs/design.md), whose §2 lists what was removed and what was adopted from [team-knowledge-kit](https://github.com/rsihare93/team-knowledge-kit).*

### Decisions

1. **The sources are git repositories, Confluence, database schemas (tbls) and Lucidchart, plus an uploads folder.** Meeting transcripts and other documents are exported by people and dropped into that folder. There are no chat, meeting or drive connectors (Slack, Teams, Zoom, Gong, Fireflies, SharePoint, Google Drive), and no Draw.io parser.
2. **The system is a search index only.** No language model runs in the pipeline.
3. **One SQLite file**, with FTS5 for keywords and sqlite-vec for vectors, replaces Postgres and pgvector.
4. **A CLI and an Agent Skill** replace the MCP gateway.

### Why each §12 component went

The §12 stack was sized for ten sources and a cross-source graph. With five sources left, four of them reached through a plain REST call or a file read, most components no longer had a job.

| §12 component | Why it was there | Why it is no longer needed |
|---|---|---|
| unstructured-ingest | One dependency for many SaaS connectors | Only Confluence remains, and it takes two REST calls |
| Onyx fork | Teams and meeting transcripts | Transcripts arrive through the uploads folder |
| CocoIndex v1 | Incremental sync and propagating deletes across many connectors | Every remaining source exposes an id and a version, so a table and a loop cover it. Its LMDB state file, which had to be reset together with Postgres, goes too |
| Postgres + pgvector in Docker | Text, vectors and graph in one transaction | SQLite holds text and vectors in one transaction, with no service to run. Its FTS5 has real BM25, which settles §14 finding 2 |
| Entity resolution, `entities`, `edges` | Joining a service's code, docs, channels and runbooks | Its main inputs (Slack channel names, the code graph, Kubernetes and Terraform names) are gone. It comes back only if the golden questions show recall lost to name mismatches |
| codebase-memory-mcp export | Service and route edges for the graph | No graph. Agents use their own code tools |
| Gateway (MCP + REST) | Keys, rate limits, audit and caps for a shared server | A local CLI over a local file needs none of these. Read-only access and the result cap stay |
| Docling | Layout and tables in attachments | MarkItDown is lighter and needs no model weights. This accepts the table flattening noted in §13.1 |

### Chosen stack (v1)

| Layer | Pick | Ceiling → upgrade |
|---|---|---|
| Sources | `git`, `httpx` REST calls (Confluence, Lucid), `tbls doc`, a folder walk | A new source is one module with `list()` and `fetch()` |
| Incremental sync | Our own loop over `(id, version)`, with a guard against partial listings | — |
| Conversion | MarkItDown 0.1.9 (MIT) | Tables or scanned PDFs matter → Docling |
| Embeddings | granite-embedding-small-english-r2 (Apache-2.0, 384 dimensions) | Content not in English → bge-m3 |
| Keyword search | SQLite FTS5, `bm25()` | — |
| Vector search | sqlite-vec 0.1.9, brute force | A few hundred thousand chunks → sqlite-vec ANN, LanceDB or pgvector |
| Access | The `kb` CLI and the `kb` skill | An agent without a shell → an MCP server over the same SQL |
| Measurement | `kb eval` over golden questions (recall@k) | — |

## Appendix: verification provenance

- Workflow run `wf_55eaddc3-97f`: 5 search angles, 21 sources fetched, 104 claims extracted, 25 verified (21 confirmed, 4 refuted).
- **Refuted claims, with reasons:**
  1. *PipesHub is Apache-2.0 with no paid self-hosted edition (0-3).* The pricing page lists a paid Enterprise edition that can be deployed on-premises, VPC or air-gapped, with feature gating.
  2. *PipesHub retrieval enforces source access controls (0-3).* `APP_LEVEL` connectors carry no source ACLs, the permission cache lasts 300 seconds, and issue #4545 let agents widen access.
  3. *SWIRL's MCP server, reranker and other features are Enterprise-only (0-3).* The reason was not recorded.
  4. *A specific list of production SCIP indexers (0-3).*
- The second pass, on 2026-11-02, used the `gh api` repository metadata and license endpoints for 85 repos. It inspected the source trees of PipesHub, RAGFlow, CocoIndex, unstructured-ingest, cognee, Weaviate and Onyx.
