# User-provided sources

`config/sources.json` is the authority. Add a source only when the learner supplies or approves it.

## Supported types

- `rss`: public RSS or Atom URL; collect recent entries.
- `web`: one public page; do not crawl the whole domain.
- `github`: public `https://github.com/<owner>/<repo>` URL; use the public API.
- `file`: UTF-8 text/Markdown inside this repository; reject paths outside it.
- `telegram`: a learner-selected public channel by default. Use `public_web` for a page readable without signing in. `export_file` and `agent_connector` require `access_authorized: true`.
- `social`: a learner-selected public page by default. Use `public_web` for a page readable without signing in. `export_file` and `agent_connector` require `access_authorized: true`.
- `manual`: dialogue input added with `sensei_store.py ingest`.

`public_web` is the default and reads only a page available without an account login. It may belong to somebody else; learner selection is sufficient. `export_file` reads an ignored local export. `agent_connector` means the active Codex or Claude Code host must use an already authorized connector and ingest selected material; the standalone collector reports that agent action is required. For the last two methods require `access_authorized: true`. Never request a token, password, cookie, or session file in chat or a tracked file.

When the learner marks a link, file, tool, repository, or idea with their configured marker (default `в обучение`), ingest it immediately and run maintenance. Preserve supplied URLs and use an outcome-oriented title. Do not ingest administrative instructions or unrelated links.

## Collection safety

- Read only; never subscribe, post, comment, like, follow, message, or modify accounts.
- Never sign in to collect a `public_web` source. If it is not publicly readable, report the limitation and continue with other sources.
- Refuse `export_file` or `agent_connector` sources without `access_authorized: true`.
- Respect HTTP failures and access controls.
- Store a compact extract, not full copyrighted articles.
- Do not collect credentials, cookies, private messages, browser profiles, or sessions.
- Deduplicate by canonical URL or stable external ID.
