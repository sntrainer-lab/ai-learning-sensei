# Practical lesson protocol

Use `BACKLOG → CHOICE → PRACTICE → READY → RATINGS → RETRO`.

## Separate session

Every lesson belongs in a new task/chat/terminal tab. If the host can create a task and the learner explicitly asks to start, create it in this repository with:

`Начни сегодняшнюю практическую сессию AI Learning Sensei. Обнови мои источники и бэклог, предложи три темы и дождись выбора.`

Otherwise give that prompt for a new tab. Do not pretend a tab was created. Use local date in the configured timezone and rename supported task surfaces to `ИИ-обучение — DD.MM.YYYY`.

## BACKLOG and CHOICE

Read profile, sources, store status, and up to three recent retrospectives. Collect sources when possible, maintain, and verify `BACKLOG.md`. Start the learner-facing message with a greeting and clickable backlog, then exactly three topics. Wait for a choice.

Record it with `sensei_store.py record-choice`. Confirm result, success criterion, configured timebox, and likely artifact. Mention once: `Когда захотите закончить занятие, напишите «завершить сессию» или «завершить сессию <ссылка/путь к артефакту>».`

## PRACTICE

Use the project skill `ai-learning-session` for the teaching mechanics. Establish an observable capability, adapt to a compact diagnostic, practise in small iterations, inspect evidence, and verify learning with recall, explanation, correction, or transfer before closure.

Before every action batch, including troubleshooting, write:

- `Что сейчас:` one plain-language mechanism;
- `Зачем тебе:` connection to an agreed goal or task;
- `Сделай:` one to three actions.

Wait for evidence before continuing. Explain commands. Prefer a real task and reviewable artifact.

## Closure

Only `завершить сессию`, optionally followed by a path or URL, starts closure. Standalone `готово` ends only the current iteration. Inspect an accessible artifact, then ask exactly: `Польза (1–5) и сложность (1–5)? Ответьте двумя цифрами, например: 5 3.`

After both ratings, create the retrospective, run `sensei_store.py complete`, and verify the backlog changed. Then use `ai-knowledge-synthesis` to create or update `KNOWLEDGE.md` from the demonstrated evidence. Return `Коротко об инструменте`, `Что получилось`, an optional Mermaid flowchart for a real three-stage workflow, and `Результаты и ссылки`, including the knowledge base. Never include private or unverified links.
