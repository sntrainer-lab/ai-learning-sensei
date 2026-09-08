#!/usr/bin/env python3
"""Local persistent store and backlog renderer for AI Learning Sensei."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


DEFAULT_ROOT = Path(__file__).resolve().parents[4]
AI_TERMS = (
    " ai ", "ии", "artificial intelligence", "machine learning", "ml ", "llm",
    "нейросет", "модель", "model", "prompt", "промпт", "agent", "агент",
    "rag", "embedding", "генератив", "generative", "chatgpt", "claude",
    "codex", "gemini", "mcp", "computer vision", "nlp", "fine-tun",
    "eval", "openai", "anthropic", "langchain", "langgraph", "crewai",
    "n8n", "hugging face", "huggingface", "stable diffusion", "midjourney",
)
PRACTICE_TERMS = (
    "guide", "tutorial", "workflow", "how to", "пример", "гайд", "инструк",
    "пошаг", "шаблон", "практик", "demo", "prototype", "автоматиза",
)
HYPE_TERMS = (
    "conference", "webinar", "summit", "анонс", "вебинар", "конференц",
    "подпиш", "breaking news", "price increase", "скидк",
)


def repo_root(cli_root: str | None = None) -> Path:
    value = cli_root or os.environ.get("SENSEI_ROOT")
    return Path(value).expanduser().resolve() if value else DEFAULT_ROOT


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def load_profile(root: Path, required: bool = True) -> dict:
    path = root / "config" / "profile.json"
    if not path.exists():
        if required:
            raise SystemExit("Missing config/profile.json. Run the onboarding interview first.")
        return {}
    return load_json(path)


def local_now(profile: dict) -> datetime:
    zone_name = profile.get("learner", {}).get("timezone", "UTC")
    try:
        zone = ZoneInfo(zone_name)
    except ZoneInfoNotFoundError:
        # Windows may not ship the IANA database. The system zone is the safest
        # dependency-free fallback when the learner configured their local zone.
        zone = datetime.now().astimezone().tzinfo or timezone.utc
    return datetime.now(zone)


def safe_backlog_path(root: Path, profile: dict) -> Path:
    raw = profile.get("backlog_file", "BACKLOG.md")
    path = (root / raw).resolve()
    if path != root and root not in path.parents:
        raise ValueError("backlog_file must stay inside the repository")
    return path


def connect(root: Path) -> sqlite3.Connection:
    path = root / "data" / "sensei.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS materials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fingerprint TEXT NOT NULL UNIQUE,
            source_type TEXT NOT NULL,
            source_name TEXT,
            external_id TEXT,
            url TEXT,
            title TEXT NOT NULL,
            content TEXT,
            published_at TEXT,
            discovered_at TEXT NOT NULL,
            score REAL NOT NULL DEFAULT 0,
            topics TEXT NOT NULL DEFAULT '[]',
            metadata TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'new'
        );
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_date TEXT NOT NULL,
            topic TEXT NOT NULL,
            lane TEXT,
            material_ids TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'selected',
            usefulness INTEGER,
            difficulty INTEGER,
            artifact TEXT,
            insight TEXT,
            unresolved TEXT,
            retrospective TEXT,
            created_at TEXT NOT NULL,
            completed_at TEXT
        );
        """
    )
    connection.commit()
    return connection


def normalize(text: str) -> str:
    return " " + re.sub(r"\s+", " ", text.lower()).strip() + " "


def profile_phrases(profile: dict, key: str) -> list[str]:
    values = profile.get(key, [])
    return [str(value).strip().lower() for value in values if str(value).strip()]


def score_material(profile: dict, title: str, content: str, source: str) -> tuple[float, list[str], bool]:
    text = normalize(f"{title} {content}")
    ai_hits = [term.strip() for term in AI_TERMS if term in text]
    relevant = bool(ai_hits)
    score = min(8.0, len(set(ai_hits)) * 1.4)
    matched: list[str] = []

    for group in ("learning_goals", "real_work_tasks", "priority_areas"):
        for phrase in profile_phrases(profile, group):
            tokens = [token for token in re.findall(r"[\w-]+", phrase) if len(token) >= 4]
            hits = sum(token in text for token in tokens)
            if hits:
                score += min(3.0, 0.7 * hits)
                matched.append(phrase)

    for phrase in profile_phrases(profile, "low_priority_areas"):
        tokens = [token for token in re.findall(r"[\w-]+", phrase) if len(token) >= 4]
        if tokens and any(token in text for token in tokens):
            score -= 3.0

    score += min(2.0, sum(term in text for term in PRACTICE_TERMS) * 0.5)
    score -= min(3.0, sum(term in text for term in HYPE_TERMS) * 0.75)
    if source == "manual":
        score += 1.5
    elif source == "github":
        score += 0.8
    return round(score, 2), matched[:5], relevant


