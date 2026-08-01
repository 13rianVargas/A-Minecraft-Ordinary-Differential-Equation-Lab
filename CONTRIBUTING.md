# Contributing

## Environment

Python 3.11 or newer; developed and verified on 3.14.5.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running the pipeline

The published entry point is the committed time series, so the analysis runs
with no hardware and no network:

```bash
python scripts/analyze.py data/timeseries.csv
```

This rewrites `data/calibration.json`, `data/rms.csv` and all 16 figures under
`figures/`. Output is deterministic — a second run is byte-identical. If a
regenerated file differs from the committed one, that is a real change in
behaviour and needs explaining in the commit message.

To rebuild the report documents:

```bash
python scripts/build_report.py
```

## Tests

```bash
pytest tests/
```

## A note on the raw logs

`scripts/extract.sh` pulls logs from a live Minecraft server, and
`scripts/parse_log.py` turns them into the time series. **Those raw logs are
not distributed and must never be committed.** Minecraft server logs record the
IP address, username and UUID of every player who connects, so publishing them
would expose personal data belonging to third parties. `logs/`, `*.log` and
`*.log.gz` are all gitignored; leave them that way. This is not hypothetical —
see [SECURITY.md](SECURITY.md) for what happened when it was not enforced.

This means the ingestion stage is not reproducible from outside the lab. To
keep it verifiable regardless, `parse_log.py` is tested against synthetic
fixtures in `tests/fixtures/` that reproduce the exact log line formats the
parser matches. **Any change to the parser needs a fixture that covers it** —
do not reach for a real log.

If you do need to run the extraction stage against your own server, copy
`.env.example` to `.env` and fill it in. `.env` is gitignored. Never hardcode a
hostname, account, key path or container name into a script.

## Conventions

- Log filenames follow the pattern documented in
  [docs/FINDINGS.md](docs/FINDINGS.md) section 3.6. The parser derives the
  scenario and replica from the filename, so a wrong name silently corrupts the
  dataset.
- CSV column names stay as they are (`escenario`, `replica`, `t_segundos`, `G`,
  `N`, `K`, `corral`). They are a data schema read by three scripts; renaming
  them is a breaking change, not a cleanup. The schema is documented in English
  in the README.
- Code, comments, docstrings and CLI output are in English. The generated
  `.docx` deliverables are in Spanish, which is intentional — that is the
  language of the report itself.
- Paths resolve from the repository root, derived from the script's own
  location. No absolute paths.

## Where things are documented

| Question | Where |
|---|---|
| What the project is and how to run it | [README.md](README.md) |
| The model, protocol, results, and known defects | [docs/FINDINGS.md](docs/FINDINGS.md) |
| Why the integrator uses `solve_ivp` and not `odeint` | [docs/FINDINGS.md](docs/FINDINGS.md) section 9.8 |
