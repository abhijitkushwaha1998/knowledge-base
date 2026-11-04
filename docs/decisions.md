# Decision record

*2026-11-04. The choices that would be expensive to reverse once building starts. Each row says what was chosen, the alternative not taken, why, what breaks if the choice is wrong, and the signal that would reopen it. [design.md](design.md) and [plan.md](plan.md) assume these. The history, including the 2026-11-03 stack these decisions replaced, is in the [research report](../research/oss-landscape-2026-11.md) §12–16, and the full 2026-11-03 design is kept in [full-design/](full-design/design.md).*

## 1. The decisions

| # | Decision | Alternative not taken | Why | If it is wrong | Revisit when |
|---|---|---|---|---|---|
| 1 | **A search index, not a wiki.** Sources are converted to text and indexed; nothing is rewritten. No language model runs in the pipeline | An LLM-written, reviewed wiki of dated facts (the team-knowledge-kit approach); LLM summary pages loaded at session start | Nothing to review, no model bill, no provider approval needed, and the agent asking already has a model. Most of the reference kit's machinery exists to serve synthesis | Agents get raw text where a synthesised answer was needed, and cross-document questions ("how does X relate to Y") go unanswered | `kb eval` shows questions that no single document answers |
| 2 | **Five sources plus an uploads folder.** Git repositories, Confluence, database schemas, Lucidchart, and a folder people drop files into. No chat, meeting or drive connectors | Slack, Teams, SharePoint, Google Drive, Zoom, Gong and Fireflies connectors, via unstructured-ingest and a fork of Onyx | Each connector is a token, an admin consent, a rate-limit story and code to maintain. Exporting a transcript into a folder costs a person thirty seconds | Knowledge that lives only in chat never reaches the index, and people stop exporting transcripts | The uploads folder is visibly neglected while chat holds the answers |
| 3 | **One SQLite file** (`.kb/kb.sqlite`) with FTS5 for keywords and sqlite-vec for vectors, fused by reciprocal rank in one SQL statement | Postgres + pgvector in Docker (the 2026-11-03 stack); a vector database service; LanceDB | No service to run, one file to delete when in doubt, text and vectors in one transaction, and FTS5 gives real BM25 where Postgres's built-in ranking does not | sqlite-vec searches by brute force and slows past a few hundred thousand chunks; multi-writer access is not a goal | Search latency exceeds about 100 ms on the vector leg, or two processes need to write |
| 4 | **Our own sync loop** over `(id, version)` per record, with a guard against partial listings | CocoIndex v1 (incremental engine with its own LMDB state file); Airbyte, dlt, an orchestrator | Every remaining source exposes an id and a version, so the loop is about forty lines. CocoIndex added a second state store that had to be reset together with the database | A source without versions appears, or a multi-step backfill needs to survive a crash | A connector cannot list cheaply, or a first sync takes longer than a laptop session |
| 5 | **A CLI and an Agent Skill**, not an MCP server. `kb search` and `kb show`, plus `SKILL.md` in `.claude/skills` and `.agents/skills` | An MCP server over stdio registered in `.mcp.json`; a REST API with keys | One setup works for Claude Code, Codex and Copilot. There is no process to keep alive and no auth layer to write | An agent that cannot run shell commands has no way in | Such an agent needs the knowledge base; an MCP server over the same SQL is then a small addition |
| 6 | **granite-embedding-small-english-r2** as the default embedding model (Apache-2.0, 384 dimensions), bge-m3 as the opt-in | bge-m3 as default (MIT, 1,024 dimensions, multilingual, 2.3 GB) | Every `kb search` is a new process that loads the model. The small model is estimated at 2–3 s per call, bge-m3 at 5–12 s, and agents search several times per task | Recall on the team's questions is noticeably worse, or content is not in English | The spike's recall@10 comparison, or non-English sources |
| 7 | **MarkItDown** for converting PDF, Word, PowerPoint, Excel and HTML | Docling (layout and table models, OCR) plus markdownify for HTML | One lightweight library covers every format, with no model weights to download | Tables in PDFs come out flattened; scanned PDFs come out empty | Tables or scanned documents matter to the questions people ask |
| 8 | **Each person syncs their own index.** No CI job, no shared index to download | A nightly CI pipeline publishing an index that teammates pull (the reference kit's model) | Nothing to host or schedule. A first index can be copied from a teammate | Every laptop re-downloads and re-embeds the same corpus, and indexes drift between teammates | Syncing takes long enough that people stop doing it |
| 9 | **Secrets by name.** `kb.toml`, the skill and `AGENTS.md` are committed and hold no secrets. Tokens live in `.kb/.env`, mode 0600, gitignored, or in the environment | Tokens in `kb.toml`; a shared vault integration | Committed files can be shared freely, and CI can supply the same variables without a file | A teammate commits `.kb/.env` by mistake (guarded: `kb init` refuses if it is tracked) | A team needs central rotation; a vault is then a way to populate the environment |
| 10 | **No per-document permissions.** Anyone who can run `kb` in the repository, or holds a copy of `kb.sqlite`, reads everything indexed | An authorization layer (SpiceDB or OpenFGA) with per-document ACLs; permission-aware connectors | Access control is which sources are connected, and those should be sources the whole team may read anyway | A source with mixed permissions is connected and content leaks to teammates who could not see it at the source | A source that is not team-wide readable becomes necessary |

## 2. Deferred, with the signal that brings each back

| Deferred | Add it when |
|---|---|
| Entities and aliases ("the money service" is `payments-api`), so one question reaches every name for a thing | `kb eval` shows questions failing because one thing goes by several names |
| A shared index built in CI and pulled by each person | Syncing on every laptop becomes a burden (decision 8) |
| An MCP server over the same search SQL | An agent that cannot run a shell command needs the knowledge base (decision 5) |
| LLM summary pages, or the reference kit's "map" layer loaded at session start | Search alone fails the golden questions (decision 1) |
| Docling | Tables in PDFs, or scanned PDFs (OCR), matter (decision 7) |
| sqlite-vec's ANN index, LanceDB or pgvector, replacing only the vector table | The index grows past a few hundred thousand chunks (decision 3) |
| Several uploads folders (`[[uploads]]` with a `name`) | A team needs more than one drop location |
| Confluence blog posts and attachments | People ask for them |
| A connector for incidents (PagerDuty, Opsgenie, Grafana) | An incident source exists that the whole team may read |

## 3. Principles

1. Files are the API: config, index and skill are files, and nothing runs between syncs.
2. Fetch only what changed, and delete only after a complete listing.
3. Search returns the team's own words with a link; synthesis is the agent's job.
4. Measured: the golden questions are scored after every change to the model, chunker or query.
5. Read-only everywhere, and secrets only by name in anything committed.
6. One command per repository, and the same experience for every teammate who clones it.

## 4. Assumptions

| # | Assumption | Status |
|---|---|---|
| A1 | One knowledge base per repository, configured by a committed `kb.toml` | confirmed 2026-11-03 |
| A2 | Every connected source may be read by the whole team | confirmed 2026-11-03 |
| A3 | Transcripts and ad-hoc documents arrive by someone saving them into a folder | confirmed 2026-11-04 |
| A4 | Agents can run shell commands in the repository | confirmed 2026-11-04 |
| A5 | Content is mostly English (default model); other languages switch to bge-m3 | assumed, to confirm per team |
| A6 | macOS and Linux laptops; Windows through WSL | assumed |
| A7 | Python with permissively licensed libraries only | confirmed 2026-11-03 |

## 5. Open questions

Each is marked † in [design.md](design.md) and listed in its §13 spike checklist: search latency per model, recall per model, Confluence `export_view` fidelity through MarkItDown, Lucid search pagination, the skill `allowed-tools` syntax, partial-clone performance, MySQL schema-only grants, sqlite-vec loading under uv's Python on both platforms.
