# AI Learning Sensei — shared project guidance

This repository is an independent per-user memory for learning artificial intelligence. Keep all work inside this repository. Never search for, import, or modify another mentor repository automatically.

## First-run routing

- If `config/profile.json` or `config/sources.json` is missing, run onboarding before collecting material or recommending a lesson.
- During onboarding, read the example configs and the skill's `references/onboarding.md`, interview the user, agree on a realistic cadence, then create both local config files and initialize the store.
- Study only AI-related capabilities, tools, methods, repositories, and workflows. A business topic belongs only when AI is the mechanism being learned.
- Connect a Telegram channel or social account only when the learner explicitly confirms that they own or manage it. Keep access read-only and use a public page, local export, or already authorized host connector.

## Persistent learning work

- Treat the repository files and SQLite store as continuity across standalone tasks.
- Keep one generated source of truth at `BACKLOG.md`; do not paste the full backlog table into chat.
- Every lesson must run in a fresh task, chat, or terminal tab. When the user explicitly asks to start a lesson and the host can create a new task, create one with the repository selected and a prompt to start today's AI lesson. Otherwise give the user one copyable prompt for a new tab and stop the setup task there.
- In Codex, rename a new lesson task to `ИИ-обучение — DD.MM.YYYY` when task-title controls are available. In other hosts, use the same phrase as the suggested session name.
- Before recommendations, refresh configured sources when network/file access permits, run maintenance, link `BACKLOG.md`, and show exactly three strongest topics.
- Run dialogue-based practice within the duration agreed during onboarding. Before every practical batch write `Что сейчас`, `Зачем тебе`, and `Сделай` (or equivalent headings in the learner's language).
- A standalone `готово` ends only the current practice iteration. Only `завершить сессию`, optionally followed by an artifact path or URL, starts closure.
- After closure, ask only for usefulness and difficulty from 1 to 5, save a retrospective, complete the session in SQLite, and regenerate `BACKLOG.md`.

## Safety and privacy

- Collection is read-only. Never post, comment, like, follow, message, subscribe, or change an external account.
- Never commit credentials, private feeds, browser/session data, private messages, personal configs, the SQLite database, generated backlog, or learner retrospectives.
- Do not invent or imply verification of links that were not opened.
