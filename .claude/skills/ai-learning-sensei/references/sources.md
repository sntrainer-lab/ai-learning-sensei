# User-provided sources

`config/sources.json` is the authority. Add a source only when the learner supplies or approves it.

## Supported types

- `rss`: public RSS or Atom URL; collect recent entries.
- `web`: one public page; do not crawl the whole domain.
- `github`: public `https://github.com/<owner>/<repo>` URL; use the public API.
- `file`: UTF-8 text/Markdown inside this repository; reject paths outside it.
- `manual`: dialogue input added with `sensei_store.py ingest`.

If authentication is required, the learner may export selected material to a local ignored file. Never request a token in chat or a tracked file.

When the learner marks a link, file, tool, repository, or idea with their configured marker (default `в обучение`), ingest it immediately and run maintenance. Preserve supplied URLs and use an outcome-oriented title. Do not ingest administrative instructions or unrelated links.

## Collection safety

- Read only; never subscribe, post, comment, like, follow, message, or modify accounts.
- Respect HTTP failures and access controls.
- Store a compact extract, not full copyrighted articles.
- Do not collect credentials, cookies, private messages, browser profiles, or sessions.
- Deduplicate by canonical URL or stable external ID.
