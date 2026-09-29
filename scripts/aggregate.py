"""Merge the changelogs listed in sources.toml into CHANGELOG.md and changelog.json.

Usage:
    python scripts/aggregate.py [--sources sources.toml] [--out-dir .]

Each source is fetched from its repo's default branch via the GitHub API. Set GH_TOKEN (or
GITHUB_TOKEN) to a token that can read every listed repo; internal repos 404 without one.
Only released sections are included, newest first by date.

Standard library only.
"""

import argparse
import json
import os
import posixpath
import re
import sys
import tomllib
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from itertools import groupby
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

VERSION_HEADING = re.compile(r"^## \[([^\]]+)\](?: - (\d{4}-\d{2}-\d{2}))?( \[YANKED\])?\s*$")
SECTION_HEADING = re.compile(r"^## ")
TYPE_HEADING = re.compile(r"^### (.+?)\s*$")
LINK_DEFINITION = re.compile(r"^\[([^\]]+)\]: (\S+)")
ENTRY = re.compile(r"^[-*] ")
CODE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
INLINE_LINK = re.compile(r"(\]\()([^)\s]+)(\))")
# [text][label], [label][], or a bare [label] not followed by ( [ or :.
REFERENCE_LINK = re.compile(r"\[([^\]]+)\]\[([^\]]*)\]|\[([^\]]+)\](?![(\[:])")
MARKDOWN_LINK = re.compile(r"\[([^\]]*)\]\((https?://[^)\s]+)\)")
GITHUB_REPO = re.compile(r"^https://github\.com/([\w.-]+/[\w.-]+)")
ISSUE_REFERENCE = re.compile(r"^[\w.-]*#\d+$")
SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
BREAKING = "**Breaking:**"


@dataclass(frozen=True)
class Source:
    name: str
    repo: str
    path: str = "CHANGELOG.md"

    @property
    def url(self) -> str:
        return f"https://github.com/{self.repo}/blob/HEAD/{self.path}"


@dataclass
class Entry:
    text: str
    breaking: bool


@dataclass
class Change:
    type: str
    entries: list[Entry] = field(default_factory=list)


@dataclass
class Release:
    component: str
    repo: str
    version: str
    date: str
    yanked: bool
    url: str | None
    summary: str | None
    changes: list[Change]


def load_sources(path: Path) -> list[Source]:
    with path.open("rb") as file:
        data = tomllib.load(file)
    return [Source(**source) for source in data["source"]]


def _api(path: str, token: str | None, accept: str = "application/vnd.github+json") -> str:
    request = urllib.request.Request(
        f"https://api.github.com/{path}",
        headers={"Accept": accept, "X-GitHub-Api-Version": "2022-11-28"},
    )
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def fetch(source: Source, token: str | None) -> str:
    try:
        return _api(f"repos/{source.repo}/contents/{source.path}", token, "application/vnd.github.raw")
    except urllib.error.HTTPError as error:
        hint = " (is GH_TOKEN set and allowed to read it?)" if error.code == 404 else ""
        raise SystemExit(f"{source.repo}/{source.path}: HTTP {error.code}{hint}") from error


class Visibility:
    """Whether GitHub repos are public. A repo the token can't see counts as private."""

    def __init__(self, token: str | None) -> None:
        self.token = token
        self.cache: dict[str, bool] = {}

    def is_public(self, repo: str) -> bool:
        repo = repo.lower()
        if repo not in self.cache:
            try:
                data = json.loads(_api(f"repos/{repo}", self.token))
                self.cache[repo] = data.get("visibility") == "public"
            except urllib.error.HTTPError as error:
                if error.code != 404:
                    raise
                self.cache[repo] = False
        return self.cache[repo]


def _fenced(lines: list[str]) -> list[bool]:
    marks, fence = [], None
    for line in lines:
        match = CODE_FENCE.match(line)
        if fence is None and match:
            fence = match.group(1)
            marks.append(True)
        elif fence is not None:
            marks.append(True)
            if re.fullmatch(re.escape(fence[0]) + f"{{{len(fence)},}}", line.strip()):
                fence = None
        else:
            marks.append(False)
    return marks


def _resolve(target: str, source: Source) -> str:
    """Make a link target from the source changelog absolute."""
    if SCHEME.match(target):
        return target
    if target.startswith("#"):
        return source.url + target
    path, _, anchor = target.partition("#")
    if path.startswith("/"):
        path = path.lstrip("/")
    else:
        path = posixpath.normpath(posixpath.join(posixpath.dirname(source.path), path))
    url = f"https://github.com/{source.repo}/blob/HEAD/{path}"
    return f"{url}#{anchor}" if anchor else url


def rewrite_links(text: str, source: Source, definitions: dict[str, str]) -> str:
    """Inline reference links and make relative targets absolute."""

    def reference(match: re.Match[str]) -> str:
        if match.group(3) is not None:
            label, shown = match.group(3), match.group(3)
        else:
            shown = match.group(1)
            label = match.group(2) or shown
        url = definitions.get(label.lower())
        return f"[{shown}]({url})" if url else match.group(0)

    text = INLINE_LINK.sub(lambda m: m.group(1) + _resolve(m.group(2), source) + m.group(3), text)
    return REFERENCE_LINK.sub(reference, text)


def _strip_blank(lines: list[str]) -> list[str]:
    while lines and not lines[0].strip():
        lines = lines[1:]
    while lines and not lines[-1].strip():
        lines = lines[:-1]
    return lines


