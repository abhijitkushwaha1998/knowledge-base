# Glossary and key components

*2026-11-04. The terms used across [design.md](design.md), [architecture.md](architecture.md), [decisions.md](decisions.md) and [plan.md](plan.md), then one paragraph on each component of the system.*

## 1. Glossary

| Term | Meaning |
|---|---|
| **Source** | Somewhere the knowledge base reads from: a git repository, a Confluence space, a database, Lucidchart, or the uploads folder |
| **Kind** | The type of a source: `git`, `confluence`, `database`, `lucid` or `uploads`. One connector module per kind |
| **Source instance** | One configured source of a kind, named so that it is the same on every teammate's machine: `git:github.com/acme/ledger`, `confluence:PAY`, `database:payments`, `lucid`, `uploads`. Sync, deletion and the `--source` filter work per instance |
| **Record** | One thing a source lists: a file in a repository, a Confluence page, a table, a diagram, an uploaded file. A connector lists records as `(id, version, title, url)` and fetches one as Markdown |
| **Document id** | The record's id prefixed with its instance, such as `confluence:PAY:123456` or `uploads:incidents/2026-10-12 review.vtt`. Stable across machines, so golden questions can name it |
| **Version** | Whatever the source offers to say "this record changed": a git blob SHA, a Confluence version number, Lucid's `lastModified`, or a sha256 of the file. Same version as stored means nothing is fetched |
| **Complete listing** | The rule that `list()` must return every record that exists, because a record that is not listed is deleted. Guarded by "delete only after a successful listing" and the 20% rule |
| **20% guard** | If more than a fifth of a source's documents would be deleted in one sync, deletion is skipped and a message printed, unless `--rebuild` is given. Protects against a listing cut short by an error |
| **Document** | A record after conversion: title, URL, version and the full Markdown `body`, stored in the `documents` table |
| **Chunk** | A piece of a document, split at Markdown headings and capped at `size_chars` (default 2,000 characters). The unit that is indexed, embedded and returned by search |
| **Context header** | The document title and heading path ("Rollback runbook › Rolling back a bad deploy") stored and embedded with every chunk, so a chunk can be found by its subject even when its own text never names it |
| **Conversion** | Turning a fetched record into Markdown: MarkItDown for PDF, Word, PowerPoint, Excel and HTML; a few lines of our own for `.vtt`; nothing for `.md` and `.txt` |
| **FTS5** | SQLite's built-in full-text search. The `chunks` table is an FTS5 table, and its `bm25()` ranking is the keyword half of search |
| **BM25** | The standard keyword ranking function: more matching terms, rarer terms and shorter chunks score higher. In FTS5, a lower `rank` is a better match |
| **Embedding** | A vector of numbers (384 for the default model) that places a text so that texts with similar meaning are near each other. Computed once per chunk during sync and once per question during search, by the same function |
| **sqlite-vec** | The SQLite extension that stores embeddings in the `chunk_vec` table and finds the nearest ones. Version 0.1.9 searches by brute force, which is fast enough into the low hundreds of thousands of chunks |
| **Hybrid search** | Running the keyword and vector searches side by side and combining them, so a question finds both exact terms and paraphrases |
| **RRF** (reciprocal rank fusion) | How the two result lists are combined: each chunk scores `1 / (60 + rank)` in each list it appears in, and the sums are sorted. It needs no calibration between BM25 scores and vector distances |
| **`kb.toml`** | The committed configuration: name, model, chunking, and one section per source. Holds no secrets |
| **`.kb/`** | The gitignored folder beside `kb.toml`: `.env` (tokens), `kb.sqlite` (the index), `repos/` (clones), `schema/` (tbls output), `logs/kb.jsonl`, `sync.lock` |
| **`.kb/.env`** | Tokens and DSNs as `KEY=value` lines, mode 0600. A variable already set in the shell wins |
| **`meta`** | The table in `kb.sqlite` recording schema version, model, revision, dimensions and chunker version. A mismatch with the code or `kb.toml` triggers a rebuild or a re-embed |
| **Rebuild** | `kb sync --rebuild`: ignore stored versions, fetch everything again, lift the 20% guard. Different from a re-embed, which recomputes chunks and vectors from stored bodies without fetching |
| **Skill** | A `SKILL.md` file with a name, a description of when it applies, and instructions. Claude Code, Codex and Copilot read it from `.claude/skills/` or `.agents/skills/`. The `kb` skill tells the agent to run `kb search` and cite the hits |
| **Golden question** | A real question the team asks, paired with the document ids that answer it, in `eval/questions.toml` |
| **Recall@k** | The share of golden questions whose expected document appears in the top `k` results. The one quality number `kb eval` reports |
| **Spike** | The short investigation before building that settles the claims marked † in the design |
| **†** | Marks a claim in the design that was not verified against documentation or a running system on 2026-11-04 |

