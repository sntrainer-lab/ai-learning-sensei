#!/usr/bin/env python3
"""Read configured public/local sources and ingest compact AI learning candidates."""

from __future__ import annotations

import argparse
import html
import ipaddress
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

import sensei_store


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title: list[str] = []
        self.description = ""
        self.text: list[str] = []
        self._in_title = False
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = True
        if tag in {"script", "style", "noscript", "svg"}:
            self._skip += 1
        values = {key.lower(): value or "" for key, value in attrs}
        if tag == "meta" and values.get("name", "").lower() == "description":
            self.description = values.get("content", "")
        if tag == "meta" and values.get("property", "").lower() == "og:description" and not self.description:
            self.description = values.get("content", "")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag == "title":
            self._in_title = False
        if tag in {"script", "style", "noscript", "svg"} and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        value = " ".join(data.split())
        if not value:
            return
        if self._in_title:
            self.title.append(value)
        elif not self._skip:
            self.text.append(value)


def safe_public_url(value: str) -> str:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("source URL must use http or https")
    if parsed.username or parsed.password:
        raise ValueError("credentials must not be embedded in a source URL")
    if parsed.hostname.lower() in {"localhost", "localhost.localdomain"}:
        raise ValueError("local HTTP endpoints are not supported")
    try:
        address = ipaddress.ip_address(parsed.hostname)
        if address.is_private or address.is_loopback or address.is_link_local:
            raise ValueError("private network endpoints are not supported")
    except ValueError as exc:
        if "not supported" in str(exc):
            raise
    return value


def fetch(url: str, timeout: int, user_agent: str, accept: str = "*/*") -> bytes:
    safe_public_url(url)
    headers = {"User-Agent": user_agent, "Accept": accept}
    token = os.environ.get("GITHUB_TOKEN")
    if token and urllib.parse.urlparse(url).hostname == "api.github.com":
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read(2_000_000)


def plain_markup(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return " ".join(html.unescape(without_tags).split())


def child_text(element: ET.Element, names: set[str]) -> str:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1].lower() in names and child.text:
            return child.text.strip()
    return ""


def entry_link(element: ET.Element) -> str:
    for child in element.iter():
        if child.tag.rsplit("}", 1)[-1].lower() != "link":
            continue
        href = child.attrib.get("href")
        if href and child.attrib.get("rel", "alternate") in {"alternate", ""}:
            return href
        if child.text and child.text.strip().startswith("http"):
            return child.text.strip()
    return ""


def parse_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        try:
            parsed = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def collect_rss(source: dict, settings: dict) -> list[dict]:
    data = fetch(source["url"], settings["timeout"], settings["user_agent"], "application/rss+xml, application/atom+xml, application/xml, text/xml")
    root = ET.fromstring(data)
    entries = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1].lower() in {"item", "entry"}]
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings["lookback_days"])
    results: list[dict] = []
    for entry in entries[:100]:
        title = plain_markup(child_text(entry, {"title"}))
        content = plain_markup(child_text(entry, {"summary", "description", "content", "encoded"}))
        published_raw = child_text(entry, {"published", "updated", "pubdate", "date"})
        published = parse_date(published_raw)
        if published and published < cutoff:
            continue
        url = entry_link(entry) or None
        external_id = child_text(entry, {"guid", "id"}) or url
        if title:
            results.append({"title": title, "content": content[:8000], "url": url,
                            "external_id": external_id,
                            "published_at": published.isoformat() if published else published_raw or None})
    return results


def collect_web(source: dict, settings: dict) -> list[dict]:
    data = fetch(source["url"], settings["timeout"], settings["user_agent"], "text/html")
    parser = PageParser()
    parser.feed(data.decode("utf-8", errors="replace"))
    title = " ".join(parser.title).strip() or source["name"]
    content = " ".join([parser.description, *parser.text])
    return [{"title": title[:240], "content": " ".join(content.split())[:8000], "url": source["url"], "external_id": source["url"]}]


