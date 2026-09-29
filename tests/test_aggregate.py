import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from aggregate import Source, merge, parse, render_markdown  # noqa: E402

SOURCE = Source(name="Engine", repo="org/engine", path="docs/CHANGELOG.md")

CHANGELOG = """# Changelog

Intro, see [migration](MIGRATION.md).

## [Unreleased]

### Added

- Not released yet.

## [1.1.0] - 2026-02-01

Short summary.

### Added

- **Breaking:** Thing, see [guide](../MIGRATION.md#step) and [#1].
  Continued line.
- Other thing, see [spec][ref].

```
## [9.9.9] - 2026-01-01
```

### Fixed

- Fix [docs](#top).

## [1.0.0] - 2026-01-01 [YANKED]

### Removed

- Old thing.

## [0.9.0]

### Added

- Undated.

[Unreleased]: https://github.com/org/engine/compare/v1.1.0...HEAD
[1.1.0]: https://github.com/org/engine/compare/v1.0.0...v1.1.0
[#1]: https://github.com/org/engine/issues/1
[ref]: https://example.com/spec
"""


class ParseTest(unittest.TestCase):
    def setUp(self):
        self.releases = parse(CHANGELOG, SOURCE)

    def test_released_dated_sections_only(self):
        self.assertEqual([r.version for r in self.releases], ["1.1.0", "1.0.0"])

    def test_fields(self):
        release = self.releases[0]
        self.assertEqual(release.date, "2026-02-01")
        self.assertEqual(release.url, "https://github.com/org/engine/compare/v1.0.0...v1.1.0")
        self.assertEqual(release.summary, "Short summary.")
        self.assertEqual([c.type for c in release.changes], ["Added", "Fixed"])
        self.assertTrue(self.releases[1].yanked)
        self.assertIsNone(self.releases[1].url)

    def test_entries_and_breaking(self):
        added = self.releases[0].changes[0].entries
        self.assertEqual(len(added), 2)
        self.assertTrue(added[0].breaking)
        self.assertFalse(added[1].breaking)
        self.assertIn("Continued line.", added[0].text)
        self.assertIn("## [9.9.9]", added[1].text)

    def test_links_made_absolute(self):
        added, fixed = (c.entries for c in self.releases[0].changes)
        self.assertIn("(https://github.com/org/engine/blob/HEAD/MIGRATION.md#step)", added[0].text)
        self.assertIn("[#1](https://github.com/org/engine/issues/1)", added[0].text)
        self.assertIn("[spec](https://example.com/spec)", added[1].text)
        self.assertIn("(https://github.com/org/engine/blob/HEAD/docs/CHANGELOG.md#top)", fixed[0].text)


class MergeTest(unittest.TestCase):
    def test_newest_first_ties_keep_source_order(self):
        editor = Source(name="Editor", repo="org/editor")
        other = parse("## [5] - 2026-02-01\n\n### Added\n\n- X.\n", editor)
        merged = merge([parse(CHANGELOG, SOURCE), other])
        self.assertEqual(
            [(r.component, r.version) for r in merged],
            [("Engine", "1.1.0"), ("Editor", "5"), ("Engine", "1.0.0")],
        )


class RenderTest(unittest.TestCase):
    def setUp(self):
        editor = Source(name="Editor", repo="org/editor")
        other = parse("## [5] - 2026-02-01\n\n### Added\n\n- X.\n", editor)
        self.markdown = render_markdown([SOURCE, editor], merge([parse(CHANGELOG, SOURCE), other]))

    def test_releases_grouped_under_date(self):
        headings = [line for line in self.markdown.splitlines() if re.match(r"##+ (?!\[9)", line)]
        self.assertEqual(
            headings,
            [
                "## 2026-02-01",
                "### [Engine 1.1.0](https://github.com/org/engine/compare/v1.0.0...v1.1.0)",
                "#### Added",
                "#### Fixed",
                "### Editor 5",
                "#### Added",
                "## 2026-01-01",
                "### Engine 1.0.0 [YANKED]",
                "#### Removed",
            ],
        )


if __name__ == "__main__":
    unittest.main()
