---
name: ai-knowledge-synthesis
description: Consolidate completed AI learning into a cumulative, evidence-linked knowledge base and concise summaries. Use after lessons, across retrospectives, or when the learner asks what they know, what remains unclear, or what to review. Do not use to summarize unrelated documents.
---

# AI Knowledge Synthesis

Convert session evidence into reusable knowledge without turning the knowledge base into a transcript. Work only inside the current AI Learning Sensei repository.

## Evidence order

Prefer evidence in this order:

1. learner-created or tested artifacts;
2. completed retrospectives and recorded session fields;
3. the learner's explicit explanations and decisions;
4. source material actually opened or verified during the session.

Do not promote an untested claim into established knowledge. Mark uncertainty, missing evidence, and conflicting results explicitly. Never invent a link or imply that a source was checked when it was not.

## Maintain two levels of memory

- `retrospectives/` records what happened in one lesson.
- `KNOWLEDGE.md` is the cumulative, current map of what the learner can reuse across lessons.

Create or update `KNOWLEDGE.md` after a completed session and when the learner requests a synthesis. Keep it concise and overwrite stale formulations instead of appending duplicate summaries.

Use this structure, omitting empty sections:

```markdown
# Моя база знаний по ИИ

## Что я уже умею
### <capability>
- Механизм: <plain-language causal explanation>
- Могу применить: <real task>
- Доказательство: <artifact or retrospective link>
- Ограничение: <boundary, risk, or condition>

## Рабочие паттерны
- <reusable principle spanning lessons>

## Нужно закрепить
- <specific gap> — <small retrieval or transfer check>

## Открытые вопросы
- <question not yet resolved>
```

## Synthesis rules

- Combine duplicate lessons under one capability and preserve the strongest evidence.
- Distinguish `видел`, `пробовал`, and `умею применять`; reserve the last state for demonstrated transfer or a reviewable artifact.
- Write mechanisms and decision rules, not tool marketing or chronological narration.
- Preserve important failures and limitations when they change future decisions.
- Link local files with repository-relative Markdown links and external sources only when verified.
- Keep sensitive configuration, credentials, private source content, and personal data out of the summary.

## Build review prompts

For every unresolved or weak capability, add one small review prompt that requires recall, judgment, or transfer rather than rereading. Prefer reviewing a few due gaps at the start of a related future lesson; do not force a quiz into every interaction.

When answering `что я уже знаю`, summarize from `KNOWLEDGE.md` and current evidence, clearly separating demonstrated capabilities from topics merely encountered.

