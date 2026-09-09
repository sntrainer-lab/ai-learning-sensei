---
name: ai-learning-sensei
description: Orchestrate a persistent, interview-led system for learning artificial intelligence. Use for onboarding, learner-provided sources, AI backlog curation, lesson routing, progress, retrospectives, and cumulative knowledge. Do not use for general tutoring unrelated to AI.
---

# AI Learning Sensei

Turn the learner's own goals and sources into a practical AI-learning trajectory. Preserve continuity in this repository and optimize for applied capability, not content consumption.

## Route the request

1. Resolve the repository root from this skill location. Keep state only in that repository.
2. If `config/profile.json` or `config/sources.json` is absent, read [onboarding.md](references/onboarding.md) and conduct onboarding. Do not recommend lessons before configuration is complete.
3. For adding, editing, or collecting sources, read [sources.md](references/sources.md).
4. For backlog refresh or prioritization, read [learning-policy.md](references/learning-policy.md).
5. For opening or running a lesson, read [daily-session.md](references/daily-session.md).
6. For closure, additionally read [retrospective-template.md](references/retrospective-template.md).
7. During practice, use the project skill `ai-learning-session` for the teaching loop.
8. After closure or for cross-session summaries, use `ai-knowledge-synthesis` and update `KNOWLEDGE.md`.

Read only the references needed for the current mode.

## Start configured work

Read `config/profile.json`, `config/sources.json`, store status, and up to three recent retrospectives. Initialize the store when necessary:

```bash
python .agents/skills/ai-learning-sensei/scripts/sensei_store.py init
python .agents/skills/ai-learning-sensei/scripts/sensei_store.py status
```

Use the equivalent `.claude/skills/...` path inside Claude Code if `.agents/...` is unavailable. Prefer the `.agents` canonical copy when both exist.

## Non-negotiable boundaries

- Teach artificial intelligence: its tools, models, agents, automation, evaluation, prompting, data workflows, content workflows, safety, and practical applications. Reject a topic when AI is incidental or absent.
- Sources come from the learner. Do not silently add the maintainer's feeds, accounts, or preferences.
- By default, treat learner-selected Telegram channels and social pages as public web sources that must be readable without signing in. Use exports or account connectors only when the learner explicitly confirms authorized access; keep every method read-only.
- Collection is read-only. Do not alter social accounts or external content.
- Keep credentials, private messages, private feeds, browser data, personal configs, SQLite state, generated backlog, and retrospectives out of Git.
- Never invent a source URL, artifact, result, or verification.
- The user's explicit instructions take precedence over general teaching preferences in this skill.

## Persistent artifacts

- `config/profile.json`: agreed learner profile and cadence.
- `config/sources.json`: only sources supplied or approved by the learner.
- `data/sensei.db`: materials and session history.
- `BACKLOG.md`: single generated backlog snapshot, overwritten on refresh.
- `retrospectives/`: one concise record per completed lesson.
- `KNOWLEDGE.md`: cumulative map of demonstrated capabilities, reusable patterns, gaps, and open questions.

Use `scripts/sensei_store.py` for deterministic state changes and `scripts/collect_sources.py` for configured read-only collection.
