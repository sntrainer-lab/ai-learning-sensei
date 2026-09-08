# User-provided sources

`config/sources.json` is the authority. Add a source only when the learner supplies or approves it.

## Supported types

- `rss`: public RSS or Atom URL; collect recent entries.
- `web`: one public page; do not crawl the whole domain.
- `github`: public `https://github.com/<owner>/<repo>` URL; use the public API.
- `file`: UTF-8 text/Markdown inside this repository; reject paths outside it.
- `telegram`: only a channel owned or managed by the learner. Require `ownership_confirmed: true` and use `public_web`, `export_file`, or `agent_connector`.
- `social`: only the learner's own social account or page. Require `ownership_confirmed: true` and use `public_web`, `export_file`, or `agent_connector`.
- `manual`: dialogue input added with `sensei_store.py ingest`.

`public_web` reads a public page. `export_file` reads an ignored local export. `agent_connector` means the active Codex or Claude Code host must use an already authorized connector and ingest selected material; the standalone collector reports that agent action is required. If authentication is required, never request a token, password, cookie, or session file in chat or a tracked file.

When the learner marks a link, file, tool, repository, or idea with their configured marker (default `в обучение`), ingest it immediately and run maintenance. Preserve supplied URLs and use an outcome-oriented title. Do not ingest administrative instructions or unrelated links.

## Collection safety

- Read only; never subscribe, post, comment, like, follow, message, or modify accounts.
- Refuse Telegram or social sources without an explicit ownership confirmation.
- Respect HTTP failures and access controls.
- Store a compact extract, not full copyrighted articles.
- Do not collect credentials, cookies, private messages, browser profiles, or sessions.
- Deduplicate by canonical URL or stable external ID.