## 2. Key components

Each paragraph names the module in [plan.md](plan.md) §1 that holds it.

**Connectors** (`kb/sources/*.py`). One module per kind, each with `list()` and `fetch(id)`. They know their source's API and nothing else: no database, no chunking, no embedding. Git reads `git ls-tree` and blob SHAs; Confluence calls two REST endpoints; the database connector runs `tbls doc` and walks the output; Lucid calls two REST endpoints and flattens shapes and lines to text; uploads walks a folder and hashes files whose size or mtime changed. Adding a source is adding one such module.

**Converter** (`kb/convert.py`). Turns a fetched file into Markdown. MarkItDown's `convert_local()` handles PDF, Word, PowerPoint, Excel and HTML, including Confluence's rendered pages. A small function of our own strips WebVTT timings and keeps speaker names. Empty output, which is what a scanned PDF gives, is stored with a warning rather than retried.

**Chunker** (`kb/chunk.py`). Splits Markdown at headings, then at blank lines when a section exceeds `size_chars`, and attaches the title and heading path to each piece. It carries a version number so a change to the algorithm re-chunks every document from its stored body.

**Embedder** (`kb/embed.py`). One function that loads the configured model at the pinned revision and returns normalised vectors. Chunks are embedded as header plus body, questions as typed. It is the only place the model is loaded, so sync and search cannot drift apart.

**Store** (`kb/store.py`). Owns `.kb/kb.sqlite`: the DDL, the schema version, opening in WAL mode (read-only for search), replacing and deleting documents in one transaction across `documents`, `chunks`, `chunk_vec` and `chunk_doc`, the `meta` checks that trigger a rebuild or re-embed, and the one search statement. Nothing else writes SQL.

**Sync loop** (`kb/sync.py`). For each configured instance: list, skip unchanged, fetch and replace changed, delete unlisted after a complete listing, with the 20% guard. Then remove documents and local folders of instances no longer in `kb.toml`. Holds the `flock` so only one sync runs. A failing source is logged and the others continue.

**Search** (`kb/store.py`, `kb/cli.py`). Embeds the question, quotes and OR-joins its words for FTS5, runs the fused query with an optional kind or instance filter written into both legs, joins `documents` for title and URL, and prints at most 20 hits. `kb show` prints one document's body.

**CLI** (`kb/cli.py`). Six commands, `init`, `sync`, `search`, `show`, `eval`, `doctor`, with fixed exit codes: 0 ok, 1 usage, 2 a source failed, 3 incompatible index, 4 lock held. `kb-init` remains as an alias.

**`kb init`** (`kb/init.py`). The wizard: finds the repository, checks tools, asks for sources and tokens without echoing them, checks each token with one read-only call, downloads the model and pins its revision, and writes `kb.toml`, `.kb/.env`, both skill files, the `AGENTS.md` pointer, `@AGENTS.md` in `CLAUDE.md` and `.kb/` in `.gitignore`, each with an idempotent merge rule. Refuses to write a secrets file that git tracks.

**Skill** (`kb/templates/SKILL.md`, written to `.claude/skills/kb/` and `.agents/skills/kb/`). Tells the agent when to search, to read hits with `kb show`, to cite titles and URLs, to say so when nothing relevant comes back, and to treat indexed text as reference material rather than instructions. Its `allowed-tools` lets Claude Code run the two commands without prompting.

**Eval** (`kb/eval.py`, `eval/questions.toml`). Runs each golden question through search and reports recall@k, marking expected ids that no longer exist. Exits non-zero below a configurable floor. It is the check that runs after any change to the model, chunker or query.

**Doctor** (`kb/doctor.py`). Prints whether Python can load SQLite extensions, the sqlite-vec version, whether the model is cached, the index's schema version and counts per source, then re-runs the token checks. The first thing to run when something looks wrong.
