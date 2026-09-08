# Contributing

Contributions are welcome when they preserve three invariants:

1. the curriculum stays focused on learning AI through practice;
2. sources and priorities belong to the learner, not the maintainer;
3. personal configuration, state, and retrospectives remain untracked by default.

Edit the canonical skill under `.agents/skills/ai-learning-sensei`, then run:

```bash
python scripts/sync_skills.py
python scripts/sync_skills.py --check
python -m unittest discover -s tests -v
```

Do not add API tokens, private feeds, session files, user profiles, generated databases, backlogs, or retrospectives to issues or commits.