def _parse_body(lines: list[str], fenced: list[bool]) -> tuple[str | None, list[Change]]:
    summary: list[str] = []
    changes: list[Change] = []
    current: list[str] | None = None

    def close() -> None:
        if current is not None and changes:
            text = "\n".join(_strip_blank(current))
            changes[-1].entries.append(Entry(text=text, breaking=text[2:].startswith(BREAKING)))

    for line, in_fence in zip(lines, fenced):
        heading = None if in_fence else TYPE_HEADING.match(line)
        if heading:
            close()
            current = None
            changes.append(Change(type=heading.group(1)))
        elif not changes:
            summary.append(line)
        elif not in_fence and ENTRY.match(line):
            close()
            current = [line]
        elif current is not None:
            current.append(line)
        elif line.strip():
            # Prose under a type heading before any entry: keep it as its own entry.
            current = [line]
    close()
    text = "\n".join(_strip_blank(summary))
    return (text or None), changes


def parse(markdown: str, source: Source) -> list[Release]:
    """Return the released sections of a Keep a Changelog file, in file order."""
    lines = markdown.removeprefix("\ufeff").replace("\r\n", "\n").replace("\r", "\n").split("\n")
    fenced = _fenced(lines)
    definitions = {}
    for line, in_fence in zip(lines, fenced):
        match = None if in_fence else LINK_DEFINITION.match(line)
        if match:
            definitions[match.group(1).lower()] = _resolve(match.group(2), source)

    body_lines = [
        (line if in_fence or SECTION_HEADING.match(line) else rewrite_links(line, source, definitions), in_fence)
        for line, in_fence in zip(lines, fenced)
        if in_fence or not LINK_DEFINITION.match(line)
    ]

    releases = []
    starts = [i for i, (line, f) in enumerate(body_lines) if not f and SECTION_HEADING.match(line)]
    for index, start in enumerate(starts):
        end = starts[index + 1] if index + 1 < len(starts) else len(body_lines)
        heading = VERSION_HEADING.match(body_lines[start][0])
        if not heading or heading.group(1).lower() == "unreleased":
            continue
        version, date, yanked = heading.group(1), heading.group(2), bool(heading.group(3))
        if not date:
            print(f"warning: {source.repo} {version} has no date, skipped", file=sys.stderr)
            continue
        section = body_lines[start + 1 : end]
        summary, changes = _parse_body([line for line, _ in section], [f for _, f in section])
        releases.append(
            Release(
                component=source.name,
                repo=source.repo,
                version=version,
                date=date,
                yanked=yanked,
                url=definitions.get(version.lower()),
                summary=summary,
                changes=changes,
            )
        )
    return releases


def _is_private(url: str, is_public) -> bool:
    match = GITHUB_REPO.match(url)
    return bool(match) and not is_public(match.group(1))


def strip_private_links(text: str, is_public) -> str:
    """Unlink URLs into non-public GitHub repos. Bare issue references are dropped."""

    def unlink(match: re.Match[str]) -> str:
        label, url = match.group(1), match.group(2)
        if not _is_private(url, is_public):
            return match.group(0)
        return "" if ISSUE_REFERENCE.match(label) else label

    lines = []
    for line in text.split("\n"):
        stripped = MARKDOWN_LINK.sub(unlink, line)
        if line.strip() and not stripped.strip():
            continue
        lines.append(re.sub(r"(?<=\S) {2,}", " ", stripped).rstrip())
    return "\n".join(lines)


def redact(sources: list[Source], releases: list[Release], is_public) -> None:
    """Remove links readers without repo access can't follow."""
    for release in releases:
        if release.url and _is_private(release.url, is_public):
            release.url = None
        if release.summary:
            release.summary = strip_private_links(release.summary, is_public)
        for change in release.changes:
            for entry in change.entries:
                entry.text = strip_private_links(entry.text, is_public)


def merge(per_source: list[list[Release]]) -> list[Release]:
    """Newest date first. Ties keep source order, then file order."""
    releases = [release for releases in per_source for release in releases]
    return sorted(releases, key=lambda release: release.date, reverse=True)


def render_markdown(sources: list[Source], releases: list[Release]) -> str:
    out = [
        "<!-- Generated by griptape-nodes-changelog from each component's CHANGELOG.md. Edit those. -->",
        "",
        "# Griptape Nodes Changelog",
    ]
    for date, group in groupby(releases, key=lambda release: release.date):
        out += ["", f"## {date}"]
        for release in group:
            label = _release_label(release)
            title = f"[{label}]({release.url})" if release.url else label
            out += ["", f"### {title}"]
            if release.summary:
                out += ["", release.summary]
            for change in release.changes:
                out += ["", f"#### {change.type}", ""]
                out += [entry.text for entry in change.entries]
    return "\n".join(out) + "\n"


def _release_label(release: Release) -> str:
    label = f"{release.component} {release.version}"
    return f"{label} [YANKED]" if release.yanked else label


def render_json(sources: list[Source], releases: list[Release]) -> str:
    data = {
        "sources": [source.name for source in sources],
        "releases": [{k: v for k, v in asdict(release).items() if k != "repo"} for release in releases],
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--sources", type=Path, default=ROOT / "sources.toml")
    parser.add_argument("--out-dir", type=Path, default=ROOT)
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    sources = load_sources(args.sources)
    releases = merge([parse(fetch(source, token), source) for source in sources])
    redact(sources, releases, Visibility(token).is_public)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "CHANGELOG.md").write_text(render_markdown(sources, releases), encoding="utf-8")
    (args.out_dir / "changelog.json").write_text(render_json(sources, releases), encoding="utf-8")
    print(f"{len(releases)} releases from {len(sources)} sources")


if __name__ == "__main__":
    main()