def fingerprint(source: str, external_id: str | None, url: str | None, title: str, content: str) -> str:
    stable = external_id or url or f"{title}\n{content}"
    return hashlib.sha256(f"{source}:{stable}".encode("utf-8")).hexdigest()


def ingest_row(connection: sqlite3.Connection, profile: dict, *, source: str, title: str,
               content: str = "", source_name: str = "", external_id: str | None = None,
               url: str | None = None, published_at: str | None = None,
               metadata: dict | None = None, status: str = "new") -> bool:
    score, topics, relevant = score_material(profile, title, content, source)
    metadata = dict(metadata or {})
    metadata["ai_relevant"] = relevant
    metadata["profile_matches"] = topics
    cur = connection.execute(
        """INSERT OR IGNORE INTO materials
        (fingerprint, source_type, source_name, external_id, url, title, content,
         published_at, discovered_at, score, topics, metadata, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (fingerprint(source, external_id, url, title, content), source, source_name,
         external_id, url, title.strip()[:240], content.strip()[:8000], published_at,
         datetime.now(timezone.utc).isoformat(), score, json.dumps(topics, ensure_ascii=False),
         json.dumps(metadata, ensure_ascii=False), status),
    )
    connection.commit()
    return cur.rowcount == 1


def cell(value: object) -> str:
    return str(value or "—").replace("|", "\\|").replace("\n", " ").strip()


def practical_result(row: sqlite3.Row, minutes: int) -> str:
    metadata = json.loads(row["metadata"] or "{}")
    if metadata.get("experiment"):
        return str(metadata["experiment"])
    text = normalize(f"{row['title']} {row['content'] or ''}")
    if any(term in text for term in ("agent", "агент", "workflow", "автоматиза", "n8n")):
        return f"Рабочий AI-сценарий с проверяемым входом и результатом за {minutes} мин."
    if any(term in text for term in ("image", "visual", "изображ", "визуал", "слайд")):
        return f"Готовый визуальный артефакт и повторяемый AI-процесс за {minutes} мин."
    if any(term in text for term in ("rag", "knowledge", "база знаний", "research", "исслед")):
        return f"Проверенный AI-поиск или мини-база знаний за {minutes} мин."
    return f"Небольшой проверяемый AI-артефакт за {minutes} мин."


def render_backlog(connection: sqlite3.Connection, root: Path, profile: dict) -> Path:
    path = safe_backlog_path(root, profile)
    minutes = int(profile.get("cadence", {}).get("session_minutes", 45))
    active = connection.execute(
        "SELECT * FROM materials WHERE status IN ('new','shortlisted') ORDER BY score DESC, discovered_at DESC, id DESC"
    ).fetchall()
    completed = connection.execute(
        "SELECT * FROM sessions WHERE status='completed' ORDER BY completed_at DESC, id DESC"
    ).fetchall()
    priorities = {row["id"] for row in active[:3]}
    now = local_now(profile)
    lines = [
        "# AI Learning Sensei — актуальный бэклог",
        "",
        f"Обновлено: {now.strftime('%Y-%m-%d %H:%M %Z')} · В бэклоге: {len(active)} · Освоено: {len(completed)}",
        "",
        "🔥 ближайший приоритет · 📌 в бэклоге · ✅ завершено",
        "",
        "## Активные темы",
        "",
        "| Статус | ID | Чему научусь | Практический результат | Источник |",
        "|---|---:|---|---|---|",
    ]
    if active:
        for row in active:
            status = "🔥" if row["id"] in priorities else "📌"
            title = cell(row["title"])
            source = cell(row["source_name"] or row["source_type"])
            if row["url"]:
                source = f"[{source}]({row['url']})"
            lines.append(f"| {status} | {row['id']} | {title} | {cell(practical_result(row, minutes))} | {source} |")
    else:
        lines.append("| — | — | Пока нет AI-тем: добавьте источники или ручную идею | — | — |")

    lines.extend(["", "## Завершённые занятия", ""])
    if completed:
        lines.extend([
            "| ID | Дата | Тема | Польза / сложность | Результат |",
            "|---:|---|---|---:|---|",
        ])
        for row in completed:
            result = cell(row["artifact"] or row["insight"] or "Завершено")
            if row["retrospective"]:
                retro_path = Path(row["retrospective"])
                try:
                    retro_ref = retro_path.resolve().relative_to(root).as_posix()
                except (OSError, ValueError):
                    retro_ref = str(retro_path)
                result = f"[{result}]({retro_ref})"
            lines.append(
                f"| S{row['id']} | {cell(row['session_date'])} | {cell(row['topic'])} | "
                f"{cell(row['usefulness'])} / {cell(row['difficulty'])} | {result} |"
            )
    else:
        lines.append("Завершённых занятий пока нет.")
    lines.extend(["", "Выберите любой ID или предложите собственную AI-тему.", ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def validate_config(root: Path) -> dict:
    profile = load_profile(root)
    sources_path = root / "config" / "sources.json"
    if not sources_path.exists():
        raise ValueError("Missing config/sources.json")
    sources = load_json(sources_path)
    learner = profile.get("learner", {})
    cadence = profile.get("cadence", {})
    errors: list[str] = []
    if not learner.get("role"):
        errors.append("learner.role is required")
    if not profile.get("learning_goals"):
        errors.append("learning_goals must contain at least one AI outcome")
    minutes = cadence.get("session_minutes", 0)
    if not isinstance(minutes, int) or not 15 <= minutes <= 120:
        errors.append("cadence.session_minutes must be an integer from 15 to 120")
    if not isinstance(sources.get("sources", []), list):
        errors.append("sources must be a list")
    supported = {"rss", "web", "github", "file", "telegram", "social"}
    account_methods = {"public_web", "export_file", "agent_connector"}
    for index, source in enumerate(sources.get("sources", [])):
        source_type = source.get("type")
        if source_type not in supported:
            errors.append(f"sources[{index}].type must be one of {sorted(supported)}")
        if source_type == "file" and not source.get("path"):
            errors.append(f"sources[{index}].path is required")
        if source_type in {"rss", "web", "github"} and not source.get("url"):
            errors.append(f"sources[{index}].url is required")
        if source_type in {"telegram", "social"}:
            method = source.get("collection_method")
            if source.get("ownership_confirmed") is not True:
                errors.append(f"sources[{index}].ownership_confirmed must be true for {source_type}")
            if method not in account_methods:
                errors.append(f"sources[{index}].collection_method must be one of {sorted(account_methods)}")
            if method == "public_web" and not source.get("url"):
                errors.append(f"sources[{index}].url is required for public_web")
            if method == "export_file" and not source.get("path"):
                errors.append(f"sources[{index}].path is required for export_file")
            if method == "agent_connector" and not source.get("connector"):
                errors.append(f"sources[{index}].connector is required for agent_connector")
    safe_backlog_path(root, profile)
    if errors:
        raise ValueError("; ".join(errors))
    zone_name = learner.get("timezone", "UTC")
    try:
        ZoneInfo(zone_name)
        timezone_available = True
    except ZoneInfoNotFoundError:
        timezone_available = False
    return {"valid": True, "sources": len(sources.get("sources", [])),
            "timezone": zone_name, "timezone_available": timezone_available}


def json_row(row: sqlite3.Row) -> dict:
    value = dict(row)
    for field in ("topics", "metadata", "material_ids"):
        if field in value and isinstance(value[field], str):
            value[field] = json.loads(value[field])
    return value


def parser() -> argparse.ArgumentParser:
    root_parser = argparse.ArgumentParser(description=__doc__)
    root_parser.add_argument("--repo-root", help="Override repository root (mainly for testing)")
    commands = root_parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate-config")
    commands.add_parser("init")
    commands.add_parser("maintain")
    commands.add_parser("status")
    recommend = commands.add_parser("recommend")
    recommend.add_argument("--limit", type=int, default=3)
    ingest = commands.add_parser("ingest")
    ingest.add_argument("--source", default="manual")
    ingest.add_argument("--source-name", default="")
    ingest.add_argument("--external-id")
    ingest.add_argument("--url")
    ingest.add_argument("--title", required=True)
    ingest.add_argument("--text", default="")
    ingest.add_argument("--published-at")
    ingest.add_argument("--metadata-json", default="{}")
    ingest.add_argument("--status", default="new")
    choice = commands.add_parser("record-choice")
    choice.add_argument("--topic", required=True)
    choice.add_argument("--lane", default="")
    choice.add_argument("--materials", nargs="*", type=int, default=[])
    complete = commands.add_parser("complete")
    complete.add_argument("--session-id", type=int, required=True)
    complete.add_argument("--usefulness", type=int, required=True)
    complete.add_argument("--difficulty", type=int, required=True)
    complete.add_argument("--artifact", default="")
    complete.add_argument("--insight", default="")
    complete.add_argument("--unresolved", default="")
    complete.add_argument("--retrospective", required=True)
    return root_parser


def main() -> int:
    args = parser().parse_args()
    root = repo_root(args.repo_root)
    try:
        if args.command == "validate-config":
            print(json.dumps(validate_config(root), ensure_ascii=False, indent=2))
            return 0
        profile = load_profile(root, required=args.command != "init")
        connection = connect(root)
        if args.command == "init":
            print(json.dumps({"database": str(root / 'data' / 'sensei.db'), "status": "ready"}, ensure_ascii=False))
        elif args.command == "ingest":
            metadata = json.loads(args.metadata_json)
            added = ingest_row(connection, profile, source=args.source, source_name=args.source_name,
                               external_id=args.external_id, url=args.url, title=args.title,
                               content=args.text, published_at=args.published_at,
                               metadata=metadata, status=args.status)
            print(json.dumps({"added": added}, ensure_ascii=False))
        elif args.command == "maintain":
            rows = connection.execute("SELECT * FROM materials ORDER BY id DESC").fetchall()
            seen: set[str] = set()
            rejected = 0
            for row in rows:
                score, topics, relevant = score_material(profile, row["title"], row["content"] or "", row["source_type"])
                metadata = json.loads(row["metadata"] or "{}")
                metadata.update({"ai_relevant": relevant, "profile_matches": topics})
                status = row["status"]
                content_key = normalize(f"{row['title']} {row['content'] or ''}")
                if status in {"new", "shortlisted"} and (not relevant or content_key in seen):
                    status = "rejected"
                    rejected += 1
                seen.add(content_key)
                connection.execute(
                    "UPDATE materials SET score=?, topics=?, metadata=?, status=? WHERE id=?",
                    (score, json.dumps(topics, ensure_ascii=False), json.dumps(metadata, ensure_ascii=False), status, row["id"]),
                )
            connection.commit()
            path = render_backlog(connection, root, profile)
            print(json.dumps({"rescored": len(rows), "rejected": rejected, "backlog": str(path)}, ensure_ascii=False))
        elif args.command == "recommend":
            rows = connection.execute(
                "SELECT * FROM materials WHERE status IN ('new','shortlisted') ORDER BY score DESC, discovered_at DESC LIMIT ?",
                (max(1, args.limit),),
            ).fetchall()
            print(json.dumps([json_row(row) for row in rows], ensure_ascii=False, indent=2))
        elif args.command == "record-choice":
            now = datetime.now(timezone.utc).isoformat()
            cur = connection.execute(
                "INSERT INTO sessions (session_date, topic, lane, material_ids, created_at) VALUES (?, ?, ?, ?, ?)",
                (local_now(profile).date().isoformat(), args.topic, args.lane,
                 json.dumps(args.materials), now),
            )
            if args.materials:
                marks = ",".join("?" for _ in args.materials)
                connection.execute(f"UPDATE materials SET status='selected' WHERE id IN ({marks})", args.materials)
            connection.commit()
            print(json.dumps({"session_id": cur.lastrowid, "status": "selected"}, ensure_ascii=False))
        elif args.command == "complete":
            if not 1 <= args.usefulness <= 5 or not 1 <= args.difficulty <= 5:
                raise ValueError("usefulness and difficulty must be from 1 to 5")
            cur = connection.execute(
                """UPDATE sessions SET status='completed', usefulness=?, difficulty=?, artifact=?, insight=?,
                unresolved=?, retrospective=?, completed_at=? WHERE id=?""",
                (args.usefulness, args.difficulty, args.artifact, args.insight, args.unresolved,
                 args.retrospective, datetime.now(timezone.utc).isoformat(), args.session_id),
            )
            connection.commit()
            if cur.rowcount != 1:
                raise ValueError(f"session {args.session_id} not found")
            path = render_backlog(connection, root, profile)
            print(json.dumps({"updated": True, "backlog": str(path)}, ensure_ascii=False))
        elif args.command == "status":
            counts = {
                "active_materials": connection.execute("SELECT COUNT(*) FROM materials WHERE status IN ('new','shortlisted')").fetchone()[0],
                "rejected_materials": connection.execute("SELECT COUNT(*) FROM materials WHERE status='rejected'").fetchone()[0],
                "completed_sessions": connection.execute("SELECT COUNT(*) FROM sessions WHERE status='completed'").fetchone()[0],
                "open_sessions": connection.execute("SELECT COUNT(*) FROM sessions WHERE status!='completed'").fetchone()[0],
            }
            recent = connection.execute("SELECT * FROM sessions ORDER BY id DESC LIMIT 5").fetchall()
            print(json.dumps({"counts": counts, "recent_sessions": [json_row(row) for row in recent]}, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Configuration or input error: {exc}") from exc


if __name__ == "__main__":
    raise SystemExit(main())