def github_coordinates(url: str) -> tuple[str, str]:
    parsed = urllib.parse.urlparse(safe_public_url(url))
    if parsed.hostname.lower() != "github.com":
        raise ValueError("github source must use github.com")
    parts = [part for part in parsed.path.strip("/").split("/") if part]
    if len(parts) < 2:
        raise ValueError("github URL must include owner and repository")
    return parts[0], parts[1].removesuffix(".git")


def collect_github(source: dict, settings: dict) -> list[dict]:
    owner, repository = github_coordinates(source["url"])
    api_url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repository)}"
    payload = json.loads(fetch(api_url, settings["timeout"], settings["user_agent"], "application/vnd.github+json"))
    topics = payload.get("topics") or []
    content = " ".join(filter(None, [payload.get("description"), "Topics: " + ", ".join(topics) if topics else ""]))
    return [{
        "title": payload.get("full_name") or f"{owner}/{repository}",
        "content": content,
        "url": payload.get("html_url") or source["url"],
        "external_id": str(payload.get("id") or source["url"]),
        "published_at": payload.get("updated_at"),
        "metadata": {"stars": payload.get("stargazers_count", 0), "language": payload.get("language"), "topics": topics},
    }]


def collect_file(source: dict, root: Path) -> list[dict]:
    path = (root / source["path"]).resolve()
    if path != root and root not in path.parents:
        raise ValueError("file source must stay inside the repository")
    if not path.is_file():
        raise FileNotFoundError(path)
    content = path.read_text(encoding="utf-8")
    title = source.get("name") or path.stem
    return [{"title": title, "content": content[:8000], "external_id": path.relative_to(root).as_posix()}]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root")
    args = parser.parse_args()
    root = sensei_store.repo_root(args.repo_root)
    profile = sensei_store.load_profile(root)
    config = sensei_store.load_json(root / "config" / "sources.json")
    collection = config.get("collection", {})
    settings = {
        "lookback_days": int(collection.get("lookback_days", 30)),
        "timeout": int(collection.get("request_timeout_seconds", 20)),
        "user_agent": str(collection.get("user_agent", "ai-learning-sensei/1.0")),
    }
    connection = sensei_store.connect(root)
    report: list[dict] = []
    collectors = {"rss": collect_rss, "web": collect_web, "github": collect_github}
    for source in config.get("sources", []):
        if not source.get("enabled", True):
            continue
        name = source.get("name") or source.get("url") or source.get("path") or "unnamed"
        try:
            source_type = source.get("type")
            if source_type in {"telegram", "social"}:
                if source.get("ownership_confirmed") is not True:
                    raise ValueError(f"{source_type} source requires ownership_confirmed: true")
                method = source.get("collection_method")
                if method == "agent_connector":
                    report.append({
                        "source": name,
                        "status": "agent_action_required",
                        "connector": source.get("connector"),
                        "message": "Use the already authorized host connector in read-only mode, then ingest selected AI material.",
                    })
                    continue
                if method == "export_file":
                    items = collect_file(source, root)
                elif method == "public_web":
                    items = collect_web(source, settings)
                else:
                    raise ValueError("collection_method must be public_web, export_file, or agent_connector")
            elif source_type == "file":
                items = collect_file(source, root)
            else:
                items = collectors[source_type](source, settings)
            added = 0
            for item in items:
                added += sensei_store.ingest_row(
                    connection, profile, source=source_type, source_name=name,
                    title=item["title"], content=item.get("content", ""),
                    url=item.get("url"), external_id=item.get("external_id"),
                    published_at=item.get("published_at"), metadata=item.get("metadata"),
                )
            report.append({"source": name, "status": "ok", "found": len(items), "added": added})
        except (KeyError, ValueError, OSError, ET.ParseError, json.JSONDecodeError, urllib.error.URLError) as exc:
            report.append({"source": name, "status": "error", "error": str(exc)})
    print(json.dumps({"sources": report}, ensure_ascii=False, indent=2))
    return 1 if report and all(item["status"] == "error" for item in report) else 0


if __name__ == "__main__":
    raise SystemExit(main())
