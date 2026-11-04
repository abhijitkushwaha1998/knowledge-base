# Knowledge base: design and configuration

> **Full design of 2026-11-03, kept for reference.** For v1 it is superseded by the simplified design in [../design.md](../design.md). What was removed and why is in [../decisions.md](../decisions.md) and [../design.md](../design.md) §2. Use this document when a deferred item comes back.

*2026-11-03. Status: design, nothing built yet. This document says how the knowledge base chosen in the [research report](../../research/oss-landscape-2026-11.md) (§12–15; [web version](https://claude.ai/artifact/AigmzbmqpLNtvbRZ1isZPX)) is configured, run locally, fed by its connectors, and queried. The diagrams are in [architecture.md](architecture.md). Library facts were checked against source and docs on 2026-11-03; † marks a claim not verified.*

## 1. Purpose and scope

The knowledge base gives any AI agent one read-only place to ask about the organisation. It covers code, documents, chat, meeting transcripts, database schemas and diagrams. It also links the things those sources talk about (services, repositories, teams, tables, runbooks) to each other. Then a question about one service can reach its code, its runbook and its on-call channel together.

**One command per repository.** `kb-init`, run inside any git repository, turns that repository into a knowledge-base project:
- It writes the source configuration into `kb.toml`.
- It writes the tokens into a local secrets file.
- It writes `.mcp.json`, so that Claude Code or another agent working in the repository can query the knowledge base.

`kb up` starts a local Postgres, and `kb sync` fills it.

**Not in scope:**
- Per-document permissions. Any caller the gateway admits can read everything indexed, so connect only sources the whole organisation may read (report §12).
- Jira.
- Write tools of any kind.
- Row data from operational databases. Only schemas are indexed.
- Incidents. No incident source exists yet (§6.11).

## 2. Architecture at a glance

See [architecture.md](architecture.md) §1 for the system diagram. Components and the versions to pin:

| Layer | Component | Pin | Reused or built |
|---|---|---|---|
| Runtime | Python | 3.11–3.13 (unstructured-ingest requires `<3.14`) | — |
| Sync engine | [CocoIndex](https://github.com/cocoindex-io/cocoindex) v1, Apache-2.0 | 1.1.0 | Reused |
| SaaS connectors | [unstructured-ingest](https://github.com/Unstructured-IO/unstructured-ingest), Apache-2.0 | 1.12.0 | Reused (indexer and downloader stages only) |
| Teams and transcripts | Onyx connectors, MIT core | fork of `backend/onyx/connectors/{teams,zoom,gong,fireflies}` | Forked |
| Code graph | [codebase-memory-mcp](https://github.com/DeusData/codebase-memory-mcp), MIT | v0.12.1 binary | Reused |
| Database schemas | [tbls](https://github.com/k1LoW/tbls), MIT | v1.96.1 binary | Reused |
| Attachment parsing | [Docling](https://github.com/docling-project/docling), MIT | lockfile | Reused |
| HTML to Markdown | [markdownify](https://github.com/matthewwithanm/python-markdownify), MIT | lockfile | Reused |
| Embedding model | [BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3), MIT | model revision hash | Reused |
| Store | Postgres 17 + [pgvector](https://github.com/pgvector/pgvector) | `pgvector/pgvector:pg17`, pinned by digest | Reused |
| Diagram parser | Draw.io XML and the Lucid REST API | — | Built |
| Entity resolution | rules, plus aliases from `kb.toml` | — | Built |
| Gateway | MCP server and REST API on the [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk), MIT | lockfile | Built |
| CLI | `kb` and `kb-init` | — | Built |

Everything built is glue: the CLI, one small module per connector, the diagram parser, entity resolution, the code-graph export, the search SQL, and the gateway. None of it holds security logic beyond token handling and the gateway's read-only, capped tools.

## 3. Quick start (local)

*Describes the intended experience. The `kb` CLI is not built yet.*

Prerequisites:
- Docker (Docker Desktop, OrbStack or colima).
- `git`.
- [uv](https://docs.astral.sh/uv/).
- `tbls`: `brew install k1LoW/tap/tbls`, or use the image `ghcr.io/k1low/tbls`.
- `codebase-memory-mcp`: the v0.12.1 release binary.

`kb-init` checks that each of these is installed and prints the install command for any that is missing.

```sh
uv tool install git+https://github.com/abhijitkushwaha1998/knowledge-base   # once per machine
cd ~/src/payments-api          # any git repository
kb-init                        # asks which sources, asks for tokens, checks each one
kb up                          # starts Postgres 17 + pgvector in Docker
kb sync                        # first full sync; later runs process only changes
claude                         # Claude Code picks up .mcp.json and can call the kb tools
```

`kb sync --live` keeps syncing on the interval set in `kb.toml`.

## 4. `kb-init`

### 4.1 What it does, in order

1. **Find the project.** Use `git rev-parse --show-toplevel` from the current directory and refuse to run outside a git repository. The project name defaults to the directory name.
2. **Check the tools.** Look for `docker`, `git`, `tbls` and `codebase-memory-mcp` on `PATH`. A missing tool is a warning with its install command, not an error, because a project that indexes no databases does not need `tbls`.
3. **Detect this repository.** Read `git remote get-url origin`. A `gitlab.*` or self-managed GitLab host and a `github.com` or GitHub Enterprise host are recognised from the URL and API probe. Pre-select this repository as the first source.
4. **Choose sources.** Show a numbered multi-select list:
   - this repository
   - more repositories or GitLab groups
   - Confluence
   - SharePoint
   - Google Drive
   - Slack
   - Teams
   - meeting transcripts (Zoom, Gong or Fireflies)
   - databases
   - Lucidchart

   Draw.io needs no choice: `.drawio` files are read from the git and Drive sources.
5. **Ask for each source's settings.** Non-secret settings are URLs, space keys, channel names and site URLs, and they go to `kb.toml`. Secrets are read with `getpass`, so they are never echoed, and go to `.kb/.env`. A value already present in the shell environment or in an existing `.kb/.env` is offered as the default, shown as "found" and never printed.
6. **Check every credential** with one read-only call (§4.3):
   - On success, print who the token is for and which scopes it has, for example "GitLab: ok, user `asha`, scopes `read_api, read_repository`, expires 2027-10-01". Missing scopes are listed by name.
   - If the token is rejected, ask again, up to three times.
   - If the service cannot be reached, offer to save the value anyway, marked unchecked.
7. **Generate the local store settings:**
   - a random 32-byte Postgres password;
   - a free localhost port, which is why `KB_POSTGRES_PORT` is not fixed;
   - `KB_DATABASE_URL` built from both.
8. **Write the files** (§4.2), then print the next step: `kb up && kb sync`.

### 4.2 Files it writes

| Path | Contents | Committed? |
|---|---|---|
| `kb.toml` | Sources and settings, no secrets (§5.1) | Yes. Teammates share it. |
| `.mcp.json` | `{"mcpServers": {"kb": {"command": "kb", "args": ["mcp"]}}}`, merged into an existing file, never overwritten | Yes. It holds no secret. |
| `.kb/.env` | Tokens, keys and the local Postgres password (§5.2), mode `0600` | No. `.kb/` is gitignored. |
| `.gitignore` | Adds `.kb/` if it is not already ignored | Yes |
| `.kb/` | Local state, filled later by `kb sync` (§11) | No |

Secrets go in `.kb/.env` rather than a root `.env` because many repositories already use `.env` for their own application. Mixing the two would load knowledge-base tokens into the app's environment, and an existing `.env` may already be committed. One ignored folder also keeps every knowledge-base file in one place.

Safety rules:
- Refuse to write `.kb/.env` if `git ls-files --error-unmatch .kb/.env` shows it is tracked. After writing `.gitignore`, confirm with `git check-ignore .kb/.env`.
- Write every file to a temporary file and rename it into place. Create `.kb/.env` with mode `0600`.
- Never print a secret, and never put one in `kb.toml` or `.mcp.json`. `kb mcp` reads `.kb/.env` itself, so the agent's configuration needs no token.

### 4.3 Credentials per connector

All scopes are read-only. Each check is one cheap request.

| Source | `.kb/.env` variables | How to create it, and the minimal scopes | Check |
|---|---|---|---|
| GitHub | `KB_GITHUB_TOKEN` | A fine-grained PAT with Repository → Contents: read and Metadata: read. One token covers one owner (user or organisation). A classic PAT needs `repo`, which also grants write, so prefer fine-grained | `GET https://api.github.com/user`, then `GET /repos/{owner}/{repo}` for each repository. A 404 means the repository is not in the token's selection |
| GitLab | `KB_GITLAB_TOKEN` | A PAT with `read_api` and `read_repository` | `GET {base}/api/v4/personal_access_tokens/self` with header `PRIVATE-TOKEN`. The response includes `scopes`, `active` and `expires_at` |
| Confluence Cloud | `KB_CONFLUENCE_EMAIL`, `KB_CONFLUENCE_TOKEN` | An API token from id.atlassian.com. A scoped token needs `read:space:confluence` and `read:page:confluence` | Unscoped token: `GET {site}/wiki/api/v2/spaces?limit=1` with basic auth. A scoped token must call `https://api.atlassian.com/ex/confluence/{cloudId}/…`, and `cloudId` comes from `{site}/_edge/tenant_info`† |
| Confluence Data Center | `KB_CONFLUENCE_TOKEN` | A PAT (Confluence 7.9+), sent as `Authorization: Bearer` | `GET {base}/rest/api/user/current` |
| Slack | `KB_SLACK_BOT_TOKEN` | A bot token (`xoxb-…`) from an app built for your own workspace, with `channels:history`, `channels:read` and `users:read`. Invite the bot to each channel it should read | `POST https://slack.com/api/auth.test`. Check `"ok": true`, because Slack returns HTTP 200 even on failure. Granted scopes come from the `x-oauth-scopes` header† |
| SharePoint and Teams | `KB_MS_TENANT_ID`, `KB_MS_CLIENT_ID`, `KB_MS_CLIENT_SECRET` | One Entra ID app registration serves both. Application permissions: `Sites.Read.All` (or `Sites.Selected` plus a per-site grant), `Team.ReadBasic.All`, `Channel.ReadBasic.All` and `ChannelMessage.Read.All`. Every one needs admin consent | `POST https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token` (client credentials, `scope=https://graph.microsoft.com/.default`), then `GET /v1.0/sites/root` and `GET /v1.0/teams?$top=1` |
| Google Drive | `KB_GDRIVE_SA_KEY_FILE` (a file path) | A service account key in JSON with the `drive.readonly` scope. Share each folder, or add the account to each shared drive, using its `client_email`. Domain-wide delegation is not needed | Exchange a signed JWT at `https://oauth2.googleapis.com/token`, then `GET /drive/v3/about?fields=user`. The returned email must equal the service account |
| Zoom | `KB_ZOOM_ACCOUNT_ID`, `KB_ZOOM_CLIENT_ID`, `KB_ZOOM_CLIENT_SECRET` | A Server-to-Server OAuth app with `cloud_recording:read:list_account_recordings:admin`, `cloud_recording:read:list_recording_files:admin` and `cloud_recording:read:meeting_transcript:admin`. Cloud recording needs a Pro plan or higher | `POST https://zoom.us/oauth/token` with `grant_type=account_credentials`. Compare the returned `scope` string with the list |
| Gong | `KB_GONG_ACCESS_KEY`, `KB_GONG_ACCESS_SECRET` | A key and secret created by a Gong technical admin. The secret is shown only once | `GET https://api.gong.io/v2/users` with basic auth† |
| Fireflies | `KB_FIREFLIES_API_KEY` | An API key, which has no scopes | `POST https://api.fireflies.ai/graphql` with `{ user { email } }`. Check that the response has no `errors` array |
| Lucidchart | `KB_LUCID_API_KEY` | A personal API key with the `DocumentReadonly` and `User` grants | `GET https://api.lucid.co/v1/users/me/profile` with `Authorization: Bearer` |
| Postgres or MySQL | `KB_DB_<NAME>_DSN`, one per database | A schema-only user. Postgres: `GRANT CONNECT`, plus `REFERENCES` on the schemas so `information_schema` shows them. MySQL: `REFERENCES, SHOW VIEW` on the database†. Never grant `SELECT` or `pg_read_all_data` | `SELECT 1`, then `tbls out -t json` into a temporary file |
| Local store | `KB_DATABASE_URL`, `KB_POSTGRES_PASSWORD`, `KB_POSTGRES_PORT` | Generated by `kb-init` | `kb up` waits for Postgres's health check |

Gotchas worth printing in the wizard:
- **GitHub:**
  - A fine-grained token can wait for organisation approval, and until then it reads only public resources.
  - Fine-grained tokens expire after 30 days by default, so set a longer expiry.
  - An organisation can block classic tokens; the response is a 403.
- **Slack:** since 2025-05-29, apps distributed outside the Slack Marketplace are limited to 1 request per minute on `conversations.history` and `conversations.replies`. Apps a company builds for its own workspace keep the normal limits. So create an internal app; do not install a third-party one.
- **Teams:** reading channel messages app-only no longer needs Microsoft's protected-API request form. It has not been billed since 2025-08-25. It still needs admin consent.
- **Gong:** allows 3 calls per second and 10,000 per day. A first backfill of a large account can take more than one day.
- **Tokens expire.** `kb-init --check` reports each token's expiry date where the service exposes one (GitLab, Confluence Cloud). Running it from cron gives early warning.

### 4.4 Re-running

`kb-init` is idempotent:
- Running it again keeps every existing value and asks only for what is missing, for example a source newly added to `kb.toml` by hand or by a teammate.
- `kb-init --reconfigure slack` asks again for one source.
- `kb-init --check` re-checks every credential without prompting, and exits non-zero if any check fails.

A teammate who clones a repository with a committed `kb.toml` runs `kb-init` once, and is asked only for their own tokens.

## 5. Configuration reference

### 5.1 `kb.toml`

```toml
# kb.toml: what this knowledge base indexes. Safe to commit, holds no secrets (they are in .kb/.env).
name = "payments-kb"

[embedding]
model = "BAAI/bge-m3"          # changing it re-embeds every chunk (§9)
dim = 1024

[chunking]
size_bytes = 2000              # CocoIndex RecursiveSplitter sizes are in bytes; roughly 400-500 English tokens
overlap_bytes = 300

[sync]
interval = "30m"               # used by kb sync --live

[[git]]
url = "https://gitlab.com/acme/payments-api"    # added by kb-init from `git remote`
[[git]]
group = "https://gitlab.com/acme/platform"       # every project in the group, subgroups included
[[git]]
url = "https://github.com/acme/ledger"

[confluence]
url = "https://acme.atlassian.net"
deployment = "cloud"           # cloud | datacenter
spaces = ["PAY", "OPS"]

[sharepoint]
sites = ["https://acme.sharepoint.com/sites/Engineering"]

[gdrive]
folders = ["1AbCdEfGhIjK"]     # folder or shared-drive IDs shared with the service account

[slack]
channels = ["payments-oncall", "eng-announce"]
full_refresh = "30d"           # re-read closed months to catch old edits (§6.5)

[teams]
teams = ["Payments"]           # display names; every channel in each team

[transcripts]
provider = "zoom"              # zoom | gong | fireflies
since = "2026-01-01"

[[database]]
name = "payments"              # DSN in .kb/.env as KB_DB_PAYMENTS_DSN
engine = "postgres"            # postgres | mysql
schemas = ["public"]

[lucid]
folders = []                   # empty: every Lucidchart document the key can read

[aliases]                      # hand-written entity resolution, applied before the rules (§7.3)
"service:payments" = ["money service", "pay-svc", "Payments API"]
```

Only the sections that are present are synced. Git sources choose GitLab or GitHub by host, and the token by provider.

### 5.2 `.kb/.env`

| Variable | Used by | Required when |
|---|---|---|
| `KB_DATABASE_URL` | `kb sync`, `kb mcp`, `kb serve` | Always (generated) |
| `KB_POSTGRES_PASSWORD`, `KB_POSTGRES_PORT` | `kb up` (Docker Compose) | Always (generated) |
| `KB_GITHUB_TOKEN` | git sources on GitHub | Any `[[git]]` source on GitHub |
| `KB_GITLAB_TOKEN` | git sources on GitLab | Any `[[git]]` source on GitLab |
| `KB_CONFLUENCE_EMAIL` | Confluence Cloud | `deployment = "cloud"` |
| `KB_CONFLUENCE_TOKEN` | Confluence | `[confluence]` |
| `KB_SLACK_BOT_TOKEN` | Slack | `[slack]` |
| `KB_MS_TENANT_ID`, `KB_MS_CLIENT_ID`, `KB_MS_CLIENT_SECRET` | SharePoint and Teams | `[sharepoint]` or `[teams]` |
| `KB_GDRIVE_SA_KEY_FILE` | Google Drive | `[gdrive]` |
| `KB_ZOOM_ACCOUNT_ID`, `KB_ZOOM_CLIENT_ID`, `KB_ZOOM_CLIENT_SECRET` | Zoom transcripts | `provider = "zoom"` |
| `KB_GONG_ACCESS_KEY`, `KB_GONG_ACCESS_SECRET` | Gong transcripts | `provider = "gong"` |
| `KB_FIREFLIES_API_KEY` | Fireflies transcripts | `provider = "fireflies"` |
| `KB_LUCID_API_KEY` | Lucidchart | `[lucid]` |
| `KB_DB_<NAME>_DSN` | tbls | Each `[[database]]`. `<NAME>` is the upper-cased `name` |

The file uses plain `KEY=value` lines, written by `kb-init`. Docker Compose reads it with `--env-file`. A variable already set in the shell overrides the file, which is how CI and servers supply secrets without one.

## 6. How connectors work

### 6.1 One contract

Every connector does the same four things:

1. **List.** Return an identifier and a version for every record that currently exists. Listing returns metadata only and never content.
2. **Fetch.** Download one record to a local file.
3. **Convert.** Turn the file into Markdown or plain text, with a title and a URL.
4. **Emit entity references.** Name the things the record is or mentions, as keys like `repo:gitlab.com/acme/payments-api` or `channel:slack/payments-oncall` (§7.3).

CocoIndex v1 supplies the incremental part. In v1 a source is plain Python: our code lists the records and mounts one processing component per record with `coco.mount_each`. The component's memo key is `(identifier, version)`.
- If the key is unchanged, the component is skipped and nothing is fetched.
- If a record is no longer listed, its component is not mounted, and CocoIndex deletes every row it produced, including chunks, embeddings and edges.

We write no delete logic. The cost is one rule that every connector must follow: **the list must be complete.** A connector that lists only recent records would make CocoIndex delete the older ones. §6.5 shows how Slack meets the rule.

Each source runs as its own CocoIndex app, so that `kb sync --source slack` cannot unmount, and so delete, another source's records.

### 6.2 unstructured-ingest as a library

For Confluence, SharePoint, Google Drive and Slack we call only unstructured-ingest's indexer and downloader stages. We do not use its pipeline, partitioner or destinations. Each stage is a plain dataclass built from a connection config and an index or download config.

- `ConfluenceIndexer.run()` (`SharepointIndexer.run_async()`, `SlackIndexer.run()`) yields `FileData` records. Each record has an `identifier`, `metadata.version`, `metadata.date_modified` and `metadata.url`.
- `ConfluenceDownloader.run(file_data)` (`SlackDownloader.run_async`) returns `{file_data, path}`, the path of a local file. Confluence may return a list when it also downloads attachments.

The glue for one source is roughly:

```python
@coco.fn(memo=True)                                   # skipped when (identifier, version) is unchanged
async def process(rec: Rec, t: Targets):
    path = (await downloader.run_async(file_data=rec.fd))["path"]
    doc = convert(path, rec.fd)                       # §7.1
    t.write(doc, chunk_and_embed(doc), entity_refs(doc))

@coco.fn
async def confluence_app(t: Targets):
    recs = (Rec(fd) for fd in ConfluenceIndexer(connection_config=conn, index_config=idx).run())
    await coco.mount_each(process, ((r.fd.identifier, r) for r in recs), t)
# Rec.__coco_memo_key__ returns (fd.identifier, fd.metadata.version)
```

*Sketch only. Exact signatures are confirmed in the first spike (§13).*

### 6.3 Per-source behaviour

| Source | Library | What is listed | Change detected by | Deletion detected by | Entities emitted |
|---|---|---|---|---|---|
| Git repositories | `git` + CocoIndex `localfs.walk_dir` + codebase-memory-mcp | Repositories in `[[git]]`, groups expanded through the API. Then, inside each clone, `*.md`, `*.mdx`, `*.drawio` and `docs/**` | `git fetch` and HEAD SHA per repository; file content per file | A file gone from the tree; a repository gone from config or group | `repo`; `doc` and `runbook` for Markdown; `service`, `route` and `calls` edges from the code graph (§6.4) |
| Confluence | unstructured-ingest | Every page in the configured spaces, each run | Page version number | Not listed any more | `doc` and `runbook` (pages labelled `runbook`†), `mentions` edges to repository URLs and known aliases |
| SharePoint | unstructured-ingest | Files in the configured sites | Record version | Not listed any more | `doc` |
| Google Drive | unstructured-ingest (or CocoIndex's own `google_drive` source) | Files in the shared folders | Modified time and version | Not listed any more | `doc`; `.drawio` files go to the diagram parser |
| Slack | unstructured-ingest | One component per channel-month (§6.5) | Message timestamps within the month | A month that disappears from the listing; `full_refresh` re-reads closed months | `channel`, `person`, `mentions` |
| Teams | Onyx fork | Threads in every channel of the configured teams | Last-modified time per thread | Not listed any more | `channel`, `person`, `mentions` |
| Meeting transcripts | Onyx fork (Zoom, Gong or Fireflies) | Meetings since `since` | Transcripts are immutable; the meeting ID is enough | Not listed any more, for example after the retention period | `meeting` (a `doc`), `person` for participants |
| Postgres / MySQL | tbls | Each `[[database]]` | Hash of the tbls JSON | Table missing from the JSON | `table`, foreign-key edges, and one schema chunk per table |
| Draw.io | diagram parser | `.drawio` (and `.drawio.svg`/`.png` with embedded XML) from git and Drive | Content hash | File gone | `diagram`, one text chunk of its labels and connections, and `mentions` edges for labels that match aliases |
| Lucidchart | Lucid REST API | `POST /v1/documents/search`, filtered to `[lucid].folders` | Document's last-modified time† | Not listed any more | Same as Draw.io, from `GET /v1/documents/{id}/contents` |

### 6.4 Code

For each repository:
- `kb sync` makes a shallow clone with the token into `.kb/repos/<host>/<path>`. Later runs fetch, and if HEAD has not moved, the repository's components are skipped.
- **Code graph.** Run `codebase-memory-mcp cli --quiet index_repository --repo-path <abs path>` with `CBM_CACHE_DIR=.kb/cbm`, so the index belongs to this project. Then read `nodes` and `edges` from `.kb/cbm/<project>.db` with Python's `sqlite3`. Export a minimal set:
  - services and routes (`nodes.label = 'Route'`);
  - `CALLS`, `HTTP_CALLS` and `ASYNC_CALLS` edges;
  - the Kubernetes and Terraform names that tie a service to its repository.

  The SQLite schema belongs to codebase-memory-mcp, which is pre-1.0, so the exporter is pinned to v0.12.1 and checked by a fixture test.
- **Docs in git.** Markdown, runbooks and ADRs in the repository are read straight from the clone by CocoIndex's `localfs.walk_dir`, and go through the same convert, chunk and embed path as Confluence pages. Their URL is the file's web URL at the indexed commit.
- **Code is not embedded in Postgres.** Agents that need code search use codebase-memory-mcp's own MCP tools in the repository, alongside `kb`.

### 6.5 Slack and the complete-list rule

Re-listing a large channel's whole history every 30 minutes would be slow and hit rate limits. Listing only recent history would delete everything older. So each channel is split into **one component per calendar month**:
- The current and previous months are re-listed on each run. The indexer is given that month's `start_date` and `end_date`.
- Closed months are mounted again with an unchanged memo key, `(channel, month, "closed")`. They cost no API calls, and their rows stay.
- `full_refresh = "30d"` re-reads every closed month once a month, to catch edits and deletions of old messages.

Messages are grouped into one document per thread. A thread longer than the chunk size is split.

*To prove in the first spike:*
- Edits within open months are caught.
- A deleted message disappears after a full refresh.
- Closed months make no API calls.

### 6.6 Teams and meeting transcripts

These connectors come from Onyx's MIT core. The fork takes `backend/onyx/connectors/teams/` and the Zoom, Gong and Fireflies connectors.

The Teams connector reads `teams_client_id`, `teams_directory_id` and `teams_client_secret`, filled from `KB_MS_*`. It imports `Office365-REST-Python-Client`, `msal`, `requests` and `pydantic`. Its permission-sync code lives in Onyx's `ee/` folder, and the fork neither needs nor copies it.

The fork replaces Onyx's `Document` output with our `(identifier, version, fetch)` contract. Transcripts arrive as text with speaker names, so no audio pipeline is needed.

### 6.7 Databases

```sh
TBLS_DSN="$KB_DB_PAYMENTS_DSN" tbls out -t json -o .kb/schema/payments.json
```

Each table becomes a `table` entity, keyed `table:payments.public.transactions`, and each foreign key becomes an edge. One chunk per table lists its columns, types, keys and comments, so that "which table holds refunds?" is answerable by search.

Linking tables to the services that use them comes from ORM model names found in code. That is a rule for later (§7.3).

### 6.8 Diagrams

- **Draw.io** files are mxGraph XML, sometimes deflate-compressed and base64-encoded inside `<diagram>`. Both forms are decoded with the standard library.
  - Cells with `vertex="1"` are shapes, and their `value` is the label.
  - Cells with `edge="1"` connect a `source` to a `target`.
  - The parser writes a `diagram` entity, one text chunk ("Payments API → Ledger: POST /entries", one line per connection), and `mentions` edges where a label matches a known alias.
- **Lucidchart** uses the same output, built from the shapes and lines in the `contents` response.

### 6.9 Adding a connector later

Write one module with:
- `list()`, which yields `(identifier, version, record)`;
- `fetch(record)`, which returns a path;
- optionally, extra entity rules.

Then add its section to `kb.toml` and its variables to the `kb-init` table. Nothing else changes.

### 6.10 Rate limits and backfill

Connectors back off on 429 responses using `Retry-After`. A first sync is dominated by fetching and parsing:
- **Attachments:** Docling's CPU benchmark is 3.1 s per page. 5,000 attachment pages take about 4.3 CPU-hours (report §14 finding 9).
- **Embedding:** throughput is measured in the spike. HTML and chat text skip Docling entirely.

### 6.11 Incidents

No open-source incident connector was found (report §10 gap 6). Runbooks are covered by Confluence and git. An incident source (PagerDuty, Opsgenie or Grafana) is a later module under §6.9.

## 7. Data processing pipeline

### 7.1 Stages

For each new or changed record:

1. **Convert.**
   - Confluence and SharePoint pages, and other HTML, go through markdownify to Markdown.
   - PDF, DOCX, PPTX and XLSX attachments go through Docling, which keeps page numbers for citations.
   - Slack and Teams threads become text with one `name: message` line per message.
   - Transcripts become speaker turns.
   - Each document keeps its title, URL, source, author and modified time.
2. **Chunk.** CocoIndex `RecursiveSplitter().split(text, chunk_size=2000, chunk_overlap=300, language="markdown")`. Sizes are in bytes and come from `kb.toml`. The splitter is tree-sitter based, so it splits on headings and paragraphs before sentences.
3. **Embed** each chunk with the configured model (§9), in process, through CocoIndex's `SentenceTransformerEmbedder`.
4. **Extract entity references** with rules: repository URLs, `#channel` names, the record's own identity (a page is a `doc`), and the aliases in `kb.toml`. These become edges from the record's `doc:` key.
5. **Write** the document, its chunks, its embeddings and its edges as declared rows of the record's component.

Once every source has run:

6. **Resolve entities** (§7.3), as one transaction that rebuilds the `entities` table.

### 7.2 Where state lives

| State | Where | Notes |
|---|---|---|
| Documents, chunks, embeddings, edges, entities | Postgres, in a Docker volume | The data agents query |
| CocoIndex's memo keys and target tracking | `.kb/cocoindex.db`, a local LMDB file (`COCOINDEX_DB`) | v1 no longer keeps this in Postgres. Only one process may open it, so `kb sync` takes a lock and `--live` runs as one process |
| Clones, code indexes, schema JSON | `.kb/repos`, `.kb/cbm`, `.kb/schema` | Rebuildable |

Postgres and `.kb/cocoindex.db` must be reset together. If CocoIndex's file says a record is written but the database was wiped, CocoIndex skips the record and it never comes back. `kb down -v` therefore deletes both.

CocoIndex is given our own asyncpg pool, built from `KB_DATABASE_URL`, rather than reading an environment variable of its own.

### 7.3 Entity resolution

Connectors emit raw entity keys, normalised to lower case with `.git`, scheme and trailing slashes stripped:
- `repo:gitlab.com/acme/payments-api`
- `service:payments`
- `channel:slack/payments-oncall`
- `table:payments.public.transactions`
- `person:asha@acme.com`
- `doc:confluence:123456`

Edges connect those keys. Entity resolution groups keys that name the same thing into one `entities` row whose `aliases` hold every key. Rules apply in this order:

1. **Hand-written aliases** from `kb.toml [aliases]`. They always win, and they are how a wrong merge is fixed.
2. **Code facts.** A Kubernetes deployment or Terraform resource named `payments` inside `payments-api` makes `service:payments` the service implemented in that repository (from codebase-memory-mcp).
3. **Links.** A page that links to a repository URL mentions that repository. A diagram label equal to an alias mentions that entity.
4. **Conventions.** `#<service>-oncall`, `-alerts` and `-dev` channels are where that service is discussed.
5. **Later:** ORM model names to tables, `CODEOWNERS` to teams, and LLM-assisted matching for names no rule catches ("the money service").

The table is rebuilt from scratch each sync, inside one transaction, so the output is deterministic. A rule change takes effect on the next run.

**Measure precision.** After the first sync, review 50 random merges by hand. A wrong merge sends a question about one service to another service's runbook.

## 8. Data model

CocoIndex creates and owns the four tables it writes. Entity resolution owns `entities`. The DDL below shows the intended shape, and the exact form comes from CocoIndex's `TableSchema`. Keys are text so that rows are stable across runs and joins need no ID lookups.

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE documents (                 -- one row per source record (CocoIndex)
  id          text PRIMARY KEY,          -- 'confluence:123456', 'git:gitlab.com/acme/payments-api:docs/runbook.md'
  source      text NOT NULL,             -- confluence | sharepoint | gdrive | slack | teams | transcripts | git | database | diagram
  url         text NOT NULL,
  title       text,
  author      text,
  version     text,                      -- the source's version or timestamp
  modified_at timestamptz
);

CREATE TABLE chunks (                    -- CocoIndex
  id          text PRIMARY KEY,          -- '<document id>#<ordinal>'
  document_id text NOT NULL,
  ord         int  NOT NULL,
  text        text NOT NULL,
  tsv         tsvector GENERATED ALWAYS AS (to_tsvector('english', text)) STORED
);
CREATE INDEX chunks_tsv ON chunks USING gin (tsv);
CREATE INDEX chunks_doc ON chunks (document_id);

CREATE TABLE embeddings (                -- CocoIndex; kept apart so a model change or a move to Qdrant touches only this table
  chunk_id  text NOT NULL,
  model     text NOT NULL,
  embedding vector(1024) NOT NULL,
  PRIMARY KEY (chunk_id, model)
);
CREATE INDEX embeddings_hnsw ON embeddings USING hnsw (embedding vector_cosine_ops);

CREATE TABLE edges (                     -- CocoIndex; endpoints are entity keys, so a deleted record takes its edges with it
  src         text NOT NULL,             -- 'doc:confluence:123456', 'service:payments', ...
  dst         text NOT NULL,
  type        text NOT NULL,             -- mentions | implemented_in | calls | documented_by | reads | discussed_in | owned_by | fk
  document_id text NOT NULL,             -- the record that asserted it
  props       jsonb NOT NULL DEFAULT '{}',
  PRIMARY KEY (src, type, dst, document_id)
);
CREATE INDEX edges_dst ON edges (dst, type);

CREATE TABLE entities (                  -- entity resolution; rebuilt each sync
  id      bigint PRIMARY KEY,
  kind    text   NOT NULL,               -- service | repo | team | person | doc | runbook | table | diagram | channel | meeting
  name    text   NOT NULL,               -- display name
  aliases text[] NOT NULL                -- every entity key that resolves here
);
CREATE INDEX entities_aliases ON entities USING gin (aliases);
```

Notes on the DDL:
- **Index declarations in CocoIndex:** the HNSW index is declared with `declare_vector_index(column="embedding", metric="cosine", method="hnsw")`. CocoIndex defaults to ivfflat, so the method is always set. The generated `tsv` column and its GIN index are added with `declare_sql_command_attachment`.
- **Foreign keys:** none, deliberately. CocoIndex adds and removes rows per component in its own order, and a constraint would fight it.
- **Documents and entities:** every document is also an entity, `doc:<id>`, so "a page mentions a service" is an ordinary edge and needs no extra table.

## 9. Models

| Purpose | Model | Where it runs | Notes |
|---|---|---|---|
| Text embeddings | **[BAAI/bge-m3](https://huggingface.co/BAAI/bge-m3)**: MIT, 1024 dimensions, 8,192-token context, about 568M parameters | In process, through sentence-transformers (CPU or Apple Silicon), in `kb sync` and `kb mcp` | Downloaded from Hugging Face on first use and pinned by revision |
| Attachment layout and tables | Docling's layout, TableFormer and OCR models | In process, only for attachments | Downloaded on first use. Their licenses are separate from Docling's MIT and are checked in the spike† |
| Code search | codebase-memory-mcp's own index | Inside its binary | Not in Postgres |
| Generative LLM | **None** in the pipeline | — | Agents that query the knowledge base bring their own. LLM-assisted entity matching is a later rule (§7.3), and its provider is chosen then |

**Why bge-m3 is the default:** it encodes queries and documents the same way, with no instruction prefixes. The same call serves ingest in CocoIndex and the question in the gateway, so one side cannot be prompted differently from the other by mistake. It is also MIT-licensed, mature, and served by sentence-transformers and Ollama alike.

**Alternatives for the first-spike comparison**, on recall@10 over about 50 real questions against a real Confluence space:

| Model | License | Dimensions | Context | Why consider it |
|---|---|---|---|---|
| `Qwen/Qwen3-Embedding-0.6B` | Apache-2.0 | 1024 (reducible) | 32k | Strong retrieval scores. Needs a query instruction, so the gateway must add it |
| `microsoft/harrier-oss-v1-0.6b` | MIT | 1024 | 32k | Released 2026-03-30. Its self-reported multilingual MTEB v2 score is 69.0† |
| `nomic-ai/nomic-embed-text-v1.5` | Apache-2.0 | 768 (reducible) | 8k | Smallest (137M) and fastest. Needs `search_query:` and `search_document:` prefixes |

**Avoid** on license grounds:
- `google/embeddinggemma-300m` (Gemma terms);
- Jina v5 embeddings (CC-BY-NC-4.0);
- models with no license or an "other" license.

**Changing the model.** Set `[embedding] model` and `dim` in `kb.toml` and run `kb sync`. The model name is part of each embedding row's key, so new rows are written beside the old ones. The gateway switches when the new model covers every chunk, and the old rows are then dropped. A dimension change needs a new column or table, because a `vector(n)` column has a fixed size.

## 10. Retrieval and the gateway

### 10.1 One search function

`kb_search(q text, qvec vector, k int)` is one SQL function with three candidate lists, fused by reciprocal rank (RRF, k = 60):

```sql
WITH vec AS (            -- nearest chunks by meaning
  SELECT chunk_id, row_number() OVER (ORDER BY embedding <=> qvec) AS r
  FROM embeddings WHERE model = current_setting('kb.model')
  ORDER BY embedding <=> qvec LIMIT 50
), kw AS (               -- built-in full-text search (ts_rank_cd, not BM25; report §14 finding 2)
  SELECT c.id AS chunk_id, row_number() OVER (ORDER BY ts_rank_cd(c.tsv, tq) DESC) AS r
  FROM chunks c, websearch_to_tsquery('english', q) tq
  WHERE c.tsv @@ tq
  ORDER BY ts_rank_cd(c.tsv, tq) DESC LIMIT 50
), seed AS (             -- the documents behind the best ten of each list
  SELECT DISTINCT 'doc:' || c.document_id AS key
  FROM chunks c JOIN (SELECT chunk_id FROM vec WHERE r <= 10 UNION SELECT chunk_id FROM kw WHERE r <= 10) t ON t.chunk_id = c.id
), linked AS (           -- one hop: entities those documents touch, then other documents touching the same entities
  SELECT DISTINCT substr(e2.src, 5) AS document_id
  FROM seed s
  JOIN edges e1     ON e1.src = s.key
  JOIN entities ent ON ent.aliases @> ARRAY[e1.dst]
  JOIN edges e2     ON e2.dst = ANY (ent.aliases) AND e2.src LIKE 'doc:%' AND e2.src <> s.key
), hop AS (
  SELECT c.id AS chunk_id, row_number() OVER (ORDER BY em.embedding <=> qvec) AS r
  FROM linked l JOIN chunks c ON c.document_id = l.document_id
  JOIN embeddings em ON em.chunk_id = c.id AND em.model = current_setting('kb.model')
  ORDER BY em.embedding <=> qvec LIMIT 50
)
SELECT chunk_id, sum(1.0 / (60 + r)) AS score
FROM (SELECT * FROM vec UNION ALL SELECT * FROM kw UNION ALL SELECT * FROM hop) u
GROUP BY chunk_id ORDER BY score DESC LIMIT k;
```

The caller joins the result to `chunks` and `documents` for text, title and URL.

*This is a sketch.* The hop treats edges as pointing from documents to entities. Edges that point the other way (`service documented_by doc`) need the mirror join, and the exact query is tuned in the spike. Keyword recall is measured before pg_textsearch (BM25) is considered (report §14).

### 10.2 Tools

All tools are read-only. Every response is capped so that an agent cannot page through the whole corpus.

| MCP tool | REST | Returns | Caps |
|---|---|---|---|
| `search(query, sources?, k)` | `GET /search?q=&sources=&k=` | Chunks with title, URL, source, snippet, score and linked entities | `k` ≤ 20; snippets ≤ 1,500 characters |
| `get_document(id, offset?, limit?)` | `GET /documents/{id}` | A document's chunks in order | ≤ 20 chunks per call |
| `get_entity(name_or_key)` | `GET /entities/{key}` | The entity, its aliases, and its edges grouped by type | ≤ 100 edges |
| `neighbors(entity, edge_type?, hops?)` | `GET /entities/{key}/neighbors` | Linked entities, with the documents that assert each link | `hops` ≤ 2; ≤ 100 results |

There is no raw-SQL tool. Without per-document permissions, a raw-SQL tool would turn a prompt injection inside any indexed page into a way to dump the corpus.

### 10.3 Transports

- **Local:** `kb mcp` runs over stdio. Claude Code starts it from `.mcp.json` and asks once to approve the project's server. It reads `.kb/.env` itself, so no token passes through the agent's configuration.
- **Shared (later):** `kb serve` runs the same tools over streamable HTTP, plus the REST routes, on a server where `kb sync --live` also runs. Callers send `Authorization: Bearer <api key>`; keys are listed in the server's environment and rate-limited per key. MCP's OAuth flow can replace keys later. Each call is logged as one JSON line: time, caller, tool, arguments and result count.

## 11. Operations

| Task | Command | Notes |
|---|---|---|
| Start or stop Postgres | `kb up` / `kb down` | Compose project `kb-<name>`. Port bound to `127.0.0.1` only. Data in a named volume |
| Reset everything | `kb down -v` | Deletes the volume **and** `.kb/cocoindex.db` together (§7.2) |
| Sync once, or keep syncing | `kb sync` / `kb sync --live` | One process at a time (LMDB lock) |
| Re-sync one source | `kb sync --source confluence` | Other sources are untouched because each source is its own CocoIndex app |
| Reprocess one source from scratch | `kb sync --source confluence --rebuild` | Drops that app's state and rows, then re-reads everything |
| Back up | `pg_dump` plus a copy of `.kb/cocoindex.db`, taken while no sync runs | Restoring Postgres without the matching state file needs `--rebuild` |
| Check tokens | `kb-init --check` | Non-zero exit if any check fails; reports expiry dates |
| Try a query | `kb search "how do I roll back payments"` | Same function the tools call |
| Upgrade a pinned component | Change the version, run the fixture tests, then `kb sync` | CocoIndex reprocesses what the change affects |

Logs are JSON lines in `.kb/logs/`, one file per command. Common failures:
- **An expired token:** the source fails, and the others continue.
- **A rate limit:** the connector backs off.
- **Two syncs at once:** the second exits with "sync already running".
- **A codebase-memory-mcp schema change after an upgrade:** the fixture test fails before any data is written.

## 12. Security notes

- **No permission gate.** Connect only spaces, channels, drives and repositories that the whole organisation may read. Anyone who can run `kb mcp` in the repository, or who holds a gateway key, can read everything indexed.
- **Least privilege.** Use read-only scopes everywhere (§4.3) and a schema-only database user. Prefer fine-grained GitHub tokens and `Sites.Selected` for SharePoint where an admin can grant per site.
- **Secrets.** Secrets live only in `.kb/.env`, mode `0600` and ignored by git, or in the server's environment. `kb-init` never prints them. Set expiry dates on tokens and rotate them by running `kb-init --reconfigure <source>`.
- **Local exposure.** Postgres listens on `127.0.0.1` only, with a random password.
- **Agents.** Tools are read-only, capped and logged, with no raw SQL (§10.2). Indexed text is untrusted input to whatever agent reads it.

## 13. Open decisions and the first spike

Settle these before building on them:

1. **The pipeline seam (§6.2).** Show that unstructured-ingest's Confluence indexer and downloader run inside CocoIndex v1 components with memo key `(identifier, version)`. Show that an edited page is reprocessed alone, and that a deleted page loses its chunks, embeddings and edges.
2. **One CocoIndex app per source** sharing one `.kb/cocoindex.db`, run in one process†.
3. **Slack month components (§6.5).** Edits within open months are caught, a full refresh removes deleted messages, and closed months make no API calls.
4. **The embedding model (§9).** Compare recall@10 for bge-m3, Qwen3-Embedding-0.6B and harrier-oss-v1-0.6b over about 50 real questions. Record embedding throughput on the target hardware.
5. **Keyword recall.** Compare built-in full-text search against pg_textsearch on the same questions, and switch only if keyword recall is the bottleneck.
6. **The codebase-memory-mcp export.** Write a fixture test against v0.12.1. Audit the licenses of its bundled grammars and embedding model.
7. **The Onyx Teams fork.** Its dependencies, and its listing cost on a large team.
8. **Licenses of Docling's model weights.**
9. **The uncertain credential checks** marked † in §4.3: Confluence scoped tokens through `cloudId`, Slack's `x-oauth-scopes` header, Gong's `/v2/users`, and MySQL schema-only grants.
10. **Entity-resolution precision** over 50 sampled merges.

## 14. CLI reference

*Specified, not built yet.*

| Command | Does |
|---|---|
| `kb-init` (also `kb init`) | Sets up the current repository as a knowledge-base project (§4) |
| `kb-init --check` | Re-checks every credential without prompting |
| `kb-init --reconfigure <source>` | Asks again for one source's settings and secrets |
| `kb up` | Starts Postgres 17 + pgvector for this project and waits until it is healthy |
| `kb down [-v]` | Stops it; `-v` also deletes the data volume and `.kb/cocoindex.db` |
| `kb sync [--source S] [--live] [--rebuild]` | Runs connectors, the pipeline and entity resolution |
| `kb search "<question>"` | Runs `kb_search` and prints results with links |
| `kb mcp` | MCP server over stdio, for `.mcp.json` |
| `kb serve [--port N]` | MCP over HTTP plus REST, with API keys, for a shared deployment |
