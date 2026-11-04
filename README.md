# knowledge-base

A local, no-server knowledge base for AI coding agents. It indexes a team's docs in git, Confluence pages, database schemas, Lucidchart diagrams and any files people drop into a shared folder (meeting transcripts, PDFs, Word documents) into one SQLite file. Agents such as Claude Code, Codex and Copilot search it with one command, `kb search`, which a committed skill tells them to run before answering questions about the team's systems.

Status: **design only**. Nothing is built yet. The design is written to be built from.

## The idea in five lines

1. `kb init`, run once in a repository, asks which sources to index and for read-only tokens, and writes the config, the secrets file and the skill.
2. `kb sync` lists every record in every source, fetches only what changed, converts it to Markdown, splits it by heading, embeds it, and writes one `.kb/kb.sqlite` file.
3. `kb search "<question>"` runs one SQL statement that fuses keyword (BM25) and vector results, and prints the hits with ids and links.
4. The `kb` skill makes the agent run that search, read the hits, and cite them.
5. `kb eval` scores a committed bank of real questions against the index, so changes are measured rather than assumed.

No language model runs in the pipeline. No Docker, no Postgres, no server, no CI job.

## Quick start (intended)

```sh
uv tool install --python 3.13 git+https://github.com/abhijitkushwaha1998/knowledge-base   # once per machine
cd ~/src/payments-api          # any git repository
kb init                        # asks which sources and tokens, checks each token, downloads the model, writes the skill
kb sync                        # the first sync reads everything; later runs process only changes
kb search "how do I roll back payments"
claude                         # the agent finds the kb skill and runs kb search itself
```

## What is in this repository

| Path | What it is |
|---|---|
| [`docs/decisions.md`](docs/decisions.md) | The choices that would be expensive to reverse, each with the alternative not taken, the reason, what breaks if it is wrong, and when to revisit it. Also what is deferred and the signal that brings it back |
| [`docs/design.md`](docs/design.md) | The design: scope, components, `kb init`, configuration, connectors and sync, data model, models, search and the skill, operations, security, the first spike, CLI reference |
| [`docs/architecture.md`](docs/architecture.md) | Four Mermaid diagrams: the system, one sync run, one question, what `kb init` writes |
| [`docs/plan.md`](docs/plan.md) | The implementation plan: package layout, build order with "done" per step, prerequisites by role, the first demo |
| [`docs/glossary.md`](docs/glossary.md) | Terms used in the documents, and one paragraph on each component |
| [`research/oss-landscape-2026-11.md`](research/oss-landscape-2026-11.md) | The research behind the choices: 85 open-source projects compared, the earlier (2026-11-03) stack in §12–15, and the simplification in §16 |
| `research/md2html.py` | Renders any of the Markdown files above into a self-contained `.html` beside it, Mermaid included |

## How to read it

1. [`docs/decisions.md`](docs/decisions.md) first: what was chosen and why, in a page.
2. [`docs/design.md`](docs/design.md) §1–3 for what the knowledge base is, then [`docs/architecture.md`](docs/architecture.md) for the pictures.
3. [`docs/design.md`](docs/design.md) §5–10 for how it is set up, fed and asked.
4. [`docs/plan.md`](docs/plan.md) to see what gets built in which order.
5. [`docs/glossary.md`](docs/glossary.md) whenever a term is unclear.
6. The research report when you want the evidence behind a choice, or to see what was considered and dropped.

## Principles, short form

- **Files are the API.** Config in `kb.toml`, the index in one SQLite file, the skill in Markdown. Nothing to keep running.
- **Fetch only what changed.** Every source exposes an id and a version; the sync loop compares them and deletes what is no longer listed.
- **Search, not synthesis.** The index returns the team's own text with links. The agent asking the question does the reasoning.
- **Measured.** A committed bank of golden questions is scored with `kb eval` after every change.
- **Secrets by name.** Committed files name environment variables; values live in a gitignored, mode-0600 file.
- **Read-only everywhere.** Tokens, database users and the CLI can only read.

## Licence

Apache-2.0. See [`LICENSE`](LICENSE). The design borrows ideas, with attribution in the documents, from [team-knowledge-kit](https://github.com/rsihare93/team-knowledge-kit) and from the open-source projects named in the research report; it copies no code from them.
