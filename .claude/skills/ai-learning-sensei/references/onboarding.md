# First-run interview

Onboarding converts an unknown learner into an explicit learning agreement. Do not copy the maintainer's profile or sources.

## Interview

Start in the user's language. Explain in one sentence that the answers will create local, Git-ignored configuration. Ask one compact numbered block covering:

1. role or current context, and two or three real tasks where AI may help;
2. desired AI capabilities or outcomes for the next 1–3 months;
3. current hands-on AI level and tools already used;
4. sources they want the mentor to follow: URLs, RSS/Atom feeds, GitHub repositories, or local files;
5. realistic cadence: sessions per week, preferred days/time, timezone, and minutes per session (normally 30–60);
6. priorities, exclusions, language, and privacy constraints.

Allow partial answers. Infer harmless formatting defaults, but do not invent sources, work goals, or credentials. Ask a follow-up only for information that would materially change the learning route.

## Agreement and persistence

Summarize 2–4 outcome-oriented AI priorities, expected practice artifacts, cadence, approved sources, and topics to avoid. Ask for correction only if the response is ambiguous; otherwise proceed.

Create `config/profile.json` from `config/profile.example.json` and `config/sources.json` from `config/sources.example.json`. Keep valid JSON and repository-relative local paths. Then run:

```bash
python .agents/skills/ai-learning-sensei/scripts/sensei_store.py validate-config
python .agents/skills/ai-learning-sensei/scripts/sensei_store.py init
python .agents/skills/ai-learning-sensei/scripts/collect_sources.py
python .agents/skills/ai-learning-sensei/scripts/sensei_store.py maintain
```

One source failure must not erase other results. Explain unsupported private sources without requesting credentials in chat. Finish with a clickable `BACKLOG.md` and the agreed rhythm. Do not start a lesson in the onboarding task; offer a fresh lesson task/session.
