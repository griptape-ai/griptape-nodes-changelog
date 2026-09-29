# Griptape Nodes Changelog

[CHANGELOG.md](CHANGELOG.md) merges the changelogs of every Griptape Nodes component into one
timeline, newest first. [changelog.json](changelog.json) holds the same data for apps and docs,
with each entry flagged `breaking` when it leads with `**Breaking:**`.

Both files are generated. Edit the component changelogs instead.

## Adding a component

Add a `[[source]]` to [sources.toml](sources.toml). The changelog must follow
[Keep a Changelog 2.0.0](https://keepachangelog.com/en/2.0.0/) and the changelog GitHub App must
be installed on the repo.

## How it updates

[aggregate.yml](.github/workflows/aggregate.yml) runs hourly, on manual dispatch, and on a
`changelog-updated` repository dispatch, which a source repo can send after it releases:

```sh
gh api repos/griptape-ai/griptape-nodes-changelog/dispatches -f event_type=changelog-updated
```

It fetches each source from its default branch and commits the output when it changes. It reads
the sources as a GitHub App with Contents: read, set by the `CHANGELOG_APP_ID` variable and the
`CHANGELOG_APP_PRIVATE_KEY` secret.

## Running locally

```sh
python -m unittest discover -s tests
GH_TOKEN=$(gh auth token) python scripts/aggregate.py
```

Python 3.11 or later, standard library only.
