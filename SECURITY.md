# Security

## Reporting

Found something that looks like exposed data or a vulnerability in this
repository? Open an issue, or contact one of the authors directly if the
finding itself is sensitive.

## What this repository deliberately does not contain

**Raw Minecraft server logs.** They are the project's primary measurement
record, and they are not distributed.

A Minecraft server writes a line like the following every time a player
connects:

```
<username>[/<ip-address>:<port>] logged in with entity id 2
```

It also logs each player's UUID. So a raw server log is, incidentally, a record
of the IP address and account identity of everyone who joined — in this case
the four authors, on their home connections. That is personal data belonging to
identifiable people, and it has no bearing on the science.

`data/timeseries.csv` is the published entry point instead. It is derived from
those logs and contains nothing but the measured quantities.

## Incident: raw logs were committed early in the project

This is recorded here because it is the more useful thing to publish.

Early in the project the raw logs were committed to the repository without
anyone considering what they contained. The repository was private throughout,
so the data was never publicly readable, but the logs sat in the git history
for the whole development period.

The problem was found during a pre-publication audit, before the repository was
ever made public.

**Remediation.** The logs were removed from every commit with `git filter-repo`
and the history was rewritten. Two follow-up passes were needed: a first pass
that removed the log files, then a second one after re-running the audit
revealed that infrastructure identifiers were still present in files that had
been *deleted in a later commit* — deleting a file does not remove its content
from history. A third pass removed unrelated third-party contact details found
in the metadata of some included documents. The affected network addresses have
since been rotated independently.

**The lesson worth carrying.** Rotating the exposed addresses was remediation,
not a control. It repaired a past exposure; it does nothing to prevent the next
one. The actual controls are the ones below.

## Controls now in place

| Control | Where |
|---|---|
| `logs/`, `*.log` and `*.log.gz` are gitignored, so raw logs cannot be recommitted | [`.gitignore`](.gitignore) |
| Host, account, key path and container name are read from the environment; none are hardcoded | [`scripts/extract.sh`](scripts/extract.sh), [`.env.example`](.env.example) |
| `.env` is gitignored; `.env.example` carries placeholders only | [`.gitignore`](.gitignore) |
| The parser is tested against synthetic fixtures, so no real log is ever needed to verify it | [`tests/fixtures/`](tests/fixtures/) |
| The constraint is stated where a contributor will actually read it | [`CONTRIBUTING.md`](CONTRIBUTING.md) |

## If you run this pipeline yourself

`scripts/extract.sh` will pull logs from your own server into `logs/`. That
directory is gitignored — leave it that way. Treat anything that directory
touches as containing personal data belonging to whoever used your server, and
publish only derived, numeric data.
