# Knowledge base architecture

> **Full design of 2026-11-03, kept for reference.** For v1 it is superseded by the simplified design in [../design.md](../design.md). What was removed and why is in [../decisions.md](../decisions.md) and [../design.md](../design.md) §2. Use this document when a deferred item comes back.

*2026-11-03. These diagrams are drawn in Mermaid, which GitHub renders in place. The design behind them is in [design.md](design.md), and the reasons for each component are in the [research report](../../research/oss-landscape-2026-11.md), §12–15. A hand-drawn version of the first diagram is in [research/architecture.html](../../research/architecture.html).*

Legend: a solid box is a reused open-source component, a dashed box is code we write or fork, and a cylinder is a Postgres table.

## 1. System

Every source feeds one sync process, `kb sync`, and that process writes to one Postgres. Agents read the knowledge base through one read-only gateway.

```mermaid
flowchart LR
  subgraph sources["Sources"]
    direction TB
    git["GitLab · GitHub<br/>repositories"]
    docs["Confluence · SharePoint<br/>Google Drive"]
    slack["Slack"]
    teams["Teams · Zoom<br/>Gong · Fireflies"]
    db[("Postgres · MySQL<br/>schema only")]
    diag["Lucidchart"]
  end

  subgraph ingest["Ingest · kb sync · CocoIndex v1, one app per source"]
    direction TB
    clone["git clone<br/>.kb/repos"]
    ui["unstructured-ingest<br/>indexer + downloader"]
    onyx["Onyx MIT fork<br/>Teams + transcripts"]
    tbls["tbls<br/>schema to JSON"]
    dparse["Diagram parser<br/>Draw.io XML · Lucid API"]
    cbm["codebase-memory-mcp<br/>code graph"]
    proc["Convert · chunk · embed<br/>markdownify · Docling · bge-m3"]
    er["Entity resolution<br/>rules + kb.toml aliases"]
  end

  subgraph store["Postgres 17 + pgvector · the one store"]
    direction TB
    documents[("documents")]
    chunks[("chunks · full-text")]
    embeddings[("embeddings · HNSW")]
    edges[("edges")]
    entities[("entities · aliases")]
  end

  subgraph access["Access"]
    direction TB
    gw["Gateway<br/>kb mcp over stdio · kb serve over HTTP<br/>read-only tools · caps · audit"]
    agents["Claude Code · agents · apps"]
  end

  deferred["Deferred until a ceiling is hit:<br/>Graphiti · Temporal · Zoekt · Qdrant or OpenSearch<br/>pg_textsearch · Debezium · Apache AGE or Neo4j"]

  git --> clone
  docs --> ui
  slack --> ui
  teams --> onyx
  db --> tbls
  diag --> dparse
  clone --> cbm
  clone --> proc
  clone -.->|".drawio files"| dparse
  ui -.->|".drawio files"| dparse
  ui --> proc
  onyx --> proc
  tbls --> proc
  dparse --> proc
  proc --> documents
  proc --> chunks
  proc --> embeddings
  proc --> edges
  cbm -->|"services · routes · calls"| edges
  edges --> er
  er --> entities
  gw -->|"one SQL query: vector + keyword + graph hop, fused by RRF"| store
  agents -->|"MCP or REST"| gw

  classDef built stroke-dasharray: 6 4
  classDef later stroke-dasharray: 2 4
  class onyx,dparse,proc,er,gw built
  class deferred later
```

Draw.io has no source of its own: `.drawio` files are picked up wherever they already live, in git repositories and on Drive. Code is not embedded. codebase-memory-mcp keeps its own per-repository index, and only its services, routes and calls are exported into `edges`.

## 2. One sync run, for one record

CocoIndex v1 runs one processing component per source record. It remembers each component's key, `(identifier, version)`, so a record whose version has not changed is skipped without being downloaded. A record that is no longer listed is not mounted, and CocoIndex deletes the rows it produced.

```mermaid
sequenceDiagram
  autonumber
  participant K as kb sync
  participant C as Connector
  participant A as Source API
  participant P as Convert, chunk, embed
  participant DB as Postgres
  K->>C: list records
  C->>A: list IDs and versions only
  A-->>C: records
  C-->>K: identifier and version for each record
  Note over K: Same version as last run: skip.<br/>Not listed any more: delete its rows.
  K->>C: download a new or changed record
  C->>A: fetch content
  A-->>C: file
  C-->>P: local file path
  P->>P: HTML to Markdown or Docling, then split and embed with bge-m3
  P->>DB: upsert documents, chunks, embeddings, edges
  Note over K,DB: After every source has run
  K->>DB: entity resolution rebuilds entities from edges and rules
```

## 3. One question, end to end

The gateway embeds the question with the same model that embedded the documents. It then runs one SQL function that unions three candidate lists and fuses them by rank.

```mermaid
sequenceDiagram
  autonumber
  participant U as Agent in the repo
  participant G as kb mcp
  participant M as bge-m3 in-process
  participant DB as Postgres
  U->>G: search "how do I roll back payments after a bad deploy"
  G->>M: embed the question
  M-->>G: 1024-dimension vector
  G->>DB: kb_search(question, vector, k)
  Note over DB: Vector top 50, plus full-text top 50,<br/>plus documents one edge away from the top hits.<br/>Fused by reciprocal rank (RRF).
  DB-->>G: chunks with titles, URLs and entities
  G-->>U: at most k results, snippets capped, source links
  U->>G: get_entity "payments" or neighbors
  G->>DB: entities and edges lookup
  DB-->>G: aliases, linked repos, runbooks, channels
  G-->>U: capped list
```

## 4. What `kb-init` sets up in a repository

`kb-init` turns the repository it runs in into a knowledge-base project. Configuration that is safe to share is committed. Secrets and local state go under the gitignored `.kb/` folder, and Postgres runs in Docker.

```mermaid
flowchart TB
  subgraph repo["Your repository"]
    direction TB
    toml["kb.toml<br/>sources and settings, no secrets<br/>committed"]
    mcp[".mcp.json<br/>runs kb mcp over stdio, no secrets<br/>committed"]
    subgraph local[".kb/ · gitignored"]
      direction TB
      env[".kb/.env · mode 0600<br/>PATs and keys, local Postgres password"]
      state["cocoindex.db · repos/ · cbm/ · schema/ · logs/"]
    end
  end

  subgraph docker["Docker · compose project kb-name"]
    pg[("Postgres 17 + pgvector<br/>bound to 127.0.0.1 only<br/>named volume for data")]
  end

  init["kb-init"] -->|"writes"| toml
  init -->|"merges"| mcp
  init -->|"writes after checking each token"| env
  up["kb up"] -->|"starts"| pg
  sync["kb sync"] -->|"reads"| toml
  sync -->|"reads"| env
  sync -->|"keeps"| state
  sync -->|"writes"| pg
  agent["Claude Code in this repo"] -->|"launches"| mcp
  mcp -->|"queries"| pg

  classDef built stroke-dasharray: 6 4
  class init,up,sync built
```
