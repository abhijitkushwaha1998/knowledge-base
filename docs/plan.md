# Implementation plan

*2026-11-04. How the design in [design.md](design.md) gets built: the package layout, the build order with what "done" means at each step, who has to provide what, and what the first demo shows. The decisions it rests on are in [decisions.md](decisions.md).*

## 1. Package layout

One Python package, `kb`, installed as a tool with `uv tool install --python 3.13`. Every module is small; the connectors are the only place that knows a source's API.

```
pyproject.toml            # pins: markitdown[pdf,docx,pptx,xlsx]==0.1.9, sqlite-vec==0.1.9, sentence-transformers,
                          #       httpx, tomli-w; console_scripts kb = kb.cli:main, kb-init = kb.cli:init_alias
kb/
  cli.py                  # argparse: init, sync, search, show, eval, doctor; exit codes (design §11)
  config.py               # reads kb.toml and .kb/.env; expands ~; env overrides file; resolves source instances
  store.py                # opens .kb/kb.sqlite (WAL, busy_timeout, mode=ro for search); DDL; SCHEMA_VERSION;
                          #   meta checks; replace_document; delete_documents; the search SQL (design §8, §10.1)
  sync.py                 # sync_source / sync_all (design §7.2); the flock; the 20% guard; orphan cleanup
  chunk.py                # heading split, size_chars, context header; CHUNKER_VERSION (design §7.8)
  embed.py                # the one embed() for chunks and queries (design §9)
  convert.py              # MarkItDown convert_local; the VTT cleaner; empty-output warning (design §7.4)
  sources/
    __init__.py           # the Source protocol: key, kind, list(), fetch(id)
    git.py                # ls-tree, blob SHAs, partial clone, web URLs (design §7.3)
    confluence.py         # Cloud v2 and Data Center listing and export_view fetch (design §7.5)
    database.py           # tbls doc into .kb/schema/<name>, then a file walk (design §7.6)
    lucid.py              # documents/search and contents → text (design §7.7)
    uploads.py            # folder walk, stat-then-hash, relative ids (design §7.4)
  init.py                 # the wizard, credential checks, model download, file writes and merge rules (design §5)
  doctor.py               # runtime, model, index, token checks (design §11)
  eval.py                 # eval/questions.toml → recall@k (design §10.4)
  templates/
    SKILL.md              # the kb skill (design §10.2)
    AGENTS.md.snippet     # the pointer (design §10.3)
tests/
  fixtures/               # one small recorded listing + one record per source; a .vtt, .docx, .pdf; a tiny git repo
  test_store.py           # DDL, replace/delete, the search SQL on hand-made chunks, schema-version mismatch
  test_sync.py            # unchanged skipped, changed replaced, unlisted deleted, 20% guard, orphan cleanup
  test_chunk.py           # heading split, size limit, header
  test_sources_*.py       # list() and fetch() against the fixtures, ids stable
  test_init.py            # files written, merge rules, refuses tracked .kb/.env
```

Rules for the code:
- A connector never touches the database; it yields records and returns text.
- `store.py` is the only module that writes SQL.
- Every `KB_*` value is redacted before logging, in one place.
- No dependency is added for what a few lines of the standard library do.

## 2. Build order

Each step ends with something runnable and a check that fails if the step is broken. Steps 1–2 give an end-to-end system on the uploads folder alone; the other sources are added one at a time.

