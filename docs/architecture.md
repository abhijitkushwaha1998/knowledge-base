# Knowledge base architecture

*2026-11-04. These diagrams are drawn in Mermaid, which GitHub renders in place. The design behind them is in [design.md](design.md). The reasons for each component are in the [research report](../research/oss-landscape-2026-11.md) §16, which simplified the 2026-11-03 stack.*

Legend: a solid box is a reused open-source component or an external system, a dashed box is code we write, and a cylinder is stored data.

## 1. System

Five sources feed one command, `kb sync`, which writes one SQLite file. Agents read it by running `kb search`, which a skill tells them to do. There is no server.

```mermaid
flowchart LR
  subgraph sources["Sources"]
    direction TB
    git["Git repositories<br/>Markdown docs · runbooks · ADRs"]
    conf["Confluence<br/>Cloud or Data Center"]
    db[("Postgres · MySQL<br/>schema only")]
    lucid["Lucidchart"]
    up["Uploads folder<br/>transcripts · PDF · Word · slides"]
  end

  subgraph ingest["kb sync · one process"]
    direction TB
    conn["Connectors<br/>git · REST · tbls doc · folder walk<br/>list id and version, fetch only changes"]
    conv["Convert to Markdown<br/>MarkItDown · VTT cleanup"]
    chunk["Chunk by heading<br/>with title and section"]
    emb["Embed<br/>granite-embedding-small"]
  end

  subgraph store[".kb/kb.sqlite · one file"]
    direction TB
    documents[("documents<br/>id · version · body")]
    chunks[("chunks<br/>FTS5 · BM25")]
    vec[("chunk_vec<br/>sqlite-vec")]
  end

  subgraph access["Access"]
    direction TB
    skill["kb skill<br/>.claude/skills · .agents/skills"]
    cli["kb search · kb show"]
    agents["Claude Code · Codex · Copilot"]
  end

  deferred["Deferred until needed:<br/>entities and aliases · shared index built in CI<br/>MCP server · LLM summary pages · Docling"]

  git --> conn
  conf --> conn
  db --> conn
  lucid --> conn
  up --> conn
  conn --> conv
  conv --> chunk
  chunk --> emb
  conv --> documents
  chunk --> chunks
  emb --> vec
  agents -->|"reads"| skill
  agents -->|"runs"| cli
  cli -->|"one SQL query: BM25 + vector, fused by RRF"| store

  classDef built stroke-dasharray: 6 4
  classDef later stroke-dasharray: 2 4
  class conn,chunk,skill,cli built
  class deferred later
```

Code itself is not indexed. Agents search the code they work in with their own tools, and other repositories contribute only their docs.

## 2. One sync run, for one record

Every connector lists the id and version of every record. A record whose version matches the stored one is skipped without being fetched. A record that is no longer listed is deleted, but only after a complete listing.

```mermaid
sequenceDiagram
  autonumber
  participant K as kb sync
  participant C as Connector
  participant S as Source
  participant P as Convert, chunk, embed
  participant DB as kb.sqlite
  K->>C: list records
  C->>S: ids and versions only
  S-->>C: every record
  C-->>K: id and version for each record
  Note over K,DB: Same version as stored, so skip it
  K->>C: fetch a new or changed record
  C->>S: download its content
  S-->>C: page, file, schema or diagram
  C-->>P: Markdown text
  P->>DB: one transaction replaces the document, its chunks and vectors
  Note over K,DB: After a complete listing, delete records no longer listed.<br/>More than 20 percent of a source needs --rebuild.
```

## 3. One question, end to end

The question is embedded with the same model that embedded the chunks. One SQL statement then fuses the keyword and vector results by rank.

```mermaid
sequenceDiagram
  autonumber
  participant A as Agent in the repo
  participant K as kb CLI
  participant M as Embedding model
  participant DB as kb.sqlite
  A->>A: the kb skill matches a question about our systems
  A->>K: kb search "how do I roll back payments after a bad deploy"
  K->>M: embed the question
  M-->>K: 384-dimension vector
  K->>DB: one SQL statement
  Note over DB: BM25 top 50 plus vector top 50,<br/>fused by reciprocal rank (RRF)
  DB-->>K: chunks with title, section and URL
  K-->>A: top hits with ids and snippets
  A->>K: kb show confluence:PAY:123456
  K-->>A: the whole document
  A->>A: answer, citing titles and URLs
```

## 4. What `kb init` sets up in a repository

Configuration that is safe to share, and the skill, are committed. Tokens, the index and logs stay in the gitignored `.kb/` folder. The embedding model is cached once per machine, and the uploads folder can be anywhere.

```mermaid
flowchart TB
  subgraph repo["Your repository"]
    direction TB
    toml["kb.toml<br/>sources, model and revision, no secrets<br/>committed"]
    skills[".claude/skills/kb · .agents/skills/kb<br/>the kb skill · committed"]
    pointer["AGENTS.md · CLAUDE.md<br/>a short pointer to kb search · committed"]
    subgraph local[".kb/ · gitignored"]
      direction TB
      env[".kb/.env · mode 0600<br/>tokens"]
      index[("kb.sqlite")]
      state["repos/ · schema/ · logs/kb.jsonl · sync.lock"]
    end
  end

  uploads["Uploads folder<br/>any path, e.g. a synced OneDrive folder"]
  cache[("Model cache<br/>HF_HOME, once per machine")]

  init["kb init"] -->|"writes"| toml
  init -->|"writes"| skills
  init -->|"adds to"| pointer
  init -->|"writes after checking each token"| env
  init -->|"downloads the model into"| cache
  sync["kb sync"] -->|"reads"| toml
  sync -->|"reads"| env
  sync -->|"reads"| uploads
  sync -->|"loads the model from"| cache
  sync -->|"keeps"| state
  sync -->|"writes"| index
  agent["Claude Code · Codex · Copilot"] -->|"loads"| skills
  agent -->|"runs kb search"| index

  classDef built stroke-dasharray: 6 4
  class init,sync built
```