| Step | Build | Done when |
|---|---|---|
| 0. Spike | The nine items in design §13, in a throwaway script | Cold `kb search` time and recall@10 are recorded for both models; sqlite-vec loads under uv's Python on macOS and Linux; the `allowed-tools` syntax is confirmed; Confluence `export_view` through MarkItDown keeps code blocks and links, or a workaround is chosen |
| 1. Store and search | `store.py`, `embed.py`, `search` and `show` in `cli.py` | `kb search` returns fused results over hand-inserted chunks; `test_store.py` covers replace, delete, RRF order and the schema-version exit |
| 2. Uploads, end to end | `uploads.py`, `convert.py`, `chunk.py`, `sync.py`, `sync` in `cli.py` | Dropping a `.vtt`, a `.docx` and a `.pdf` into a folder and running `kb sync` makes them searchable; editing one re-indexes only it; deleting one removes it; a cut-short walk does not delete (the guard); the lock refuses a second sync |
| 3. Git | `git.py` | `url = "."` indexes this repository's Markdown with stable ids; a second `[[git]]` entry clones and indexes a GitHub repository; a changed file is re-indexed by blob SHA |
| 4. Confluence | `confluence.py` | A space is listed with versions and only changed pages are fetched, on Cloud; Data Center is covered by a fixture until a server is available |
| 5. Database | `database.py` | A Postgres database with a schema-only user yields one document per table; a dropped table disappears on the next sync |
| 6. Lucid | `lucid.py` | A diagram's shapes and connections are searchable; pagination of the search endpoint is confirmed |
| 7. Init, skill, doctor | `init.py`, `doctor.py`, templates | Running `kb init` in a fresh clone of a repository with a committed `kb.toml` asks only for tokens, downloads the model, writes both `SKILL.md` files, appends to `AGENTS.md`, `CLAUDE.md` and `.gitignore` idempotently, and refuses a tracked `.kb/.env`; Claude Code runs `kb search` without a prompt |
| 8. Eval | `eval.py`, the first `eval/questions.toml` | About 20 real questions across the five sources; `kb eval` prints recall@10 and marks missing ids; the number is recorded in the README's status line |

Order of work after step 2 can follow whichever source the team has credentials for first. Step 7 is last because the wizard is the part most shaped by what the earlier steps turned out to need.

## 3. Prerequisites by role

| Who | Provides | Needed from step |
|---|---|---|
| Anyone on the team | A laptop with `git`, `uv`, Python 3.13 via uv, and about 3 GB free (torch, the model, the index) | 1 |
| The uploads folder owner | One shared folder (OneDrive, Dropbox or a plain directory) that every teammate has synced, and the first few transcripts and documents in it | 2 |
| A Confluence admin or any user with an API token | A read-only API token for a user who can see the chosen spaces, and the space keys | 4 |
| A database owner | A schema-only user per database (`CONNECT` plus `REFERENCES`, never `SELECT`) and its DSN; `tbls` installed on the laptops that sync it | 5 |
| A Lucidchart user who can see the team's diagrams | A personal API key with the `DocumentReadonly` grant | 6 |
| A GitHub or GitLab user | A fine-grained read-only token, only if repositories other than the current one are indexed | 3 |
| The team | About 20 real questions with the document that answers each, in `eval/questions.toml` | 8 |

## 4. The first demo

After step 3, in a repository the team already works in:

1. `kb init` with two sources: this repository and the uploads folder.
2. Drop three files into the folder: last week's meeting transcript, the architecture deck, a runbook exported from Confluence as a Word file.
3. `kb sync`. It prints listed, changed and deleted counts per source.
4. Open Claude Code in the repository and ask a question the transcript answers. The agent runs `kb search`, reads the hit with `kb show`, and cites the transcript by title.
5. Edit the transcript, `kb sync` again: only that file is re-indexed.
6. `kb eval` with five questions written for the demo.

What the demo deliberately does not show: Confluence, databases and Lucid (steps 4–6), and anything about the agent's reasoning quality, which is the agent's, not the knowledge base's.

## 5. Risks to watch while building

| Risk | Where it shows | Mitigation already in the design |
|---|---|---|
| `kb search` is too slow for an agent loop | Step 0 timing | Small default model; measure before choosing |
| Confluence macros lost in conversion | Step 0, step 4 | `export_view` instead of `storage`; fall back to pre-processing `<ac:structured-macro>` if needed |
| A partial listing deletes a source | Step 2 tests | Delete only after a complete listing; the 20% guard |
| OneDrive downloads every file on every sync | Step 2 on a real OneDrive folder | Stat before hash |
| Two teammates' indexes disagree | Step 8 | Ids are relative and derived from the remote URL; the eval bank uses those ids |
| sqlite-vec fails to load | Step 0 | `kb doctor` names the fix; install via uv's Python |
